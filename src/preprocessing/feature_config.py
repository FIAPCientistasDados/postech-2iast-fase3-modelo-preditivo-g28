"""Selecao de features das bases analiticas do projeto.

Arquivo sugerido: src/preprocessing/feature_config.py

As listas usam os nomes presentes em:
    data/processed/base_analitica_aluno.parquet
    data/processed/base_analitica_municipio.parquet

Variaveis-alvo, identificadores e resultados contemporaneos ficam fora de X.
Quando uma coluna opcional nao existir, ela e ignorada e reportada pela funcao
``resolver_grupos``. Isso permite evoluir a ABT sem quebrar o treinamento.
"""
from __future__ import annotations

import pandas as pd

HISTORICO_MUNICIPIO = [
    "indicador_t1",
    "participacao_t1",
    "salto_necessario",
    "indicador_t2",
    "variacao_t1",
    "meta_t1",
    "gap_meta_t1",
]

LOG_MUNICIPIO = [
    "populacao",
    "area_km2",
    "densidade_hab_km2",
    "pib_per_capita_reais",
    "pib_mil_reais",
    "qtd_alunos_inse",
]

CONTEXTO_MUNICIPIO = [
    "media_inse",
    *[f"pc_nivel_{i}" for i in range(1, 9)],
    "participacao_vab_agro_pct",
    "participacao_vab_industria_pct",
    "participacao_vab_adm_publica_pct",
    "participacao_vab_servicos_pct",
    "ideb_ideb_observado_ultimo",
    "ideb_ideb_observado_anterior",
    "ideb_ideb_observado_variacao",
    "ideb_ideb_nota_portugues_ultimo",
    "ideb_ideb_nota_matematica_ultimo",
    "ideb_ideb_nota_media_ultimo",
    "ideb_ideb_rendimento_ultimo",
    "ideb_ideb_meta_ultimo",
    "ideb_aprovacao_ai_pct_ultimo",
    "ideb_aprovacao_1ano_pct_ultimo",
    "ideb_aprovacao_2ano_pct_ultimo",
    "ref_ideb",
]

CATEGORICAS_MUNICIPIO = ["sigla_uf", "rede"]

LOG_ALUNO = [
    "escola_qtd_avaliados",
    "escola_qtd_registros",
    *LOG_MUNICIPIO,
]

CONTEXTO_ALUNO = [
    "escola_taxa_presenca",
    *CONTEXTO_MUNICIPIO,
]

CATEGORICAS_ALUNO = ["rede", "sigla_uf", "tp_serie"]

COLUNAS_PROIBIDAS_ALUNO = {
    "alfabetizado",
    "id_aluno",
    "id_escola",
    "id_municipio",
    "proficiencia",
    "indicador_t",
    "atingiu_meta_t",
    "gap_meta_t",
}

COLUNAS_PROIBIDAS_MUNICIPIO = {
    "indicador_t",
    "atingiu_meta_t",
    "gap_meta_t",
    "id_municipio",
    "nome_municipio",
}


def grupos_municipio() -> dict[str, list[str]]:
    return {
        "historico": list(HISTORICO_MUNICIPIO),
        "log": list(LOG_MUNICIPIO),
        "numericas": list(CONTEXTO_MUNICIPIO),
        "categoricas": list(CATEGORICAS_MUNICIPIO),
    }


def grupos_aluno() -> dict[str, list[str]]:
    return {
        "historico": list(HISTORICO_MUNICIPIO),
        "log": list(LOG_ALUNO),
        "numericas": list(CONTEXTO_ALUNO),
        "categoricas": list(CATEGORICAS_ALUNO),
    }


def colunas(grupos: dict[str, list[str]]) -> list[str]:
    """Achata os grupos, preservando a ordem e removendo duplicatas."""
    return list(dict.fromkeys(c for lista in grupos.values() for c in lista))


def resolver_grupos(
    df: pd.DataFrame,
    grupos: dict[str, list[str]],
    estrito: bool = False,
) -> tuple[dict[str, list[str]], list[str]]:
    """Mantem somente colunas existentes e devolve a lista das ausentes."""
    resolvidos: dict[str, list[str]] = {}
    ausentes: list[str] = []
    for nome, lista in grupos.items():
        resolvidos[nome] = [c for c in lista if c in df.columns]
        ausentes.extend(c for c in lista if c not in df.columns)
    ausentes = list(dict.fromkeys(ausentes))
    if estrito and ausentes:
        raise KeyError(f"Colunas ausentes na base: {ausentes}")
    return resolvidos, ausentes


def preparar_xy(
    df: pd.DataFrame,
    grupos: dict[str, list[str]],
    alvo: str,
    estrito: bool = False,
) -> tuple[pd.DataFrame, pd.Series]:
    """Seleciona X e y, eliminando linhas sem target."""
    if alvo not in df.columns:
        raise KeyError(f"Alvo ausente na base: {alvo}")
    dados = df.dropna(subset=[alvo]).copy()
    grupos_validos, ausentes = resolver_grupos(dados, grupos, estrito=estrito)
    cols = colunas(grupos_validos)
    if not cols:
        raise ValueError("Nenhuma feature configurada foi encontrada na base.")
    x = dados[cols].copy()
    for c in grupos_validos.get("categoricas", []):
        x[c] = x[c].astype("string")
    y = dados[alvo]
    x.attrs["grupos_features"] = grupos_validos
    x.attrs["features_ausentes"] = ausentes
    return x, y
