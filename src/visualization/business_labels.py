"""Rotulos de negocio para tabelas, graficos e explicabilidade.

Arquivo sugerido: src/visualization/business_labels.py
"""
from __future__ import annotations

ROTULOS: dict[str, str] = {
    "alfabetizado": "Aluno alfabetizado",
    "indicador_t": "Alfabetizados no ano (%)",
    "atingiu_meta_t": "Atingiu a meta do ano",
    "gap_meta_t": "Distancia para a meta (p.p.)",
    "indicador_t1": "Alfabetizados no ano anterior (%)",
    "indicador_t2": "Alfabetizados dois anos antes (%)",
    "nivel_t1": "Nivel de alfabetizacao no ano anterior",
    "participacao_t1": "Participacao na avaliacao anterior (%)",
    "variacao_t1": "Variacao recente do indicador (p.p.)",
    "meta_t1": "Meta do ano anterior (%)",
    "gap_meta_t1": "Distancia da meta no ano anterior (p.p.)",
    "meta_t": "Meta do ano-alvo (%)",
    "salto_necessario": "Avanco necessario para atingir a meta (p.p.)",
    "populacao": "Populacao",
    "log_populacao": "Populacao em escala logaritmica",
    "area_km2": "Area territorial (km²)",
    "densidade_hab_km2": "Densidade demografica (hab./km²)",
    "pib_mil_reais": "PIB municipal (mil R$)",
    "pib_per_capita_reais": "PIB per capita (R$)",
    "participacao_vab_agro_pct": "Participacao da agropecuaria no PIB (%)",
    "participacao_vab_industria_pct": "Participacao da industria no PIB (%)",
    "participacao_vab_adm_publica_pct": "Participacao da administracao publica no PIB (%)",
    "participacao_vab_servicos_pct": "Participacao dos servicos no PIB (%)",
    "media_inse": "Nivel socioeconomico medio (INSE)",
    "qtd_alunos_inse": "Alunos considerados no INSE",
    **{f"pc_nivel_{i}": f"Alunos no nivel socioeconomico {i} (%)" for i in range(1, 9)},
    "ideb_ideb_observado_ultimo": "IDEB mais recente",
    "ideb_ideb_observado_anterior": "IDEB anterior",
    "ideb_ideb_observado_variacao": "Variacao recente do IDEB",
    "ideb_ideb_nota_portugues_ultimo": "Nota de Portugues mais recente",
    "ideb_ideb_nota_matematica_ultimo": "Nota de Matematica mais recente",
    "ideb_ideb_nota_media_ultimo": "Nota media mais recente",
    "ideb_ideb_rendimento_ultimo": "Rendimento do IDEB mais recente",
    "ideb_ideb_meta_ultimo": "Meta do IDEB mais recente",
    "ideb_aprovacao_ai_pct_ultimo": "Aprovacao nos anos iniciais (%)",
    "ideb_aprovacao_1ano_pct_ultimo": "Aprovacao no 1º ano (%)",
    "ideb_aprovacao_2ano_pct_ultimo": "Aprovacao no 2º ano (%)",
    "ref_ideb": "Ano de referencia do IDEB",
    "rede": "Rede de ensino",
    "rede_codigo": "Codigo da rede",
    "sigla_uf": "UF",
    "nome_uf": "Estado",
    "nome_regiao": "Regiao",
    "tp_serie": "Serie avaliada",
    "escola_qtd_registros": "Registros da escola",
    "escola_qtd_avaliados": "Alunos avaliados na escola",
    "escola_taxa_presenca": "Presenca na avaliacao na escola (%)",
    "ano": "Ano da avaliacao",
    "ano_alvo": "Ano-alvo",
    "probabilidade_alfabetizado": "Probabilidade de alfabetizacao",
    "risco_nao_atingir": "Risco de nao atingir a meta",
    "indicador_previsto": "Indicador previsto (%)",
}


def _sem_prefixo_transformer(nome: str) -> str:
    return nome.split("__", 1)[1] if "__" in nome else nome


def rotulo(nome: str) -> str:
    """Traduz nomes tecnicos e colunas one-hot para linguagem de negocio."""
    nome = _sem_prefixo_transformer(str(nome))
    if nome.startswith("ausente_"):
        return f"Sem informacao: {rotulo(nome[len('ausente_') :])}"
    if nome in ROTULOS:
        return ROTULOS[nome]
    for base in ("sigla_uf", "rede", "tp_serie", "rede_codigo"):
        prefixo = f"{base}_"
        if nome.startswith(prefixo):
            return f"{ROTULOS.get(base, base)}: {nome[len(prefixo):]}"
    return nome.replace("_", " ").capitalize()


def rotular(nomes) -> list[str]:
    return [rotulo(nome) for nome in nomes]
