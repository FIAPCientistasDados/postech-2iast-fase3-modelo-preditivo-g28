"""Treinamento dos modelos de aluno e municipio.

Arquivo sugerido: src/modeling/train_models.py

Entradas:
    data/processed/base_analitica_aluno.parquet
    data/processed/base_analitica_municipio.parquet

Saidas:
    models/modelo_aluno.joblib
    models/modelo_aluno.json
    models/modelo_aluno_oof.parquet
    models/modelo_aluno_backtest_<ano>.parquet, quando houver dois anos
    models/modelo_municipio.joblib
    models/modelo_municipio.json
    models/modelo_municipio_oof.parquet
    models/modelo_municipio_backtest_<ano>.parquet, quando houver dois anos

O pipeline salvo inclui preprocessamento e estimador. Identificadores, nomes e
alvos contemporaneos sao removidos das features. A validacao agrupa por
municipio para evitar que o mesmo municipio apareca simultaneamente no treino e
na validacao.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.evaluation.metricas import avaliar_classificacao, avaliar_regressao, risco_de_nao_atingir
from src.evaluation.validacao import validar_por_grupos, validar_regressao_por_grupos
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
    "id_aluno", "id_escola", "id_municipio",
    "proficiencia", "indicador_t", "atingiu_meta_t", "gap_meta_t",
    "_gold_processed_at",
}

EXCLUIR_MUNICIPIO = {
    TARGET_MUNICIPIO_REGRESSAO,
    TARGET_MUNICIPIO_CLASSIFICACAO,
    "gap_meta_t", "id_municipio", "nome_municipio",
    "_gold_processed_at",
}


def _one_hot_encoder() -> OneHotEncoder:
    """Compatibilidade entre versoes recentes e antigas do scikit-learn."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def separar_features(df: pd.DataFrame, target: str, excluir: set[str]) -> tuple[pd.DataFrame, pd.Series]:
    dados = df.dropna(subset=[target]).copy()
    y = dados[target]
    colunas = [c for c in dados.columns if c not in excluir]
    x = dados[colunas].copy()

    # Evita objetos arbitrarios no ColumnTransformer.
    categoricas = x.select_dtypes(include=["object", "string", "category", "bool", "boolean"]).columns
    for coluna in categoricas:
        x[coluna] = x[coluna].astype("string")
    return x, y


def construir_pipeline(x: pd.DataFrame, estimador: object) -> Pipeline:
    categoricas = list(x.select_dtypes(include=["object", "string", "category", "bool", "boolean"]).columns)
    numericas = [c for c in x.columns if c not in categoricas]

    transformadores = []
    if numericas:
        transformadores.append((
            "num",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scaler", StandardScaler()),
            ]),
            numericas,
        ))
    if categoricas:
        transformadores.append((
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", _one_hot_encoder()),
            ]),
            categoricas,
        ))

    prep = ColumnTransformer(transformadores=transformadores, remainder="drop", verbose_feature_names_out=True)
    return Pipeline([("prep", prep), ("modelo", estimador)])


def amostra_estratificada(df: pd.DataFrame, n: int | None, target: str, seed: int = SEED) -> pd.DataFrame:
    if not n or len(df) <= n:
        return df.copy()
    fracoes = df[target].value_counts(normalize=True, dropna=False)
    partes = []
    for valor, fracao in fracoes.items():
        grupo = df[df[target] == valor]
        tamanho = max(1, min(len(grupo), int(round(n * fracao))))
        partes.append(grupo.sample(tamanho, random_state=seed))
    return pd.concat(partes).sample(frac=1, random_state=seed).reset_index(drop=True)


def buscar_hiperparametros(pipeline: Pipeline, distribuicoes: dict, x: pd.DataFrame, y, grupos, n_iter: int, scoring: str, n_splits: int = 5, n_jobs: int = -1) -> RandomizedSearchCV:
    n_grupos = pd.Series(grupos).nunique()
    splits = min(n_splits, n_grupos)
    if splits < 2:
        raise ValueError("Sao necessarios pelo menos dois municipios para a busca.")
    busca = RandomizedSearchCV(
        pipeline,
        distribuicoes,
        n_iter=n_iter,
        scoring=scoring,
        cv=GroupKFold(n_splits=splits),
        random_state=SEED,
        n_jobs=n_jobs,
        refit=True,
        return_train_score=True,
        error_score="raise",
    )
    busca.fit(x, y, groups=grupos)
    return busca


def resumo_busca(busca: RandomizedSearchCV) -> pd.DataFrame:
    resultados = pd.DataFrame(busca.cv_results_)
    parametros = [c for c in resultados if c.startswith("param_")]
    colunas = parametros + ["mean_train_score", "mean_test_score", "std_test_score", "rank_test_score"]
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
    return sorted(pd.to_numeric(df.loc[df[target].notna(), coluna_ano], errors="coerce").dropna().astype(int).unique())


