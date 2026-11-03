# Dicionário de Dados - Camada Silver

## alunos.parquet

| Campo | Descrição | Tipo sugerido |
|----------|----------|----------|
| nu_ano_avaliacao | Ano da avaliação aplicada | Inteiro |
| co_uf | Código da Unidade Federativa | Inteiro |
| sigla_uf | Sigla do estado | String |
| id_aluno | Identificador único do aluno | String |
| tp_serie | Série avaliada | String |
| id_escola | Identificador da escola | String |
| tp_dependencia | Tipo de dependência administrativa da escola | Inteiro |
| id_municipio | Código IBGE do município | String |
| no_municipio | Nome do município | String |
| presente | Indica presença na avaliação | Boolean |
| in_preenchimento_lp | Indica preenchimento da prova de Língua Portuguesa | Boolean |
| co_caderno_lp | Código da prova aplicada | String |
| vl_peso_aluno_lp | Peso amostral do aluno | Float |
| proficiencia | Proficiência em Língua Portuguesa | Float |
| alfabetizado | Variável alvo (0 = não alfabetizado, 1 = alfabetizado) | Integer |
| ano | Ano de referência | Integer |

## censo_2022_municipios.parquet

| Campo | Descrição |
|---------|---------|
| id_municipio | Código IBGE do município |
| nome_municipio | Nome do município |
| area_km2 | Área territorial |
| densidade_hab_km2 | Densidade populacional |
| populacao | População residente |
| ano_referencia | Ano do censo utilizado |

## dim_estados.parquet

| Campo | Descrição |
|---------|---------|
| id_uf | Código IBGE da UF |
| sigla_uf | Sigla da UF |
| nome_uf | Nome do estado |
| nome_regiao | Região geográfica |

## dim_municipios.parquet

| Campo | Descrição |
|---------|---------|
| id_municipio | Código IBGE do município |
| nome_municipio | Nome do município |
| id_uf | Código da UF |
| sigla_uf | Sigla da UF |
| nome_uf | Nome do estado |
| nome_regiao | Região do país |

## ideb_anos_iniciais.parquet

Contém indicadores educacionais históricos (IDEB, aprovação e desempenho).

## inse_2023_municipios.parquet

Contém indicadores socioeconômicos (INSE) e distribuição dos alunos por níveis socioeconômicos.

## pib_municipal.parquet

Contém indicadores econômicos municipais e composição do VAB.

## resultados_municipios.parquet

Contém o Indicador Criança Alfabetizada por município.

## resultados_uf.parquet

Contém o Indicador Criança Alfabetizada por UF.

## metas_municipio.parquet

Metas municipais de alfabetização.

## metas_uf.parquet

Metas estaduais de alfabetização.

## meta_brasil.parquet

Metas nacionais de alfabetização.

## municipio.parquet

Agregados da avaliação por município.

### Atenção
Essas variáveis podem causar data leakage quando utilizadas para prever resultados do mesmo ano:

- indicador_pct
- vl_media_lp
- pc_aluno_nivel_0_lp até pc_aluno_nivel_8_lp

Recomenda-se utilizar apenas valores defasados (t-1).

## uf.parquet

Agregados da avaliação por UF.

# Classificação para Modelagem

## Target
- alfabetizado

## Variáveis Demográficas
- id_municipio
- co_uf
- sigla_uf
- tp_serie
- tp_localizacao
- tp_capital
- populacao
- densidade_hab_km2

## Variáveis Socioeconômicas
- media_inse
- pc_nivel_1 até pc_nivel_8
- pib_mil_reais
- vab_agro_mil_reais
- vab_industria_mil_reais
- vab_servicos_mil_reais
- vab_adm_publica_mil_reais

## Variáveis Educacionais Históricas
- ideb_observado
- ideb_meta
- ideb_nota_media
- aprovacao_ai_pct
- aprovacao_1ano_pct
- aprovacao_2ano_pct
