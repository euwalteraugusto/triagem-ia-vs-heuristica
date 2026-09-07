# -*- coding: utf-8 -*-
"""
Roda os 80 e-mails de mock_emails.json contra:
  (a) o LLM via Groq (prompt corrigido)
  (b) a baseline heurística
Salva um CSV com todos os resultados e imprime acurácia estratificada +
matriz de confusão para cada abordagem.
"""
import json
import time
import csv
import pandas as pd
from core import classificar_llm, classificar_heuristica

with open("mock_emails.json", "r", encoding="utf-8") as f:
    mocks = json.load(f)

linhas = []

print(f"Avaliando {len(mocks)} e-mails (LLM + Heurística)...\n")

for i, item in enumerate(mocks, 1):
    esperado = item["categoria_esperada"]
    comp = item["complexidade"]

    res_llm = classificar_llm(item["assunto"], item["corpo"])
    res_heur = classificar_heuristica(item["assunto"], item["corpo"])

    linhas.append({
        "id": item["id"],
        "assunto": item["assunto"],
        "complexidade": comp,
        "categoria_esperada": esperado,
        "categoria_llm": res_llm["categoria"],
        "acerto_llm": res_llm["categoria"] == esperado,
        "tokens_llm": res_llm["tokens_total"],
        "latencia_llm_ms": res_llm["latencia_ms"],
        "fallback_llm": res_llm["fallback_ativado"],
        "categoria_heuristica": res_heur["categoria"],
        "acerto_heuristica": res_heur["categoria"] == esperado,
        "latencia_heuristica_ms": res_heur["latencia_ms"],
    })

    print(f"[{i}/{len(mocks)}] {item['assunto'][:40]:40s} | esperado={esperado:25s} | LLM={res_llm['categoria']:25s} | Heur={res_heur['categoria']}")
    time.sleep(1.2)  # proteção de rate limit do tier gratuito da Groq

df = pd.DataFrame(linhas)
df.to_csv("resultados_avaliacao.csv", index=False, encoding="utf-8-sig")

print("\n" + "=" * 70)
print("RESUMO GERAL")
print("=" * 70)

for metodo, col in [("LLM", "acerto_llm"), ("Heurística", "acerto_heuristica")]:
    total = len(df)
    acertos = df[col].sum()
    print(f"\n{metodo}: {acertos}/{total} = {acertos/total*100:.2f}%")
    for comp in ["Simples", "Complexo"]:
        sub = df[df["complexidade"] == comp]
        a = sub[col].sum()
        t = len(sub)
        print(f"  {comp}: {a}/{t} = {a/t*100:.2f}%")

print(f"\nCusto médio LLM: {df['tokens_llm'].mean():.1f} tokens | mediana latência: {df['latencia_llm_ms'].median():.1f} ms")
print(f"Latência média Heurística: {df['latencia_heuristica_ms'].mean():.4f} ms (praticamente instantânea)")
print(f"Fallbacks de parsing do LLM: {df['fallback_llm'].sum()}")

print("\nResultados completos salvos em resultados_avaliacao.csv")
