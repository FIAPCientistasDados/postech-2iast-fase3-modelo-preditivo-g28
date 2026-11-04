# Dicionário de Dados Consolidado · Camada Silver

## 1. Visão geral

Este documento consolida as tabelas da camada Silver utilizadas no Tech Challenge Fase 3 para análise e modelagem da alfabetização. Para cada fonte, são apresentados:

- grão da tabela;
- finalidade analítica;
- campo;
- tipo recomendado;
- descrição;
- observações de uso na modelagem.

> **Importante:** os tipos abaixo são tipos analíticos recomendados. Antes da modelagem, o schema físico dos arquivos Parquet deve ser validado com `pyarrow` ou `pandas`, pois alguns códigos podem ter sido armazenados como números na origem. Identificadores, como código IBGE, aluno e escola, devem ser tratados como texto para preservar zeros à esquerda e impedir operações matemáticas sem sentido.

---

## 2. Catálogo das fontes

| Arquivo | Fonte temática | Grão | Finalidade principal |
|---|---|---|---|
| `alunos.parquet` | Microdados da avaliação de alfabetização | ano × aluno | Target individual, presença, proficiência e peso amostral |
| `censo_2022_municipios.parquet` | Censo Demográfico 2022 | município | População, área e densidade territorial |
| `dim_estados.parquet` | Dimensão geográfica | UF | Padronização de estados e regiões |
| `dim_municipios.parquet` | Dimensão geográfica | município | Padronização de municípios e relacionamentos territoriais |
| `ideb_anos_iniciais.parquet` | IDEB e rendimento escolar | ano × município × rede | Histórico educacional anterior ao alvo |
| `inse_2023_municipios.parquet` | INSE | município × recorte da fonte | Contexto socioeconômico dos estudantes |
| `pib_municipal.parquet` | PIB dos municípios | ano × município | Contexto econômico e composição do VAB |
| `resultados_municipios.parquet` | Indicador Criança Alfabetizada | ano × município × rede | Resultado oficial municipal e participação |
| `resultados_uf.parquet` | Indicador Criança Alfabetizada | ano × UF × rede | Resultado agregado estadual |
| `metas_municipio.parquet` | Metas de alfabetização | ano-meta × município × rede | Meta anual por município |
| `metas_uf.parquet` | Metas de alfabetização | ano-meta × UF × rede | Meta anual por UF |
| `meta_brasil.parquet` | Metas de alfabetização | ano-meta × rede | Referência nacional |
| `municipio.parquet` | Agregado da mesma avaliação | ano × município × rede | Estatísticas agregadas da prova por município |
| `uf.parquet` | Agregado da mesma avaliação | ano × UF × rede | Estatísticas agregadas da prova por UF |

---

## 3. Convenções de tipos

| Tipo lógico | Uso recomendado |
|---|---|
| `string` | Identificadores, códigos, nomes, siglas e categorias |
| `int64` | Anos, contagens e códigos sem risco de perda de zeros à esquerda |
| `float64` | Percentuais, notas, proficiências, pesos, valores monetários e taxas |
| `boolean` | Indicadores binários de presença, preenchimento e flags |
| `datetime64[ns]` | Datas e horários de processamento |
| `category` | Variáveis categóricas com domínio controlado durante a modelagem |

---

# 4. Dicionário por arquivo

## 4.1 `alunos.parquet`

**Descrição:** base granular dos estudantes listados para a avaliação. O universo válido do target é composto por estudantes presentes e com prova de Língua Portuguesa preenchida.

