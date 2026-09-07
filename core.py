# -*- coding: utf-8 -*-
"""
Módulo central de classificação. Extraído de api.py para ser reusado tanto
pelo daemon IMAP quanto pelo script de avaliação em massa (mocks), evitando
duplicação de lógica entre os dois fluxos.
"""
import os
import json
import time
import re
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CATEGORIAS = [
    "Dívidas e Cobranças", "Estágio e Educação", "Trabalho e Projetos",
    "Compras Online", "Assinaturas e Serviços", "Promoções e Propaganda",
    "Alertas de Segurança", "Redes Sociais", "Viagens e Reservas",
    "Finanças Pessoais", "Eventos e Convites", "Documentos e Protocolos",
    "Newsletters e Notícias", "Suporte Técnico", "Outros Assuntos",
]

MODEL_ID = "qwen/qwen3.8-27b"

# --- PROMPT CORRIGIDO -------------------------------------------------
# Adiciona regras explícitas de desambiguação para o padrão de erro
# sistemático identificado no relatório anterior (ex: "Fechamento do
# Ibovespa" indo parar em "Finanças Pessoais" em vez de "Newsletters e
# Notícias" em 4/4 ocorrências).
PROMPT_SISTEMA = """Você é um classificador automático de e-mails corporativos.
Analise o assunto e o corpo do e-mail e retorne APENAS um JSON válido.

Categorias permitidas: "Dívidas e Cobranças", "Estágio e Educação", "Trabalho e Projetos",
"Compras Online", "Assinaturas e Serviços", "Promoções e Propaganda", "Alertas de Segurança",
"Redes Sociais", "Viagens e Reservas", "Finanças Pessoais", "Eventos e Convites",
"Documentos e Protocolos", "Newsletters e Notícias", "Suporte Técnico", "Outros Assuntos".

Formato de saída: {"categoria": "Nome da Categoria"}

Regras de desambiguação (aplique nesta ordem):
1. Se o e-mail é um boletim/notícia/análise GERAL sobre mercado, economia, bolsa de valores,
   juros ou câmbio, e NÃO menciona nenhuma conta, saldo, cobrança ou dado pessoal do
   destinatário -> classifique como "Newsletters e Notícias", mesmo que fale de dinheiro.
2. Só use "Finanças Pessoais" quando o texto trata de uma situação financeira ESPECÍFICA
   e pessoal do destinatário (ex: reembolso próprio, conciliação de despesa pessoal,
   imposto retido no salário dele) - não para notícias genéricas de mercado.
3. Se o e-mail relata uma falha técnica/erro de sistema (app, site, API, servidor) como
   causa central do problema, prefira "Suporte Técnico", mesmo que o texto também mencione
   cobrança ou dinheiro como consequência da falha.
4. Se o e-mail se encaixar em duas categorias, escolha sempre a mais específica
   (ex: prefira "Dívidas e Cobranças" a "Finanças Pessoais" quando há uma cobrança concreta
   em disputa, não uma questão de conciliação pessoal)."""


def classificar_llm(assunto: str, corpo: str, max_chars: int = 300):
    """Chama o LLM (Groq) e retorna dict com categoria, tokens, latência e flag de fallback."""
    corpo_truncado = corpo[:max_chars]
    inicio = time.time()
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": f"Assunto: {assunto}\nCorpo: {corpo_truncado}"},
        ],
        model=MODEL_ID,
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=50,
    )
    latencia_ms = round((time.time() - inicio) * 1000, 2)
    tokens_total = resp.usage.total_tokens
    resultado_bruto = resp.choices[0].message.content

    fallback = False
    try:
        categoria = json.loads(resultado_bruto).get("categoria", "Outros Assuntos")
        if categoria not in CATEGORIAS:
            fallback = True  # categoria fora da taxonomia = falha de formatação semântica
    except Exception:
        categoria = "Outros Assuntos"
        fallback = True

    return {
        "categoria": categoria,
        "tokens_total": tokens_total,
        "latencia_ms": latencia_ms,
        "fallback_ativado": fallback,
    }


# --- BASELINE HEURÍSTICA (palavras-chave) -----------------------------
# Regras simples de correspondência por palavra-chave, na ordem de
# prioridade abaixo. É a "baseline fraca" que serve de contraponto ao LLM
# na comparação custo/latência/acurácia do TCC.

REGRAS_HEURISTICA = [
    ("Alertas de Segurança", ["login", "acesso", "senha", "dispositivo", "roubad", "clonad", "phishing", "token", "bloqueio judicial", "restrição judicial"]),
    ("Dívidas e Cobranças", ["boleto", "fatura", "cobrança", "cobrando", "parcela", "dívida", "quitar", "estorno da multa"]),
    ("Suporte Técnico", ["erro", "não funciona", "não abre", "travou", "bug", "indisponibilidade", "servidor", "api de pagamentos", "sincroniza"]),
    ("Assinaturas e Serviços", ["assinatura", "plano premium", "cancelar", "renovação", "upgrade", "downgrade"]),
    ("Newsletters e Notícias", ["ibovespa", "boletim", "resumo econômico", "panorama", "editorial", "notícia", "análise semanal", "radar de mercado"]),
    ("Finanças Pessoais", ["reembolso", "adiantamento", "imposto de renda retido", "conciliar", "despesa pessoal"]),
    ("Documentos e Protocolos", ["contrato", "certidão", "comprovante", "informe de rendimentos", "licenciamento", "cláusula"]),
    ("Eventos e Convites", ["convite", "ingresso", "evento", "workshop", "conferência", "hackathon", "webinar"]),
    ("Viagens e Reservas", ["voo", "hotel", "reserva", "embarque", "check-in", "hospedagem"]),
    ("Trabalho e Projetos", ["entrevista", "reunião", "sprint", "projeto", "squad", "deploy", "feature"]),
    ("Promoções e Propaganda", ["desconto", "promoção", "cashback", "oferta exclusiva", "pré-aprovado"]),
]


def classificar_heuristica(assunto: str, corpo: str):
    """Classificador baseline: primeira regra de palavra-chave que casar, na ordem definida."""
    texto = f"{assunto} {corpo}".lower()
    inicio = time.time()
    categoria = "Outros Assuntos"
    for cat, palavras in REGRAS_HEURISTICA:
        if any(p in texto for p in palavras):
            categoria = cat
            break
    latencia_ms = round((time.time() - inicio) * 1000, 4)
    return {
        "categoria": categoria,
        "tokens_total": 0,
        "latencia_ms": latencia_ms,
        "fallback_ativado": False,
    }
