import smtplib, json, os, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.environ.get("EMAIL_USUARIO")
SENHA = os.environ.get("SENHA_EMAIL")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")

with open("mock_emails.json", "r", encoding="utf-8") as f:
    mocks = json.load(f)

print(f"Iniciando injeção de {len(mocks)} e-mails mockados...")

try:
    server = smtplib.SMTP_SSL(SMTP_HOST, 465)
    server.login(EMAIL, SENHA)
    
    for item in mocks:
        msg = MIMEMultipart()
        msg['From'] = item['remetente']
        msg['To'] = EMAIL
        msg['Subject'] = f"[MOCK] {item['assunto']}"
        msg.attach(MIMEText(item['corpo'], 'plain'))
        
        server.send_message(msg)
        print(f"Enviado: {item['assunto']}")
        time.sleep(1) # Previne bloqueio de spam do Gmail
        
    server.quit()
    print("Injeção concluída! Mova-os para 'Classificador_Teste' no Gmail se não houver filtro.")
except Exception as e:
    print(f"Erro no SMTP: {e}")