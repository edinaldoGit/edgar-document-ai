# EDGAR - Registro Mestre de Experimentos

Este arquivo identifica quais execuções e artefatos são válidos para os
resultados finais do TCC.

A regra geral é:

- `OFFICIAL`: pode fornecer resultados para o texto final;
- `PRELIMINARY`: execução válida historicamente, mas substituída;
- `EXPLORATORY`: usada para investigar alternativas, não representa o EDGAR final;
- `DIAGNOSTIC`: usada para análise de erros ou compreensão de casos específicos;
- `SUPERSEDED`: execução substituída por outra mais recente ou metodologicamente corrigida.

Resultados marcados como preliminares, exploratórios, diagnósticos ou
substituídos não devem ser apresentados como resultados principais do TCC.

---

## 1. Dataset experimental

### Status: OFFICIAL

Arquivos principais:

- `experiments/datasets/documents.json`
- `experiments/datasets/questions.json`
- `experiments/datasets/dataset_manifest.json`
- `experiments/datasets/corpus_report.json`
- `experiments/datasets/reference_answer_contexts.json`

Dataset final:

- 4 documentos didáticos;
- 578 páginas curadas;
- 26 consultas;
- categorias:
  - `text_retrieval`
  - `visual_evidence`
  - `table_retrieval`
  - `multimodal_reasoning`

Convenção do gabarito:

- `expected_evidence.source_page`: página física no PDF-fonte;
- `expected_evidence.page`: página do PDF curado/indexado;
- `expected_evidence.component_type`: tipo de componente esperado.

As métricas de retrieval devem sempre utilizar `expected_evidence.page`.

---

## 2. Ingestão e indexação

### `20260918_142622_lilac_ingestion`

Status: PRELIMINARY

Escopo:

- execução anterior em documento isolado;
- utilizada durante o desenvolvimento do pipeline.

Não utilizar como resultado do corpus final.

### `20260919_153145_corpus_ingestion`

Status: SUPERSEDED

Execução completa anterior do corpus.

Foi substituída pela execução oficial posterior.

### `20260919_182500_corpus_ingestion`

Status: OFFICIAL

Artefato:

- `experiments/runs/20260919_182500_corpus_ingestion/corpus_ingestion_report.json`

Esta é a ingestão/indexação de referência do EDGAR atualmente utilizado pelos
experimentos posteriores.

Resultado consolidado:

- 4 documentos;
- 578 páginas curadas;
- 7.522 componentes indexados;
- tempo total aproximado: 5.424,631 s.

Tempos por documento registrados:

- statistics: 1.226 componentes, 593,795 s;
- calculus: 3.147 componentes, 1.792,644 s;
- graphs: 952 componentes, 1.196,756 s;
- physics: 2.197 componentes, 1.841,422 s.

A ingestão não deve ser repetida sem que a validação funcional identifique
um problema sistêmico que afete o conteúdo indexado.

---

## 3. Retrieval

### Runs históricos

- `20260919_201949_retrieval`
- `20260919_202454_retrieval`
- `20260919_205912_retrieval`
- `20260919_212616_retrieval`
- `20260919_214957_retrieval`

Status: EXPLORATORY / SUPERSEDED

Foram utilizados durante o desenvolvimento e investigação de estratégias de
retrieval.

Não utilizar seus `page_hit_rate` ou `component_hit_rate` diretamente no texto
final.

### `20260919_203148_retrieval`

Status: SUPERSEDED

Execução histórica do retrieval semântico.

O relatório original não armazena o `doc_id` das evidências
e suas métricas foram calculadas antes das correções do
gabarito e da verificação de identidade documental.

Não utilizar suas taxas históricas diretamente.

### `20261008_032812_document_aware_retrieval`

Status: OFFICIAL

Artefato:

- `experiments/runs/20261008_032812_document_aware_retrieval/retrieval_report.json`

Configuração:

- mesmo índice persistente de 7.522 componentes;
- 26 consultas;
- retrieval semântico corpus-wide;
- top-20;
- sem filtro por documento, agrupamento ou reranking;
- identificação completa de documento e componente.

Critérios corrigidos:

- Page Hit: documento correto e página correta;
- Component Hit: documento correto, página correta e tipo correto.

