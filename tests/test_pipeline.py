import pytest
import pipeline_audio_transcricao as pipe


def test_modulo_importavel_sem_executar_pipeline():
    # Se o import disparasse o pipeline (ffmpeg/pastas), isto nem rodaria.
    assert hasattr(pipe, "main")


def test_formatar_timestamp():
    assert pipe.formatar_timestamp(0) == "00:00:00"
    assert pipe.formatar_timestamp(65) == "00:01:05"
    assert pipe.formatar_timestamp(3661) == "01:01:01"
    # floats são truncados para o segundo inteiro
    assert pipe.formatar_timestamp(4.9) == "00:00:04"


def test_extrair_paragrafos(deepgram_data):
    paras = pipe.extrair_paragrafos(deepgram_data)
    assert len(paras) == 1
    assert len(paras[0]["sentences"]) == 2


def test_extrair_paragrafos_vazio(deepgram_data_sem_paragraphs):
    assert pipe.extrair_paragrafos(deepgram_data_sem_paragraphs) == []
    assert pipe.extrair_paragrafos({}) == []


def test_extrair_transcript(deepgram_data_sem_paragraphs):
    assert pipe.extrair_transcript(deepgram_data_sem_paragraphs) == "A flat transcript with no sentences."
    assert pipe.extrair_transcript({}) == ""


def test_extrair_idioma(deepgram_data):
    assert pipe.extrair_idioma(deepgram_data) == "en"
    assert pipe.extrair_idioma({}) is None


def test_montar_texto_simples(deepgram_data):
    paras = pipe.extrair_paragrafos(deepgram_data)
    texto = pipe.montar_texto_simples(paras)
    assert texto == "Welcome to our product. Today I'll show how it works."


def test_montar_frases(deepgram_data):
    paras = pipe.extrair_paragrafos(deepgram_data)
    frases = pipe.montar_frases(paras)
    assert frases == [
        (0.0, 4.0, "Welcome to our product."),
        (5.0, 13.0, "Today I'll show how it works."),
    ]


def test_montar_frases_vazio():
    assert pipe.montar_frases([]) == []


def test_montar_texto_com_tempo():
    frases = [
        (0.0, 4.0, "Bem-vindo ao nosso produto."),
        (5.0, 13.0, "Hoje vou mostrar como funciona."),
    ]
    esperado = (
        "[00:00:00 -> 00:00:04] Bem-vindo ao nosso produto.\n"
        "[00:00:05 -> 00:00:13] Hoje vou mostrar como funciona."
    )
    assert pipe.montar_texto_com_tempo(frases) == esperado


# ── Word-level JSON (formato ElevenLabs Scribe) ──────────────────

def test_extrair_palavras(deepgram_data):
    words = pipe.extrair_palavras(deepgram_data)
    assert len(words) == 3
    assert words[0]["punctuated_word"] == "Welcome"


def test_extrair_palavras_vazio():
    assert pipe.extrair_palavras({}) == []


def test_montar_words_json_com_pontuacao(deepgram_data):
    words = pipe.extrair_palavras(deepgram_data)
    assert pipe.montar_words_json(words, usar_pontuacao=True) == [
        {"text": "Welcome",  "start": 0.0, "end": 0.5, "type": "word"},
        {"text": " ",        "start": 0.5, "end": 0.6, "type": "spacing"},
        {"text": "to",       "start": 0.6, "end": 0.7, "type": "word"},
        {"text": " ",        "start": 0.7, "end": 0.9, "type": "spacing"},
        {"text": "product.", "start": 0.9, "end": 4.0, "type": "word"},
    ]


def test_montar_words_json_sem_pontuacao(deepgram_data):
    words = pipe.extrair_palavras(deepgram_data)
    tokens = pipe.montar_words_json(words, usar_pontuacao=False)
    assert [t["text"] for t in tokens if t["type"] == "word"] == ["welcome", "to", "product"]


def test_montar_words_json_vazio():
    assert pipe.montar_words_json([]) == []


def test_montar_words_json_uma_palavra_sem_spacing():
    words = [{"word": "oi", "punctuated_word": "Oi", "start": 0.0, "end": 0.3}]
    assert pipe.montar_words_json(words) == [
        {"text": "Oi", "start": 0.0, "end": 0.3, "type": "word"},
    ]


def test_construir_words_json(deepgram_data):
    obj = pipe.construir_words_json(deepgram_data)
    assert obj["words"][0] == {"text": "Welcome", "start": 0.0, "end": 0.5, "type": "word"}
    assert obj["words"][-1] == {"text": "product.", "start": 0.9, "end": 4.0, "type": "word"}


def test_construir_words_json_sem_palavras():
    assert pipe.construir_words_json({}) == {"words": []}


# ── Task 5: parse_args ────────────────────────────────────────────

def test_parse_args_sem_flag():
    assert pipe.parse_args([]) == (True, False, False)


def test_parse_args_timestamps():
    assert pipe.parse_args(["--timestamps"]) == (False, True, False)


def test_parse_args_words_json():
    assert pipe.parse_args(["--words-json"]) == (False, False, True)


