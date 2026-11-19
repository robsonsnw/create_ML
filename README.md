# create_ML

Skill para o [Claude Code](https://claude.com/claude-code) que responde: **"vale a pena colocar Machine Learning neste projeto?"**

Rode `/create_ML` na raiz do seu projeto. Sem fazer perguntas, ela:

1. **Varre o código** (linguagens, banco, regras manuais, chamadas a LLM, feedback do usuário, infra, dados pessoais).
2. **Dá o veredito de viabilidade técnica**, com nota de 0 a 100 em 5 dimensões.
3. **Estima os ganhos** (custo de LLM evitado, tempo humano, qualidade) em faixas, com a conta à vista.
4. **Sugere a infra mínima** (CPU antes de GPU, reaproveitando o que já existe).
5. **Gera o `ML_PLANO.md`**: um prompt em fases para a sua IA construir o ML sob medida.

Agnóstica de banco e de linguagem. Só lê o seu projeto; a única escrita é o `ML_PLANO.md`.

## Instalação

```bash
git clone https://github.com/robsonsnw/create_ML ~/.claude/skills/create_ML
```

No Windows: `%USERPROFILE%\.claude\skills\create_ML`. Abra uma sessão nova do Claude Code.

## Comandos

| Comando | O que faz |
|---|---|
| `/create_ML` | varre a pasta atual e grava `ML_PLANO.md` na raiz |
| `/create_ML <pasta>` | idem, para outra pasta |
| `/create_ML --so-diagnostico` | só o resumo no terminal, sem criar arquivo |
| `/create_ML --saida <arquivo.md>` | grava o plano em outro caminho |
| `/create_ML --foco <caso>` | força o caso de uso (ex.: `classificacao`) |

## Padrões embutidos

Extraídos de um sistema real em produção: modelo em sombra antes de decidir, ativação por segmento com critérios, auto-reversão, confiança calibrada, anonimização em 3 barreiras, TF-IDF + regressão logística, separação treino/teste por hash, treino versionado, aprendizado com as ações do usuário, camada de acesso fina e tolerante a falha, auditoria de todos os desfechos e liberação gradual.

## Estrutura

- `SKILL.md`: instruções da skill
- `scripts/varrer.py`: scanner (só biblioteca padrão do Python 3)
- `references/`: critérios, padrões de ML e molde do plano

## Licença

MIT.
