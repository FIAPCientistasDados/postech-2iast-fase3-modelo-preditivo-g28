"""Treinamento com uso controlado de memória.

Destino sugerido:
    src/modeling/train_models.py

Entradas:
    data/processed/base_analitica_aluno.parquet
    data/processed/base_analitica_municipio.parquet

Principais proteções contra OOM:
    - amostragem do Parquet de alunos por lotes, antes de criar um DataFrame total;
    - ``--amostra`` limita busca, OOF, backtest e ajuste final do aluno;
    - one-hot encoding esparso em float32;
    - busca e estimadores com uma única thread por padrão;
    - apenas três folds OOF para aluno;
    - remoção de features completamente nulas no recorte de treino.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Limita bibliotecas numéricas antes de importar NumPy/scikit-learn.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.evaluation.classification_metrics import (
    avaliar_classificacao,
    avaliar_regressao,
    risco_de_nao_atingir,
)
from src.evaluation.model_validation import (
    validar_por_grupos,
    validar_regressao_por_grupos,
)
from src.modeling.model_registry import SEED, classificadores, regressores

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

ALUNO_PATH = PROCESSED_DIR / "base_analitica_aluno.parquet"
MUNICIPIO_PATH = PROCESSED_DIR / "base_analitica_municipio.parquet"

TARGET_ALUNO = "alfabetizado"
TARGET_MUNICIPIO_REGRESSAO = "indicador_t"
TARGET_MUNICIPIO_CLASSIFICACAO = "atingiu_meta_t"

EXCLUIR_ALUNO = {
    TARGET_ALUNO,
    "id_aluno",
    "id_escola",
    "id_municipio",
    "proficiencia",
    "indicador_t",
    "atingiu_meta_t",
    "gap_meta_t",
    "_gold_processed_at",
}

EXCLUIR_MUNICIPIO = {
    TARGET_MUNICIPIO_REGRESSAO,
    TARGET_MUNICIPIO_CLASSIFICACAO,
    "gap_meta_t",
    "id_municipio",
    "nome_municipio",
    "_gold_processed_at",
}


def _normalizar_chave_estrato(valor) -> str:
    if pd.isna(valor):
        return "<NA>"
    return str(valor)


def _alocar_amostra_por_estrato(
    contagens: Counter,
    tamanho_amostra: int,
) -> dict[tuple[str, str], int]:
    """Distribui a amostra proporcionalmente por ano e target."""
    total = sum(contagens.values())
    if tamanho_amostra >= total:
        return dict(contagens)

    quotas_reais = {
        chave: tamanho_amostra * quantidade / total
        for chave, quantidade in contagens.items()
    }
    alocacao = {
        chave: min(quantidade, int(np.floor(quotas_reais[chave])))
        for chave, quantidade in contagens.items()
    }

    # Preserva todos os estratos quando o tamanho permite.
    if tamanho_amostra >= len(contagens):
        for chave, quantidade in contagens.items():
            if quantidade > 0 and alocacao[chave] == 0:
                alocacao[chave] = 1

    restante = tamanho_amostra - sum(alocacao.values())
    ordem = sorted(
        contagens,
        key=lambda chave: quotas_reais[chave] - np.floor(quotas_reais[chave]),
        reverse=True,
    )

    while restante > 0:
        alterou = False
        for chave in ordem:
            if alocacao[chave] < contagens[chave]:
                alocacao[chave] += 1
                restante -= 1
                alterou = True
                if restante == 0:
                    break
        if not alterou:
            break

    return alocacao


def ler_amostra_aluno_parquet(
    caminho: Path,
    n: int | None,
    seed: int = SEED,
    batch_size: int = 20_000,
) -> pd.DataFrame:
    """Lê uma amostra estratificada sem carregar o Parquet inteiro.

    O primeiro passe lê somente ``ano`` e ``alfabetizado`` para contar os
    estratos. O segundo passe seleciona exatamente a quantidade alocada em cada
    estrato usando distribuição hipergeométrica por lote.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Base de aluno não encontrada: {caminho}")

    parquet = pq.ParquetFile(caminho)
    total_linhas = parquet.metadata.num_rows

    if n is None or n <= 0:
        raise ValueError(
            "Informe --amostra com um limite positivo. "
            "A leitura integral foi desabilitada para proteger a memória."
        )

    n = min(int(n), int(total_linhas))
    print(f"[aluno] Parquet: {total_linhas:,} linhas; limite solicitado: {n:,}.")

    contagens: Counter = Counter()
    for batch in parquet.iter_batches(
        columns=["ano", TARGET_ALUNO],
        batch_size=batch_size,
        use_threads=False,
    ):
        pequeno = batch.to_pandas()
        pequeno = pequeno.dropna(subset=[TARGET_ALUNO])
        for chave, quantidade in pequeno.groupby(
            ["ano", TARGET_ALUNO],
            dropna=False,
            observed=True,
        ).size().items():
            estrato = (
                _normalizar_chave_estrato(chave[0]),
                _normalizar_chave_estrato(chave[1]),
            )
            contagens[estrato] += int(quantidade)

    if not contagens:
        raise ValueError("Não há linhas com target de aluno observado no Parquet.")

    alocacao = _alocar_amostra_por_estrato(contagens, n)
    restantes_total = dict(contagens)
    restantes_amostra = dict(alocacao)
    rng = np.random.default_rng(seed)
    partes: list[pd.DataFrame] = []

    for batch in parquet.iter_batches(
        batch_size=batch_size,
        use_threads=False,
    ):
        lote = batch.to_pandas()
        lote = lote.dropna(subset=[TARGET_ALUNO])

        for chave, grupo in lote.groupby(
            ["ano", TARGET_ALUNO],
            dropna=False,
            observed=True,
            sort=False,
        ):
            estrato = (
                _normalizar_chave_estrato(chave[0]),
                _normalizar_chave_estrato(chave[1]),
            )
            disponivel_lote = len(grupo)
            disponivel_futuro = restantes_total[estrato]
            necessario = restantes_amostra[estrato]

            if necessario <= 0:
                quantidade = 0
            elif necessario >= disponivel_futuro:
                quantidade = disponivel_lote
            else:
                quantidade = int(
                    rng.hypergeometric(
                        ngood=necessario,
                        nbad=disponivel_futuro - necessario,
                        nsample=disponivel_lote,
                    )
                )

            if quantidade > 0:
                indices = rng.choice(
                    grupo.index.to_numpy(),
                    size=quantidade,
                    replace=False,
                )
                partes.append(lote.loc[indices].copy())

            restantes_total[estrato] -= disponivel_lote
            restantes_amostra[estrato] -= quantidade

        del lote

    if not partes:
        raise ValueError("A amostragem não selecionou nenhuma linha.")

    amostra = pd.concat(partes, ignore_index=True)
    if len(amostra) != sum(alocacao.values()):
        raise RuntimeError(
            f"Amostra incompleta: esperado={sum(alocacao.values())}, "
            f"obtido={len(amostra)}."
        )

    amostra = amostra.sample(frac=1, random_state=seed).reset_index(drop=True)
    memoria_mb = amostra.memory_usage(deep=True).sum() / 1024**2
    print(
        f"[aluno] Amostra carregada: {len(amostra):,} linhas x "
        f"{amostra.shape[1]} colunas; {memoria_mb:.1f} MB."
    )
    print(
        "[aluno] Distribuição por ano e target:\n"
        + amostra.groupby(["ano", TARGET_ALUNO], observed=True).size().to_string()
    )
    return amostra