**Grão:** `ano × id_aluno`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `nu_ano_avaliacao` | `int64` | Ano em que a avaliação foi aplicada | Variável temporal da fonte |
| `ano` | `int64` | Ano de referência padronizado | Usado em filtros e alinhamento temporal |
| `co_uf` | `string` | Código da Unidade Federativa | Tratar como identificador, não como medida |
| `sigla_uf` | `category` | Sigla da Unidade Federativa | Feature categórica contextual |
| `id_aluno` | `string` | Identificador único do aluno | Chave técnica; não usar como feature |
| `tp_serie` | `category` | Série ou etapa escolar avaliada | Feature categórica quando houver variação válida |
| `id_escola` | `string` | Identificador da escola nos microdados | Chave de agrupamento; não usar como número |
| `tp_dependencia` | `category` | Dependência administrativa da escola | Ex.: federal, estadual, municipal ou privada, conforme domínio da fonte |
| `id_municipio` | `string` | Código IBGE do município | Chave de relacionamento territorial |
| `no_municipio` | `string` | Nome do município | Campo descritivo; não usar diretamente no modelo |
| `presente` | `boolean` | Indica presença do estudante na avaliação | Define o universo elegível ao target |
| `in_preenchimento_lp` | `boolean` | Indica preenchimento da prova de Língua Portuguesa | Deve ser verdadeiro para o target observado |
| `co_caderno_lp` | `string` | Código do caderno de prova de Língua Portuguesa | Metadado da aplicação; avaliar risco de informação pós-aplicação |
| `vl_peso_aluno_lp` | `float64` | Peso amostral do estudante em Língua Portuguesa | Usado em métricas e agregações ponderadas |
| `proficiencia` | `float64` | Proficiência do estudante em Língua Portuguesa | Origina o target; **não usar como feature para prever `alfabetizado`** |
| `alfabetizado` | `int64` ou `boolean` | Target: 0 = não alfabetizado; 1 = alfabetizado | Definido pelo corte de proficiência; usar somente para presentes com prova preenchida |
| `co_bloco_1` a `co_bloco_4` | `string` | Código dos blocos de questões aplicados | Metadado da prova; não usar sem análise de leakage |
| `tx_resposta_bloco_1` a `tx_resposta_bloco_4` | `string` | Sequência de respostas do estudante | Informação da mesma prova; alto risco de target circular |
| `tx_gabarito_bloco_1` a `tx_gabarito_bloco_4` | `string` | Sequência de gabaritos oficiais | Não usar para produzir features do modelo principal |
| `_arquivo_fonte` | `string` | Nome ou caminho lógico do arquivo de origem | Linhagem e auditoria |
| `_processed_at` | `datetime64[ns]` | Data e hora do processamento | Metadado técnico; não usar como feature |

### Regras de modelagem

- Target principal: `alfabetizado`.
- Filtrar `presente = 1` e `in_preenchimento_lp = 1`.
- Não transformar ausência em `alfabetizado = 0`.
- Não usar `proficiencia`, respostas ou gabaritos para prever `alfabetizado`.
- Usar `vl_peso_aluno_lp` nas métricas ponderadas, quando aplicável.

---

## 4.2 `censo_2022_municipios.parquet`

**Descrição:** informações demográficas e territoriais dos municípios.

**Grão:** município.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `id_municipio` | `string` | Código IBGE do município | Chave de relacionamento |
| `nome_municipio` | `string` | Nome oficial do município | Campo descritivo |
| `area_km2` | `float64` | Área territorial do município em km² | Feature territorial; candidata a `log1p` |
| `densidade_hab_km2` | `float64` | Habitantes por km² | Feature territorial; candidata a `log1p` |
| `populacao` | `int64` | População residente | Feature de porte; candidata a `log1p` |
| `ano_referencia` | `int64` | Ano de referência da informação censitária | Controle de defasagem temporal |

---

## 4.3 `dim_estados.parquet`

**Descrição:** dimensão de Unidades Federativas e regiões brasileiras.

**Grão:** UF.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `id_uf` | `string` | Código IBGE da UF | Chave geográfica |
| `sigla_uf` | `category` | Sigla da UF | Feature categórica e chave de relacionamento |
| `nome_uf` | `string` | Nome da Unidade Federativa | Campo descritivo |
| `nome_regiao` | `category` | Macrorregião geográfica | Feature categórica e análise territorial |

---

## 4.4 `dim_municipios.parquet`

**Descrição:** dimensão municipal usada para padronizar nomes, códigos e relacionamentos territoriais.

**Grão:** município.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `id_municipio` | `string` | Código IBGE do município | Chave principal |
| `nome_municipio` | `string` | Nome oficial do município | Campo descritivo |
| `id_uf` | `string` | Código IBGE da UF | Chave estrangeira para estados |
| `sigla_uf` | `category` | Sigla da UF | Feature contextual e relacionamento |
| `nome_uf` | `string` | Nome da Unidade Federativa | Campo descritivo |
| `nome_regiao` | `category` | Região geográfica do município | Análise territorial e segmentação |

---

## 4.5 `ideb_anos_iniciais.parquet`

**Descrição:** histórico de rendimento, notas e IDEB dos anos iniciais do ensino fundamental.

