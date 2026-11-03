"""Metricas para os modelos de aluno e municipio.

Arquivo sugerido: src/evaluation/classification_metrics.py

Suporta classificacao binaria, regressao, peso amostral, calibracao,
bootstrap por municipio e diagnostico de ausencia de dados.
"""
from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    r2_score,
    roc_auc_score,
    roc_curve,
)


def _arrays_validos(y, score, sample_weight=None):
    y = np.asarray(y)
    score = np.asarray(score, dtype=float)
    mascara = pd.notna(y) & np.isfinite(score)
    if sample_weight is None:
        return y[mascara], score[mascara], None
    peso = np.asarray(sample_weight, dtype=float)
    mascara &= np.isfinite(peso)
    return y[mascara], score[mascara], peso[mascara]


def _auc_segura(y, proba, sample_weight=None) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, proba, sample_weight=sample_weight))


def _auc_pr_segura(y, proba, sample_weight=None) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(average_precision_score(y, proba, sample_weight=sample_weight))


def avaliar_classificacao(y, proba, limiar: float = 0.5, sample_weight=None) -> dict[str, float]:
    """Avalia classificacao binaria; 1 e a classe positiva.

    Para aluno, 0 representa nao alfabetizado. Para municipio, 0 representa
    nao atingiu a meta. Por isso tambem reporta metricas da classe negativa.
    """
    y, proba, peso = _arrays_validos(y, proba, sample_weight)
    y = y.astype(int)
    if len(y) == 0:
        raise ValueError("Nenhuma observacao valida para avaliacao.")
    pred = (proba >= limiar).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1], sample_weight=peso).ravel()
    total = tn + fp + fn + tp
    precisao = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall > 0 else 0.0
    precisao_neg = tn / (tn + fn) if tn + fn > 0 else 0.0
    recall_neg = tn / (tn + fp) if tn + fp > 0 else 0.0
    return {
        "auc_roc": _auc_segura(y, proba, peso),
        "auc_pr": _auc_pr_segura(y, proba, peso),
        "acuracia": float((tp + tn) / total) if total else float("nan"),
        "precisao": float(precisao),
        "recall": float(recall),
        "f1": float(f1),
        "precisao_negativos": float(precisao_neg),
        "recall_negativos": float(recall_neg),
        "limiar": float(limiar),
        "taxa_base": float((tp + fn) / total) if total else float("nan"),
        "n": int(len(y)),
    }


def matriz_confusao(y, proba, limiar: float = 0.5, rotulos=("0", "1")) -> pd.DataFrame:
    y, proba, _ = _arrays_validos(y, proba)
    pred = (proba >= limiar).astype(int)
    matriz = confusion_matrix(y.astype(int), pred, labels=[0, 1])
    return pd.DataFrame(matriz, index=[f"real {rotulos[0]}", f"real {rotulos[1]}"], columns=[f"previsto {rotulos[0]}", f"previsto {rotulos[1]}"])


def curva_roc(y, proba, sample_weight=None) -> pd.DataFrame:
    y, proba, peso = _arrays_validos(y, proba, sample_weight)
    if len(np.unique(y)) < 2:
        return pd.DataFrame(columns=["fpr", "tpr", "limiar"])
    fpr, tpr, limiar = roc_curve(y, proba, sample_weight=peso)
    return pd.DataFrame({"fpr": fpr, "tpr": tpr, "limiar": limiar})


def curva_pr(y, proba, sample_weight=None) -> pd.DataFrame:
    y, proba, peso = _arrays_validos(y, proba, sample_weight)
    if len(np.unique(y)) < 2:
        return pd.DataFrame(columns=["precisao", "recall", "limiar"])
    precisao, recall, limiar = precision_recall_curve(y, proba, sample_weight=peso)
    return pd.DataFrame({"precisao": precisao[:-1], "recall": recall[:-1], "limiar": limiar})


def varrer_limiares(y, proba, limiares=None, sample_weight=None, passo: float = 0.02) -> pd.DataFrame:
    if limiares is None:
        limiares = np.round(np.arange(0.10, 0.91, passo), 2)
    return pd.DataFrame([avaliar_classificacao(y, proba, t, sample_weight) for t in limiares])


def limiar_por_recall_negativos(y, proba, recall_minimo: float, sample_weight=None) -> float:
    tabela = varrer_limiares(y, proba, sample_weight=sample_weight, passo=0.01)
    elegiveis = tabela[tabela["recall_negativos"] >= recall_minimo]
    return float(elegiveis["limiar"].min() if not elegiveis.empty else tabela["limiar"].max())


