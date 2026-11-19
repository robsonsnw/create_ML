# Critérios de viabilidade, ganhos e infra

## 1. Cinco dimensões (0 a 100 cada; nota final = média ponderada)

| Dimensão | Peso | Pergunta que o código responde | Sinais fortes (JSON/código) |
|---|---|---|---|
| Caso de uso | 30% | Existe decisão repetitiva que hoje é manual, por regra ou por chamada paga a LLM? | `candidatos`, `chamadas_llm`, `regras_manuais`, colunas em `colunas_categoricas` |
| Dados | 30% | Há exemplos com o **rótulo certo** (ou como obtê-los)? Quantos? | tabela com coluna de tipo/status + texto/atributos; `auditoria_historico`; `campos_de_texto` |
| Feedback | 15% | O usuário corrige/aprova a decisão (rótulo grátis)? | `sinais_de_feedback`: aprovar, rejeitar, editar, reagendar |
| Infra | 15% | Dá para treinar e servir sem reescrever o sistema? | `infra` (Docker), `agendador`, `filas`, CI, testes |
| Risco | 10% (inverso) | Privacidade, erro caro, regulação | `privacidade`; decisão irreversível; setor regulado |

Faixas: **≥ 70** `VIÁVEL AGORA`; **40–69** `VIÁVEL COM PRÉ-REQUISITOS`; **< 40** `NÃO COMPENSA AINDA`.
Teto: sem **nenhum** rótulo possível (nem retroativo, nem por feedback), a nota final não passa de 39.
As `notas_grosseiras` do script são só ponto de partida; ajuste lendo o código e diga o motivo do ajuste.

## 2. Tipo de problema → abordagem inicial

| Situação | Abordagem | Por quê |
|---|---|---|
| Texto curto/médio de domínio estreito → categoria | **TF-IDF + regressão logística** (scikit-learn) | em benchmark interno (480 textos, 20 classes) venceu embeddings (96% x 62–74%), aprende com 3–12 exemplos por classe, treina em segundos |
| Tabela (campos numéricos/categóricos) → classe ou número | Gradient boosting (LightGBM/XGBoost) ou regressão logística | forte com poucos milhares de linhas |
| Série temporal (volume, receita, demanda) | Previsão estatística (Prophet/statsmodels), não rede neural | poucos pontos, sazonalidade |
| Anomalia/fraude sem rótulo | Isolation Forest / regras estatísticas | não exige rótulo |
| Busca por similaridade/recomendação | TF-IDF + cosseno; embeddings só se a busca for semântica aberta | embeddings pesam mais e vazam mais |
| Imagem/áudio/documento escaneado | Modelo pré-treinado/serviço pronto | treinar do zero raramente compensa |
| Extração de campos de texto | Regex/regras primeiro; LLM como fallback | barato e auditável |
| Já chama LLM pago para classificar | **Padrão "sombra → ativação"** (padrões 1–3): o modelo local aprende com as respostas da LLM e passa a decidir sozinho onde provar precisão | corta custo e latência sem perder qualidade |

**Quando NÃO usar ML (dizer no veredito):** a regra cabe em 20 linhas e é estável; menos de ~30 exemplos por classe e sem feedback; erro é irreversível e sem humano revisando; o ganho é < 1 dia de trabalho por mês; dado não pode ser usado (base legal ausente).

## 3. Volumes mínimos (regra prática)

| Tipo | Mínimo para começar | Confortável |
|---|---|---|
| Classificação de texto | 10 exemplos/classe | 50+/classe |
| Tabular | 1.000 linhas | 10.000+ |
| Série temporal | 2 ciclos sazonais (ex.: 24 meses) | 3+ |
| Anomalia | 500 eventos normais | 5.000+ |

Sem o mínimo hoje, mas com fluxo que gera rótulo (feedback), o veredito é `VIÁVEL COM PRÉ-REQUISITOS` com a **Fase 0: coletar** primeiro.

## 4. Ganhos (sempre faixa, conta à vista, premissa marcada)

| Ganho | Como estimar | Fórmula |
|---|---|---|
| Custo de LLM evitado | chamadas/mês (do código/logs) × custo por chamada × cobertura do modelo | cobertura realista inicial 30–60% das chamadas (o modelo só decide onde prova ≥ 97% de precisão) |
| Tempo humano | decisões/mês × minutos por decisão × % automatizado | % inicial 20–50% |
| Qualidade | erros hoje (se medido) × redução esperada 20–60% | só com baseline medido |
| Receita/retenção | casos previstos × taxa de ação × valor | só com dado de negócio; senão `[premissa]` |
| Latência | tempo da chamada externa → previsão local em ms | citar ordem de grandeza |

Medida central de economia: **cobertura na precisão-alvo** (fração dos casos que o modelo resolve sozinho com precisão ≥ alvo). Acurácia geral engana.
Se não houver dado de volume no código, escrever `[premissa: N/mês]` e mostrar a fórmula para o usuário trocar o número.

## 5. Matriz de infra (escolher a menor que serve)

| Cenário | Infra mínima |
|---|---|
| Texto/tabular, < 300 mil exemplos | **CPU, 1–2 vCPU, 1–2 GB RAM**; treino em job noturno dentro do serviço existente ou container irmão; sem GPU |
| 300 mil a 5 mi de exemplos | 4 vCPU, 8 GB; treino em lote semanal; amostrar por classe (teto por classe) |
| Embeddings/modelo pré-treinado local | +1–2 GB RAM para o modelo; GPU só se > 25 textos/s for necessário |
| Deep learning próprio | GPU sob demanda (nuvem); justificar por escrito por que o clássico não basta |
| Servir | previsão em processo (modelo pequeno em memória, cache com TTL) — sem serviço de inferência separado até haver necessidade medida |
| Armazenar | tabelas no **banco que o projeto já usa**: `exemplos`, `modelos` (artefato JSON/bytes), `config`, `contadores`; banco separado só se o volume ou o isolamento exigir |
| Agendar | o agendador que já existe (cron, APScheduler, Celery, BullMQ, Quartz...); senão cron do SO/container |
| Observar | contadores por segmento no banco + auditoria; painel simples antes de ferramenta externa |

Sempre informar: custo extra mensal em faixa (ex.: "R$ 0–60 se couber nos containers atuais"), e o que **reaproveitar** do que já existe.

## 6. Riscos a listar (use só os que se aplicam)

Rótulo ruim (regra antiga errada vira "verdade"); deriva (a lei, o produto ou o texto mudam); vazamento de dado pessoal no vetor/artefato; decisão automática sem revisão; viés por segmento pequeno; dependência de um único dado; treino segurando CPU do serviço principal.
