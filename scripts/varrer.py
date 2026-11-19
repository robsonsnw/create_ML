#!/usr/bin/env python3
"""Varredura de viabilidade de ML. Só stdlib. Uso: python varrer.py <pasta> [--json saida.json]
Imprime um JSON com sinais objetivos do código (stack, banco, candidatos a ML, dados, infra, privacidade).
Não decide nada: a skill lê este JSON e faz o diagnóstico."""
import json, os, re, sys
from collections import Counter, defaultdict

IGNORAR = {".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist", "build", ".next", "target", "vendor",
           ".idea", ".vscode", "graphify-out", ".pytest_cache", ".mypy_cache", "coverage", "site-packages", ".gradle", "bin", "obj"}
EXT_LANG = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
            ".kt": "Kotlin", ".go": "Go", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".rs": "Rust", ".scala": "Scala", ".swift": "Swift",
            ".dart": "Dart", ".sql": "SQL", ".prisma": "Prisma", ".ipynb": "Notebook"}
FONTE = set(EXT_LANG) - {".sql", ".ipynb", ".prisma"}
MANIFESTOS = {"requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "package.json", "pom.xml", "build.gradle", "build.gradle.kts",
              "go.mod", "Gemfile", "composer.json", "Cargo.toml", "pubspec.yaml"}
MAX_BYTES = 400_000
GRANDES = [0]

LIBS = {
    "ml_python": r"\b(scikit-learn|sklearn|xgboost|lightgbm|catboost|torch|tensorflow|keras|statsmodels|prophet|numpy|pandas|scipy)\b",
    "ml_js": r"(@tensorflow/tfjs|onnxruntime|brain\.js|ml5|natural\b|compromise)",
    "ml_outros": r"(smile-core|weka|deeplearning4j|tribuo|ml\.net|gorgonia|linfa|onnx)",
    "nlp_embeddings": r"\b(transformers|sentence-transformers|spacy|nltk|gensim|faiss|pgvector|chromadb|qdrant|pinecone|weaviate)\b",
    "llm": r"\b(openai|anthropic|google-generativeai|genai|langchain|llama[-_]?index|openrouter|ollama|mistralai|cohere|litellm)\b",
}
BANCOS = {
    "PostgreSQL": r"(psycopg2?|asyncpg|node-postgres|postgres(ql)?|supabase|\bpgx\b|npgsql)",
    "MySQL/MariaDB": r"(mysql|mariadb|pymysql)",
    "SQLite": r"sqlite",
    "MongoDB": r"(mongodb|pymongo|mongoose|\bmotor\b)",
    "SQL Server": r"(mssql|pyodbc|sqlserver|tedious)",
    "Oracle": r"(oracledb|cx_oracle|ojdbc)",
    "Redis": r"\bredis\b",
    "Elasticsearch/OpenSearch": r"(elasticsearch|opensearch)",
    "Neo4j/grafo": r"(neo4j|gremlin)",
    "DynamoDB/Firestore": r"(dynamodb|firestore|firebase)",
    "ORM": r"\b(sqlalchemy|prisma|typeorm|sequelize|hibernate|gorm|activerecord|eloquent|drizzle|knex)\b",
}
AGENDADOR = r"\b(apscheduler|celery|bullmq|node-cron|sidekiq|quartz|hangfire|temporal|airflow|crontab|cron)\b"
FILAS = r"\b(rabbitmq|kafka|sqs|pubsub|nats|celery|bullmq)\b"
FRAMEWORKS = {"FastAPI": r"\bfastapi\b", "Django": r"\bdjango\b", "Flask": r"\bflask\b", "Express": r"\bexpress\b", "NestJS": r"@nestjs",
              "Next.js": r"\bnext\b", "React": r"\breact\b", "Vue": r"\bvue\b", "Angular": r"@angular", "Spring": r"spring-boot",
              "Rails": r"\brails\b", "Laravel": r"laravel", "ASP.NET": r"aspnetcore", "Gin/Fiber": r"(gin-gonic|gofiber)"}