**Grão:** `ano × município × rede`, conforme disponibilidade da fonte.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano ou edição de referência do IDEB | Deve ser anterior ao ano-alvo |
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `rede` | `category` | Rede de ensino do indicador | Preservar no grão ou filtrar explicitamente |
| `aprovacao_ai_pct` | `float64` | Taxa de aprovação nos anos iniciais, em % | Feature histórica |
| `aprovacao_1ano_pct` | `float64` | Taxa de aprovação no 1º ano, em % | Feature histórica |
| `aprovacao_2ano_pct` | `float64` | Taxa de aprovação no 2º ano, em % | Feature histórica |
| `ideb_rendimento` | `float64` | Componente de rendimento usado no IDEB | Altamente correlacionado com aprovação |
| `ideb_nota_matematica` | `float64` | Nota de Matemática na avaliação correspondente | Utilizar somente edição anterior ao alvo |
| `ideb_nota_portugues` | `float64` | Nota de Língua Portuguesa na avaliação correspondente | Utilizar somente edição anterior ao alvo |
| `ideb_nota_media` | `float64` | Nota média de desempenho educacional | Pode ser redundante com as notas por área |
| `ideb_observado` | `float64` | IDEB observado | Feature histórica importante |
| `ideb_meta` | `float64` | Meta do IDEB para o recorte | Verificar disponibilidade temporal antes do uso |

### Regra temporal

Para prever um resultado no ano `t`, utilizar somente a última edição do IDEB disponível antes de `t`.

---

## 4.6 `inse_2023_municipios.parquet`

**Descrição:** nível socioeconômico médio e distribuição dos estudantes por níveis socioeconômicos.

**Grão:** município, possivelmente combinado com rede, localização ou outro recorte da publicação.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `ano` ou `ano_referencia` | `int64` | Ano de referência do INSE | Controle de defasagem |
| `media_inse` | `float64` | Nível socioeconômico médio | Feature socioeconômica |
| `qtd_alunos_inse` | `int64` | Quantidade de estudantes considerados no cálculo | Medida de cobertura; candidata a `log1p` |
| `pc_nivel_1` | `float64` | Percentual de estudantes no nível socioeconômico 1 | Composição socioeconômica |
| `pc_nivel_2` | `float64` | Percentual de estudantes no nível socioeconômico 2 | Composição socioeconômica |
| `pc_nivel_3` | `float64` | Percentual de estudantes no nível socioeconômico 3 | Composição socioeconômica |
| `pc_nivel_4` | `float64` | Percentual de estudantes no nível socioeconômico 4 | Composição socioeconômica |
| `pc_nivel_5` | `float64` | Percentual de estudantes no nível socioeconômico 5 | Composição socioeconômica |
| `pc_nivel_6` | `float64` | Percentual de estudantes no nível socioeconômico 6 | Composição socioeconômica |
| `pc_nivel_7` | `float64` | Percentual de estudantes no nível socioeconômico 7 | Composição socioeconômica |
| `pc_nivel_8` | `float64` | Percentual de estudantes no nível socioeconômico 8 | Alta ausência observada; avaliar ablação |
| `tp_localizacao` | `category` | Localização urbana ou rural, conforme domínio da fonte | Feature contextual |
| `tp_capital` | `boolean` ou `category` | Indica se o município é capital | Feature territorial |
| `tp_tipo_rede` | `category` | Tipo de rede considerada | Preservar o grão ou filtrar explicitamente |

---

## 4.7 `pib_municipal.parquet`

**Descrição:** indicadores econômicos municipais e componentes do Valor Adicionado Bruto.

**Grão:** `ano × município`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `ano_pib` | `int64` | Ano de referência dos dados econômicos | Controle de defasagem |
| `pib_mil_reais` | `float64` | Produto Interno Bruto, em milhares de reais | Candidata a `log1p` |
| `vab_agro_mil_reais` | `float64` | VAB da agropecuária, em milhares de reais | Base para participação setorial |
| `vab_industria_mil_reais` | `float64` | VAB da indústria, em milhares de reais | Base para participação setorial |
| `vab_servicos_mil_reais` | `float64` | VAB dos serviços, em milhares de reais | Base para participação setorial |
| `vab_adm_publica_mil_reais` | `float64` | VAB da administração pública, em milhares de reais | Base para participação setorial |

### Features derivadas

| Feature derivada | Tipo | Definição analítica |
|---|---|---|
| `pib_per_capita_reais` | `float64` | PIB dividido pela população, após compatibilização de unidade |
| `participacao_vab_agro_pct` | `float64` | Participação da agropecuária no total econômico usado como denominador |
| `participacao_vab_industria_pct` | `float64` | Participação da indústria |
| `participacao_vab_servicos_pct` | `float64` | Participação dos serviços |
| `participacao_vab_adm_publica_pct` | `float64` | Participação da administração pública |

