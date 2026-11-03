"""Validacao por municipio, backtest temporal e testes de robustez.

Arquivo sugerido: src/evaluation/validacao.py

O modulo e autocontido e nao depende de ``src.preprocessing.splits``. Para
classificacao usa StratifiedGroupKFold quando disponivel; para regressao usa
GroupKFold. O municipio deve ser informado em ``grupos``.
"""
from __future__ import annotations

# Permite executar como modulo e diretamente pelo caminho do arquivo.
if __package__ in (None, ""):
    import sys
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GroupKFold, learning_curve
from sklearn.pipeline import Pipeline

from src.evaluation.classification_metrics import avaliar_classificacao, avaliar_regressao

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:  # compatibilidade com sklearn antigo
    StratifiedGroupKFold = None


def cv_por_municipio(n_splits: int = 5, seed: int = 42):
    """CV de classificacao sem misturar municipios entre treino e validacao."""
    if StratifiedGroupKFold is not None:
        return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return GroupKFold(n_splits=n_splits)


def cv_por_municipio_regressao(n_splits: int = 5):
    return GroupKFold(n_splits=n_splits)


def _validar_entradas(x, y, grupos, n_splits):
    if len(x) != len(y) or len(x) != len(grupos):
        raise ValueError("x, y e grupos precisam ter o mesmo tamanho.")
    n_grupos = pd.Series(grupos).nunique(dropna=True)
    if n_grupos < n_splits:
        raise ValueError(f"Ha {n_grupos} grupos, menos que n_splits={n_splits}.")


def validar_por_grupos(pipeline: Pipeline, x: pd.DataFrame, y, grupos, n_splits: int = 5, sample_weight=None, limiar: float = 0.5, seed: int = 42) -> tuple[pd.DataFrame, np.ndarray]:
    """Gera metricas por fold e probabilidades out-of-fold por municipio."""
    y = np.asarray(y).astype(int)
    grupos = np.asarray(grupos)
    peso = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
    _validar_entradas(x, y, grupos, n_splits)
    oof = np.full(len(y), np.nan)
    linhas = []
    cv = cv_por_municipio(n_splits, seed)
    for fold, (treino, validacao) in enumerate(cv.split(x, y, grupos)):
        modelo = clone(pipeline)
        fit_params = {} if peso is None else {"modelo__sample_weight": peso[treino]}
        modelo.fit(x.iloc[treino], y[treino], **fit_params)
        proba_treino = modelo.predict_proba(x.iloc[treino])[:, 1]
        proba_validacao = modelo.predict_proba(x.iloc[validacao])[:, 1]
        oof[validacao] = proba_validacao
        peso_treino = None if peso is None else peso[treino]
        peso_validacao = None if peso is None else peso[validacao]
        linhas.append({"fold": fold, "conjunto": "treino", **avaliar_classificacao(y[treino], proba_treino, limiar, peso_treino)})
        linhas.append({"fold": fold, "conjunto": "validacao", **avaliar_classificacao(y[validacao], proba_validacao, limiar, peso_validacao)})
    if np.isnan(oof).any():
        raise RuntimeError("A validacao nao produziu predicao OOF para todas as linhas.")
    return pd.DataFrame(linhas), oof


def resumir_folds(tabela: pd.DataFrame, metricas=("auc_roc", "auc_pr", "f1", "recall_negativos")) -> pd.DataFrame:
    existentes = [m for m in metricas if m in tabela.columns]
    agrupado = tabela.groupby("conjunto")[existentes]
    return pd.concat({"media": agrupado.mean(), "desvio": agrupado.std()}, axis=1).round(4)


def backtest_temporal(pipeline: Pipeline, x_treino, y_treino, x_teste, y_teste, sample_weight_treino=None, sample_weight_teste=None, limiar: float = 0.5) -> tuple[dict, np.ndarray, Pipeline]:
    """Treina em anos anteriores e avalia em um ano posterior."""
    modelo = clone(pipeline)
    fit_params = {} if sample_weight_treino is None else {"modelo__sample_weight": np.asarray(sample_weight_treino)}
    modelo.fit(x_treino, np.asarray(y_treino), **fit_params)
    proba = modelo.predict_proba(x_teste)[:, 1]
    metricas = avaliar_classificacao(y_teste, proba, limiar, sample_weight_teste)
    return metricas, proba, modelo


