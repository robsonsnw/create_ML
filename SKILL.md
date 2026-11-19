---
name: create_ML
description: Varre o código de um projeto, diagnostica se Machine Learning é tecnicamente viável, estima os ganhos, sugere a infra e gera um plano em Markdown (ML_PLANO.md) para outra IA construir o ML sob medida. Agnóstica de banco. Não faz perguntas. Use para "/create_ML", "viabilidade de ML", "dá para colocar ML neste projeto?", "plano de ML", "diagnóstico de ML".
---

# create_ML

Roda sozinha, **sem perguntar nada**, e entrega um diagnóstico + um `ML_PLANO.md` pronto para colar numa IA construtora.

## Comandos

| Comando | O que faz |
|---|---|
| `/create_ML` | **sem pasta informada, varre tudo a partir da pasta onde o usuário rodou o comando (a pasta atual), incluindo todas as subpastas e arquivos em qualquer profundidade**; diagnostica e grava `ML_PLANO.md` nessa pasta |
| `/create_ML <pasta>` | idem, para outra pasta |
| `/create_ML --so-diagnostico` | só o resumo no terminal, não grava arquivo |
| `/create_ML --saida <arquivo.md>` | grava o plano em outro caminho |
| `/create_ML --foco <caso>` | força o caso de uso (ex.: `--foco classificacao`); sem isso a skill escolhe o melhor |

Argumento ausente = padrão. Nunca pedir confirmação: escolher o padrão e registrar a suposição no plano.

## Fluxo (executar nesta ordem, sem parar)

1. **Varrer.** Pasta-alvo = argumento, ou, se ausente, a **pasta atual de trabalho** (nunca perguntar, nunca subir para a pasta-pai). Rodar `python <pasta-da-skill>/scripts/varrer.py <pasta-alvo>` (só stdlib; em Windows usar `python`, em Linux `python3`). A varredura é recursiva (todas as subpastas e arquivos); só pula pastas de dependência/build/cache (`node_modules`, `.venv`, `dist`, `.git` etc.) e arquivos acima de 400 KB, e o JSON informa o que foi pulado (`pastas_ignoradas`, `arquivos_grandes_pulados`): citar isso no plano. Guardar o JSON. Se o script falhar, varrer com Glob/Grep e seguir.
2. **Confirmar lendo código.** Com o JSON, abrir **no máximo 10 arquivos** (use `offset`/`limit`, não leia arquivo inteiro): os `principais_arquivos` do caso de uso mais forte, o esquema do banco (tabelas centrais), um `chamadas_llm`/`regras_manuais` se existir, o `Dockerfile` e o arquivo do agendador. Objetivo: provar ou derrubar cada candidato do script (ele conta palavras, não entende).
3. **Escolher casos de uso** (até 3, ranqueados) usando `references/criterios.md`: tipo de problema, rótulo existente, volume, feedback, risco.
4. **Pontuar viabilidade** nas 5 dimensões de `references/criterios.md` e dar **veredito**: `VIÁVEL AGORA`, `VIÁVEL COM PRÉ-REQUISITOS` ou `NÃO COMPENSA AINDA` (com o que falta e como medir).
5. **Estimar ganhos** (tabela do `references/criterios.md`): sempre em faixa, com a conta mostrada e a premissa marcada `[premissa]` quando o dado não está no código. Nunca inventar número sem base.
6. **Sugerir a infra** pela matriz de `references/criterios.md` (a menor que resolve; CPU antes de GPU; reaproveitar o que já existe no projeto).
7. **Gerar o `ML_PLANO.md`** com o molde de `references/modelo-plano.md`, adaptado ao stack e ao banco achados. Os padrões de construção vêm de `references/padroes-ml.md` (são a parte fixa e testada em produção).
8. **Responder no terminal** com o resumo curto do bloco "Saída" abaixo.

## Regras

- **Agnóstica de banco**: o plano descreve o acesso ao ML como uma interface fina (`ler_exemplos`, `gravar_exemplo`, `ler_modelo`, `gravar_modelo`, `config`) e mostra o mapeamento para o banco detectado (Postgres, MySQL, SQLite, Mongo, outro). Se não achar banco, propor SQLite/arquivo e dizer isso.
- **Agnóstica de linguagem**: o treino pode rodar em Python mesmo que o app seja Node/Java/etc. (microserviço ou job). Dizer qual e por quê.
- **Só leitura no projeto do usuário**: a única escrita é o `ML_PLANO.md` (ou o caminho de `--saida`). Não instalar nada, não editar código, não rodar migração.
- **Honestidade**: sem dados rotulados nem como obtê-los, o veredito é `NÃO COMPENSA AINDA` e o plano vira "como começar a coletar". Se o caso de uso for melhor resolvido por regra ou SQL, dizer.
- **Privacidade primeiro**: se `privacidade` do JSON tiver dados pessoais, o plano inclui a seção de anonimização (padrão 5 de `padroes-ml.md`) e cita LGPD/GDPR conforme o contexto.
- **Segredos**: nunca copiar valor de `.env`, chave ou senha para o plano; citar só o nome da variável.
- **Idioma**: o plano e a resposta saem no idioma do usuário (padrão: português com acentos).
- **Monorepo**: se houver vários serviços, diagnosticar o conjunto e apontar em qual serviço o ML entra.

## Saída no terminal (formato fixo, cabe em uma tela)

```
VEREDITO: <VIÁVEL AGORA | VIÁVEL COM PRÉ-REQUISITOS | NÃO COMPENSA AINDA>   (nota X/100)
Stack: <linguagens, framework, banco>
Melhor caso de uso: <1 linha>  | Outros: <até 2>
Ganho estimado: <faixa + unidade>  [premissas: ...]
Infra: <1 linha>  | Custo extra: <faixa>
Falta antes de começar: <até 3 itens, ou "nada">
Risco principal: <1 linha>
Plano: <caminho do ML_PLANO.md>
Próximo passo: colar o ML_PLANO.md na sua IA e pedir "execute a Fase 1".
```

## Arquivos

- `scripts/varrer.py` — scanner (stdlib), devolve JSON de sinais.
- `references/criterios.md` — pontuação, ganhos, matriz de infra, quando não usar ML.
- `references/padroes-ml.md` — padrões de construção testados em produção (sombra, ativação, calibração, anonimização, treino, auditoria).
- `references/modelo-plano.md` — molde do `ML_PLANO.md`.