> As fórmulas devem ser documentadas no código para deixar claro o denominador empregado.

---

## 4.8 `resultados_municipios.parquet`

**Descrição:** resultado municipal do Indicador Criança Alfabetizada.

**Grão:** `ano × município × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano do indicador | Chave temporal |
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `rede` | `category` | Rede de ensino do resultado | Preservar no grão |
| `indicador_pct` | `float64` | Percentual de estudantes alfabetizados | Target municipal no ano corrente; feature apenas se defasada |
| `participacao_pct` | `float64` | Percentual de participação na avaliação | Feature somente se disponível antes do alvo ou defasada |
| `nivel` | `string`, `category` ou `float64` | Nível ou classificação publicada | Confirmar domínio físico antes da modelagem |

### Risco de leakage

`indicador_pct` do mesmo ano não pode ser usado para prever `alfabetizado` ou o próprio resultado municipal do mesmo ciclo. Para modelagem temporal, criar versões como `indicador_t1` e `participacao_t1`.

---

## 4.9 `resultados_uf.parquet`

**Descrição:** resultado do Indicador Criança Alfabetizada agregado por Unidade Federativa.

**Grão:** `ano × UF × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano do indicador | Chave temporal |
| `id_uf` ou `co_uf` | `string` | Código IBGE da UF | Chave territorial |
| `sigla_uf` | `category` | Sigla da UF | Chave e categoria |
| `rede` | `category` | Rede de ensino | Parte do grão |
| `indicador_pct` | `float64` | Percentual estadual de estudantes alfabetizados | Alto risco de leakage no mesmo ano |
| `participacao_pct` | `float64` | Participação estadual na avaliação | Usar apenas se temporalmente disponível |
| `nivel` | `string`, `category` ou `float64` | Nível ou classificação publicada | Confirmar domínio físico |

---

## 4.10 `metas_municipio.parquet`

**Descrição:** metas anuais de alfabetização por município.

**Grão:** `ano-meta × município × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano para o qual a meta foi definida | Chave temporal da meta |
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `rede` | `category` | Rede de ensino da meta | Parte do grão |
| `meta_pct` | `float64` | Meta percentual de alfabetização | Usada após a previsão do nível para derivar risco |
| `ano_fonte` | `int64` | Ano da publicação ou origem da trajetória | Auditoria e alinhamento temporal |

---

## 4.11 `metas_uf.parquet`

**Descrição:** metas anuais de alfabetização por Unidade Federativa.

**Grão:** `ano-meta × UF × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano da meta | Chave temporal |
| `id_uf` ou `co_uf` | `string` | Código da UF | Chave territorial |
| `sigla_uf` | `category` | Sigla da UF | Chave descritiva |
| `rede` | `category` | Rede de ensino | Parte do grão |
| `meta_pct` | `float64` | Meta estadual de alfabetização | Comparações e monitoramento estadual |
| `ano_fonte` | `int64` | Ano da fonte da meta | Auditoria temporal |

---

## 4.12 `meta_brasil.parquet`

**Descrição:** metas nacionais de alfabetização.

**Grão:** `ano-meta × rede` ou `ano-meta`, conforme a publicação.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano da meta nacional | Chave temporal |
| `rede` | `category` | Rede ou recorte da meta, quando disponível | Confirmar domínio na fonte |
| `meta_pct` | `float64` | Meta nacional de alfabetização | Referência de contexto e comunicação |
| `ano_fonte` | `int64` | Ano da publicação | Auditoria temporal |

---

## 4.13 `municipio.parquet`

**Descrição:** agregados da avaliação no nível municipal, produzidos a partir da mesma aplicação da prova.

**Grão:** `ano × município × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano da avaliação | Chave temporal |
| `id_municipio` | `string` | Código IBGE do município | Chave territorial |
| `rede` | `category` | Rede de ensino | Parte do grão |
| `indicador_pct` | `float64` | Percentual agregado de alfabetizados | Alto risco de leakage no ano do target |
| `vl_media_lp` | `float64` | Proficiência média municipal em Língua Portuguesa | Alto risco de leakage no mesmo ciclo |
| `pc_aluno_nivel_0_lp` | `float64` | Percentual de estudantes no nível 0 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_1_lp` | `float64` | Percentual de estudantes no nível 1 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_2_lp` | `float64` | Percentual de estudantes no nível 2 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_3_lp` | `float64` | Percentual de estudantes no nível 3 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_4_lp` | `float64` | Percentual de estudantes no nível 4 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_5_lp` | `float64` | Percentual de estudantes no nível 5 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_6_lp` | `float64` | Percentual de estudantes no nível 6 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_7_lp` | `float64` | Percentual de estudantes no nível 7 de LP | Resultado da mesma avaliação; leakage |
| `pc_aluno_nivel_8_lp` | `float64` | Percentual de estudantes no nível 8 de LP | Resultado da mesma avaliação; leakage |

