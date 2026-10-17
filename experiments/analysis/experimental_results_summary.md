# Resultados experimentais consolidados

## Protocolo

- Quatro configurações: E1, E2, E3 e E4.
- 26 perguntas distribuídas entre quatro documentos.
- Recuperação avaliada em Top-5, Top-10 e Top-20.
- Faithfulness comparado nas mesmas 24 perguntas válidas.
- Response Relevancy avaliado nas 26 perguntas.
- Todas as configurações tiveram 26 gerações bem-sucedidas.

## Resultados gerais

| Configuração | Page Hit@5 | Page Hit@10 | Page Hit@20 | Component Hit@20 | Faithfulness (24) | Relevancy (26) |
|---|---:|---:|---:|---:|---:|---:|
| E1 | 23/26 | 24/26 | 25/26 | N/A | 0.9514 | 0.8339 |
| E2 | 24/26 | 24/26 | 25/26 | N/A | 0.8681 | 0.7800 |
| E3 | 20/26 | 22/26 | 25/26 | 5/26 | 0.8319 | 0.7993 |
| E4 | 19/26 | 22/26 | 24/26 | 13/26 | 0.7833 | 0.7803 |

## Resultados por tipo de evidência

| Configuração | Tipo | Questões | Page Hit@20 | Component Hit@20 | Response Relevancy |
|---|---|---:|---:|---:|---:|
| E1 | figure | 17 | 16/17 | N/A | 0.8100 |
| E1 | table | 5 | 5/5 | N/A | 0.9404 |
| E1 | plain_text | 4 | 4/4 | N/A | 0.8026 |
| E2 | figure | 17 | 16/17 | N/A | 0.7291 |
| E2 | table | 5 | 5/5 | N/A | 0.9352 |
| E2 | plain_text | 4 | 4/4 | N/A | 0.8021 |
| E3 | figure | 17 | 16/17 | 0/17 | 0.7898 |
| E3 | table | 5 | 5/5 | 1/5 | 0.8844 |
| E3 | plain_text | 4 | 4/4 | 4/4 | 0.7328 |
| E4 | figure | 17 | 15/17 | 8/17 | 0.7738 |
| E4 | table | 5 | 5/5 | 1/5 | 0.8443 |
| E4 | plain_text | 4 | 4/4 | 4/4 | 0.7277 |

## Tempos registrados de geração

| Configuração | Total registrado (s) | Média por pergunta (s) |
|---|---:|---:|
| E1 | 467.9 | 18.0 |
| E2 | 465.3 | 17.9 |
| E3 | 284.9 | 11.0 |
| E4 | 342.9 | 13.2 |

## Particularidades do protocolo experimental

- E1 e E2 recuperaram até 20 evidências, mas a geração utilizou somente as evidências completas que couberam no orçamento de 5.000 tokens de entrada.
- E3 e E4 utilizaram as 20 evidências recuperadas na geração, sem esse corte adicional de contexto.
- O índice E3 foi construído removendo 641 registros de figuras cuja representação textual consistia exclusivamente em descrições visuais. Assim, a ausência de recuperação direta dessas figuras no E3 é influenciada pela própria definição da ablação.
- Na comparação pareada de Faithfulness, foram excluídas `statistics_q003`, sem pontuação válida no E4, e `statistics_q006`, sem pontuação válida no E3.

## Limitações de interpretação

- Page Hit mede recuperação da página esperada, não do elemento exato.
- Component Hit usa documento, página e tipo de componente, não o identificador exato da evidência.
- Component Hit não é diretamente aplicável aos baselines E1/E2.
- E3 remove os registros de figuras com descrições visuais; a ausência dessas figuras no índice influencia diretamente o resultado.
- Faithfulness mede suporte nas evidências, não correção factual.
- Response Relevancy não substitui verificação da resposta de referência.
- O conjunto possui apenas 26 perguntas.
- Os tempos registrados não representam comparação controlada de desempenho computacional.

## Proveniência

Os caminhos dos relatórios originais estão registrados em `experimental_results_master.json`, no campo `sources` de cada configuração.
