# Dicionário de Dados

## Visão geral

| Nº | Arquivo | Descrição | Granularidade esperada |
|---:|---|---|---|
| 1 | `uf.parquet` | Resultados agregados de alfabetização por UF | Ano, UF, série e rede |
| 2 | `meta_alfabetizacao_brasil.parquet` | Resultados e metas nacionais de alfabetização | Ano e rede |
| 3 | `meta_alfabetizacao_uf.parquet` | Resultados e metas de alfabetização por UF | Ano, UF e rede |
| 4 | `meta_alfabetizacao_municipio.parquet` | Resultados e metas municipais de alfabetização | Ano, município e rede |
| 5 | `municipio.parquet` | Resultados agregados de alfabetização por município | Ano, município, série e rede |
| 6 | `alunos.parquet` | Microdados individualizados dos estudantes avaliados | Ano, aluno e aplicação |
| 7 | `pib_municipal.json` | Indicadores econômicos municipais | Município, ano, variável e unidade |
| 8 | `censo_2022.json` | Indicadores territoriais e demográficos municipais | Município, ano, variável e unidade |
| 9 | `ibge_estados.parquet` | Dimensão geográfica de estados e regiões | Estado |
| 10 | `ibge_municipios.parquet` | Dimensão geográfica de municípios | Município |

---

## 1. `uf.parquet`

### Descrição

Resultados agregados da avaliação de alfabetização por ano, Unidade da Federação, série e rede de ensino.

### Granularidade

Uma linha por combinação de:

`ano + sigla_uf + serie + rede`

### Chave sugerida

`ano`, `sigla_uf`, `serie`, `rede`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de aplicação da avaliação estadual. |
| `sigla_uf` | `STRING` | Não | Sigla de duas letras da Unidade da Federação. |
| `serie` | `INT` | Não | Código do ano ou série escolar avaliada. |
| `rede` | `STRING` | Não | Código ou identificação da rede de ensino avaliada. |
| `taxa_alfabetizacao` | `DOUBLE` | Sim | Percentual de estudantes avaliados considerados alfabetizados. |
| `media_portugues` | `DOUBLE` | Sim | Média ponderada em Língua Portuguesa, equalizada com a escala do Saeb. |
| `proporcao_aluno_nivel_0` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 0. |
| `proporcao_aluno_nivel_1` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 1. |
| `proporcao_aluno_nivel_2` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 2. |
| `proporcao_aluno_nivel_3` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 3. |
| `proporcao_aluno_nivel_4` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 4. |
| `proporcao_aluno_nivel_5` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 5. |
| `proporcao_aluno_nivel_6` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 6. |
| `proporcao_aluno_nivel_7` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 7. |
| `proporcao_aluno_nivel_8` | `DOUBLE` | Sim | Percentual de estudantes classificados no nível de desempenho 8. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão do registro. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| UF válida | `sigla_uf` deve possuir duas letras e existir na dimensão de estados. |
| Percentuais válidos | Taxas e proporções devem estar entre 0 e 100. |
| Soma dos níveis | Quando preenchidos, os níveis 0 a 8 devem somar aproximadamente 100. |
| Unicidade | Não deve haver duplicidade na chave sugerida. |

---

## 2. `meta_alfabetizacao_brasil.parquet`

### Descrição

Resultados observados, metas anuais e percentual de participação da avaliação de alfabetização no Brasil.

### Granularidade

Uma linha por combinação de:

`ano + rede`

### Chave sugerida

`ano`, `rede`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de referência do resultado nacional observado. |
| `rede` | `STRING` | Não | Rede de ensino representada pelo resultado nacional. |
| `taxa_alfabetizacao` | `DOUBLE` | Sim | Percentual nacional observado de estudantes alfabetizados. |
| `meta_alfabetizacao_2024` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2024. |
| `meta_alfabetizacao_2025` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2025. |
| `meta_alfabetizacao_2026` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2026. |
| `meta_alfabetizacao_2027` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2027. |
| `meta_alfabetizacao_2028` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2028. |
| `meta_alfabetizacao_2029` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2029. |
| `meta_alfabetizacao_2030` | `DOUBLE` | Sim | Meta nacional de alfabetização para 2030. |
| `percentual_participacao` | `DOUBLE` | Sim | Percentual de participação dos estudantes elegíveis na avaliação. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Percentuais válidos | Resultados, metas e participação devem estar entre 0 e 100. |
| Unicidade | Não deve haver duplicidade por `ano` e `rede`. |
| Evolução das metas | Verificar se as metas seguem a trajetória esperada até 2030. |
| Ausência de resultado | Resultado nulo não deve ser transformado automaticamente em zero. |