def _one_hot_encoder() -> OneHotEncoder:
    """One-hot esparso e em float32 para reduzir uso de memória."""
    parametros = {
        "handle_unknown": "ignore",
        "dtype": np.float32,
    }
    try:
        return OneHotEncoder(
            sparse_output=True,
            min_frequency=10,
            **parametros,
        )
    except TypeError:
        return OneHotEncoder(
            sparse=True,
            **parametros,
        )


def separar_features(
    df: pd.DataFrame,
    target: str,
    excluir: set[str],
    colunas_features: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """Cria X e y; no treino remove colunas totalmente nulas."""
    if target not in df.columns:
        raise KeyError(f"Target ausente: {target}")

    dados = df.dropna(subset=[target]).copy()
    y = dados[target]

    if colunas_features is None:
        candidatas = [c for c in dados.columns if c not in excluir]
        totalmente_nulas = [c for c in candidatas if dados[c].isna().all()]
        if totalmente_nulas:
            print(
                "[features] Removendo colunas totalmente nulas: "
                f"{totalmente_nulas}"
            )
        colunas_features = [c for c in candidatas if c not in totalmente_nulas]
    else:
        faltantes = [c for c in colunas_features if c not in dados.columns]
        if faltantes:
            raise KeyError(f"Features ausentes no DataFrame: {faltantes}")

    x = dados[colunas_features].copy()
    categoricas = x.select_dtypes(
        include=["object", "string", "category", "bool", "boolean"]
    ).columns
    for coluna in categoricas:
        x[coluna] = x[coluna].astype("string")

    return x, y


def construir_pipeline(x: pd.DataFrame, estimador: object) -> Pipeline:
    categoricas = list(
        x.select_dtypes(
            include=["object", "string", "category", "bool", "boolean"]
        ).columns
    )
    numericas = [c for c in x.columns if c not in categoricas]

    transformadores = []
    if numericas:
        transformadores.append(
            (
                "num",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="median",
                                add_indicator=True,
                                keep_empty_features=False,
                            ),
                        ),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numericas,
            )
        )

    if categoricas:
        transformadores.append(
            (
                "cat",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="most_frequent",
                                keep_empty_features=False,
                            ),
                        ),
                        ("onehot", _one_hot_encoder()),
                    ]
                ),
                categoricas,
            )
        )

    if not transformadores:
        raise ValueError("Nenhuma feature disponível para construir o pipeline.")

    prep = ColumnTransformer(
        transformers=transformadores,
        remainder="drop",
        sparse_threshold=1.0,
        verbose_feature_names_out=True,
        n_jobs=1,
    )
    return Pipeline([("prep", prep), ("modelo", estimador)])