Validação de equivalência:

- 26/26 rankings iguais nas dimensões página e tipo;
- 26/26 ranks de Page Hit e Component Hit iguais;
- mesmas métricas agregadas.

A nova execução é a fonte oficial das métricas de retrieval.
A análise quantitativa de cascata anterior permanece válida.

Resultados finais:

| Métrica | Hits | Taxa |
|---|---:|---:|
| Page Hit@5 | 19/26 | 0,7308 |
| Page Hit@10 | 22/26 | 0,8462 |
| Page Hit@20 | 24/26 | 0,9231 |
| Component Hit@5 | 8/26 | 0,3077 |
| Component Hit@10 | 10/26 | 0,3846 |
| Component Hit@20 | 13/26 | 0,5000 |

Artefatos derivados:

- `experiments/scripts/recalculate_retrieval_metrics.py`
- `experiments/analysis/retrieval_comparison.json`
- `experiments/analysis/cascade_error_analysis.json`

Definição de Component Hit:

o mesmo resultado recuperado deve possuir simultaneamente o documento correto,
a página esperada e o tipo de componente esperado.

---

## 4. Geração de respostas

### `20260922_001610_generation`

Status: OFFICIAL

Artefato:

- `experiments/runs/20260922_001610_generation/generation_report.json`

Configuração principal:

- 26 consultas;
- retrieval corpus-wide;
- top-20 evidências;
- `max_new_tokens = 128`;
- resposta com referências no formato `[Evidence N]`.

Resultado:

- 26/26 consultas processadas;
- tempo total: 343,11 s.

Este run é a fonte fixa das respostas avaliadas posteriormente.

As respostas não devem ser regeneradas para substituir silenciosamente os
resultados desta execução.

---

## 5. Avaliação RAGAS

### `20260930_232735_ragas`

Status: PARTIALLY OFFICIAL

Artefato:

- `experiments/runs/20260930_232735_ragas/ragas_report.json`

Foram avaliadas:

- Faithfulness;
- Response Relevancy.

#### Response Relevancy

Status: OFFICIAL

Resultado:

- 26/26 valores válidos;
- média: 0,7802690828580391.

Configuração relevante:

- RAGAS 0.4.3;
- API legada `ragas.metrics`;
- `ResponseRelevancy` com `strictness = 1`;
- embeddings do próprio EDGAR.

#### Faithfulness deste run

Status: PRELIMINARY / SUPERSEDED

A média de aproximadamente 0,6994 não deve ser apresentada como resultado final.

Motivo:

o contexto fornecido ao avaliador continha apenas o texto das evidências,
enquanto o gerador havia recebido contexto estruturado com metadados de
evidência.

O Faithfulness foi reavaliado posteriormente com representação mais fiel ao
contexto usado na geração.

---

## 6. Faithfulness final

### `20261001_205026_faithfulness`

Status: INCOMPLETE / SUPERSEDED

Artefato:

- `experiments/runs/20261001_205026_faithfulness/faithfulness_report.json`

A execução contém apenas 23 resultados e foi substituída pela execução seguinte.

Não utilizar no texto final.

### `20261001_210850_faithfulness`

Status: OFFICIAL

Artefato:

- `experiments/runs/20261001_210850_faithfulness/faithfulness_report.json`

Configuração:

- respostas fixas do run de geração `20260922_001610_generation`;
- 20 evidências estruturadas por consulta;
- RAGAS Faithfulness;
- avaliador com `max_new_tokens = 512`.

Resultado:

- 26 consultas tentadas;
- 25 valores de Faithfulness válidos;
- média dos 25 valores válidos: 0,7920.

### `statistics_q003`

Status: EXCLUDED FROM FAITHFULNESS MEAN

Motivo:

- falha persistente do parser do avaliador;
- inconsistência observada no próprio material-fonte entre texto e legendas;
- a avaliação diagnóstica ad hoc não foi incorporada à média oficial.

Artefato diagnóstico:

- `experiments/analysis/statistics_q003_ragas_issue.json`

O valor diagnóstico obtido separadamente não deve substituir a avaliação
oficial ausente.

---

## 7. Resumo final das métricas de geração