---

## 3. `meta_alfabetizacao_uf.parquet`

### Descrição

Resultados observados, metas anuais e percentual de participação por Unidade da Federação.

### Granularidade

Uma linha por combinação de:

`ano + sigla_uf + rede`

### Chave sugerida

`ano`, `sigla_uf`, `rede`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de referência do resultado estadual. |
| `sigla_uf` | `STRING` | Não | Sigla da Unidade da Federação. |
| `rede` | `STRING` | Não | Rede de ensino considerada no resultado. |
| `taxa_alfabetizacao` | `DOUBLE` | Sim | Percentual estadual observado de estudantes alfabetizados. |
| `meta_alfabetizacao_2024` | `DOUBLE` | Sim | Meta estadual para 2024. |
| `meta_alfabetizacao_2025` | `DOUBLE` | Sim | Meta estadual para 2025. |
| `meta_alfabetizacao_2026` | `DOUBLE` | Sim | Meta estadual para 2026. |
| `meta_alfabetizacao_2027` | `DOUBLE` | Sim | Meta estadual para 2027. |
| `meta_alfabetizacao_2028` | `DOUBLE` | Sim | Meta estadual para 2028. |
| `meta_alfabetizacao_2029` | `DOUBLE` | Sim | Meta estadual para 2029. |
| `meta_alfabetizacao_2030` | `DOUBLE` | Sim | Meta estadual para 2030. |
| `percentual_participacao` | `DOUBLE` | Sim | Percentual de participação dos estudantes na avaliação. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| UF válida | A UF deve existir na dimensão `ibge_estados`. |
| Percentuais válidos | Resultados, metas e participação devem estar entre 0 e 100. |
| Unicidade | Não deve haver duplicidade por `ano`, `sigla_uf` e `rede`. |
| Valores ausentes | Valores nulos devem ser mantidos como ausência de informação. |

---

## 4. `meta_alfabetizacao_municipio.parquet`

### Descrição

Resultados observados, metas anuais, nível de alfabetização e participação por município.

### Granularidade

Uma linha por combinação de:

`ano + id_municipio + rede`

### Chave sugerida

`ano`, `id_municipio`, `rede`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de referência do resultado municipal. |
| `id_municipio` | `STRING` | Não | Código IBGE do município com sete dígitos. |
| `rede` | `STRING` | Não | Rede de ensino avaliada, como Municipal. |
| `taxa_alfabetizacao` | `DOUBLE` | Sim | Percentual observado de estudantes alfabetizados no município. |
| `meta_alfabetizacao_2024` | `DOUBLE` | Sim | Meta municipal para 2024. |
| `meta_alfabetizacao_2025` | `DOUBLE` | Sim | Meta municipal para 2025. |
| `meta_alfabetizacao_2026` | `DOUBLE` | Sim | Meta municipal para 2026. |
| `meta_alfabetizacao_2027` | `DOUBLE` | Sim | Meta municipal para 2027. |
| `meta_alfabetizacao_2028` | `DOUBLE` | Sim | Meta municipal para 2028. |
| `meta_alfabetizacao_2029` | `DOUBLE` | Sim | Meta municipal para 2029. |
| `meta_alfabetizacao_2030` | `DOUBLE` | Sim | Meta municipal para 2030. |
| `nivel_alfabetizacao` | `INT` | Sim | Código da classificação do nível de alfabetização do município. |
| `percentual_participacao` | `DOUBLE` | Sim | Percentual de participação dos estudantes na avaliação. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Município válido | `id_municipio` deve possuir sete dígitos e existir na dimensão municipal. |
| Percentuais válidos | Resultados, metas e participação devem estar entre 0 e 100. |
| Nível válido | O domínio de `nivel_alfabetizacao` deve ser validado no dicionário da fonte. |
| Unicidade | Não deve haver duplicidade por `ano`, `id_municipio` e `rede`. |

---

## 5. `municipio.parquet`

### Descrição

Resultados agregados da avaliação de alfabetização por município, ano, série e rede.

### Granularidade

Uma linha por combinação de:

`ano + id_municipio + serie + rede`

### Chave sugerida

