# Dicionário de Dados Completo - Camada Silver

## Visão Geral
Base utilizada no Tech Challenge Fase 3 para modelagem de alfabetização.

---

## alunos.parquet

### Descrição
Base granular por aluno avaliado.

| Campo | Tipo | Descrição |
|---------|---------|---------|
| nu_ano_avaliacao | int | Ano da avaliação |
| co_uf | string/int | Código da UF |
| sigla_uf | string | Sigla da UF |
| id_aluno | string | Identificador do aluno |
| tp_serie | int | Série avaliada |
| id_escola | string | Identificador da escola |
| tp_dependencia | int | Dependência administrativa |
| id_municipio | string | Código IBGE do município |
| no_municipio | string | Nome do município |
| presente | int/bool | Presença na avaliação |
| in_preenchimento_lp | int/bool | Preenchimento da prova |
| co_caderno_lp | string | Código do caderno |
| vl_peso_aluno_lp | float | Peso amostral |
| proficiencia | float | Proficiência LP |
| alfabetizado | int | TARGET (0/1) |
| ano | int | Ano referência |
| co_bloco_1..4 | string | Bloco de questões |
| tx_resposta_bloco_1..4 | string | Respostas do aluno |
| tx_gabarito_bloco_1..4 | string | Gabarito oficial |
| _arquivo_fonte | string | Arquivo origem |
| _processed_at | timestamp | Data processamento |

### Observações
- Variável alvo: alfabetizado.
- Possível engenharia de atributos usando acertos por bloco.
- Não utilizar gabaritos para construir features diretamente.

---

## censo_2022_municipios.parquet

Informações demográficas municipais.

Campos:
- id_municipio
- nome_municipio
- area_km2
- densidade_hab_km2
- populacao
- ano_referencia

Uso recomendado: contexto territorial.

---

## dim_estados.parquet

Dimensão de estados.

Campos:
- id_uf
- sigla_uf
- nome_uf
- nome_regiao

---

## dim_municipios.parquet

Dimensão de municípios.

Campos:
- id_municipio
- nome_municipio
- id_uf
- sigla_uf
- nome_uf
- nome_regiao

---

## ideb_anos_iniciais.parquet

Histórico educacional por município.

Campos principais:
- aprovacao_ai_pct
- aprovacao_1ano_pct
- aprovacao_2ano_pct
- ideb_rendimento
- ideb_nota_matematica
- ideb_nota_portugues
- ideb_nota_media
- ideb_observado
- ideb_meta

### Valor analítico
Forte candidato para feature histórica.

---

## inse_2023_municipios.parquet

Indicador socioeconômico.

Campos principais:
- media_inse
- qtd_alunos_inse
- pc_nivel_1 até pc_nivel_8
- tp_localizacao
- tp_capital
- tp_tipo_rede

### Valor analítico
Principal conjunto socioeconômico do projeto.

---

## pib_municipal.parquet

Indicadores econômicos.

Campos:
- pib_mil_reais
- vab_agro_mil_reais
- vab_industria_mil_reais
- vab_servicos_mil_reais
- vab_adm_publica_mil_reais
- ano_pib

### Features derivadas sugeridas
- PIB per capita
- Participação do agro
- Participação da indústria
- Participação dos serviços

---

## resultados_municipios.parquet

Indicador Criança Alfabetizada.

Campos:
- indicador_pct
- participacao_pct
- nivel

### Atenção
Pode causar leakage se utilizado no mesmo ano do alvo.

---

## resultados_uf.parquet

Resultado agregado por UF.

---

## metas_municipio.parquet

Metas futuras municipais.

Campos:
- meta_pct
- ano
- ano_fonte

---

## metas_uf.parquet

Metas estaduais.

---

## meta_brasil.parquet

Metas nacionais.

---

## municipio.parquet

Resultados agregados da mesma avaliação.

### Campos Críticos
- indicador_pct
- vl_media_lp
- pc_aluno_nivel_0_lp até pc_aluno_nivel_8_lp

### Risco
ALTO RISCO DE DATA LEAKAGE.
Usar apenas versões defasadas (t-1).

---

## uf.parquet

Mesmo conceito de municipio.parquet porém agregado por estado.

### Risco
ALTO RISCO DE DATA LEAKAGE.

---

# Recomendação de Modelagem

## Target
- alfabetizado

## Features Seguras
### Demográficas
- populacao
- densidade_hab_km2
- regiao
- uf

### Socioeconômicas
- media_inse
- pc_nivel_1 a pc_nivel_8
- pib_mil_reais

### Educacionais Históricas
- ideb_observado
- ideb_meta
- aprovacao_ai_pct
- aprovacao_1ano_pct
- aprovacao_2ano_pct

## Features com Leakage
- indicador_pct
- vl_media_lp
- pc_aluno_nivel_0_lp a pc_aluno_nivel_8_lp
- resultados do mesmo ano da avaliação-alvo
