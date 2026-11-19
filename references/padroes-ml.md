# Padrões de construção do ML (extraídos de um sistema real em produção)

Parte fixa do plano. Cada padrão tem **regra**, **valor de partida** (ajustável) e **por quê**. Independem de banco e de domínio: os exemplos usam "classe" (o que se prevê) e "segmento" (o recorte em que se mede, ex.: categoria, região, produto).

## 1. Nunca decide de cara: SOMBRA primeiro
O modelo novo classifica o **mesmo** caso que o caminho atual (regra, LLM ou humano) e só **compara**; não muda nenhuma resposta. Grava contadores de concordância por segmento (sem texto). Nunca levanta exceção para o chamador.
*Por quê:* prova de precisão com dado real antes de qualquer risco.

## 2. Ativação por segmento, com critérios checados no servidor
Um **segmento** (classe, ou classe × categoria) só passa a ser decidido pelo modelo quando, no **conjunto de teste nunca treinado**: `MIN_EXEMPLOS=50`, `MIN_PREVISTOS=10` (vezes em que o modelo se arriscou) e `MIN_PRECISAO=0.97`. O botão/flag só reflete o que o servidor conferiu.
*Por quê:* um segmento ruim não contamina os bons.

## 3. Vigilância com auto-reversão
Depois de ativo, `AMOSTRA_PCT=5%` das decisões do modelo são **conferidas** pelo caminho anterior (vence na discordância; seleção estável pelo hash do texto). Janela das últimas `100` conferências; se discordar em mais de `5%`, o segmento **volta sozinho** ao caminho anterior, com aviso e registro. Nova versão do modelo **revalida** os segmentos ativos.

## 4. Confiança calibrada, não bruta
Regressão logística é tímida: no benchmark, acerto 95,8% mas só 10% dos casos passavam de 85% de confiança. Aplicar **temperatura** (escala nos logits) ajustada **só com dados de treino**, e medir a **cobertura à precisão-alvo** (97%). `LIMIAR=0.85` de confiança para o modelo "se arriscar".
*Por quê:* sem calibrar, o ML quase nunca é usado. Foi o maior ganho do benchmark, maior que trocar de motor.

## 5. Privacidade por construção (se há texto/dado pessoal)
Três barreiras, nesta ordem, em **funções puras** (sem banco, sem rede):
1. **Marcadores**: número de pedido/protocolo/documento, CPF/CNPJ, e-mail, telefone, CEP, valores, datas e qualquer número viram `<id> <doc> <email> <tel> <cep> <valor> <data> <num>`. O mais específico primeiro.
2. **Vocabulário fechado**: só entram palavras/pares que aparecem em **muitas** fontes (`MIN_DOCUMENTOS=50` em `MIN_ENTIDADES=10` entidades diferentes). Nome próprio aparece em uma entidade só e nunca passa. **Sem vocabulário, nada é coletado.**
3. **Vetor hasheado**: palavras viram posições (`DIM=2^20`) com contagem; a palavra não é guardada.
O exemplo gravado **não tem** identificador de cliente, de registro nem texto legível. `MIN_TOKENS_UTEIS=8`: texto curto demais não vira exemplo.
Se o projeto não tem dado pessoal, simplificar para as barreiras 1 e 3.

## 6. Modelo simples, treino em biblioteca, previsão em código puro
TF-IDF + regressão logística multinomial. **Treino** com scikit-learn (matriz esparsa, L-BFGS; 300 mil exemplos em ~13 s); se a biblioteca faltar, caminho em Python puro mais lento, **mesmo artefato**. **Previsão** em código puro (poucas contas). Artefato guarda **só números** (posição, classe, peso), podado para as `MAX_POR_CLASSE=400` posições de maior peso por classe; métricas medidas **no modelo já podado**.
Constantes: `MIN_DF=2`, `MIN_POR_CLASSE=3`, `MAX_EXEMPLOS=300_000`, `MAX_POR_CLASSE_TREINO=30_000` (classe frequente não domina), teto de operações para não segurar a CPU do serviço.

## 7. Separação treino/teste fixa pelo hash
`teste` se `int(hash[:8],16) % 10 == 0` (~10%). O mesmo exemplo cai sempre do mesmo lado, em **qualquer versão**: nunca há exemplo de teste treinado.