Status: OFFICIAL

Artefato:

- `experiments/analysis/generation_metrics_summary.json`

Resultados gerais:

| Métrica | Casos válidos | Média |
|---|---:|---:|
| Faithfulness | 25/26 | 0,7920 |
| Response Relevancy | 26/26 | 0,7803 |

Resultados por documento, categoria e dificuldade presentes nesse artefato
podem ser usados de forma descritiva.

Devido ao tamanho reduzido dos grupos, diferenças entre subgrupos não devem ser
interpretadas como evidência estatística de causalidade.

---

## 8. Análise de cascata retrieval -> geração

Status: OFFICIAL AS DESCRIPTIVE ANALYSIS

Artefato:

- `experiments/analysis/cascade_error_analysis.json`

Classificação em top-20:

- `exact_component_hit`: página e tipo esperados recuperados;
- `page_only_hit`: página esperada recuperada, mas não o tipo esperado;
- `page_miss`: página gold não recuperada.

Resultados:

| Status | n | Faithfulness médio | Response Relevancy médio |
|---|---:|---:|---:|
| exact_component_hit | 13 | 0,8861 | 0,7315 |
| page_only_hit | 11 | 0,6742 | 0,8421 |
| page_miss | 2 | 0,8750 | 0,7573 |

Os resultados são descritivos.

Não interpretar essas diferenças como relações causais devido ao número reduzido
de consultas e à possibilidade de evidências semanticamente equivalentes fora
do componente gold.

---

## 9. Diagnóstico qualitativo pós-retrieval

Status: DIAGNOSTIC

Artefato:

- `experiments/analysis/post_retrieval_error_cases.json`

Casos observados incluem:

- seleção inadequada de evidência pelo gerador;
- uso de componente vizinho semanticamente equivalente;
- geração incompleta;
- representação/serialização insuficiente de tabela.

Conclusão operacional:

recuperar o componente gold não garante que o gerador utilize corretamente essa
evidência.

---

## 10. Auditoria de truncamento

Status: DIAGNOSTIC

Artefato:

- `experiments/analysis/generation_truncation_audit.json`

Com `max_new_tokens = 128`:

- 26 respostas avaliadas;
- 3 respostas claramente truncadas;
- taxa observada: 3/26 = 0,1154.

Casos:

- `calculus_q007`;
- `graphs_q003`;
- `statistics_q006`.

`physics_q006` permanece como caso ambíguo e não foi contado como truncamento
confirmado.

Esta limitação deve ser relatada, sem regenerar retroativamente as respostas
oficiais.

---

## 11. Estratégias exploratórias de retrieval

Status: EXPLORATORY

Artefatos:

- `experiments/analysis/retrieval_comparison.json`
- `experiments/analysis/page_grouping_analysis.json`

Foram investigadas estratégias alternativas como reranking e agrupamento por
página.

Essas estratégias não substituíram o retrieval semântico utilizado no EDGAR
oficial.

Resultados negativos ou neutros podem ser mencionados na discussão se forem
úteis para justificar a configuração escolhida, mas não devem ser apresentados
como configuração principal.

---

## 12. Próximos experimentos antes do congelamento final

Ainda pendentes:

1. validação funcional pela aplicação cliente;
2. decisão formal sobre necessidade ou não de nova ingestão;
3. congelamento da configuração E4;
4. baselines/ablações controladas;
5. avaliação objetiva de rastreabilidade;
6. consolidação de latência e desempenho;
7. pequena análise de erros dos componentes intermediários;
8. tabela-mestre final dos resultados;
9. validação completa do repositório.

Após essas etapas, os experimentos serão considerados encerrados e o trabalho
passará para a revisão e reescrita do texto do TCC.

---

## 13. Regra para o texto final

Antes de inserir qualquer número no TCC:

1. localizar o resultado neste registro;
2. confirmar que seu status permite uso no texto;
3. citar o artefato oficial correspondente;
4. não substituir resultados oficiais por diagnósticos posteriores;
5. distinguir observação empírica, hipótese, interpretação e limitação.

Este arquivo deve ser atualizado sempre que um novo experimento for declarado
oficial.

---

## 14. Auditoria de integridade e congelamento da ingestão