`ano`, `id_municipio`, `serie`, `rede`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de aplicação da avaliação. |
| `id_municipio` | `STRING` | Não | Código IBGE do município com sete dígitos. |
| `serie` | `INT` | Não | Código do ano ou série escolar avaliada. |
| `rede` | `STRING` | Não | Código ou identificação da rede de ensino. |
| `taxa_alfabetizacao` | `DOUBLE` | Sim | Percentual de estudantes avaliados considerados alfabetizados. |
| `media_portugues` | `DOUBLE` | Sim | Média ponderada municipal em Língua Portuguesa. |
| `proporcao_aluno_nivel_0` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 0. |
| `proporcao_aluno_nivel_1` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 1. |
| `proporcao_aluno_nivel_2` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 2. |
| `proporcao_aluno_nivel_3` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 3. |
| `proporcao_aluno_nivel_4` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 4. |
| `proporcao_aluno_nivel_5` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 5. |
| `proporcao_aluno_nivel_6` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 6. |
| `proporcao_aluno_nivel_7` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 7. |
| `proporcao_aluno_nivel_8` | `DOUBLE` | Sim | Percentual municipal de estudantes no nível 8. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Município válido | O município deve existir na dimensão `ibge_municipios`. |
| Percentuais válidos | Taxas e proporções devem estar entre 0 e 100. |
| Soma dos níveis | Quando preenchidos, os níveis devem somar aproximadamente 100. |
| Unicidade | Não deve haver duplicidade na chave sugerida. |

---

## 6. `alunos.parquet`

### Descrição

Microdados dos estudantes participantes da avaliação de alfabetização.

### Granularidade

Uma linha por estudante em cada aplicação da avaliação.

### Chave candidata

`ano`, `id_aluno`, `caderno`