## 8. Treino agendado, versionado, com tolerância
Noturno (ex.: 03h30) **só se** houver `MIN_NOVOS=200` exemplos novos; botão manual exige `MIN_TOTAL=60`. Cada treino cria uma **versão**; vira a vigente só se o acerto no teste não for pior que `vigente − 2 pontos` (`TOLERANCIA=0.02`); senão fica **candidata** e uma pessoa decide. **Trava de concorrência** (um treino por vez). Estado do treino gravado na config.

## 9. Aprender com o que o usuário FAZ
Rótulo sai da ação, sem exigir clique de "certo/errado": usuário aceita a sugestão → exemplo confirmado (`PESO_USUARIO=3`); faz **outra** ação que implica outra classe → correção. Correção que **contradiz** o modelo só entra quando `CASOS_PARECIDOS=3` correções semelhantes (textos diferentes, cosseno ≥ `0.4`; cosseno ≥ `0.99` = mesmo texto, não conta duas vezes) chegam para o mesmo par "classe do modelo → classe do usuário". Caso que o modelo não classificou e o usuário rotula entra direto.
*Por quê:* proteção contra erro e manipulação; o rótulo é gratuito.

## 10. Camada de acesso fina e tolerante a falha
Um **único módulo** fala com o armazenamento do ML (interface: `ler_exemplos, gravar_exemplo, ler_vocabulario, gravar_modelo, ler_modelo, config_get/set, contadores`). Trocar de banco = trocar só esse módulo. Sem configuração ou base fora do ar → devolve "indisponível" e **o sistema segue pelo caminho anterior**. Pausa de 60 s após falha (não tentar a cada requisição). Cache em memória com TTL (vocabulário e modelo ~10 min, config ~60 s). Todo valor por parâmetro nomeado (sem concatenar SQL). Erros sem segredo.

## 11. Chave de cache por "modelo de texto"
Dois textos que só diferem em número, data ou nome de parte geram a **mesma chave** (usa as mesmas barreiras do padrão 5). Evita reclassificar o repetido.

## 12. Auditoria de todo desfecho
Registrar pedido, sucesso, **recusa** (poucos exemplos, já em andamento, sem permissão, base fora), **falha** e o **"nada a fazer"** das rotinas automáticas; também o que roda por console/script. Teste que prove o registro em todos os desfechos, pela rota e não só pela função. Contadores de economia (decisões do modelo, conferências, discordâncias) por dia.

## 13. Liberação gradual (feature flag)
Coleta, treino e ativação ligam por **chave de configuração**: desligado → piloto (um cliente/ambiente) → liberado para todos. Sem coleta ligada, nada é gravado.

## 14. Teste de aceitação antes de confiar
Benchmark repetível com validação cruzada (5 dobras), **curva de aprendizado** (3, 5, 8, 12, 19 exemplos/classe), **escala** (20 mil a 300 mil), medindo acerto, F1, **cobertura à precisão de 97%** e erro de calibração. Registrar o limite honesto: dados sintéticos são mais fáceis que os reais; repetir com dados reais assim que existirem.

## Esqueleto de armazenamento (adaptar ao banco)
| Entidade | Campos mínimos |
|---|---|
| `exemplo_ml` | `hash` (único), `vetor` (json esparso), `classe`, `segmento`, `origem` (modelo/usuário), `peso`, `vocab_versao`, `criado_em` |
| `vocabulario_ml` | `versao`, `dados` (lista fechada), `tamanho`, `criado_em` |
| `modelo_ml` | `versao`, `artefato` (json: posição, classe, peso, temperatura), `metricas`, `estado` (sombra/candidata/vigente), `criado_em` |
| `ativacao_ml` | `segmento`, `classe`, `ativo`, `janela` (últimas conferências), `atualizado_em` |
| `comparacao_ml` | `versao`, `segmento`, `classe_esperada`, `acertou`, `confiante`, contadores por dia |
| `config_ml` | chave/valor (`coleta_ligada`, `treino_estado`, ...) |
Nenhuma dessas tabelas tem identificador de cliente/entidade de negócio nem texto legível.