def avaliar_regressao(y, pred) -> dict[str, float]:
    y, pred, _ = _arrays_validos(y, pred)
    y = y.astype(float)
    if len(y) == 0:
        raise ValueError("Nenhuma observacao valida para avaliacao de regressao.")
    spearman = stats.spearmanr(y, pred).statistic if len(y) > 1 else np.nan
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "r2": float(r2_score(y, pred)) if len(y) > 1 else float("nan"),
        "vies": float((pred - y).mean()),
        "spearman": float(spearman),
        "n": int(len(y)),
    }


def risco_de_nao_atingir(pred_nivel, meta, residuos) -> np.ndarray:
    residuos = np.sort(np.asarray(residuos, dtype=float))
    residuos = residuos[np.isfinite(residuos)]
    if len(residuos) == 0:
        raise ValueError("A distribuicao de residuos esta vazia.")
    folga = np.asarray(meta, dtype=float) - np.asarray(pred_nivel, dtype=float)
    risco = np.searchsorted(residuos, folga, side="right") / len(residuos)
    return np.where(np.isnan(folga), np.nan, risco)


def brier(y, proba, sample_weight=None) -> float:
    y, proba, peso = _arrays_validos(y, proba, sample_weight)
    return float(np.average((proba - y.astype(float)) ** 2, weights=peso))


def ks(y, proba, sample_weight=None) -> float:
    curva = curva_roc(y, proba, sample_weight)
    return float((curva["tpr"] - curva["fpr"]).max()) if not curva.empty else float("nan")


def curva_calibracao(y, proba, n_faixas: int = 10, sample_weight=None) -> pd.DataFrame:
    y, proba, peso = _arrays_validos(y, proba, sample_weight)
    y = y.astype(float)
    peso = np.ones_like(proba) if peso is None else peso
    faixa = np.clip((proba * n_faixas).astype(int), 0, n_faixas - 1)
    linhas = []
    for indice in range(n_faixas):
        mascara = faixa == indice
        if mascara.any():
            linhas.append({
                "faixa": f"{indice / n_faixas:.1f} a {(indice + 1) / n_faixas:.1f}",
                "prevista": float(np.average(proba[mascara], weights=peso[mascara])),
                "observada": float(np.average(y[mascara], weights=peso[mascara])),
                "n": int(mascara.sum()),
                "peso": float(peso[mascara].sum()),
            })
    return pd.DataFrame(linhas)


def ic_bootstrap(y, proba, grupos, metrica: Callable = roc_auc_score, n_reamostras: int = 200, sample_weight=None, seed: int = 42, nivel: float = 0.95) -> dict[str, float]:
    y = np.asarray(y)
    proba = np.asarray(proba)
    grupos = np.asarray(grupos)
    peso = None if sample_weight is None else np.asarray(sample_weight)
    validos = pd.notna(y) & np.isfinite(proba) & pd.notna(grupos)
    y, proba, grupos = y[validos], proba[validos], grupos[validos]
    peso = None if peso is None else peso[validos]
    codigos, inverso = np.unique(grupos, return_inverse=True)
    por_grupo = [np.flatnonzero(inverso == g) for g in range(len(codigos))]
    rng = np.random.default_rng(seed)

    def calcular(idx):
        kwargs = {} if peso is None else {"sample_weight": peso[idx]}
        try:
            return float(metrica(y[idx], proba[idx], **kwargs))
        except ValueError:
            return np.nan

    valores = []
    for _ in range(n_reamostras):
        sorteio = rng.integers(0, len(codigos), len(codigos))
        idx = np.concatenate([por_grupo[g] for g in sorteio])
        valores.append(calcular(idx))
    valores = np.asarray(valores, dtype=float)
    valores = valores[np.isfinite(valores)]
    alfa = (1 - nivel) / 2
    todos = np.arange(len(y))
    return {
        "estimativa": calcular(todos),
        "ic_inferior": float(np.quantile(valores, alfa)) if len(valores) else np.nan,
        "ic_superior": float(np.quantile(valores, 1 - alfa)) if len(valores) else np.nan,
        "desvio": float(valores.std(ddof=1)) if len(valores) > 1 else np.nan,
        "n_reamostras_validas": int(len(valores)),
    }


def auc_da_ausencia(x: pd.DataFrame, y, sample_weight=None) -> pd.DataFrame:
    y = np.asarray(y).astype(int)
    linhas = []
    for coluna in x.columns:
        ausente = x[coluna].isna().to_numpy(dtype=float)
        n_ausentes = int(ausente.sum())
        if n_ausentes in (0, len(ausente)):
            continue
        auc = roc_auc_score(y, ausente, sample_weight=sample_weight)
        linhas.append({"variavel": coluna, "ausentes": n_ausentes, "auc_ausencia": float(max(auc, 1 - auc))})
    if not linhas:
        return pd.DataFrame(columns=["variavel", "ausentes", "auc_ausencia"])
    return pd.DataFrame(linhas).sort_values("auc_ausencia", ascending=False).reset_index(drop=True)