def treinar_aluno(modelo: str = "random_forest", n_iter: int = 10, amostra: int | None = 300_000) -> dict:
    base = pd.read_parquet(ALUNO_PATH)
    anos = _anos_observados(base, "ano", TARGET_ALUNO)
    if not anos:
        raise ValueError("A base de aluno nao possui target observado.")

    catalogo = classificadores(n_jobs=-1)
    if modelo not in catalogo:
        raise KeyError(f"Modelo '{modelo}' indisponivel. Opcoes: {sorted(catalogo)}")
    estimador, distribuicoes = catalogo[modelo]

    # Se houver dois anos ou mais, o mais recente e reservado ao backtest.
    ano_teste = anos[-1] if len(anos) >= 2 else None
    treino = base[base["ano"] < ano_teste].copy() if ano_teste is not None else base.copy()
    teste = base[base["ano"] == ano_teste].copy() if ano_teste is not None else None

    busca_df = amostra_estratificada(treino.dropna(subset=[TARGET_ALUNO]), amostra, TARGET_ALUNO)
    x_busca, y_busca = separar_features(busca_df, TARGET_ALUNO, EXCLUIR_ALUNO)
    pipeline = construir_pipeline(x_busca, estimador)
    busca = buscar_hiperparametros(
        pipeline, distribuicoes, x_busca, y_busca.astype(int),
        busca_df.loc[x_busca.index, "id_municipio"],
        n_iter=n_iter, scoring="roc_auc", n_splits=3, n_jobs=1,
    )

    x_treino, y_treino = separar_features(treino, TARGET_ALUNO, EXCLUIR_ALUNO)
    final = clone(busca.best_estimator_)

    n_splits_oof = min(5, treino["id_municipio"].nunique())
    metricas_folds, oof = validar_por_grupos(
        final, x_treino, y_treino.astype(int), treino.loc[x_treino.index, "id_municipio"],
        n_splits=n_splits_oof,
    )
    saida_oof = treino.loc[x_treino.index, ["ano", "id_aluno", "id_municipio", TARGET_ALUNO]].copy()
    saida_oof["probabilidade_alfabetizado"] = oof
    saida_oof.to_parquet(MODELS_DIR / "modelo_aluno_oof.parquet", index=False, compression="zstd")

    backtest = None
    if teste is not None and not teste.empty:
        final.fit(x_treino, y_treino.astype(int))
        x_teste, y_teste = separar_features(teste, TARGET_ALUNO, EXCLUIR_ALUNO)
        x_teste = x_teste.reindex(columns=x_treino.columns)
        proba = final.predict_proba(x_teste)[:, 1]
        backtest = avaliar_classificacao(y_teste.astype(int), proba)
        saida = teste.loc[x_teste.index, ["ano", "id_aluno", "id_municipio", TARGET_ALUNO]].copy()
        saida["probabilidade_alfabetizado"] = proba
        saida.to_parquet(MODELS_DIR / f"modelo_aluno_backtest_{ano_teste}.parquet", index=False, compression="zstd")

    # Ajuste final em todos os anos observados.
    x_final, y_final = separar_features(base, TARGET_ALUNO, EXCLUIR_ALUNO)
    final = construir_pipeline(x_final, clone(estimador).set_params(**{
        k.replace("modelo__", ""): v for k, v in busca.best_params_.items()
    }))
    final.fit(x_final, y_final.astype(int))

    meta = {
        "tipo": "classificacao",
        "alvo": TARGET_ALUNO,
        "classe_de_interesse_publica": 0,
        "modelo": modelo,
        "anos_observados": anos,
        "ano_backtest": ano_teste,
        "melhores_hiperparametros": busca.best_params_,
        "auc_cv_busca": float(busca.best_score_),
        "backtest": backtest,
        "features": list(x_final.columns),
        "chave_grupo_validacao": "id_municipio",
    }
    salvar_modelo(final, "modelo_aluno", meta)
    resumo_busca(busca).to_csv(MODELS_DIR / "modelo_aluno_busca.csv", index=False)
    metricas_folds.to_csv(MODELS_DIR / "modelo_aluno_folds.csv", index=False)
    print(f"[modelo aluno] {modelo} | AUC CV={busca.best_score_:.3f} | backtest={backtest}")
    return meta


