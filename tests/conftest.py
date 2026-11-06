import os
import sys
from pathlib import Path

# core.py instancia o cliente Groq no import e exige uma chave; usamos uma falsa.
# Nenhum teste faz chamada de rede (o cliente é sempre substituído por um mock).
os.environ.setdefault("GROQ_API_KEY", "chave-falsa-para-testes")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
