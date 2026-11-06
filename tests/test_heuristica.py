import json
from pathlib import Path

import pytest

import core

MOCKS = Path(__file__).resolve().parent.parent / "mock_emails.json"


def _categoria(assunto="", corpo=""):
    return core.classificar_heuristica(assunto, corpo)["categoria"]


@pytest.mark.parametrize(
    "categoria,palavra",
    [(cat, p) for cat, palavras in core.REGRAS_HEURISTICA for p in palavras],
)
def test_cada_palavra_chave_leva_a_sua_categoria(categoria, palavra):
    assert _categoria(assunto=f"Aviso sobre {palavra}") == categoria


def test_sem_palavra_chave_cai_em_outros_assuntos():
    assert _categoria("Olá", "Tudo bem por aí?") == "Outros Assuntos"


def test_texto_vazio_cai_em_outros_assuntos():
    assert _categoria("", "") == "Outros Assuntos"


def test_ignora_maiusculas_e_minusculas():
    assert _categoria("BOLETO VENCIDO") == "Dívidas e Cobranças"


def test_procura_tambem_no_corpo():
    assert _categoria("Aviso", "Seu voo foi remarcado.") == "Viagens e Reservas"


def test_primeira_regra_na_ordem_de_prioridade_vence():
    # "senha" (Alertas de Segurança) vem antes de "boleto" (Dívidas e Cobranças).
    assert _categoria("Senha alterada", "Segue o boleto") == "Alertas de Segurança"
    # "boleto" (Dívidas) vem antes de "desconto" (Promoções).
    assert _categoria("Boleto com desconto") == "Dívidas e Cobranças"


def test_formato_do_retorno():
    resultado = core.classificar_heuristica("Fatura", "do cartão")

    assert set(resultado) == {"categoria", "tokens_total", "latencia_ms", "fallback_ativado"}
    assert resultado["tokens_total"] == 0
    assert resultado["fallback_ativado"] is False
    assert resultado["latencia_ms"] >= 0


def test_regras_usam_apenas_categorias_da_taxonomia():
    categorias_regras = {cat for cat, _ in core.REGRAS_HEURISTICA}

    assert categorias_regras <= set(core.CATEGORIAS)
    assert "Outros Assuntos" in core.CATEGORIAS


def test_palavras_chave_estao_em_minusculas():
    # A heurística compara com texto.lower(); palavra com maiúscula nunca casaria.
    for _, palavras in core.REGRAS_HEURISTICA:
        for palavra in palavras:
            assert palavra == palavra.lower()


def test_massa_de_mocks_sempre_resulta_em_categoria_valida():
    emails = json.loads(MOCKS.read_text(encoding="utf-8"))

    assert emails, "mock_emails.json não pode estar vazio"
    for email in emails:
        assert _categoria(email["assunto"], email["corpo"]) in core.CATEGORIAS