A unicidade da chave deve ser validada antes da criação da tabela Silver.

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `ano` | `INT` | Não | Ano de aplicação da avaliação. |
| `id_municipio` | `STRING` | Não | Código IBGE do município associado ao estudante ou escola. |
| `id_escola` | `STRING` | Não | Identificador da escola, normalmente correspondente ao código INEP. |
| `id_aluno` | `STRING` | Não | Identificador técnico do estudante na avaliação. |
| `caderno` | `INT` | Sim | Código da versão ou caderno de prova aplicado. |
| `serie` | `INT` | Não | Código do ano ou série escolar do estudante. |
| `rede` | `STRING` | Não | Código da rede de ensino do estudante. |
| `presenca` | `INT` ou `BOOLEAN` | Sim | Indicador de presença do estudante na avaliação. |
| `preenchimento_caderno` | `INT` ou `BOOLEAN` | Sim | Indicador de preenchimento válido do caderno. |
| `alfabetizado` | `INT` ou `BOOLEAN` | Sim | Indicador de classificação do estudante como alfabetizado. |
| `proficiencia` | `DOUBLE` | Sim | Pontuação estimada do estudante na escala de proficiência. |
| `peso_aluno` | `DOUBLE` | Sim | Peso associado ao estudante para estimativas representativas. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source_table` | `STRING` | Não | Nome da tabela de origem. |

### Uso no modelo de Machine Learning

| Campo | Papel |
|---|---|
| `alfabetizado` | Variável-alvo do modelo de classificação. |
| `peso_aluno` | Possível peso amostral no treinamento e nas métricas. |
| `id_aluno` | Identificador para auditoria. Não deve ser utilizado diretamente como feature. |
| `id_escola` | Identificador ou variável de agrupamento. Não deve ser tratado como número contínuo. |
| `id_municipio` | Chave de integração e possível agrupamento da validação. |
| `proficiencia` | Vazamento direto de dados. Não utilizar como feature para prever `alfabetizado`. |
| `presenca` | Filtro de elegibilidade, após validação dos códigos. |
| `preenchimento_caderno` | Filtro de validade do registro, após validação dos códigos. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Target válido | `alfabetizado` deve conter somente os valores previstos pelo domínio oficial. |
| Identificadores | IDs devem ser armazenados como texto. |
| Peso válido | `peso_aluno` deve ser maior que zero quando informado. |
| Proficiência | Valores devem respeitar os limites da escala da avaliação. |
| Duplicidade | Validar a unicidade por aluno, ano e aplicação. |

---

## 7. `pib_municipal.json`

### Descrição

Indicadores econômicos municipais em formato longo.

### Granularidade

Uma linha por combinação de:

`Município (Código) + Ano + Variável (Código) + Unidade de Medida (Código)`

### Campos

| Campo original | Nome Silver sugerido | Tipo recomendado | Aceita nulo | Descrição |
|---|---|---|:---:|---|
| `Nível Territorial (Código)` | `nivel_territorial_codigo` | `STRING` | Não | Código do nível geográfico. |
| `Nível Territorial` | `nivel_territorial_nome` | `STRING` | Não | Nome do nível geográfico, como Município. |
| `Unidade de Medida (Código)` | `unidade_medida_codigo` | `STRING` | Não | Código da unidade de medida. |
| `Unidade de Medida` | `unidade_medida_nome` | `STRING` | Não | Nome da unidade, como Mil Reais ou percentual. |
| `Valor` | `valor` | `DOUBLE` | Sim | Valor da variável econômica. |
| `Município (Código)` | `id_municipio` | `STRING` | Não | Código IBGE do município com sete dígitos. |
| `Município` | `municipio_nome_original` | `STRING` | Não | Nome do município conforme retornado pela fonte. |
| `Variável (Código)` | `variavel_codigo` | `STRING` | Não | Código da variável econômica. |
| `Variável` | `variavel_nome` | `STRING` | Não | Descrição da variável econômica. |
| `Ano (Código)` | `ano_codigo` | `STRING` | Não | Código do período de referência. |
| `Ano` | `ano` | `INT` | Não | Ano de referência do indicador econômico. |

### Domínios observados

| Campo | Código | Descrição observada |
|---|---:|---|
| `variavel_codigo` | `37` | Produto Interno Bruto a preços correntes. |
| `variavel_codigo` | `516` | Participação do valor adicionado bruto, conforme descrição completa da fonte. |
| `unidade_medida_codigo` | `40` | Mil Reais. |
| `unidade_medida_codigo` | `2` | Percentual. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Município válido | O código deve possuir sete dígitos e existir na dimensão municipal. |
| Unidade compatível | Cada variável deve ser interpretada com sua respectiva unidade. |
| Valor numérico | Pontos e vírgulas decimais devem ser padronizados antes da conversão. |
| Unicidade | Não deve haver duplicidade por município, ano, variável e unidade. |

---

## 8. `censo_2022.json`

### Descrição

Indicadores territoriais e demográficos municipais do Censo 2022 em formato longo.

### Granularidade

Uma linha por combinação de:

`Município (Código) + Ano + Variável (Código) + Unidade de Medida (Código)`

### Campos

| Campo original | Nome Silver sugerido | Tipo recomendado | Aceita nulo | Descrição |
|---|---|---|:---:|---|
| `Nível Territorial (Código)` | `nivel_territorial_codigo` | `STRING` | Não | Código do nível geográfico. |
| `Nível Territorial` | `nivel_territorial_nome` | `STRING` | Não | Nome do nível geográfico, como Município. |
| `Unidade de Medida (Código)` | `unidade_medida_codigo` | `STRING` | Não | Código da unidade de medida. |
| `Unidade de Medida` | `unidade_medida_nome` | `STRING` | Não | Nome da unidade de medida. |
| `Valor` | `valor` | `DOUBLE` | Sim | Valor observado para a variável censitária. |
| `Município (Código)` | `id_municipio` | `STRING` | Não | Código IBGE do município com sete dígitos. |
| `Município` | `municipio_nome_original` | `STRING` | Não | Nome do município conforme retornado pela fonte. |
| `Variável (Código)` | `variavel_codigo` | `STRING` | Não | Código da variável censitária. |
| `Variável` | `variavel_nome` | `STRING` | Não | Descrição da variável censitária. |
| `Ano (Código)` | `ano_codigo` | `STRING` | Não | Código do período censitário. |
| `Ano` | `ano` | `INT` | Não | Ano de referência do Censo. |

### Domínios observados

| Campo | Código | Descrição observada |
|---|---:|---|
| `variavel_codigo` | `93` | População residente. |
| `variavel_codigo` | `6318` | Área da unidade territorial. |
| `unidade_medida_codigo` | `45` | Pessoas. |
| `unidade_medida_codigo` | `26` | Quilômetros quadrados. |

### Indicador derivado

| Indicador | Fórmula | Unidade |
|---|---|---|
| `densidade_demografica` | `populacao_residente / area_km2` | Habitantes por km² |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Município válido | O código deve possuir sete dígitos e existir na dimensão municipal. |
| População válida | A população deve ser maior ou igual a zero. |
| Área válida | A área deve ser maior que zero. |
| Unidade compatível | A unidade deve corresponder à variável consultada. |
| Unicidade | Não deve haver duplicidade por município, ano, variável e unidade. |

---

## 9. `ibge_estados.parquet`

### Descrição

Dimensão territorial das Unidades da Federação e grandes regiões brasileiras.

### Granularidade

Uma linha por Unidade da Federação.

### Chave primária sugerida

`estado_id`

### Chave alternativa

`estado_sigla`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `estado_id` | `STRING` | Não | Código IBGE da Unidade da Federação. |
| `estado_sigla` | `STRING` | Não | Sigla de duas letras da Unidade da Federação. |
| `estado_nome` | `STRING` | Não | Nome oficial da Unidade da Federação. |
| `regiao_id` | `STRING` | Não | Código IBGE da grande região. |
| `regiao_sigla` | `STRING` | Não | Sigla da grande região, como N ou NE. |
| `regiao_nome` | `STRING` | Não | Nome da grande região brasileira. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source` | `STRING` | Não | Endereço ou identificação da fonte de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Estado único | `estado_id` e `estado_sigla` devem ser únicos. |
| Sigla válida | `estado_sigla` deve possuir duas letras. |
| Região preenchida | Todo estado deve estar associado a uma grande região. |
| Integridade | Nome, sigla e código devem representar a mesma UF. |