def curva_de_aprendizado(pipeline: Pipeline, x: pd.DataFrame, y, grupos, fracoes=(0.1, 0.25, 0.5, 0.75, 1.0), n_splits: int = 5, scoring: str = "roc_auc", n_jobs: int = -1, seed: int = 42) -> pd.DataFrame:
    tamanhos, treino, validacao = learning_curve(
        pipeline, x, y, groups=grupos, cv=cv_por_municipio(n_splits, seed),
        train_sizes=list(fracoes), scoring=scoring, n_jobs=n_jobs, shuffle=False,
    )
    return pd.DataFrame({
        "tamanho": tamanhos,
        "treino_media": treino.mean(axis=1),
        "treino_desvio": treino.std(axis=1),
        "validacao_media": validacao.mean(axis=1),
        "validacao_desvio": validacao.std(axis=1),
    })


def validar_regressao_por_grupos(pipeline: Pipeline, x: pd.DataFrame, y, grupos, n_splits: int = 5) -> tuple[pd.DataFrame, np.ndarray]:
    y = np.asarray(y, dtype=float)
    grupos = np.asarray(grupos)
    _validar_entradas(x, y, grupos, n_splits)
    oof = np.full(len(y), np.nan)
    linhas = []
    for fold, (treino, validacao) in enumerate(cv_por_municipio_regressao(n_splits).split(x, y, grupos)):
        modelo = clone(pipeline)
        modelo.fit(x.iloc[treino], y[treino])
        pred_treino = modelo.predict(x.iloc[treino])
        pred_validacao = modelo.predict(x.iloc[validacao])
        oof[validacao] = pred_validacao
        linhas.append({"fold": fold, "conjunto": "treino", **avaliar_regressao(y[treino], pred_treino)})
        linhas.append({"fold": fold, "conjunto": "validacao", **avaliar_regressao(y[validacao], pred_validacao)})
    return pd.DataFrame(linhas), oof


def embaralhar_dentro_de_grupos(y, grupos, seed: int = 42) -> np.ndarray:
    y = np.asarray(y)
    grupos = np.asarray(grupos)
    rng = np.random.default_rng(seed)
    saida = y.copy()
    for grupo in np.unique(grupos):
        indices = np.flatnonzero(grupos == grupo)
        saida[indices] = y[rng.permutation(indices)]
    return saida


def predicao_por_uf_excluida(pipeline: Pipeline, x: pd.DataFrame, y, uf, sample_weight=None, regressao: bool = False) -> np.ndarray:
    y = np.asarray(y)
    uf = np.asarray(uf)
    peso = None if sample_weight is None else np.asarray(sample_weight)
    saida = np.full(len(y), np.nan)
    for sigla in pd.Series(uf).dropna().unique():
        treino = np.flatnonzero(uf != sigla)
        validacao = np.flatnonzero(uf == sigla)
        modelo = clone(pipeline)
        fit_params = {} if peso is None else {"modelo__sample_weight": peso[treino]}
        modelo.fit(x.iloc[treino], y[treino], **fit_params)
        saida[validacao] = modelo.predict(x.iloc[validacao]) if regressao else modelo.predict_proba(x.iloc[validacao])[:, 1]
    return saida


def diferenca_bootstrap_pareada(y, score_a, score_b, grupos, metrica: Callable, n_reamostras: int = 200, sample_weight=None, seed: int = 42, nivel: float = 0.95) -> dict[str, float]:
    y = np.asarray(y)
    a = np.asarray(score_a)
    b = np.asarray(score_b)
    grupos = np.asarray(grupos)
    peso = None if sample_weight is None else np.asarray(sample_weight)
    codigos, inverso = np.unique(grupos, return_inverse=True)
    por_grupo = [np.flatnonzero(inverso == g) for g in range(len(codigos))]
    rng = np.random.default_rng(seed)

    def calcular(indices, score):
        kwargs = {} if peso is None else {"sample_weight": peso[indices]}
        try:
            return float(metrica(y[indices], score[indices], **kwargs))
        except ValueError:
            return np.nan

    diferencas = []
    for _ in range(n_reamostras):
        indices = np.concatenate([por_grupo[g] for g in rng.integers(0, len(codigos), len(codigos))])
        diferencas.append(calcular(indices, a) - calcular(indices, b))
    diferencas = np.asarray(diferencas, dtype=float)
    diferencas = diferencas[np.isfinite(diferencas)]
    alfa = (1 - nivel) / 2
    todos = np.arange(len(y))
    metrica_a = calcular(todos, a)
    metrica_b = calcular(todos, b)
    return {
        "metrica_a": metrica_a,
        "metrica_b": metrica_b,
        "diferenca": metrica_a - metrica_b,
        "ic_inferior": float(np.quantile(diferencas, alfa)) if len(diferencas) else np.nan,
        "ic_superior": float(np.quantile(diferencas, 1 - alfa)) if len(diferencas) else np.nan,
        "n_reamostras_validas": int(len(diferencas)),
    }
