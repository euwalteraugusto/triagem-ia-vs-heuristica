# -*- coding: utf-8 -*-
import pandas as pd
from sklearn.metrics import confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("resultados_avaliacao.csv")

categorias = sorted(set(df["categoria_esperada"]) | set(df["categoria_llm"]) | set(df["categoria_heuristica"]))

for nome, col in [("LLM", "categoria_llm"), ("Heurística", "categoria_heuristica")]:
    cm = confusion_matrix(df["categoria_esperada"], df[col], labels=categorias)
    cm_df = pd.DataFrame(cm, index=categorias, columns=categorias)
    cm_df.to_csv(f"matriz_confusao_{nome.lower()}.csv", encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(categorias)))
    ax.set_yticks(range(len(categorias)))
    ax.set_xticklabels(categorias, rotation=90, fontsize=8)
    ax.set_yticklabels(categorias, fontsize=8)
    ax.set_xlabel("Categoria Prevista")
    ax.set_ylabel("Categoria Esperada")
    ax.set_title(f"Matriz de Confusão — {nome}")
    for i in range(len(categorias)):
        for j in range(len(categorias)):
            if cm[i, j] > 0:
                ax.text(j, i, cm[i, j], ha="center", va="center",
                        color="white" if cm[i, j] > cm.max()/2 else "black", fontsize=8)
    fig.colorbar(im)
    plt.tight_layout()
    plt.savefig(f"matriz_confusao_{nome.lower()}.png", dpi=150)
    plt.close()
    print(f"Matriz de confusão ({nome}) salva: matriz_confusao_{nome.lower()}.png / .csv")

# Erros do LLM (para discussão qualitativa na defesa)
erros_llm = df[~df["acerto_llm"]][["assunto", "complexidade", "categoria_esperada", "categoria_llm"]]
print(f"\n{len(erros_llm)} erros do LLM (todos textos únicos, sem pseudo-replicação):")
print(erros_llm.to_string(index=False))