def amostra_estratificada_memoria(
    df: pd.DataFrame,
    n: int | None,
    target: str,
) -> pd.DataFrame:
    """Reduz um DataFrame já amostrado, preservando ano e target."""
    if n is None or len(df) <= n:
        return df.copy()

    partes = []
    for _, grupo in df.groupby(["ano", target], observed=True, dropna=False):
        quantidade = max(1, int(round(n * len(grupo) / len(df))))
        quantidade = min(quantidade, len(grupo))
        partes.append(grupo.sample(n=quantidade, random_state=SEED))

    saida = pd.concat(partes, ignore_index=True)
    if len(saida) > n:
        saida = saida.sample(n=n, random_state=SEED)
    return saida.sample(frac=1, random_state=SEED).reset_index(drop=True)


def buscar_hiperparametros(
    pipeline: Pipeline,
    distribuicoes: dict,
    x: pd.DataFrame,
    y,
    grupos,
    n_iter: int,
    scoring: str,
    n_splits: int = 3,
) -> RandomizedSearchCV:
    n_grupos = pd.Series(grupos).nunique(dropna=True)
    splits = min(n_splits, n_grupos)
    if splits < 2:
        raise ValueError("São necessários pelo menos dois municípios.")

    busca = RandomizedSearchCV(
        pipeline,
        distribuicoes,
        n_iter=n_iter,
        scoring=scoring,
        cv=GroupKFold(n_splits=splits),
        random_state=SEED,
        n_jobs=1,
        pre_dispatch=1,
        refit=True,
        return_train_score=False,
        error_score="raise",
        verbose=1,
    )
    busca.fit(x, y, groups=grupos)
    return busca


def resumo_busca(busca: RandomizedSearchCV) -> pd.DataFrame:
    resultados = pd.DataFrame(busca.cv_results_)
    parametros = [c for c in resultados if c.startswith("param_")]
    colunas = parametros + [
        "mean_test_score",
        "std_test_score",
        "rank_test_score",
    ]
    saida = resultados[colunas].copy()
    saida.columns = [c.replace("param_modelo__", "") for c in saida.columns]
    return saida.sort_values("rank_test_score").reset_index(drop=True)