### Regra de segurança

Usar esses campos somente em versões defasadas, como `t-1`, quando forem conhecidos antes do resultado a ser previsto.

---

## 4.14 `uf.parquet`

**Descrição:** agregados da avaliação no nível estadual.

**Grão:** `ano × UF × rede`.

| Campo | Tipo recomendado | Descrição | Uso e observações |
|---|---|---|---|
| `ano` | `int64` | Ano da avaliação | Chave temporal |
| `id_uf` ou `co_uf` | `string` | Código da UF | Chave territorial |
| `sigla_uf` | `category` | Sigla da UF | Chave descritiva |
| `rede` | `category` | Rede de ensino | Parte do grão |
| `indicador_pct` | `float64` | Percentual estadual de alfabetizados | Alto risco de leakage no mesmo ano |
| `vl_media_lp` | `float64` | Proficiência média estadual | Alto risco de leakage no mesmo ano |
| `pc_aluno_nivel_0_lp` a `pc_aluno_nivel_8_lp` | `float64` | Distribuição estadual dos estudantes por nível | Resultado contemporâneo da mesma avaliação |

---

# 5. Classificação para modelagem

## 5.1 Targets

| Target | Grão | Tipo | Definição |
|---|---|---|---|
| `alfabetizado` | aluno | binário | 1 quando o estudante alcança o corte definido; 0 quando não alcança, apenas no universo avaliado válido |
| `indicador_t` | município | contínuo | Percentual municipal de alfabetizados no ano-alvo |
| `atingiu_meta_t` | município | binário | Indica se `indicador_t` alcançou `meta_t` |
| `gap_meta_t` | município | contínuo | Diferença entre o indicador observado e a meta do ano-alvo |

> `indicador_t`, `atingiu_meta_t` e `gap_meta_t` são resultados, não features do modelo municipal do mesmo ano.

## 5.2 Identificadores e campos descritivos

| Campo | Classificação | Regra |
|---|---|---|
| `id_aluno` | identificador | Excluir das features |
| `id_escola` | identificador/grupo | Usar para agrupamento e diagnóstico, não como número |
| `id_municipio` | identificador/grupo | Usar em joins, folds e relatórios; excluir como número |
| `id_uf`, `co_uf` | identificador | Preferir `sigla_uf` como categórica |
| nomes de município, UF e região | descritivo/categórico | Usar somente categorias explicitamente previstas |
| `_arquivo_fonte`, `_processed_at` | metadado | Excluir das features |

## 5.3 Variáveis demográficas e territoriais

| Campo | Tipo analítico | Uso recomendado |
|---|---|---|
| `sigla_uf` | categórica | Captura contexto estadual; interpretar sem causalidade |
| `nome_regiao` | categórica | Análise territorial e segmentação |
| `tp_localizacao` | categórica | Contexto urbano/rural |
| `tp_capital` | binária/categórica | Indica capital |
| `populacao` | numérica | Aplicar `log1p` |
| `area_km2` | numérica | Aplicar `log1p` |
| `densidade_hab_km2` | numérica | Aplicar `log1p` |

## 5.4 Variáveis socioeconômicas

| Campo | Tipo analítico | Uso recomendado |
|---|---|---|
| `media_inse` | numérica | Contexto socioeconômico |
| `qtd_alunos_inse` | numérica | Cobertura do INSE; aplicar `log1p` |
| `pc_nivel_1` a `pc_nivel_8` | numérica percentual | Imputar dentro da pipeline; avaliar colinearidade e ausência |
| `pib_mil_reais` | numérica monetária | Aplicar `log1p` |
| `pib_per_capita_reais` | numérica monetária | Aplicar `log1p` |
| componentes do VAB | numérica monetária | Preferir participações derivadas quando apropriado |
| participações setoriais do VAB | percentual | Contexto econômico e segmentação |

## 5.5 Variáveis educacionais históricas