def treinar_municipio(modelo: str = "random_forest", n_iter: int = 20) -> dict:
    base = pd.read_parquet(MUNICIPIO_PATH)
    anos = _anos_observados(base, "ano_alvo", TARGET_MUNICIPIO_REGRESSAO)
    if not anos:
        raise ValueError("A base municipal nao possui indicador_t observado.")

    catalogo = regressores(n_jobs=1)
    if modelo not in catalogo:
        raise KeyError(f"Modelo '{modelo}' indisponivel. Opcoes: {sorted(catalogo)}")
    estimador, distribuicoes = catalogo[modelo]

    ano_teste = anos[-1] if len(anos) >= 2 else None
    treino = base[base["ano_alvo"] < ano_teste].copy() if ano_teste is not None else base.copy()
    teste = base[base["ano_alvo"] == ano_teste].copy() if ano_teste is not None else None

    x_treino, y_treino = separar_features(treino, TARGET_MUNICIPIO_REGRESSAO, EXCLUIR_MUNICIPIO)
    pipeline = construir_pipeline(x_treino, estimador)
    busca = buscar_hiperparametros(
        pipeline, distribuicoes, x_treino, y_treino.astype(float),
        treino.loc[x_treino.index, "id_municipio"],
        n_iter=n_iter, scoring="neg_mean_absolute_error", n_splits=5, n_jobs=-1,
    )

    n_splits_oof = min(5, treino["id_municipio"].nunique())
    metricas_folds, oof = validar_regressao_por_grupos(
        busca.best_estimator_, x_treino, y_treino,
        treino.loc[x_treino.index, "id_municipio"], n_splits=n_splits_oof,
    )
    residuos = y_treino.to_numpy(dtype=float) - oof
    saida_oof = treino.loc[x_treino.index, ["ano_alvo", "id_municipio", "rede", TARGET_MUNICIPIO_REGRESSAO, "meta_t", TARGET_MUNICIPIO_CLASSIFICACAO]].copy()
    saida_oof["indicador_previsto"] = oof
    saida_oof["risco_nao_atingir"] = risco_de_nao_atingir(oof, saida_oof["meta_t"], residuos)
    saida_oof.to_parquet(MODELS_DIR / "modelo_municipio_oof.parquet", index=False, compression="zstd")

    backtest = None
    if teste is not None and not teste.empty:
        x_teste, y_teste = separar_features(teste, TARGET_MUNICIPIO_REGRESSAO, EXCLUIR_MUNICIPIO)
        x_teste = x_teste.reindex(columns=x_treino.columns)
        pred = busca.best_estimator_.predict(x_teste)
        backtest = avaliar_regressao(y_teste, pred)
        risco = risco_de_nao_atingir(pred, teste.loc[x_teste.index, "meta_t"], residuos)
        saida = teste.loc[x_teste.index, ["ano_alvo", "id_municipio", "rede", TARGET_MUNICIPIO_REGRESSAO, "meta_t", TARGET_MUNICIPIO_CLASSIFICACAO]].copy()
        saida["indicador_previsto"] = pred
        saida["risco_nao_atingir"] = risco
        saida.to_parquet(MODELS_DIR / f"modelo_municipio_backtest_{ano_teste}.parquet", index=False, compression="zstd")

    x_final, y_final = separar_features(base, TARGET_MUNICIPIO_REGRESSAO, EXCLUIR_MUNICIPIO)
    final = construir_pipeline(x_final, clone(estimador).set_params(**{
        k.replace("modelo__", ""): v for k, v in busca.best_params_.items()
    }))
    _, oof_final = validar_regressao_por_grupos(
        final, x_final, y_final, base.loc[x_final.index, "id_municipio"],
        n_splits=min(5, base.loc[x_final.index, "id_municipio"].nunique()),
    )
    residuos_final = y_final.to_numpy(dtype=float) - oof_final
    final.fit(x_final, y_final.astype(float))

    meta = {
        "tipo": "regressao_com_risco_derivado",
        "alvo_modelado": TARGET_MUNICIPIO_REGRESSAO,
        "alvo_operacional": "risco de nao atingir meta_t",
        "modelo": modelo,
        "anos_observados": anos,
        "ano_backtest": ano_teste,
        "melhores_hiperparametros": busca.best_params_,
        "mae_cv_busca": float(-busca.best_score_),
        "backtest": backtest,
        "features": list(x_final.columns),
        "chave_grupo_validacao": "id_municipio",
        "residuos_validacao": [float(v) for v in residuos_final],
    }
    salvar_modelo(final, "modelo_municipio", meta)
    resumo_busca(busca).to_csv(MODELS_DIR / "modelo_municipio_busca.csv", index=False)
    metricas_folds.to_csv(MODELS_DIR / "modelo_municipio_folds.csv", index=False)
    print(f"[modelo municipio] {modelo} | MAE CV={-busca.best_score_:.3f} | backtest={backtest}")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina os modelos do Tech Challenge")
    parser.add_argument("--alvo", choices=["aluno", "municipio", "todos"], default="todos")
    parser.add_argument("--modelo-aluno", default="random_forest")
    parser.add_argument("--modelo-municipio", default="random_forest")
    parser.add_argument("--n-iter", type=int, default=20)
    parser.add_argument("--amostra", type=int, default=300_000)
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if args.alvo in ("aluno", "todos"):
        treinar_aluno(args.modelo_aluno, max(5, args.n_iter // 2), args.amostra)
    if args.alvo in ("municipio", "todos"):
        treinar_municipio(args.modelo_municipio, args.n_iter)


if __name__ == "__main__":
    main()