---

## 10. `ibge_municipios.parquet`

### Descrição

Dimensão territorial dos municípios brasileiros, contendo vínculos com estado, região, microrregião, mesorregião, região imediata e região intermediária.

### Granularidade

Uma linha por município.

### Chave primária sugerida

`municipio_id`

### Campos

| Campo | Tipo recomendado | Aceita nulo | Descrição |
|---|---|:---:|---|
| `municipio_id` | `STRING` | Não | Código IBGE do município com sete dígitos. |
| `municipio_nome` | `STRING` | Não | Nome oficial do município. |
| `microrregiao_id` | `STRING` | Sim | Código da microrregião associada ao município. |
| `microrregiao_nome` | `STRING` | Sim | Nome da microrregião. |
| `mesorregiao_id` | `STRING` | Sim | Código da mesorregião associada ao município. |
| `mesorregiao_nome` | `STRING` | Sim | Nome da mesorregião. |
| `estado_id` | `STRING` | Não | Código IBGE da Unidade da Federação. |
| `estado_sigla` | `STRING` | Não | Sigla da Unidade da Federação. |
| `estado_nome` | `STRING` | Não | Nome da Unidade da Federação. |
| `regiao_id` | `STRING` | Não | Código da grande região brasileira. |
| `regiao_sigla` | `STRING` | Não | Sigla da grande região brasileira. |
| `regiao_nome` | `STRING` | Não | Nome da grande região brasileira. |
| `regiao_imediata_id` | `STRING` | Sim | Código da região geográfica imediata. |
| `regiao_imediata_nome` | `STRING` | Sim | Nome da região geográfica imediata. |
| `regiao_intermediaria_id` | `STRING` | Sim | Código da região geográfica intermediária. |
| `regiao_intermediaria_nome` | `STRING` | Sim | Nome da região geográfica intermediária. |
| `ri_estado_id` | `STRING` | Sim | Código do estado retornado na estrutura da região intermediária. |
| `ri_estado_sigla` | `STRING` | Sim | Sigla do estado retornada na estrutura da região intermediária. |
| `ri_estado_nome` | `STRING` | Sim | Nome do estado retornado na estrutura da região intermediária. |
| `ri_regiao_id` | `STRING` | Sim | Código da região retornado na estrutura da região intermediária. |
| `ri_regiao_sigla` | `STRING` | Sim | Sigla da região retornada na estrutura da região intermediária. |
| `ri_regiao_nome` | `STRING` | Sim | Nome da região retornada na estrutura da região intermediária. |
| `_ingested_at` | `TIMESTAMP` | Não | Data e horário UTC de ingestão. |
| `_source` | `STRING` | Não | Endereço ou identificação da fonte de origem. |

### Regras de qualidade