def salvar_modelo(pipeline: Pipeline, nome: str, metadados: dict) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = MODELS_DIR / f"{nome}.joblib"
    joblib.dump(pipeline, caminho, compress=3)

    meta = dict(metadados)
    meta["salvo_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta["arquivo_modelo"] = caminho.name
    (MODELS_DIR / f"{nome}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return caminho


def _anos_observados(df: pd.DataFrame, coluna_ano: str, target: str) -> list[int]:
    return sorted(
        pd.to_numeric(
            df.loc[df[target].notna(), coluna_ano],
            errors="coerce",
        )
        .dropna()
        .astype(int)
        .unique()
    )


def treinar_aluno(
    modelo: str = "logistic_regression",
    n_iter: int = 1,
    amostra: int = 5_000,
) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    base = ler_amostra_aluno_parquet(ALUNO_PATH, n=amostra)
    anos = _anos_observados(base, "ano", TARGET_ALUNO)
    if not anos:
        raise ValueError("A amostra de aluno não possui target observado.")

    catalogo = classificadores(n_jobs=1)
    if modelo not in catalogo:
        raise KeyError(f"Modelo '{modelo}' indisponível. Opções: {sorted(catalogo)}")
    estimador, distribuicoes = catalogo[modelo]

    ano_teste = anos[-1] if len(anos) >= 2 else None
    if ano_teste is not None:
        treino = base[base["ano"] < ano_teste].copy()
        teste = base[base["ano"] == ano_teste].copy()
        if treino.empty or teste.empty:
            ano_teste = None
            treino = base.copy()
            teste = None
    else:
        treino = base.copy()
        teste = None

    busca_df = amostra_estratificada_memoria(
        treino.dropna(subset=[TARGET_ALUNO]),
        n=min(amostra, len(treino)),
        target=TARGET_ALUNO,
    )
    x_busca, y_busca = separar_features(
        busca_df,
        TARGET_ALUNO,
        EXCLUIR_ALUNO,
    )
    features = list(x_busca.columns)
    pipeline = construir_pipeline(x_busca, estimador)

    busca = buscar_hiperparametros(
        pipeline=pipeline,
        distribuicoes=distribuicoes,
        x=x_busca,
        y=y_busca.astype(int),
        grupos=busca_df.loc[x_busca.index, "id_municipio"],
        n_iter=max(1, n_iter),
        scoring="roc_auc",
        n_splits=3,
    )

    # OOF apenas no recorte de treino já limitado por --amostra.
    x_treino, y_treino = separar_features(
        treino,
        TARGET_ALUNO,
        EXCLUIR_ALUNO,
        colunas_features=features,
    )
    grupos_treino = treino.loc[x_treino.index, "id_municipio"]
    n_splits_oof = min(3, grupos_treino.nunique(dropna=True))
    if n_splits_oof < 2:
        raise ValueError("Poucos municípios para validação OOF do aluno.")

    metricas_folds, oof = validar_por_grupos(
        clone(busca.best_estimator_),
        x_treino,
        y_treino.astype(int),
        grupos_treino,
        n_splits=n_splits_oof,
    )
    saida_oof = treino.loc[
        x_treino.index,
        ["ano", "id_aluno", "id_municipio", TARGET_ALUNO],
    ].copy()
    saida_oof["probabilidade_alfabetizado"] = oof
    saida_oof.to_parquet(
        MODELS_DIR / "modelo_aluno_oof.parquet",
        index=False,
        compression="zstd",
    )

    backtest = None
    if teste is not None and not teste.empty:
        modelo_backtest = clone(busca.best_estimator_)
        modelo_backtest.fit(x_treino, y_treino.astype(int))
        x_teste, y_teste = separar_features(
            teste,
            TARGET_ALUNO,
            EXCLUIR_ALUNO,
            colunas_features=features,
        )
        proba = modelo_backtest.predict_proba(x_teste)[:, 1]
        backtest = avaliar_classificacao(y_teste.astype(int), proba)
        saida = teste.loc[
            x_teste.index,
            ["ano", "id_aluno", "id_municipio", TARGET_ALUNO],
        ].copy()
        saida["probabilidade_alfabetizado"] = proba
        saida.to_parquet(
            MODELS_DIR / f"modelo_aluno_backtest_{ano_teste}.parquet",
            index=False,
            compression="zstd",
        )

    # Ajuste final apenas na amostra lida, nunca no Parquet inteiro.
    x_final, y_final = separar_features(
        base,
        TARGET_ALUNO,
        EXCLUIR_ALUNO,
        colunas_features=features,
    )
    parametros = {
        chave.replace("modelo__", ""): valor
        for chave, valor in busca.best_params_.items()
    }
    estimador_final = clone(estimador).set_params(**parametros)
    final = construir_pipeline(x_final, estimador_final)
    final.fit(x_final, y_final.astype(int))

    metadados = {
        "tipo": "classificacao",
        "alvo": TARGET_ALUNO,
        "classe_de_interesse_publica": 0,
        "modelo": modelo,
        "amostra_maxima": int(amostra),
        "linhas_treino_final": int(len(x_final)),
        "anos_observados": anos,
        "ano_backtest": ano_teste,
        "melhores_hiperparametros": busca.best_params_,
        "auc_cv_busca": float(busca.best_score_),
        "backtest": backtest,
        "features": features,
        "chave_grupo_validacao": "id_municipio",
    }
    salvar_modelo(final, "modelo_aluno", metadados)
    resumo_busca(busca).to_csv(
        MODELS_DIR / "modelo_aluno_busca.csv",
        index=False,
    )
    metricas_folds.to_csv(
        MODELS_DIR / "modelo_aluno_folds.csv",
        index=False,
    )
    print(
        f"[modelo aluno] {modelo} | AUC CV={busca.best_score_:.3f} "
        f"| backtest={backtest}"
    )
    return metadados


def treinar_municipio(
    modelo: str = "ridge",
    n_iter: int = 5,
) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not MUNICIPIO_PATH.exists():
        raise FileNotFoundError(f"Base municipal não encontrada: {MUNICIPIO_PATH}")

    base = pd.read_parquet(MUNICIPIO_PATH)
    anos = _anos_observados(base, "ano_alvo", TARGET_MUNICIPIO_REGRESSAO)
    if not anos:
        raise ValueError("A base municipal não possui indicador_t observado.")

    catalogo = regressores(n_jobs=1)
    if modelo not in catalogo:
        raise KeyError(f"Modelo '{modelo}' indisponível. Opções: {sorted(catalogo)}")
    estimador, distribuicoes = catalogo[modelo]

    ano_teste = anos[-1] if len(anos) >= 2 else None
    if ano_teste is not None:
        treino = base[base["ano_alvo"] < ano_teste].copy()
        teste = base[base["ano_alvo"] == ano_teste].copy()
        if treino.empty or teste.empty:
            ano_teste = None
            treino = base.copy()
            teste = None
    else:
        treino = base.copy()
        teste = None

    x_treino, y_treino = separar_features(
        treino,
        TARGET_MUNICIPIO_REGRESSAO,
        EXCLUIR_MUNICIPIO,
    )
    features = list(x_treino.columns)
    pipeline = construir_pipeline(x_treino, estimador)
    busca = buscar_hiperparametros(
        pipeline=pipeline,
        distribuicoes=distribuicoes,
        x=x_treino,
        y=y_treino.astype(float),
        grupos=treino.loc[x_treino.index, "id_municipio"],
        n_iter=max(1, n_iter),
        scoring="neg_mean_absolute_error",
        n_splits=5,
    )

    grupos_treino = treino.loc[x_treino.index, "id_municipio"]
    n_splits_oof = min(5, grupos_treino.nunique(dropna=True))
    metricas_folds, oof = validar_regressao_por_grupos(
        busca.best_estimator_,
        x_treino,
        y_treino,
        grupos_treino,
        n_splits=n_splits_oof,
    )
    residuos = y_treino.to_numpy(dtype=float) - oof

    colunas_saida = [
        "ano_alvo",
        "id_municipio",
        TARGET_MUNICIPIO_REGRESSAO,
        "meta_t",
        TARGET_MUNICIPIO_CLASSIFICACAO,
    ]
    if "rede" in treino.columns:
        colunas_saida.insert(2, "rede")

    saida_oof = treino.loc[x_treino.index, colunas_saida].copy()
    saida_oof["indicador_previsto"] = oof
    saida_oof["risco_nao_atingir"] = risco_de_nao_atingir(
        oof,
        saida_oof["meta_t"],
        residuos,
    )
    saida_oof.to_parquet(
        MODELS_DIR / "modelo_municipio_oof.parquet",
        index=False,
        compression="zstd",
    )

    backtest = None
    if teste is not None and not teste.empty:
        x_teste, y_teste = separar_features(
            teste,
            TARGET_MUNICIPIO_REGRESSAO,
            EXCLUIR_MUNICIPIO,
            colunas_features=features,
        )
        pred = busca.best_estimator_.predict(x_teste)
        backtest = avaliar_regressao(y_teste, pred)
        risco = risco_de_nao_atingir(
            pred,
            teste.loc[x_teste.index, "meta_t"],
            residuos,
        )
        saida = teste.loc[x_teste.index, colunas_saida].copy()
        saida["indicador_previsto"] = pred
        saida["risco_nao_atingir"] = risco
        saida.to_parquet(
            MODELS_DIR / f"modelo_municipio_backtest_{ano_teste}.parquet",
            index=False,
            compression="zstd",
        )

    x_final, y_final = separar_features(
        base,
        TARGET_MUNICIPIO_REGRESSAO,
        EXCLUIR_MUNICIPIO,
        colunas_features=features,
    )
    parametros = {
        chave.replace("modelo__", ""): valor
        for chave, valor in busca.best_params_.items()
    }
    estimador_final = clone(estimador).set_params(**parametros)
    final = construir_pipeline(x_final, estimador_final)

    grupos_final = base.loc[x_final.index, "id_municipio"]
    _, oof_final = validar_regressao_por_grupos(
        final,
        x_final,
        y_final,
        grupos_final,
        n_splits=min(5, grupos_final.nunique(dropna=True)),
    )
    residuos_final = y_final.to_numpy(dtype=float) - oof_final
    final.fit(x_final, y_final.astype(float))

    metadados = {
        "tipo": "regressao_com_risco_derivado",
        "alvo_modelado": TARGET_MUNICIPIO_REGRESSAO,
        "alvo_operacional": "risco de não atingir meta_t",
        "modelo": modelo,
        "anos_observados": anos,
        "ano_backtest": ano_teste,
        "melhores_hiperparametros": busca.best_params_,
        "mae_cv_busca": float(-busca.best_score_),
        "backtest": backtest,
        "features": features,
        "chave_grupo_validacao": "id_municipio",
        "residuos_validacao": [float(v) for v in residuos_final],
    }
    salvar_modelo(final, "modelo_municipio", metadados)
    resumo_busca(busca).to_csv(
        MODELS_DIR / "modelo_municipio_busca.csv",
        index=False,
    )
    metricas_folds.to_csv(
        MODELS_DIR / "modelo_municipio_folds.csv",
        index=False,
    )
    print(
        f"[modelo município] {modelo} | MAE CV={-busca.best_score_:.3f} "
        f"| backtest={backtest}"
    )
    return metadados


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Treina modelos com uso controlado de memória."
    )
    parser.add_argument(
        "--alvo",
        choices=["aluno", "municipio", "todos"],
        default="todos",
    )
    parser.add_argument(
        "--modelo-aluno",
        default="logistic_regression",
    )
    parser.add_argument(
        "--modelo-municipio",
        default="ridge",
    )
    parser.add_argument(
        "--n-iter",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--amostra",
        type=int,
        default=5_000,
        help="Limite total de linhas do modelo de aluno.",
    )
    args = parser.parse_args()

    if args.alvo in ("aluno", "todos"):
        treinar_aluno(
            modelo=args.modelo_aluno,
            n_iter=max(1, args.n_iter),
            amostra=args.amostra,
        )
    if args.alvo in ("municipio", "todos"):
        treinar_municipio(
            modelo=args.modelo_municipio,
            n_iter=max(1, args.n_iter),
        )


if __name__ == "__main__":
    main()