CAND = {
    "classificacao": r"\b(classif\w*|categor\w*|tipo_\w+|tagging|rotul\w*|label\w*|triage|triagem)\b",
    "previsao": r"\b(predict\w*|previs\w*|forecast\w*|churn|inadimpl\w*)\b",
    "recomendacao": r"\b(recomend\w*|recommend\w*|sugest\w*|suggest\w*|ranking)\b",
    "anomalia_fraude": r"\b(anomal\w*|fraud\w*|outlier|suspeit\w*)\b",
    "priorizacao_score": r"\b(priorid\w*|priority|score|urgenc\w*)\b",
    "extracao_texto": r"\b(extra[ií]\w*|ocr|resum\w*|summar\w*|sentiment\w*)\b",
}
FEEDBACK = r"\b(feedback|aprov\w*|rejeit\w*|accept\w*|reject\w*|corrig\w*|rating|avalia\w*|thumbs)\b"
TEXTO = r"\b(descri[cç][aã]o|description|texto|conteudo|content|mensagem|message|observa\w*|coment\w*|ementa|assunto|subject)\b"
AUDITORIA = r"\b(audit\w*|historico|history|eventos?)\b"
PII = {"cpf_cnpj": r"\b(cpf|cnpj)\b", "email": r"\be-?mail\b", "telefone": r"\b(telefone|phone|celular)\b", "senha": r"\b(password|senha)\b",
       "saude": r"\b(diagn[oó]stico|prontu[aá]rio|cid10|patient|paciente)\b", "financeiro": r"\b(cart[aã]o|iban|conta_bancaria|card_number)\b",
       "menores": r"\b(menor de idade|crian[cç]a|minor)\b"}
LLM_CHAMADA = r"(\.chat\.completions|\.messages\.create|generate_content|ChatCompletion|openrouter\.ai|/v1/messages)"
REGRAS_MANUAIS = r"(if|elif|case|when)\b[^\n]{0,80}\b(in|contains|includes|startswith|endswith|match|re\.search)\b"


def ler(p):
    try:
        if os.path.getsize(p) > MAX_BYTES:
            GRANDES[0] += 1
            return ""
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def varrer(raiz):
    raiz = os.path.abspath(raiz)
    r = {"raiz": raiz, "arquivos": 0, "linhas": 0, "linguagens": Counter(), "manifestos": [], "testes": 0, "infra": [], "ci": [],
         "dados_arquivos": Counter(), "sql_tabelas": 0, "modelos_orm": 0,
         "pastas": 0, "pastas_ignoradas": Counter(), "arquivos_grandes_pulados": 0}
    manifesto_txt = []
    hits = {k: Counter() for k in ["ml", "bancos", "frameworks", "cand", "pii", "feedback", "texto", "auditoria", "agendador",
                                   "filas", "llm_chamada", "regras_manuais"]}
    exemplos = defaultdict(list)
    colunas_tipo, tabelas = Counter(), []
    for d, dirs, files in os.walk(raiz):
        for x in dirs:
            if x in IGNORAR:
                r["pastas_ignoradas"][x] += 1
        dirs[:] = [x for x in dirs if x not in IGNORAR]
        r["pastas"] += 1
        rel_d = os.path.relpath(d, raiz)
        for n in files:
            p = os.path.join(d, n)
            rel = os.path.normpath(os.path.join(rel_d, n)).replace("\\", "/")
            ext = os.path.splitext(n)[1].lower()
            r["arquivos"] += 1
            if n in MANIFESTOS:
                r["manifestos"].append(rel)
                manifesto_txt.append(ler(p))
            if n == "Dockerfile" or n.startswith(("Dockerfile.", "docker-compose")) or n in (
                    "compose.yaml", "compose.yml", "Procfile", "serverless.yml", "vercel.json", "fly.toml", "render.yaml", "app.yaml"):
                r["infra"].append(rel)
            if ".github/workflows" in rel or n in (".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml"):
                r["ci"].append(rel)
            if ext in (".csv", ".parquet", ".jsonl", ".xlsx", ".pkl", ".joblib", ".onnx", ".h5", ".pt"):
                r["dados_arquivos"][ext] += 1
            if re.search(r"(^|/)(tests?|__tests__|spec)(/|$)|(test_|_test\.|\.test\.|\.spec\.)", rel):
                r["testes"] += 1
            if ext not in EXT_LANG:
                continue
            r["linguagens"][EXT_LANG[ext]] += 1
            txt = ler(p)
            if not txt:
                continue
            if ext in FONTE:
                r["linhas"] += txt.count("\n") + 1
            low = txt.lower()
            if ext in (".sql", ".prisma") or re.search(r"migration|schema|models?", rel.lower()):
                tabelas += re.findall(r"(?i)create\s+table\s+(?:if\s+not\s+exists\s+)?[\"`]?([\w.]+)", txt)
                r["modelos_orm"] += len(re.findall(r"^\s*(?:class\s+\w+\((?:db\.Model|Base|models\.Model)|model\s+\w+\s*\{)", txt, re.M))
                for c in re.findall(r"(?im)^\s*[\"`]?(tipo\w*|status|categoria\w*|classe|natureza|prioridade|etapa|type|category|kind|label)[\"`]?\s+\w+", txt):
                    colunas_tipo[c.lower()] += 1
            for k, rx in LIBS.items():
                m = re.findall(rx, low)
                if m:
                    hits["ml"][k] += len(m)
            for k, rx in BANCOS.items():
                if re.search(rx, low):
                    hits["bancos"][k] += 1
            for k, rx in FRAMEWORKS.items():
                if re.search(rx, low):
                    hits["frameworks"][k] += 1
            for k, rx in CAND.items():
                c = len(re.findall(rx, low))
                if c:
                    hits["cand"][k] += c
                    exemplos[k].append((rel, c))
            for k, rx in PII.items():
                if re.search(rx, low):
                    hits["pii"][k] += 1
            for key, rx in (("feedback", FEEDBACK), ("texto", TEXTO), ("auditoria", AUDITORIA), ("agendador", AGENDADOR), ("filas", FILAS)):
                c = len(re.findall(rx, low))
                if c:
                    hits[key][rel] = c
            c = len(re.findall(LLM_CHAMADA, txt))
            if c:
                hits["llm_chamada"][rel] = c
            c = len(re.findall(REGRAS_MANUAIS, txt))
            if c >= 4:
                hits["regras_manuais"][rel] = c
    mt = "\n".join(manifesto_txt).lower()
    ml_manifesto = {}
    for k, rx in LIBS.items():
        achou = sorted({m if isinstance(m, str) else m[0] for m in re.findall(rx, mt)})
        if achou:
            ml_manifesto[k] = achou
    for k, rx in BANCOS.items():
        if re.search(rx, mt):
            hits["bancos"][k] += 1
    for k, rx in FRAMEWORKS.items():
        if re.search(rx, mt):
            hits["frameworks"][k] += 1
    top = lambda c, n=8: [{"arquivo": a, "ocorrencias": b} for a, b in c.most_common(n)]
    r["sql_tabelas"] = len(set(tabelas))
    r["linguagens"] = dict(r["linguagens"].most_common())
    r["dados_arquivos"] = dict(r["dados_arquivos"])
    r["bancos"] = dict(hits["bancos"].most_common())
    r["frameworks"] = dict(hits["frameworks"].most_common())
    r["ml_nas_dependencias"] = ml_manifesto
    r["candidatos"] = {k: {"total": hits["cand"][k],
                           "principais_arquivos": [{"arquivo": a, "n": n} for a, n in sorted(exemplos[k], key=lambda x: -x[1])[:5]]}
                       for k in CAND if hits["cand"][k]}
    r["colunas_categoricas"] = dict(colunas_tipo.most_common(8))
    r["tabelas_amostra"] = sorted(set(tabelas))[:40]
    r["chamadas_llm"] = top(hits["llm_chamada"])
    r["regras_manuais"] = top(hits["regras_manuais"])
    r["campos_de_texto"] = top(hits["texto"], 6)
    r["sinais_de_feedback"] = top(hits["feedback"], 6)
    r["auditoria_historico"] = top(hits["auditoria"], 5)
    r["agendador"] = top(hits["agendador"], 4)
    r["filas"] = top(hits["filas"], 3)
    r["privacidade"] = dict(hits["pii"].most_common())
    r["arquivos_grandes_pulados"] = GRANDES[0]
    r["pastas_ignoradas"] = dict(r["pastas_ignoradas"])
    r["gpu_mencionada"] = bool(re.search(r"(nvidia|cuda|gpu)", mt))
    return r


