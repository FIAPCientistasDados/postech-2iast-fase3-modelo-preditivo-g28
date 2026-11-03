"""Mapas coropleticos municipais com GeoJSON e Matplotlib.

Arquivo sugerido: src/visualization/municipality_maps.py

O modulo nao baixa dados. A malha GeoJSON deve existir em
``data/external/ibge/malha_municipios.json``. O identificador municipal e
normalizado como texto de sete digitos, compativel com a Gold e a base analitica.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize, TwoSlopeNorm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MALHA_PADRAO = PROJECT_ROOT / "data" / "external" / "ibge" / "malha_municipios.json"


def _codigo_municipio(valor) -> str | None:
    if pd.isna(valor):
        return None
    texto = str(valor).strip().removesuffix(".0")
    return texto.zfill(7)


def carregar_malha(path: Path = MALHA_PADRAO) -> dict[str, list[np.ndarray]]:
    """Carrega GeoJSON e devolve municipio para aneis exteriores."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Malha municipal nao encontrada: {path}. "
            "Informe o caminho de um GeoJSON municipal do IBGE."
        )
    dados = json.loads(path.read_text(encoding="utf-8"))
    malha: dict[str, list[np.ndarray]] = {}
    for feature in dados.get("features", []):
        propriedades = feature.get("properties", {})
        codigo = propriedades.get("codarea") or propriedades.get("CD_MUN") or propriedades.get("id")
        codigo = _codigo_municipio(codigo)
        geometria = feature.get("geometry") or {}
        tipo = geometria.get("type")
        coordenadas = geometria.get("coordinates", [])
        if codigo is None or tipo not in {"Polygon", "MultiPolygon"}:
            continue
        partes = coordenadas if tipo == "MultiPolygon" else [coordenadas]
        aneis = [np.asarray(poligono[0], dtype=float) for poligono in partes if poligono]
        if aneis:
            malha[codigo] = aneis
    if not malha:
        raise ValueError("O GeoJSON nao contem geometrias municipais reconhecidas.")
    return malha


def valores_por_municipio(
    df: pd.DataFrame,
    coluna_valor: str,
    coluna_id: str = "id_municipio",
) -> dict[str, float]:
    """Converte um DataFrame em dicionario para desenho do mapa."""
    if coluna_id not in df or coluna_valor not in df:
        raise KeyError(f"Colunas necessarias: {coluna_id} e {coluna_valor}")
    tabela = df[[coluna_id, coluna_valor]].drop_duplicates(coluna_id, keep="last").copy()
    tabela[coluna_id] = tabela[coluna_id].map(_codigo_municipio)
    tabela[coluna_valor] = pd.to_numeric(tabela[coluna_valor], errors="coerce")
    return dict(zip(tabela[coluna_id], tabela[coluna_valor]))


def mapa_municipios(
    valores: dict[str, float],
    malha: dict[str, list[np.ndarray]],
    ax: plt.Axes | None = None,
    cmap: str = "RdYlGn_r",
    vmin: float | None = None,
    vmax: float | None = None,
    centro: float | None = None,
    titulo: str = "",
    rotulo_barra: str = "",
    cor_sem_dado: str = "#e6e6e6",
) -> plt.Axes:
    """Pinta cada municipio pelo valor; municipios sem valor ficam cinza."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 10))
    normalizados = {_codigo_municipio(k): v for k, v in valores.items()}
    poligonos, cores, sem_dado = [], [], []
    for codigo, aneis in malha.items():
        valor = normalizados.get(codigo)
        ausente = valor is None or not np.isfinite(float(valor))
        for anel in aneis:
            if ausente:
                sem_dado.append(anel)
            else:
                poligonos.append(anel)
                cores.append(float(valor))
    if sem_dado:
        ax.add_collection(PolyCollection(sem_dado, facecolors=cor_sem_dado, edgecolors="none"))
    if poligonos:
        array = np.asarray(cores, dtype=float)
        minimo = float(np.nanmin(array)) if vmin is None else vmin
        maximo = float(np.nanmax(array)) if vmax is None else vmax
        if minimo == maximo:
            minimo, maximo = minimo - 0.5, maximo + 0.5
        norm = TwoSlopeNorm(vmin=minimo, vcenter=centro, vmax=maximo) if centro is not None and minimo < centro < maximo else Normalize(vmin=minimo, vmax=maximo)
        colecao = PolyCollection(poligonos, array=array, cmap=cmap, norm=norm, edgecolors="none")
        ax.add_collection(colecao)
        barra = plt.colorbar(colecao, ax=ax, shrink=0.62, pad=0.01)
        barra.set_label(rotulo_barra)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_axis_off()
    if titulo:
        ax.set_title(titulo)
    return ax
