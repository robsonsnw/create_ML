# Molde do ML_PLANO.md

Gerar o arquivo com **exatamente** estas seções, preenchidas com o que foi achado (caminhos de arquivo reais, nomes de tabela reais, comandos do stack real). O arquivo é um **prompt para outra IA**: imperativo, sem ambiguidade, sem perguntas abertas. Onde faltou dado: `[premissa: ...]`. Nunca incluir segredos.

```markdown
# ML_PLANO — <nome do projeto>
Gerado por /create_ML em <data>. Instrução para a IA construtora: execute as fases na ordem, uma por vez; ao fim de cada fase rode os testes da fase e pare se algum falhar. Não altere comportamento existente: o ML entra em SOMBRA e só decide onde provar precisão.

## 1. Diagnóstico
- Veredito: <...> (nota X/100) | Dimensões: caso de uso N, dados N, feedback N, infra N, risco N
- Stack: <linguagens, frameworks, banco, agendador, deploy>
- Evidências: <5 a 8 itens `arquivo:linha` que sustentam o veredito>
- Pré-requisitos que faltam: <lista ou "nenhum">

## 2. Caso de uso escolhido
- Problema: <entrada → saída>   | Hoje resolvido por: <regra/LLM/humano em `arquivo:linha`>
- Classes/segmentos: <de onde vêm; coluna ou enum real>
- Fonte de rótulos: <tabela/coluna/ação do usuário que gera o rótulo>
- Outros casos (não construir agora): <até 2>

## 3. Ganhos esperados
| Ganho | Conta | Faixa | Premissa |
|---|---|---|---|
Medida de sucesso: <cobertura à precisão ≥ 97% ≥ X%; custo de LLM −Y%>

## 4. Infra
- Reaproveitar: <o que já existe>
- Acrescentar: <o mínimo; CPU/GPU, RAM, jobs, tabelas>
- Custo extra: <faixa>
- Variáveis de configuração novas (só nomes): <lista; reaproveitar as existentes antes de criar>

## 5. Arquitetura
- Módulo de acesso ao armazenamento (único ponto): `<caminho/nome>` com a interface do padrão 10, mapeada para <banco>
- Mapeamento das tabelas (esqueleto de `padroes-ml.md`) para <banco>: DDL/migração em <formato do projeto>
- Onde o modelo é chamado no fluxo atual: `arquivo:linha` (antes do caminho atual, com fallback)
- Diagrama (mermaid): coleta → vocabulário → treino → sombra → ativação → decisão → conferência

## 6. Padrões obrigatórios
<Copiar os padrões 1 a 14 de `padroes-ml.md` que se aplicam, com os valores de partida, e dizer quais foram ajustados e por quê. Riscar os que não se aplicam (ex.: padrão 5 sem dado pessoal).>

## 7. Fases (cada uma com Entrega, Arquivos, Testes, Critério de pronto)
- **Fase 0 — Coletar** (se faltar rótulo): gravar rótulo a partir de <ação>; nenhuma mudança de comportamento.
- **Fase 1 — Base e dados**: tabelas, módulo de acesso, anonimização (se houver), vocabulário, coleta com chave de liberação.
- **Fase 2 — Modelo e treino**: TF-IDF+LR (ou o escolhido), separação por hash, calibração, poda, treino agendado e por comando, versões.
- **Fase 3 — Sombra**: comparar com o caminho atual; contadores por segmento; tela/relatório simples.
- **Fase 4 — Ativação e vigilância**: critérios, flag por segmento, amostra de conferência, auto-reversão.
- **Fase 5 — Aprender com o usuário**: sinais de feedback, regra dos casos parecidos.
- **Fase 6 — Operação**: auditoria de todos os desfechos, contadores de economia, benchmark com dados reais.

## 8. Testes obrigatórios
<Lista concreta: anonimização não vaza dado pessoal; separação teste nunca treinada; treino com poucos exemplos recusa; base fora do ar → caminho anterior; reversão automática; auditoria em sucesso/recusa/falha; subir o serviço do zero.>

## 9. Riscos e como mitigar
<Da seção 6 de `criterios.md`, só os que se aplicam.>

## 10. Definição de pronto
<Critérios mensuráveis: cobertura, precisão, custo, latência, auditoria, documentação atualizada.>
```

Tamanho alvo do plano: 250 a 500 linhas. Mais que isso = cortar prosa, não conteúdo técnico.