def nota(r):
    """Pontuação grosseira 0-100 por dimensão (a skill refina lendo o código)."""
    cand = sum(v["total"] for v in r["candidatos"].values())
    return {
        "casos_de_uso": min(100, len(r["candidatos"]) * 15 + (25 if r["chamadas_llm"] else 0) + (20 if r["regras_manuais"] else 0) + min(15, cand // 20)),
        "dados": min(100, (30 if r["bancos"] else 0) + (25 if r["campos_de_texto"] else 0) + (25 if r["auditoria_historico"] else 0)
                     + (20 if r["sinais_de_feedback"] else 0)),
        "infra": min(100, (35 if r["infra"] else 0) + (25 if r["agendador"] else 0) + (20 if r["ci"] else 0) + (20 if r["testes"] else 0)),
        "feedback_loop": min(100, len(r["sinais_de_feedback"]) * 20 + (30 if r["auditoria_historico"] else 0)),
        "risco_privacidade": min(100, len(r["privacidade"]) * 20),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print("uso: python varrer.py <pasta> [--json saida.json]", file=sys.stderr)
        sys.exit(2)
    res = varrer(sys.argv[1])
    res["notas_grosseiras"] = nota(res)
    out = json.dumps(res, ensure_ascii=False, indent=1)
    if "--json" in sys.argv:
        dest = sys.argv[sys.argv.index("--json") + 1]
        with open(dest, "w", encoding="utf-8") as f:
            f.write(out)
        print("ok:", dest)
    else:
        print(out)
