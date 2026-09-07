import os, json, time, sqlite3, imaplib, email, unicodedata
from email.header import decode_header
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse

from core import classificar_llm, classificar_heuristica

DB_FILE = "database.db"
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
is_processing = False  # Lock de concorrência


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs_triagem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid_email TEXT,
                message_id TEXT,
                remetente TEXT,
                assunto TEXT,
                texto_bruto TEXT,
                categoria TEXT,
                tokens_total INTEGER,
                latencia_ms REAL,
                fallback_ativado BOOLEAN DEFAULT 0,
                categoria_heuristica TEXT,
                latencia_heuristica_ms REAL,
                categoria_imap TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migração leve: adiciona colunas novas se o banco já existir sem elas
        cols = [r[1] for r in conn.execute("PRAGMA table_info(logs_triagem)").fetchall()]
        if "categoria_heuristica" not in cols:
            conn.execute("ALTER TABLE logs_triagem ADD COLUMN categoria_heuristica TEXT")
        if "latencia_heuristica_ms" not in cols:
            conn.execute("ALTER TABLE logs_triagem ADD COLUMN latencia_heuristica_ms REAL")
        if "categoria_imap" not in cols:
            conn.execute("ALTER TABLE logs_triagem ADD COLUMN categoria_imap TEXT")


def extrair_texto(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    return msg.get_payload(decode=True).decode('utf-8', errors='ignore')


def processar_caixa():
    global is_processing
    if is_processing:
        return
    is_processing = True

    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        mail.login(os.environ.get("EMAIL_USUARIO"), os.environ.get("SENHA_EMAIL"))
        mail.select('"Classificador_Teste"')

        status, mensagens = mail.uid('SEARCH', None, 'UNSEEN')
        uids = mensagens[0].split()

        if not uids:
            return

        status, listas = mail.list()
        pastas_existentes = [p.decode().split(' "/" ')[-1].replace('"', '') for p in listas]

        for uid in uids:
            status, dados = mail.uid('FETCH', uid, '(BODY.PEEK[])')
            msg = email.message_from_bytes(dados[0][1])

            assunto_header = decode_header(msg["Subject"])[0]
            assunto = assunto_header[0]
            if isinstance(assunto, bytes):
                assunto = assunto.decode(assunto_header[1] or 'utf-8', errors='ignore')

            remetente = msg.get("From", "Desconhecido")
            message_id = msg.get("Message-ID", "").strip()
            corpo_bruto = extrair_texto(msg)

            # Classificação por LLM (motor de produção) e heurística (baseline comparativa)
            res_llm = classificar_llm(assunto, corpo_bruto)
            res_heur = classificar_heuristica(assunto, corpo_bruto)

            categoria_exibicao = res_llm["categoria"]
            corpo_log = corpo_bruto[:300]

            # Remove acentos APENAS para criar a pasta no servidor IMAP
            categoria_imap = ''.join(c for c in unicodedata.normalize('NFD', categoria_exibicao) if unicodedata.category(c) != 'Mn')

            if categoria_imap not in pastas_existentes:
                mail.create(f'"{categoria_imap}"')
                pastas_existentes.append(categoria_imap)

            mail.uid('COPY', uid, f'"{categoria_imap}"')
            mail.uid('STORE', uid, '+FLAGS', '(\\Deleted)')

            with sqlite3.connect(DB_FILE) as conn:
                conn.execute(
                    """INSERT INTO logs_triagem
                       (uid_email, message_id, remetente, assunto, texto_bruto, categoria,
                        tokens_total, latencia_ms, fallback_ativado,
                        categoria_heuristica, latencia_heuristica_ms, categoria_imap)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (uid.decode(), message_id or "SEM-ID", remetente, assunto, corpo_log,
                     categoria_exibicao, res_llm["tokens_total"], res_llm["latencia_ms"],
                     res_llm["fallback_ativado"], res_heur["categoria"], res_heur["latencia_ms"],
                     categoria_imap)
                )

            time.sleep(1.5)  # Proteção de Rate Limit da Groq

        mail.expunge()
    except Exception as e:
        print(f"Erro no processamento: {e}")
    finally:
        mail.logout()
        is_processing = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(processar_caixa, 'interval', minutes=2)
    scheduler.start()

    import threading
    threading.Thread(target=processar_caixa).start()

    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/api/stats")
def get_stats():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        geral = cursor.execute("""
            SELECT COUNT(*) as total,
                   AVG(latencia_ms) as avg_latencia,
                   AVG(tokens_total) as avg_tokens,
                   AVG(latencia_heuristica_ms) as avg_latencia_heuristica,
                   SUM(CASE WHEN categoria = categoria_heuristica THEN 1 ELSE 0 END) as concordancia_llm_heuristica
            FROM logs_triagem
        """).fetchone()

        por_categoria = cursor.execute("""
            SELECT categoria, COUNT(*) as volume, AVG(latencia_ms) as latencia, AVG(tokens_total) as tokens
            FROM logs_triagem GROUP BY categoria
        """).fetchall()

    return {
        "geral": dict(geral),
        "por_categoria": [dict(row) for row in por_categoria],
    }


@app.get("/api/logs")
def get_logs():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        logs = conn.execute("SELECT * FROM logs_triagem ORDER BY timestamp DESC LIMIT 20").fetchall()
    return [dict(log) for log in logs]


@app.post("/api/undo/{uid}")
def undo_move(uid: str):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            log = conn.execute("SELECT * FROM logs_triagem WHERE uid_email = ?", (uid,)).fetchone()

        if not log:
            return {"status": "error", "message": "Registro não encontrado."}

        # Usa categoria_imap (nome real da pasta no servidor, sem acento) —
        # log["categoria"] é só o rótulo de exibição e o IMAP não aceita
        # acentos na sessão sem encoding especial, o que causava o erro
        # "'ascii' codec can't encode character" no estorno.
        pasta = log["categoria_imap"] or log["categoria"]
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(os.environ.get("EMAIL_USUARIO"), os.environ.get("SENHA_EMAIL"))
        mail.select(f'"{pasta}"')

        status, msgs = mail.search(None, f'(HEADER Message-ID "{log["message_id"]}")')
        ids = msgs[0].split()

        if ids:
            for target_id in ids:
                mail.copy(target_id, '"Classificador_Teste"')
                mail.store(target_id, '+FLAGS', '\\Deleted')
            mail.expunge()

            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("DELETE FROM logs_triagem WHERE uid_email = ?", (uid,))

        mail.logout()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def serve_dashboard():
    return FileResponse("index.html")
