"""Testes de classificar_llm com o cliente Groq substituído por um dublê."""
import json
from types import SimpleNamespace

import pytest

import core


class ClienteFalso:
    def __init__(self, conteudo, tokens=42):
        self.conteudo = conteudo
        self.tokens = tokens
        self.chamadas = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        return SimpleNamespace(
            usage=SimpleNamespace(total_tokens=self.tokens),
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.conteudo))],
        )


@pytest.fixture
def usar_cliente(monkeypatch):
    def _usar(conteudo, tokens=42):
        falso = ClienteFalso(conteudo, tokens)
        monkeypatch.setattr(core, "client", falso)
        return falso

    return _usar


def test_categoria_valida_sem_fallback(usar_cliente):
    usar_cliente(json.dumps({"categoria": "Suporte Técnico"}), tokens=77)

    r = core.classificar_llm("App travou", "Não abre")

    assert r["categoria"] == "Suporte Técnico"
    assert r["tokens_total"] == 77
    assert r["fallback_ativado"] is False
    assert r["latencia_ms"] >= 0


def test_categoria_fora_da_taxonomia_ativa_fallback(usar_cliente):
    usar_cliente(json.dumps({"categoria": "Categoria Inventada"}))

    r = core.classificar_llm("x", "y")

    assert r["fallback_ativado"] is True
    assert r["categoria"] == "Categoria Inventada"


def test_json_invalido_cai_em_outros_assuntos(usar_cliente):
    usar_cliente("isto não é json")

    r = core.classificar_llm("x", "y")

    assert r["categoria"] == "Outros Assuntos"
    assert r["fallback_ativado"] is True


def test_json_sem_chave_categoria_usa_outros_assuntos(usar_cliente):
    usar_cliente("{}")

    r = core.classificar_llm("x", "y")

    assert r["categoria"] == "Outros Assuntos"
    assert r["fallback_ativado"] is False  # "Outros Assuntos" pertence à taxonomia


def test_corpo_e_truncado_e_modelo_configurado(usar_cliente):
    falso = usar_cliente(json.dumps({"categoria": "Outros Assuntos"}))

    core.classificar_llm("Assunto", "a" * 1000, max_chars=10)

    chamada = falso.chamadas[0]
    assert chamada["model"] == core.MODEL_ID
    assert chamada["messages"][0]["role"] == "system"
    assert chamada["messages"][1]["content"] == "Assunto: Assunto\nCorpo: " + "a" * 10