def test_parse_args_both():
    assert pipe.parse_args(["--both"]) == (True, True, False)


def test_parse_args_all():
    assert pipe.parse_args(["--all"]) == (True, True, True)


def test_parse_args_invalido_sai_com_erro():
    with pytest.raises(SystemExit) as exc:
        pipe.parse_args(["--xpto"])
    assert exc.value.code != 0


def test_parse_args_flags_demais_sai_com_erro():
    with pytest.raises(SystemExit) as exc:
        pipe.parse_args(["--both", "--timestamps"])
    assert exc.value.code != 0


# ── Task 6: montar_prompt_frases, parsear_resposta_numerada ──────

def test_montar_prompt_frases():
    frases = [
        (0.0, 4.0, "Welcome to our product."),
        (5.0, 13.0, "Today I'll show how it works."),
    ]
    assert pipe.montar_prompt_frases(frases) == (
        "1. Welcome to our product.\n"
        "2. Today I'll show how it works."
    )


def test_parsear_resposta_numerada_ok():
    resposta = "1. Bem-vindo ao nosso produto.\n2. Hoje vou mostrar como funciona."
    assert pipe.parsear_resposta_numerada(resposta, 2) == [
        "Bem-vindo ao nosso produto.",
        "Hoje vou mostrar como funciona.",
    ]


def test_parsear_resposta_numerada_com_linhas_em_branco_e_parenteses():
    resposta = "\n1) Linha um.\n\n2) Linha dois.\n"
    assert pipe.parsear_resposta_numerada(resposta, 2) == ["Linha um.", "Linha dois."]


def test_parsear_resposta_numerada_contagem_diferente_retorna_none():
    resposta = "1. Só uma linha."
    assert pipe.parsear_resposta_numerada(resposta, 2) is None


# ── Task 7: traduzir_frases, construir_texto_timestamps ──────────

def test_traduzir_frases_alinha_por_posicao(monkeypatch):
    frases = [
        (0.0, 4.0, "Welcome to our product."),
        (5.0, 13.0, "Today I'll show how it works."),
    ]

    def fake_chat(system, user):
        assert user == "1. Welcome to our product.\n2. Today I'll show how it works."
        return "1. Bem-vindo ao nosso produto.\n2. Hoje vou mostrar como funciona."

    monkeypatch.setattr(pipe, "_openrouter_chat", fake_chat)
    assert pipe.traduzir_frases(frases) == [
        "Bem-vindo ao nosso produto.",
        "Hoje vou mostrar como funciona.",
    ]


def test_traduzir_frases_contagem_errada_retorna_none(monkeypatch):
    frases = [(0.0, 4.0, "A."), (5.0, 13.0, "B.")]
    monkeypatch.setattr(pipe, "_openrouter_chat", lambda s, u: "1. Só uma linha.")
    assert pipe.traduzir_frases(frases) is None


def test_construir_texto_timestamps_pt_sem_traducao(deepgram_data):
    texto = pipe.construir_texto_timestamps(deepgram_data, "pt-BR")
    assert texto == (
        "[00:00:00 -> 00:00:04] Welcome to our product.\n"
        "[00:00:05 -> 00:00:13] Today I'll show how it works."
    )


def test_construir_texto_timestamps_traduz_frase_a_frase(monkeypatch, deepgram_data):
    monkeypatch.setattr(
        pipe, "traduzir_frases",
        lambda frases: ["Bem-vindo ao nosso produto.", "Hoje vou mostrar como funciona."],
    )
    texto = pipe.construir_texto_timestamps(deepgram_data, "en")
    assert texto == (
        "[00:00:00 -> 00:00:04] Bem-vindo ao nosso produto.\n"
        "[00:00:05 -> 00:00:13] Hoje vou mostrar como funciona."
    )


def test_construir_texto_timestamps_fallback_contagem(monkeypatch, deepgram_data):
    monkeypatch.setattr(pipe, "traduzir_frases", lambda frases: None)
    monkeypatch.setattr(pipe, "traduzir_para_ptbr", lambda texto: "Bloco traduzido.")
    texto = pipe.construir_texto_timestamps(deepgram_data, "en")
    assert texto == "[00:00:00 -> 00:00:13] Bloco traduzido."


def test_construir_texto_timestamps_fallback_sem_paragraphs(deepgram_data_sem_paragraphs):
    texto = pipe.construir_texto_timestamps(deepgram_data_sem_paragraphs, "pt-BR")
    assert texto == "[00:00:00 -> 00:00:07] A flat transcript with no sentences."


def test_construir_texto_timestamps_sem_paragraphs_traduz_em_bloco(monkeypatch, deepgram_data_sem_paragraphs):
    # Sem frases E idioma != pt: o transcript plano é traduzido em bloco.
    monkeypatch.setattr(pipe, "traduzir_para_ptbr", lambda texto: "Transcript plano traduzido.")
    texto = pipe.construir_texto_timestamps(deepgram_data_sem_paragraphs, "en")
    assert texto == "[00:00:00 -> 00:00:07] Transcript plano traduzido."
