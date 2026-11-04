## Postech Tech Challenge | Fase 3: 

**Integrantes do Grupo (2IAST grupo 28):**

✅ Célia Maria Tomitsuka - RM374490

✅ Nelson da Silva Paz - RM374983

✅ Nelson Toshikazu Yamamoto - RM374494

---

## Visão geral

Este projeto utiliza a camada Gold construída a partir de dados educacionais, territoriais e socioeconômicos para desenvolver soluções de Machine Learning aplicadas à alfabetização no Brasil.

A solução combina cinco frentes:

1. diagnóstico da qualidade da camada Gold e das bases analíticas;
2. exploração dos padrões educacionais, territoriais e socioeconômicos;
3. previsão do nível municipal de alfabetização e do risco de não atingir metas;
4. segmentação de municípios com condições semelhantes;
5. interpretação dos modelos e tradução dos resultados em ações de política pública.

O projeto atende aos requisitos do Tech Challenge de análise exploratória, hipóteses, tratamento de dados, engenharia de atributos, prevenção de vazamento, pré-processamento integrado, treinamento, validação, interpretabilidade e aplicação estratégica.

---

## Sumário

1. [Contexto do problema](#1-contexto-do-problema)
2. [Objetivo analítico](#2-objetivo-analítico)
3. [Respostas obrigatórias do Tech Challenge](#3-respostas-obrigatórias-do-tech-challenge)
4. [Descrição dos dados](#4-descrição-dos-dados)
5. [Qualidade da camada Gold](#5-qualidade-da-camada-gold)
6. [Análise exploratória e hipóteses](#6-análise-exploratória-e-hipóteses)
7. [Pipeline de Machine Learning](#7-pipeline-de-machine-learning)
8. [Comparação e escolha dos modelos](#8-comparação-e-escolha-dos-modelos)
9. [Diagnóstico e projeção do risco](#9-diagnóstico-e-projeção-do-risco)
10. [Segmentação e perfis municipais](#10-segmentação-e-perfis-municipais)
11. [Interpretabilidade](#11-interpretabilidade)
12. [Insights principais](#12-insights-principais)
13. [Aplicação prática](#13-aplicação-prática)
14. [Limitações](#14-limitações)
15. [Evoluções futuras](#15-evoluções-futuras)
16. [Estrutura do repositório](#16-estrutura-do-repositório)
17. [Como executar](#17-como-executar)
18. [Entregáveis](#18-entregáveis)
19. [Checklist de conformidade](#19-checklist-de-conformidade)

---

## 1. Contexto do problema

A alfabetização ao final do 2º ano do ensino fundamental é um indicador central da trajetória escolar. O Indicador Criança Alfabetizada permite acompanhar o percentual de estudantes que alcançam o nível esperado, enquanto as metas municipais e estaduais estabelecem trajetórias futuras.

O indicador observado explica a situação depois da avaliação. A necessidade de gestão é anterior: antecipar risco, reconhecer municípios vulneráveis, identificar fatores associados ao desempenho e agrupar territórios com condições semelhantes.

A cobertura dos microdados evoluiu entre 2023 e 2025:

| Ano | Alunos listados | Presentes | Municípios | UFs | Presença | Avaliados com prova | Alfabetizados, valor bruto |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 1.747.439 | 1.503.058 | 4.873 | 23 | 86,0% | 1.502.809 | 58,4% |
| 2024 | 2.120.560 | 1.852.788 | 5.519 | 26 | 87,4% | 1.851.852 | 59,8% |
| 2025 | 2.222.792 | 1.969.921 | 5.556 | 27 | 88,6% | 1.966.605 | 66,3% |

O crescimento do percentual bruto não é interpretado isoladamente como efeito de uma política, pois cobertura, composição, participação e contexto também mudaram.

---

## 2. Objetivo analítico

Construir uma pipeline reproduzível de Machine Learning capaz de:

- analisar a qualidade e a cobertura dos dados da camada Gold;
- identificar fatores associados à alfabetização;
- prever o nível municipal do indicador;
- derivar o risco de não atingir a meta futura;
- organizar municípios em perfis de contexto;
- interpretar as variáveis das quais os modelos dependem;
- produzir rankings e perfis úteis para priorização de políticas públicas.

O projeto utiliza uma target observada. Alunos ausentes não são classificados automaticamente como não alfabetizados, e a proficiência contemporânea não é usada como feature para prever `alfabetizado`.

---

## 3. Respostas obrigatórias do Tech Challenge

### 3.1 Quais fatores mais impactam a alfabetização?

O fator mais importante nos dois modelos é o **histórico de alfabetização do próprio território**.

No modelo de aluno:

- nível de alfabetização no ano anterior: queda de AUC de aproximadamente **0,053** após permutação;
- UF: aproximadamente **0,010**;
- código da rede e percentual anterior de alfabetizados: abaixo de **0,010**;
- INSE, IDEB anterior, presença na avaliação e estrutura econômica possuem contribuições menores.

No modelo municipal:

- embaralhar o nível de alfabetização anterior aumenta o erro absoluto em aproximadamente **12 p.p.**;
- a segunda variável fica abaixo de **0,5 p.p.**;
- IDEB, meta, avanço necessário, participação, notas, população e região acrescentam sinal complementar, mas muito menor.

**Resposta:** o desempenho passado é o principal fator preditivo. UF, rede, IDEB e contexto socioeconômico refinam a previsão, mas não substituem o histórico. Importância preditiva não significa causalidade.

### 3.2 Quais municípios apresentam maior risco educacional?

O ranking de 2026 analisa **5.477 municípios** e ordena cada município pelo risco de não atingir a meta.

No teste temporal de 2025, o modelo final apresentou:

- MAE: **3,2 p.p.**;
- RMSE: **4,65 p.p.**;
- R²: **0,918**;
- viés: **-0,25 p.p.**;
- Spearman: **0,96**;
- AUC do risco: **0,985**.

Na projeção, os maiores riscos ficam próximos de **0,99**. A análise de estabilidade identificou:

- **1.985 municípios** no núcleo da lista em pelo menos 95% das reamostragens;
- **32 municípios** na franja instável;
- **3.460 municípios** fora do núcleo.

**Resposta:** os municípios prioritários são os primeiros colocados em `reports/municipios_risco_2026.csv`. O ranking deve orientar triagem e apoio técnico, não sanções automáticas.

### 3.3 Quais regiões possuem padrões semelhantes?

Foram segmentados **5.477 municípios** em dois perfis:

| Perfil | Municípios | Participação |
|---|---:|---:|
| IDEB alto, INSE alto e menor porte | 3.278 | 60% |
| IDEB baixo, INSE baixo e maior porte | 2.199 | 40% |

O perfil de melhor contexto concentra-se no Sudeste, com **41%**, e no Sul, com **33%**. O perfil de maior vulnerabilidade concentra-se no Nordeste, com **63%**, e no Norte, com **16%**.

**Resposta:** padrões semelhantes não correspondem exatamente às macrorregiões. Municípios de regiões diferentes podem compartilhar o mesmo perfil e demandar estratégias semelhantes.

### 3.4 Como prever municípios que podem não atingir metas futuras?

A estratégia escolhida foi:

1. prever o nível futuro de `indicador_t`;
2. comparar a previsão com `meta_t`;
3. usar a distribuição dos resíduos fora da amostra para calcular o risco de não atingir.

A comparação de formulações mostrou:

| Formulação | Resultado no teste de 2025 |
|---|---:|
| Classificação direta, regressão logística | AUC **0,795** |
| Classificação direta, Random Forest | AUC **0,781** |
| Risco derivado de Ridge | AUC **0,837** |
| Risco derivado de Random Forest | AUC **0,864** |

A Random Forest de regressão obteve, na comparação inicial:

- MAE: **9,874 p.p.**;
- RMSE: **12,444 p.p.**;
- R²: **0,405**;
- viés: **-8,053 p.p.**;
- Spearman: **0,827**;
- AUC do risco: **0,864**.

O refinamento e diagnóstico final registrados no notebook 05 chegaram a MAE de **3,2 p.p.**, Spearman de **0,96** e AUC de risco de **0,985**.

**Resposta:** prever primeiro o nível educacional e aplicar a meta depois foi mais robusto que prever diretamente a classe `atingiu_meta_t`, pois separa o fenômeno educacional da regra administrativa da meta.

### 3.5 Quais variáveis possuem maior influência nos modelos?

As importâncias por permutação mostram:

- histórico de alfabetização como principal variável nos dois modelos;
- UF e rede como fatores contextuais relevantes no modelo de aluno;
- IDEB, INSE, meta, avanço necessário, participação e economia como variáveis complementares;
- concentração muito forte da importância municipal em uma única feature histórica.

**Resposta:** a trajetória anterior domina a previsão. As demais variáveis ajudam a ajustar diferenças contextuais, mas possuem importância individual muito menor.

---

## 4. Descrição dos dados

### 4.1 Camada Gold

As principais tabelas são:

| Tabela | Grão | Finalidade |
|---|---|---|
| `dim_municipio` | município | chaves e atributos territoriais |
| `fato_aluno` | ano × aluno | presença, prova, peso, proficiência e target |
| `indicador_municipio` | ano × município × rede | indicador observado |
| `metas_municipio` | ano × município × rede | metas municipais |
| `metas_uf` | ano × UF × rede | metas estaduais |
| `ideb_municipio` | ano × município × rede | IDEB, notas e rendimento |
| `contexto_municipio` | município | população, economia e INSE |

### 4.2 Bases analíticas

| Base | Linhas | Colunas | Grão |
|---|---:|---:|---|
| `base_analitica_municipio.parquet` | 43.788 | 59 | ano-alvo × município × rede |
| `base_analitica_aluno.parquet` | 5.320.756 | 61 | ano × aluno |

A base municipal preserva `rede`. Qualquer análise com uma linha por município deve filtrar explicitamente a rede municipal ou definir uma regra de agregação.

---

## 5. Qualidade da camada Gold

O diagnóstico executou **18 checagens automáticas**:

- **17 aprovadas**;
- **1 em investigação**.

Foram aprovadas verificações de:

- unicidade das chaves;
- ausência de relacionamentos órfãos;
- percentuais entre 0 e 100;
- metas não decrescentes;
- target binário;
- proficiência válida entre **572,4 e 904,4**;
- concordância de **100%** entre `alfabetizado` e `proficiência >= 743`.

A única falha foi a reconciliação do cálculo ponderado com o indicador Gold:

```text
MAE = 0,317 p.p. em 15.570 registros comparáveis
```

Distribuição do erro absoluto:

- mediana: **0,250 p.p.**;
- primeiro quartil: **0,117 p.p.**;
- terceiro quartil: **0,380 p.p.**;
- desvio-padrão: **1,483 p.p.**;
- máximo: **75 p.p.**.

A diferença típica é pequena, mas o caso extremo deve ser investigado por ano, município, rede, peso e denominador.

---

## 6. Análise exploratória e hipóteses

### 6.1 Principais associações

| Variável | Spearman com o indicador atual |
|---|---:|
| Indicador do ano anterior | **0,691** |
| Meta do ano-alvo | **0,569** |
| IDEB mais recente | **0,505** |
| Nota de Matemática | **0,480** |
| Nota de Português | **0,471** |
| Avanço necessário | **-0,456** |
| População | **-0,279** |
| Agropecuária no PIB | **0,257** |
| INSE médio | **0,093** |
| PIB per capita | **0,028** |

A UF apresentou `Eta² ≈ 0,357`, com Kruskal-Wallis H de **1.944,3**, confirmando heterogeneidade territorial relevante.

### 6.2 Hipóteses testadas

| Hipótese | Resultado |
|---|---|
| UF captura heterogeneidade relevante | Suportada |
| Histórico e IDEB antecipam o indicador | Suportada |
| Contexto socioeconômico acrescenta sinal | Suportada, com efeito moderado |
| Há relações não lineares | A testar com modelos de árvore |
| Features de dois anos têm cobertura insuficiente | Suportada |
| Maior parte da variação está entre alunos da mesma escola | Não suportada |

Decomposição descritiva da variação individual:

- entre municípios: **18,0%**;
- entre escolas do mesmo município: **47,1%**;
- entre alunos da mesma escola: **34,9%**.

### 6.3 Assimetria e nulos

Variáveis com forte assimetria:

- população: **38,32**;
- quantidade de alunos no INSE: **26,27**;
- indústria no PIB: **15,04**;
- área: **13,83**;
- densidade: **13,36**;
- PIB per capita: **6,91**.

Maiores taxas de nulos:

- `pc_nivel_8`: **44,3%**;
- variação do IDEB: **14,4%**;
- IDEB anterior: **13,2%**.

Esses resultados sustentam imputação na pipeline, `log1p` nas variáveis muito assimétricas e ablação de features com baixa cobertura.

---

## 7. Pipeline de Machine Learning

A pipeline inclui:

1. seleção de features disponíveis antes do resultado;
2. exclusão de identificadores, targets e variáveis com leakage;
3. remoção de colunas totalmente nulas no treino;
4. imputação de numéricas pela mediana;
5. transformação `log1p` nas variáveis de porte e renda;
6. codificação de categóricas;
7. padronização quando exigida pelo algoritmo;
8. ajuste do pré-processamento dentro de cada fold;
9. validação agrupada por município;
10. teste temporal em ano posterior;
11. persistência do pipeline completo, métricas e previsões.

Regras contra vazamento:

- `proficiencia` não entra para prever `alfabetizado`;
- ausência não vira automaticamente classe 0;
- `indicador_t`, `atingiu_meta_t` e `gap_meta_t` não são features municipais;
- IDEB e histórico usam referências anteriores;
- threshold e modelo são escolhidos sem otimização no teste.

---

## 8. Comparação e escolha dos modelos

A classificação direta foi comparada com a regressão do nível municipal.

A taxa de atingimento mudou de **56,0% em 2024 para 72,8% em 2025**, diferença de **16,9 p.p.**. A variável “avanço necessário” tinha AUC de **0,487** em 2024 e **0,748** em 2025, mostrando instabilidade da regra de atingimento.

A regressão com risco derivado foi escolhida porque:

- alcançou melhor AUC temporal;
- preservou melhor a ordem dos municípios;
- permitiu separar previsão educacional e meta administrativa;
- apresentou melhor generalização do que a classificação direta.

---

## 9. Diagnóstico e projeção do risco

### 9.1 Avaliação final de 2025

| Métrica | Resultado |
|---|---:|
| MAE | **3,2 p.p.** |
| RMSE | **4,65 p.p.** |
| R² | **0,918** |
| Viés | **-0,25 p.p.** |
| Spearman | **0,96** |
| AUC do risco | **0,985** |
| Acurácia | **0,941** |
| F1 | **0,959** |
| Precisão | **0,972** |
| Recall | **0,946** |
| Precisão dos negativos | **0,864** |
| Recall dos negativos | **0,927** |

Comparação com regras simples:

| Estratégia | AUC |
|---|---:|
| Modelo | **0,985** |
| Avanço necessário | 0,741 |
| Indicador anterior | 0,642 |

### 9.2 Extrapolação para UF não vista

| Métrica | Resultado |
|---|---:|
| MAE | **10,08 p.p.** |
| RMSE | **13,05 p.p.** |
| R² | **0,54** |
| Viés | **+0,63 p.p.** |
| Spearman | **0,73** |
| AUC do risco | **0,718** |

O desempenho cai quando a UF não aparece no treinamento. O modelo é mais confiável para municípios novos de contextos estaduais já observados.

### 9.3 Nota de consistência dos artefatos

O notebook 09 exibe metadados de uma execução intermediária, com MAE **10,4 p.p.**, RMSE **13,1 p.p.**, R² **0,34**, viés **-8,5 p.p.** e Spearman **0,82**. O notebook 05 contém a avaliação final mais recente, com MAE **3,2 p.p.** e AUC **0,985**. Antes da entrega definitiva, o notebook 09 deve ser regenerado com o mesmo artefato final para eliminar essa divergência documental.

---

## 10. Segmentação e perfis municipais

### 10.1 Segmentação

- municípios: **5.477**;
- variáveis: **17**;
- valores imputados: **1.318**;
- segmentos escolhidos: **2**;
- silhueta: **0,182**;
- Davies-Bouldin: **2,064**;
- WCSS: **78.237**.

Os dois primeiros componentes do PCA explicam **47,9%** da variância, e são necessários seis componentes para alcançar 80%.

### 10.2 Perfis

| Indicador | Melhor contexto | Maior vulnerabilidade |
|---|---:|---:|
| Municípios | 3.278 | 2.199 |
| IDEB | 6,6 | 5,4 |
| Português | 226,1 | 198,8 |
| Matemática | 241,9 | 209,5 |
| INSE | 5,17 | 4,40 |
| PIB per capita | R$ 33.799 | R$ 13.556 |
| Risco médio | 0,36 | 0,43 |
| Risco ≥ 50% | 33,2% | 41,5% |

A silhueta baixa confirma que os municípios formam um contínuo. Os perfis são recortes operacionais, não categorias naturais.

---

## 11. Interpretabilidade

A importância por permutação foi escolhida para funcionar de modo uniforme com os modelos persistidos.

- No modelo de aluno, o histórico anterior reduz a AUC em cerca de **0,053** quando embaralhado.
- No modelo municipal, o histórico anterior aumenta o MAE em aproximadamente **12 p.p.**.
- UF, rede, IDEB, INSE, meta e economia aparecem como fatores secundários.

A interpretação deve responder “de que variáveis o modelo depende”, não “qual variável causa alfabetização”.

---

## 12. Insights principais

1. **A trajetória passada domina a previsão.** `indicador_t1` tem Spearman de 0,691 e lidera a importância dos modelos.
2. **A UF importa.** Aproximadamente 35,7% da heterogeneidade está associada às diferenças estaduais, sem implicar causalidade.
3. **Contexto socioeconômico acrescenta sinal, mas não domina.** INSE e PIB per capita têm correlações menores que histórico e IDEB.
4. **Municípios maiores tendem a apresentar indicador menor na análise descritiva**, com Spearman de -0,279.
5. **A maior heterogeneidade individual está entre escolas do mesmo município**, com 47,1% na decomposição aproximada.
6. **Prever o nível e aplicar a meta depois é mais robusto** que classificar diretamente o atingimento.
7. **Os dois perfis têm municípios de alto risco.** O perfil define o tipo de estratégia; o ranking define a prioridade.
8. **A extrapolação estadual é limitada.** A AUC cai de 0,985 para 0,718 quando a UF não foi vista no treino.

---

## 13. Aplicação prática

### Priorização anual

O ranking permite ordenar municípios por risco de não atingir a meta e direcionar apoio técnico, acompanhamento e formação.

### Estratégia por perfil

- **IDEB baixo, INSE baixo e maior porte:** intervenção mais estrutural, com foco em recuperação de aprendizagem, acompanhamento pedagógico e suporte territorial.
- **IDEB alto, INSE alto e menor porte:** acompanhamento focalizado, especialmente quando o risco decorre de meta exigente ou queda recente.

### Uso responsável

- o risco não deve gerar sanção automática;
- o modelo de aluno não deve rotular crianças;
- decisões devem combinar previsão, conhecimento local e capacidade operacional;
- a atualização precisa ocorrer em cada novo ciclo de dados.

---

## 14. Limitações

- poucas variáveis individuais no modelo de aluno;
- dependência elevada do histórico;
- série temporal curta;
- alta colinearidade entre IDEB, notas e indicadores socioeconômicos;
- 44,3% de nulos em `pc_nivel_8`;
- perda de desempenho em UF não vista;
- risco de mudanças de patamar entre anos;
- agrupamentos com fronteiras difusas;
- importância preditiva não representa causalidade;
- divergência documental entre os artefatos mostrados nos notebooks 05 e 09;
- reconciliação Gold com MAE de 0,317 p.p. e caso extremo ainda em investigação.

---

## 15. Evoluções futuras

- incluir variáveis individuais e escolares com governança adequada;
- atualizar a série com novos anos;
- recalibrar o risco em cada ciclo;
- testar modelos multinível;
- investigar os outliers da reconciliação Gold;
- monitorar drift por UF, rede e perfil;
- criar painel executivo;
- avaliar programas com métodos causais;
- incorporar custo e capacidade de intervenção ao ranking.

---

## 16. Estrutura do repositório

```text
.
├── data/
│   ├── bronze/                 # dados brutos locais, fora do Git
│   ├── gold/                   # camada Gold
│   └── processed/              # bases analíticas
├── notebooks/
│   └── analysis/
│       ├── 01_diagnostico_gold_e_bases_analiticas.ipynb
│       ├── 02_exploracao_dos_dados.ipynb
│       ├── 03_hipoteses_e_diretrizes_de_modelagem.ipynb
│       ├── 04_comparacao_de_formulacoes_municipais.ipynb
│       ├── 05_diagnostico_e_projecao_do_risco_municipal.ipynb
│       ├── 06_segmentacao_de_municipios.ipynb
│       ├── 07_perfis_municipais_e_prioridades.ipynb
│       ├── 08_interpretabilidade_dos_modelos.ipynb
│       └── 09_aplicacao_estrategica_tech_challenge.ipynb
├── src/
│   ├── preprocessing/
│   ├── modeling/
│   ├── evaluation/
│   └── visualization/
├── models/
├── reports/
├── images/
├── tests/
├── environment.yml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 17. Como executar

### 17.1 Ambiente Conda

```bash
conda env create -f environment.yml
conda activate teste_2
```

### 17.2 Ambiente pip

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 17.3 Testes

```bash
pytest -q
```

### 17.4 Notebooks

Execute os notebooks na ordem numérica. Exemplo:

```bash
jupyter nbconvert \
  --to notebook \
  --execute \
  --inplace \
  --ExecutePreprocessor.timeout=1800 \
  notebooks/analysis/01_diagnostico_gold_e_bases_analiticas.ipynb
```

### 17.5 Git

```bash
git add -A
git status
git commit -m "Atualiza entrega do Tech Challenge Fase 3"
git push origin "$(git branch --show-current)"
```

O `.gitignore` deve conter:

```gitignore
/data/bronze/
__pycache__/
*.py[cod]
```

---

## 18. Entregáveis

- repositório Git completo;
- código modular em `src/`;
- notebooks executáveis;
- README detalhado;
- `requirements.txt` e `environment.yml`;
- modelos persistidos;
- ranking municipal de risco;
- segmentação e perfis;
- tabelas de importância;
- gráficos;
- apresentação executiva;
- vídeo de até cinco minutos.

Principais arquivos:

```text
reports/municipios_risco_2026.csv
reports/segmentacao_municipios.csv
reports/perfis_municipais_e_prioridades.csv
reports/importancia_permutacao_aluno.csv
reports/importancia_permutacao_municipio.csv
```

---

## 19. Checklist de conformidade

- [x] Camada Gold da Fase 2 utilizada
- [x] Target observada
- [x] Alunos ausentes fora do target válido
- [x] Análise exploratória
- [x] Hipóteses analíticas
- [x] Imputação de valores ausentes
- [x] Transformação de numéricas e categóricas
- [x] Prevenção de data leakage
- [x] Pré-processamento integrado ao modelo
- [x] Validação agrupada por município
- [x] Teste temporal
- [x] Baselines reportados
- [x] Comparação de algoritmos e formulações
- [x] Interpretabilidade
- [x] Segmentação territorial
- [x] Respostas às cinco perguntas estratégicas
- [x] Limitações e aplicação prática
- [x] Código modular em `src/`
- [x] Dados brutos e caches fora do Git
- [ ] Regenerar o notebook 09 com o mesmo artefato final do notebook 05
- [ ] Confirmar execução completa em ambiente limpo
- [ ] Confirmar todos os artefatos na branch `main`
- [ ] Atualizar apresentação e vídeo com os números finais

---

## Nota de uso responsável

Este projeto é acadêmico e demonstrativo. As previsões devem apoiar triagem, investigação e priorização por equipes técnicas. Nenhuma saída deve ser usada isoladamente para decisões automáticas sobre alunos, escolas ou municípios.