| Campo | Tipo analítico | Regra temporal |
|---|---|---|
| `indicador_t1` | numérica percentual | Resultado do ano anterior |
| `participacao_t1` | numérica percentual | Participação anterior |
| `ideb_observado` ou versão `ultimo` | numérica | Última edição disponível antes do alvo |
| `ideb_meta` | numérica | Usar somente se disponível antes do alvo e se fizer sentido na formulação |
| `ideb_nota_media` | numérica | Verificar redundância com notas por área |
| `ideb_nota_matematica` | numérica | Usar versão histórica |
| `ideb_nota_portugues` | numérica | Usar versão histórica |
| `ideb_rendimento` | numérica | Usar versão histórica |
| `aprovacao_ai_pct` | numérica percentual | Usar versão anterior ao alvo |
| `aprovacao_1ano_pct` | numérica percentual | Usar versão anterior ao alvo |
| `aprovacao_2ano_pct` | numérica percentual | Usar versão anterior ao alvo |

## 5.6 Meta e risco

| Campo | Tipo | Uso recomendado |
|---|---|---|
| `meta_t` | numérica percentual | Aplicar após prever o nível municipal |
| `salto_necessario` | numérica em p.p. | Usar com cautela; depende de histórico e meta |
| `risco_nao_atingir` | probabilidade | Saída derivada da previsão e dos resíduos |

---

# 6. Matriz de risco de data leakage

| Campo ou grupo | Risco | Motivo | Tratamento recomendado |
|---|---|---|---|
| `proficiencia` | crítico | Define diretamente `alfabetizado` | Excluir do modelo de aluno |
| respostas e gabaritos dos blocos | crítico | Reconstroem o resultado da mesma prova | Excluir do modelo principal |
| `indicador_pct` do mesmo ano | crítico | É o próprio resultado agregado | Usar apenas `t-1` |
| `vl_media_lp` do mesmo ano | crítico | Resume a mesma avaliação do target | Usar apenas versão anterior |
| `pc_aluno_nivel_0_lp` a `pc_aluno_nivel_8_lp` do mesmo ano | crítico | Distribuição da mesma prova | Usar apenas versões defasadas |
| `indicador_t` | crítico | Target municipal | Excluir das features |
| `atingiu_meta_t` | crítico | Target derivado | Excluir das features |
| `gap_meta_t` | crítico | Derivado do indicador observado | Excluir das features |
| presença e tamanho da escola medidos no dia da prova | temporal | Não existem antes da aplicação | Separar modelo pré-prova e pós-aplicação |
| meta do ano-alvo | metodológico | Faz parte da regra de atingimento | Preferir aplicar depois da previsão do nível |
| identificadores | alto | Podem memorizar entidades | Usar apenas em joins, agrupamento e relatórios |
| datas de processamento e arquivo-fonte | alto | Metadados sem significado educacional | Excluir |

---

# 7. Regras recomendadas de preparação

1. Preservar os códigos de aluno, escola, município e UF como `string`.
2. Preservar `ano`, `id_municipio` e `rede` nas chaves das tabelas municipais.
3. Ajustar imputação, escalonamento e encoding somente no conjunto de treino.
4. Usar imputação pela mediana para numéricas e categoria explícita para categóricas ausentes.
5. Criar indicador de ausência quando a falta do dado puder ser informativa.
6. Aplicar `log1p` em população, área, densidade, quantidades e valores monetários positivos muito assimétricos.
7. Controlar colinearidade entre IDEB, notas, rendimento, INSE e faixas socioeconômicas.
8. Remover colunas totalmente nulas no recorte de treino e manter o mesmo schema no teste.
9. Agrupar validação por município ou escola, conforme o caso de uso.
10. Respeitar o tempo: uma feature só entra se estivesse disponível antes do resultado previsto.
11. Usar o teste temporal apenas para avaliação final.
12. Comparar o modelo com baselines simples, especialmente o resultado do ano anterior.

---

# 8. Observação sobre completude do schema

Este dicionário consolida os campos explicitamente documentados para a camada Silver. Arquivos que contenham colunas adicionais devem ter o schema físico exportado e comparado com este documento.

Exemplo para listar o schema de todos os Parquets:

```python
from pathlib import Path
import pyarrow.parquet as pq

for caminho in sorted(Path("data/silver").glob("*.parquet")):
    print(f"\n## {caminho.name}")
    schema = pq.ParquetFile(caminho).schema_arrow
    for campo in schema:
        print(f"- {campo.name}: {campo.type}")
```

A atualização do dicionário deve acompanhar qualquer mudança de nome, tipo, unidade, grão ou regra temporal das fontes.