Status: OFFICIAL / COMPLETED

Snapshot mantido:
`20260919_182500_corpus_ingestion`

Artefato:
- `experiments/analysis/index_integrity_audit.json`

Resultados:
- 7.522 componentes auditados;
- 568 páginas com componentes indexados;
- 741 componentes com crop;
- 0 inconsistências estruturais detectadas.

Cobertura do corpus:
- 578 páginas curadas;
- 568 páginas com componentes indexados;
- 8 páginas sem conteúdo detectável pelo PyMuPDF;
- 2 páginas contendo apenas cabeçalho/rodapé.

Páginas sem componentes:
- statistics_001: 24, 42, 48, 104;
- graphs_001: 34, 46, 62, 104;
- physics_001: 96, 152.

Limitação conhecida:
- physics_q006 apresenta problemas de extração textual
  e reconstrução de tabela;
- o problema foi diagnosticado, mas não justifica
  reingestão completa neste estágio.

Decisão:
- manter o índice oficial de 7.522 componentes;
- não reexecutar a ingestão integral;
- preservar os resultados experimentais existentes;
- prosseguir para baselines e ablações controladas.

A auditoria não comprova correção semântica de todos
os componentes.

## 15. Consolidação final das avaliações E1-E4

Status: OFFICIAL / EVALUATION COMPLETED

Data de consolidação: 2026-10-11.

Artefatos principais:
- `experiments/analysis/experimental_results_master.json`
- `experiments/analysis/experimental_results_summary.md`

Configurações:
- E1: RAG textual com fragmentos de 1.000 caracteres e sobreposição de 200.
- E2: RAG textual com uma representação por página.
- E3: EDGAR sem os 641 registros de figuras baseados exclusivamente em descrições visuais.
- E4: EDGAR completo, com 7.522 componentes indexados.

Protocolo:
- Quatro documentos e 26 perguntas.
- Recuperação Top-20, sem reranking ou agrupamento de páginas.
- 26 gerações bem-sucedidas em cada configuração.
- Faithfulness avaliado em 24 perguntas pareadas.
- Response Relevancy avaliado nas 26 perguntas.
- E1/E2: geração limitada a 5.000 tokens de entrada.
- E3/E4: geração com as 20 evidências recuperadas.

Resultados consolidados:

| Métrica | E1 | E2 | E3 | E4 |
|---|---:|---:|---:|---:|
| Page Hit@5 | 23/26 | 24/26 | 20/26 | 19/26 |
| Page Hit@10 | 24/26 | 24/26 | 22/26 | 22/26 |
| Page Hit@20 | 25/26 | 25/26 | 25/26 | 24/26 |
| Component Hit@20 | N/A | N/A | 5/26 | 13/26 |
| Faithfulness (24 pareadas) | 0.9514 | 0.8681 | 0.8319 | 0.7833 |
| Response Relevancy (26) | 0.8339 | 0.7800 | 0.7993 | 0.7803 |

Recuperação direta de figuras:
- E3: 0/17 em Component Hit@20.
- E4: 8/17 em Component Hit@20.
- Component Hit considera documento, página e tipo, não identidade exata da figura.

Interpretação:
- E1 apresentou as maiores médias nas métricas automatizadas de geração.
- E4 apresentou maior recuperação de componentes, especialmente figuras, em comparação com E3.
- A ablação E3 remove registros visuais, e não somente o texto de suas descrições.
- Faithfulness não demonstra correção factual da resposta.
- O conjunto de 26 perguntas limita a generalização.
- Os tempos registrados não constituem comparação computacional controlada.

Decisão:
- Encerrar novas execuções de recuperação, geração e RAGAS desta rodada.
- Preservar os índices e relatórios oficiais.
- Utilizar o relatório-mestre como fonte quantitativa do TCC II.
- Realizar a análise qualitativa dos erros na etapa de discussão.

Pendências antes do congelamento integral do repositório:
- Validar o funcionamento da aplicação cliente.
- Executar a verificação final de código e testes.
- Revisar os arquivos modificados e não rastreados.
- Registrar o estado final no controle de versão.

O encerramento das avaliações não equivale, por si só,
à validação funcional completa do sistema.
