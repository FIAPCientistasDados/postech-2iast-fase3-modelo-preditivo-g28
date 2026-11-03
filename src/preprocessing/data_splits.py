"""Divisoes temporais, validacao agrupada e amostragem estratificada.

Arquivo sugerido: src/preprocessing/data_splits.py
"""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupKFold

SEED = 42

try:
    from sklearn.model_selection import StratifiedGroupKFold
except ImportError:
    StratifiedGroupKFold = None


def split_temporal(
    df: pd.DataFrame,
    ano_treino: int | list[int] | tuple[int, ...],
    ano_teste: int,
    coluna_ano: str = "ano",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa anos de treino e um ano posterior de teste."""
    if coluna_ano not in df.columns:
        raise KeyError(f"Coluna temporal ausente: {coluna_ano}")
    anos_treino = {ano_treino} if isinstance(ano_treino, int) else set(ano_treino)
    treino = df[df[coluna_ano].isin(anos_treino)].copy()
    teste = df[df[coluna_ano] == ano_teste].copy()
    if treino.empty:
        raise ValueError(f"Nenhuma linha para treino nos anos {sorted(anos_treino)}.")
    if teste.empty:
        raise ValueError(f"Nenhuma linha para teste no ano {ano_teste}.")
    if max(anos_treino) >= ano_teste:
        raise ValueError("O ano de teste deve ser posterior aos anos de treino.")
    return treino, teste


def cv_por_municipio(n_splits: int = 5, seed: int = SEED):
    if StratifiedGroupKFold is not None:
        return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return GroupKFold(n_splits=n_splits)


def cv_por_municipio_regressao(n_splits: int = 5) -> GroupKFold:
    # GroupKFold nao oferece shuffle em varias versoes do sklearn.
    return GroupKFold(n_splits=n_splits)


def amostra_estratificada(
    df: pd.DataFrame,
    n: int,
    alvo: str,
    seed: int = SEED,
) -> pd.DataFrame:
    """Amostra de tamanho aproximado n preservando a distribuicao do alvo."""
    if alvo not in df.columns:
        raise KeyError(f"Alvo ausente: {alvo}")
    dados = df.dropna(subset=[alvo])
    if n >= len(dados):
        return dados.copy()
    proporcoes = dados[alvo].value_counts(normalize=True)
    partes = []
    restante = n
    itens = list(proporcoes.items())
    for posicao, (classe, proporcao) in enumerate(itens):
        grupo = dados[dados[alvo] == classe]
        tamanho = restante if posicao == len(itens) - 1 else int(round(n * proporcao))
        tamanho = min(max(1, tamanho), len(grupo), restante)
        partes.append(grupo.sample(n=tamanho, random_state=seed))
        restante -= tamanho
    amostra = pd.concat(partes, ignore_index=False)
    return amostra.sample(frac=1, random_state=seed).reset_index(drop=True)