| Regra | Validação |
|---|---|
| Município único | `municipio_id` deve ser único. |
| Código válido | O código municipal deve possuir sete dígitos. |
| Estado válido | `estado_id` deve existir na dimensão de estados. |
| Consistência estadual | Sigla, nome e código do estado devem ser consistentes. |
| Consistência regional | Região do município deve ser igual à região associada ao estado. |

---

# Relacionamentos entre as tabelas

| Tabela de origem | Campo | Tabela de destino | Campo | Cardinalidade esperada |
|---|---|---|---|---|
| `alunos` | `id_municipio` | `ibge_municipios` | `municipio_id` | Muitos para um |
| `municipio` | `id_municipio` | `ibge_municipios` | `municipio_id` | Muitos para um |
| `meta_alfabetizacao_municipio` | `id_municipio` | `ibge_municipios` | `municipio_id` | Muitos para um |
| `pib_municipal` | `Município (Código)` | `ibge_municipios` | `municipio_id` | Muitos para um |
| `censo_2022` | `Município (Código)` | `ibge_municipios` | `municipio_id` | Muitos para um |
| `ibge_municipios` | `estado_id` | `ibge_estados` | `estado_id` | Muitos para um |
| `uf` | `sigla_uf` | `ibge_estados` | `estado_sigla` | Muitos para um |
| `meta_alfabetizacao_uf` | `sigla_uf` | `ibge_estados` | `estado_sigla` | Muitos para um |

---

# Campos com domínio pendente de validação

| Campo | Tabelas | Validação necessária |
|---|---|---|
| `rede` | `uf`, `municipio`, `alunos` | Traduzir os códigos numéricos de rede conforme o dicionário oficial. |
| `serie` | `uf`, `municipio`, `alunos` | Confirmar o significado de cada código de série. |
| `presenca` | `alunos` | Confirmar qual código representa presença, ausência ou situação inválida. |
| `preenchimento_caderno` | `alunos` | Confirmar a semântica dos códigos existentes. |
| `alfabetizado` | `alunos` | Confirmar o domínio e o tratamento dos valores ausentes. |
| `caderno` | `alunos` | Identificar as versões de prova representadas pelos códigos. |
| `nivel_alfabetizacao` | `meta_alfabetizacao_municipio` | Associar cada código à classificação oficial. |

---

# Convenções recomendadas

| Item | Convenção |
|---|---|
| Identificadores | Armazenar como `STRING`, mesmo quando formados apenas por números. |
| Percentuais | Armazenar como `DOUBLE`, na escala de 0 a 100. |
| Datas de ingestão | Armazenar em UTC no tipo `TIMESTAMP`. |
| Valores ausentes | Manter como `NULL`. Não substituir automaticamente por zero. |
| Código municipal | Padronizar com sete dígitos. |
| Código de UF | Padronizar com duas letras maiúsculas. |
| Nomes de colunas | Utilizar `snake_case`, sem espaços, acentos ou caracteres especiais. |
| Rastreabilidade | Preservar `_ingested_at`, `_source` e `_source_table`. |
| Ano de referência | Manter separado da data de ingestão do arquivo. |
| Data do lote | Utilizar `2026-10-19` como data de processamento ou ingestão do lote. |

---

# Observações para Machine Learning

| Coluna | Classificação | Orientação |
|---|---|---|
| `alfabetizado` | Target | Utilizar como variável-alvo. |
| `proficiencia` | Vazamento direto | Não utilizar como feature para prever `alfabetizado`. |
| `id_aluno` | Identificador | Não utilizar como variável numérica. |
| `id_escola` | Identificador ou grupo | Pode ser utilizado para divisão agrupada, mas não como número contínuo. |
| `id_municipio` | Identificador ou grupo | Utilizar para integração e separação agrupada. |
| `peso_aluno` | Peso amostral | Avaliar uso no treinamento e nas métricas. |
| `taxa_alfabetizacao` do mesmo ano | Possível vazamento | Utilizar somente após análise temporal. |
| `media_portugues` do mesmo ano | Possível vazamento | Preferir valores históricos de anos anteriores. |
| Proporções dos níveis do mesmo ano | Possível vazamento | Preferir versões defasadas. |
| PIB municipal | Feature contextual | Preservar o ano de referência do indicador. |
| População | Feature contextual | Preservar o ano de referência censitário. |
| Densidade demográfica | Feature derivada | Calcular como população dividida pela área. |
| Região e UF | Features territoriais | Codificar como variáveis categóricas. |
