"""Estilo visual unico e exportacao de figuras.

Arquivo sugerido: src/visualization/plot_style.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGES_DIR = PROJECT_ROOT / "images"

AZUL = "#1f4e79"
LARANJA = "#d9822b"
CINZA = "#8c8c8c"
VERDE = "#3b7a57"
VERMELHO = "#b23a48"
ROXO = "#6c5b7b"
PALETA = [AZUL, LARANJA, VERDE, VERMELHO, CINZA, ROXO]
CORES_REGIAO = {
    "Norte": VERDE,
    "Nordeste": LARANJA,
    "Centro-Oeste": ROXO,
    "Sudeste": AZUL,
    "Sul": CINZA,
}


def aplicar_estilo() -> None:
    sns.set_theme(style="whitegrid", context="notebook", palette=PALETA)
    mpl.rcParams.update({
        "figure.figsize": (10, 5.5),
        "figure.dpi": 110,
        "savefig.dpi": 180,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })


def salvar_figura(
    fig: plt.Figure,
    nome: str,
    diretorio: Path = IMAGES_DIR,
    formato: str = "png",
) -> Path:
    """Salva a figura com layout ajustado e fecha somente quando solicitado externamente."""
    diretorio.mkdir(parents=True, exist_ok=True)
    sufixo = formato.lstrip(".")
    destino = diretorio / f"{nome}.{sufixo}"
    fig.tight_layout()
    fig.savefig(destino, bbox_inches="tight", facecolor="white")
    return destino


def formatar_percentual(ax: plt.Axes, eixo: str = "x", casas: int = 0) -> None:
    formatter = mpl.ticker.FuncFormatter(lambda valor, _: f"{valor:.{casas}f}%")
    (ax.xaxis if eixo == "x" else ax.yaxis).set_major_formatter(formatter)


# Aliases curtos para notebooks antigos.
salvar = salvar_figura
fmt_pct = formatar_percentual
