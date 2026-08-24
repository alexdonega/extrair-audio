# Transcrição com Timestamps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar flags de CLI (`--timestamps`, `--both`) ao pipeline para gerar uma transcrição extra com uma frase por linha prefixada por `[HH:MM:SS -> HH:MM:SS]`, preservando o comportamento atual sem flag.

**Architecture:** Refatorar o corpo procedural do script em funções pequenas e puras (testáveis sem rede/ffmpeg), movendo todo o fluxo de execução para uma função `main()` protegida por `if __name__ == "__main__"`. As funções puras (formatação de tempo, navegação no JSON do Deepgram, montagem de texto, parsing de tradução) são cobertas por testes; a orquestração de rede é testada via monkeypatch. O loop principal decide, por arquivo, quais variantes faltam e grava cada uma.

**Tech Stack:** Python 3.10+ (testado em 3.14), `requests`, `python-dotenv`, `pytest` 9.x.

---

## File Structure

- **Modify:** `pipeline_audio_transcricao.py` — refatorado em funções puras + `main()`. Mesmo arquivo único (o projeto é um script standalone; não há pacote).
- **Create:** `tests/test_pipeline.py` — testes unitários das funções puras e da orquestração de tradução (com monkeypatch).
- **Create:** `tests/conftest.py` — fixture com um `data` de exemplo do Deepgram (com e sem `paragraphs`).
- **Modify:** `README.md` — documentar as novas flags.

### Funções-alvo no `pipeline_audio_transcricao.py`

| Função | Responsabilidade | Pura? |
|---|---|---|
| `parse_args(argv)` | Resolve `(gerar_simples, gerar_timestamps)`; uso+exit em flag inválida | sim (exceto `sys.exit`) |
| `formatar_timestamp(segundos)` | `float` → `"HH:MM:SS"` | sim |
| `_primeira_alternativa(data)` | Navega até `channels[0].alternatives[0]` | sim |
| `extrair_paragrafos(data)` | Lista de parágrafos (ou `[]`) | sim |
| `extrair_transcript(data)` | Transcript plano (fallback) | sim |
| `extrair_idioma(data)` | `detected_language` do canal | sim |
| `montar_texto_simples(paragraphs)` | Texto em parágrafos (comportamento atual) | sim |
| `montar_frases(paragraphs)` | `[(start, end, texto), ...]` | sim |
| `montar_texto_com_tempo(frases)` | Linhas `[ini -> fim] texto` | sim |
| `montar_prompt_frases(frases)` | Prompt numerado `"1. ...\n2. ..."` | sim |
| `parsear_resposta_numerada(resposta, n)` | `list[str]` de tamanho `n` ou `None` | sim |
| `_openrouter_chat(system, user)` | Chamada genérica ao OpenRouter | não (rede) |
| `traduzir_para_ptbr(texto)` | Tradução em bloco (mantida) | não (rede) |
| `traduzir_frases(frases)` | Tradução numerada → `list[str]` ou `None` | não (rede) |
| `construir_texto_timestamps(...)` | Orquestra frases+tradução+fallbacks → str | não (rede) |
| `main()` | Setup, extração, loop de transcrição | não |

---

## Task 1: Tornar o módulo importável + `formatar_timestamp`

Hoje o módulo executa todo o pipeline no import (ffmpeg, leitura de pastas), então nenhum teste consegue importá-lo. Esta task move o corpo para `main()` e adiciona a primeira função pura.

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_pipeline.py`:

```python
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
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: erro no import / coleta (o módulo tenta rodar o pipeline e/ou `formatar_timestamp` não existe).

- [ ] **Step 3: Refatorar `pipeline_audio_transcricao.py`**

Manter o cabeçalho (shebang, docstring, imports, `load_dotenv`, configs, `traduzir_para_ptbr`).
Adicionar `formatar_timestamp` logo após as configs (antes de `traduzir_para_ptbr` é indiferente; manter junto das demais funções de formatação):

```python
def formatar_timestamp(segundos):
    """Converte segundos (float) em 'HH:MM:SS'."""
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
```

Mover TODO o código procedural de execução (a partir de `# ── Setup ──`, incluindo `PASTA_*.mkdir`, a verificação do FFmpeg, a extração de áudio e o loop de transcrição) para dentro de uma função `main()`. No final do arquivo, adicionar:

```python
def main():
    # (todo o corpo procedural movido para cá, com indentação)
    ...


if __name__ == "__main__":
    main()
```

> Nota: `import shutil` que hoje está no meio do corpo deve subir para o topo do arquivo junto dos outros imports. O bloco `if __name__ == "__main__"` garante que importar o módulo nos testes não dispara nada.

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Sanidade — o script ainda roda**

Run: `python pipeline_audio_transcricao.py` (sem MP3s novos, deve pular tudo e imprimir o rodapé "Processamento concluído!").
Expected: roda sem exceção; comportamento idêntico ao de antes.

---

## Task 2: Fixture de dados do Deepgram

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Criar a fixture**

Criar `tests/conftest.py`:

```python
import pytest


@pytest.fixture
def deepgram_data():
    """Resposta simplificada do Deepgram COM paragraphs (2 frases)."""
    return {
        "metadata": {"duration": 18.0},
        "results": {
            "channels": [
                {
                    "detected_language": "en",
                    "alternatives": [
                        {
                            "transcript": "Welcome to our product. Today I'll show how it works.",
                            "paragraphs": {
                                "paragraphs": [
                                    {
                                        "sentences": [
                                            {"text": "Welcome to our product.", "start": 0.0, "end": 4.0},
                                            {"text": "Today I'll show how it works.", "start": 5.0, "end": 13.0},
                                        ]
                                    }
                                ]
                            },
                        }
                    ],
                }
            ]
        },
    }


@pytest.fixture
def deepgram_data_sem_paragraphs():
    """Resposta do Deepgram SEM paragraphs (só transcript plano)."""
    return {
        "metadata": {"duration": 7.0},
        "results": {
            "channels": [
                {
                    "detected_language": "en",
                    "alternatives": [
                        {"transcript": "A flat transcript with no sentences.", "paragraphs": {}}
                    ],
                }
            ]
        },
    }
```

- [ ] **Step 2: Confirmar que a fixture coleta**

Run: `python -m pytest tests/ -v`
Expected: os testes da Task 1 continuam PASS; nenhuma coleta quebrada.

- [ ] **Step 3: Commit (Tasks 1-2)**

```bash
git add pipeline_audio_transcricao.py tests/test_pipeline.py tests/conftest.py
git commit -m "refactor: tornar pipeline importável e adicionar formatar_timestamp"
```

> Se o diretório ainda não for um repositório git, pular o commit (o projeto não é versionado hoje). Os commits seguintes têm a mesma ressalva.

---

## Task 3: Navegação no JSON (`extrair_paragrafos`, `extrair_transcript`, `extrair_idioma`)

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tests/test_pipeline.py`:

```python
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
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_pipeline.py -k "extrair" -v`
Expected: FAIL (`AttributeError: module ... has no attribute 'extrair_paragrafos'`).

- [ ] **Step 3: Implementar as funções**

Adicionar ao módulo (junto das demais funções puras):

```python
def _primeira_alternativa(data):
    """Retorna o dict da 1ª alternativa do 1º canal (ou {})."""
    channels = data.get("results", {}).get("channels", [{}])
    alternatives = channels[0].get("alternatives", [{}])
    return alternatives[0]


def extrair_paragrafos(data):
    """Lista de parágrafos do Deepgram, ou [] se não houver."""
    return _primeira_alternativa(data).get("paragraphs", {}).get("paragraphs", [])


def extrair_transcript(data):
    """Transcript plano (fallback quando não há paragraphs)."""
    return _primeira_alternativa(data).get("transcript", "")


def extrair_idioma(data):
    """Idioma detectado no 1º canal, ou None."""
    channels = data.get("results", {}).get("channels", [{}])
    return channels[0].get("detected_language")
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -k "extrair" -v`
Expected: PASS (4 testes).

---

## Task 4: Montagem de texto (`montar_texto_simples`, `montar_frases`, `montar_texto_com_tempo`)

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
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
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_pipeline.py -k "montar" -v`
Expected: FAIL (funções inexistentes).

- [ ] **Step 3: Implementar as funções**

```python
def montar_texto_simples(paragraphs):
    """Texto em parágrafos (comportamento histórico, sem timestamp)."""
    return "\n\n".join(
        " ".join(s["text"] for s in p["sentences"])
        for p in paragraphs
    )


def montar_frases(paragraphs):
    """Lista achatada de (start, end, texto) na ordem original."""
    frases = []
    for p in paragraphs:
        for s in p["sentences"]:
            frases.append((s["start"], s["end"], s["text"]))
    return frases


def montar_texto_com_tempo(frases):
    """Uma frase por linha: '[HH:MM:SS -> HH:MM:SS] texto'."""
    return "\n".join(
        f"[{formatar_timestamp(start)} -> {formatar_timestamp(end)}] {texto}"
        for start, end, texto in frases
    )
```

> Nota: no `main()`, a montagem do texto sem timestamp passa a usar `montar_texto_simples(...)` em vez do `"\n\n".join(...)` inline. Isso será feito na Task 8.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -k "montar" -v`
Expected: PASS (4 testes).

- [ ] **Step 5: Commit (Tasks 3-4)**

```bash
git add pipeline_audio_transcricao.py tests/test_pipeline.py
git commit -m "refactor: extrair navegação JSON e montagem de texto em funções puras"
```

---

## Task 5: `parse_args`

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
import pytest


def test_parse_args_sem_flag():
    assert pipe.parse_args([]) == (True, False)


def test_parse_args_timestamps():
    assert pipe.parse_args(["--timestamps"]) == (False, True)


def test_parse_args_both():
    assert pipe.parse_args(["--both"]) == (True, True)


def test_parse_args_invalido_sai_com_erro():
    with pytest.raises(SystemExit) as exc:
        pipe.parse_args(["--xpto"])
    assert exc.value.code != 0


def test_parse_args_flags_demais_sai_com_erro():
    with pytest.raises(SystemExit) as exc:
        pipe.parse_args(["--both", "--timestamps"])
    assert exc.value.code != 0
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_pipeline.py -k "parse_args" -v`
Expected: FAIL (`parse_args` inexistente).

- [ ] **Step 3: Implementar a função**

```python
def parse_args(argv):
    """Resolve as variantes a gerar: (gerar_simples, gerar_timestamps).

    - sem flag       -> (True,  False)  # só transcrição simples (padrão)
    - --timestamps   -> (False, True)   # só versão com timestamp
    - --both         -> (True,  True)   # ambas
    Flag inválida    -> imprime uso e encerra com código != 0.
    """
    if not argv:
        return (True, False)
    if len(argv) == 1:
        if argv[0] == "--timestamps":
            return (False, True)
        if argv[0] == "--both":
            return (True, True)
    print(
        "Uso: python pipeline_audio_transcricao.py [--timestamps | --both]",
        file=sys.stderr,
    )
    sys.exit(2)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -k "parse_args" -v`
Expected: PASS (5 testes).

---

## Task 6: Tradução numerada — partes puras (`montar_prompt_frases`, `parsear_resposta_numerada`)

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
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
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_pipeline.py -k "prompt_frases or parsear" -v`
Expected: FAIL.

- [ ] **Step 3: Implementar as funções**

Adicionar `import re` ao topo do arquivo (junto dos outros imports) e:

```python
def montar_prompt_frases(frases):
    """Monta o prompt numerado '1. ...\\n2. ...' a partir das frases."""
    return "\n".join(
        f"{i}. {texto}" for i, (_, _, texto) in enumerate(frases, start=1)
    )


def parsear_resposta_numerada(resposta, n_frases):
    """Converte a resposta numerada em list[str].

    Retorna None (sinal de fallback) se a contagem de linhas não-vazias
    não bater com n_frases.
    """
    linhas = [l.strip() for l in resposta.strip().splitlines() if l.strip()]
    if len(linhas) != n_frases:
        return None
    textos = []
    for linha in linhas:
        m = re.match(r"^\d+[.)]\s*(.*)$", linha)
        textos.append(m.group(1) if m else linha)
    return textos
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -k "prompt_frases or parsear" -v`
Expected: PASS (4 testes).

---

## Task 7: Tradução numerada — orquestração (`_openrouter_chat`, `traduzir_frases`) e `construir_texto_timestamps`

**Files:**
- Modify: `pipeline_audio_transcricao.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_traduzir_frases_alinha_por_posicao(monkeypatch):
    frases = [
        (0.0, 4.0, "Welcome to our product."),
        (5.0, 13.0, "Today I'll show how it works."),
    ]

    def fake_chat(system, user):
        # confere que o prompt enviado é o numerado
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
    # idioma pt -> não traduz, frases originais com tempos
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
    # traduzir_frases falha (None) -> tradução em bloco numa linha única
    monkeypatch.setattr(pipe, "traduzir_frases", lambda frases: None)
    monkeypatch.setattr(pipe, "traduzir_para_ptbr", lambda texto: "Bloco traduzido.")
    texto = pipe.construir_texto_timestamps(deepgram_data, "en")
    assert texto == "[00:00:00 -> 00:00:13] Bloco traduzido."


def test_construir_texto_timestamps_fallback_sem_paragraphs(monkeypatch, deepgram_data_sem_paragraphs):
    # sem paragraphs e idioma pt -> uma linha com a duração total
    texto = pipe.construir_texto_timestamps(deepgram_data_sem_paragraphs, "pt-BR")
    assert texto == "[00:00:00 -> 00:00:07] A flat transcript with no sentences."
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python -m pytest tests/test_pipeline.py -k "traduzir_frases or construir_texto" -v`
Expected: FAIL.

- [ ] **Step 3: Refatorar/implementar**

Substituir o corpo de `traduzir_para_ptbr` para reutilizar um helper `_openrouter_chat`, e adicionar `traduzir_frases` + `construir_texto_timestamps`:

```python
SYSTEM_TRADUCAO_BLOCO = (
    "Você é um tradutor profissional. Traduza o texto a seguir para português "
    "brasileiro (pt-BR). Mantenha a formatação original (parágrafos, quebras de "
    "linha). Retorne APENAS a tradução, sem comentários adicionais."
)

SYSTEM_TRADUCAO_FRASES = (
    "Você é um tradutor profissional. Traduza para português brasileiro (pt-BR) "
    "cada linha numerada a seguir. Retorne EXATAMENTE a mesma estrutura numerada, "
    "uma tradução por linha, na mesma ordem, sem comentários nem linhas extras."
)


def _openrouter_chat(system_prompt, user_content):
    """Chamada genérica de chat ao OpenRouter; retorna o conteúdo de texto."""
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def traduzir_para_ptbr(texto):
    """Traduz texto para pt-BR em bloco (versão sem timestamp)."""
    return _openrouter_chat(SYSTEM_TRADUCAO_BLOCO, texto)


def traduzir_frases(frases):
    """Traduz frase a frase em UMA chamada (numerada).

    Retorna list[str] alinhada às frases, ou None se a contagem não bater.
    """
    prompt = montar_prompt_frases(frases)
    resposta = _openrouter_chat(SYSTEM_TRADUCAO_FRASES, prompt)
    return parsear_resposta_numerada(resposta, len(frases))


def construir_texto_timestamps(data, idioma):
    """Monta o conteúdo da variante com timestamp a partir do JSON do Deepgram.

    - Com paragraphs: uma frase por linha; traduz frase a frase se idioma != pt.
    - Sem paragraphs: linha única com a duração total (fallback).
    - Tradução frase a frase que falha na contagem: cai para tradução em bloco
      numa linha única [primeiro_inicio -> ultimo_fim].
    """
    precisa_traduzir = bool(idioma) and not idioma.startswith("pt")
    paragraphs = extrair_paragrafos(data)
    frases = montar_frases(paragraphs)

    if not frases:
        # Fallback: transcript plano em uma linha única.
        print(" -> ⚠️  Aviso: Deepgram não retornou frases; usando transcript plano.")
        transcript = extrair_transcript(data)
        if precisa_traduzir:
            transcript = traduzir_para_ptbr(transcript)
        duracao = data.get("metadata", {}).get("duration")
        fim = formatar_timestamp(duracao) if duracao else ""
        return f"[{formatar_timestamp(0)} -> {fim}] {transcript}"

    if precisa_traduzir:
        traducoes = traduzir_frases(frases)
        if traducoes is None:
            # Fallback seguro: bloco único, ainda com timestamps de abertura/fim.
            print(" -> ⚠️  Aviso: contagem de frases traduzidas não bateu; usando bloco único.")
            texto_bloco = traduzir_para_ptbr(" ".join(t for _, _, t in frases))
            inicio = formatar_timestamp(frases[0][0])
            fim = formatar_timestamp(frases[-1][1])
            return f"[{inicio} -> {fim}] {texto_bloco}"
        frases = [(s, e, traducoes[i]) for i, (s, e, _) in enumerate(frases)]

    return montar_texto_com_tempo(frases)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -k "traduzir_frases or construir_texto" -v`
Expected: PASS (6 testes).

- [ ] **Step 5: Commit (Tasks 5-7)**

```bash
git add pipeline_audio_transcricao.py tests/test_pipeline.py
git commit -m "feat: parse_args e tradução por frase com timestamps (funções puras + orquestração)"
```

---

## Task 8: Conectar tudo no `main()` (flags, idempotência por variante, gravação)

**Files:**
- Modify: `pipeline_audio_transcricao.py`

> Esta task altera o fluxo do loop de transcrição. As funções já existem e estão testadas; aqui apenas as conectamos. Não há teste unitário novo (o loop depende de rede/ffmpeg/arquivos); a verificação é manual nos Steps 4-5.

- [ ] **Step 1: Ler quais variantes gerar no início do `main()`**

Logo no começo de `main()`, antes do setup das pastas, adicionar:

```python
    gerar_simples, gerar_timestamps = parse_args(sys.argv[1:])
```

- [ ] **Step 2: Reescrever o loop de transcrição**

Substituir o loop atual (`for mp3_path in audios:` … até o `except`) por:

```python
    for mp3_path in audios:
        nome     = mp3_path.stem
        txt_path = PASTA_TRANSCRICOES / f"{nome}.txt"
        ts_path  = PASTA_TRANSCRICOES / f"{nome}-timestamps.txt"

        precisa_simples    = gerar_simples    and not txt_path.exists()
        precisa_timestamps = gerar_timestamps and not ts_path.exists()

        if not precisa_simples and not precisa_timestamps:
            print(f" -> ✅ {mp3_path.name}: Já processado (variantes solicitadas existem). Pulando.")
            continue

        print(f" -> 🧠 Transcrevendo: {mp3_path.name}")
        print(f"    (Enviando para Deepgram Nova-3...)")

        with open(mp3_path, "rb") as f:
            audio_bytes = f.read()

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/mp3",
        }

        try:
            response = requests.post(
                DEEPGRAM_URL,
                headers=headers,
                data=audio_bytes,
                timeout=300,
            )
            response.raise_for_status()
            data = response.json()

            idioma = extrair_idioma(data)
            traduzindo = bool(idioma) and not idioma.startswith("pt")
            if traduzindo:
                print(f" -> 🌐 Idioma detectado: {idioma}. Traduzindo para pt-BR...")

            # Variante SEM timestamp
            if precisa_simples:
                paragraphs = extrair_paragrafos(data)
                if paragraphs:
                    texto = montar_texto_simples(paragraphs)
                else:
                    texto = extrair_transcript(data)
                if not texto.strip():
                    print(f" -> ⚠️  Aviso: Transcrição vazia para {mp3_path.name}")
                else:
                    if traduzindo:
                        texto = traduzir_para_ptbr(texto)
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(texto)
                    print(f" -> ✅ Transcrição salva: {txt_path.name}")

            # Variante COM timestamp
            if precisa_timestamps:
                texto_ts = construir_texto_timestamps(data, idioma)
                if not texto_ts.strip():
                    print(f" -> ⚠️  Aviso: Transcrição com timestamp vazia para {mp3_path.name}")
                else:
                    with open(ts_path, "w", encoding="utf-8") as f:
                        f.write(texto_ts)
                    print(f" -> ✅ Transcrição com timestamp salva: {ts_path.name}")

        except Exception as e:
            print(f" -> ❌ Erro ao processar {mp3_path.name}: {e}")
```

- [ ] **Step 3: Rodar a suíte completa (garante que o refactor não quebrou as puras)**

Run: `python -m pytest tests/ -v`
Expected: PASS (todos os testes das Tasks 1-7).

- [ ] **Step 4: Verificação manual — sem flag e flag inválida**

Run: `python pipeline_audio_transcricao.py --xpto`
Expected: imprime "Uso: ..." em stderr e sai com código 2 (`echo $?` → 2 no bash).

Run: `python pipeline_audio_transcricao.py`
Expected: gera/pula apenas `<nome>.txt` (comportamento atual). Se houver um MP3 de teste em `02-audio/`, conferir que NÃO cria `-timestamps.txt`.

- [ ] **Step 5: Verificação manual — `--timestamps` e `--both` + idempotência**

Pré-requisito: ter pelo menos um `.mp3` em `02-audio/` e as API keys no `.env`.

Run: `python pipeline_audio_transcricao.py --timestamps`
Expected: cria `<nome>-timestamps.txt` no formato `[HH:MM:SS -> HH:MM:SS] frase`, uma frase por linha. Não cria `<nome>.txt` se ele não existir.

Run: `python pipeline_audio_transcricao.py --both`
Expected: cria o que faltar (ex.: `<nome>.txt`), pula o que já existe.

Run de novo: `python pipeline_audio_transcricao.py --both`
Expected: "Já processado ... Pulando." para o arquivo; nenhuma chamada ao Deepgram.

- [ ] **Step 6: Commit**

```bash
git add pipeline_audio_transcricao.py
git commit -m "feat: flags --timestamps/--both com idempotência por variante no loop principal"
```

---

## Task 9: Documentar as flags no README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Adicionar seção de flags**

Após o bloco "Opção B / Opção C" (antes de "Estrutura de pastas"), inserir:

```markdown
### 3. Variantes de transcrição (timestamps)

Por padrão, o script gera a transcrição limpa em parágrafos (`<nome>.txt`).
Use uma flag para gerar também (ou apenas) a versão com marcação de tempo,
útil para edição de vídeo com IA (corte, montagem, legenda):

| Comando | Resultado |
|---|---|
| `python pipeline_audio_transcricao.py` | Só a versão **sem** timestamp (`<nome>.txt`) — padrão |
| `python pipeline_audio_transcricao.py --timestamps` | Só a versão **com** timestamp (`<nome>-timestamps.txt`) |
| `python pipeline_audio_transcricao.py --both` | As **duas** versões |

A versão com timestamp tem uma frase por linha:

```text
[00:00:00 -> 00:00:04] Bem-vindo ao nosso produto.
[00:00:05 -> 00:00:13] Hoje vou mostrar como funciona.
```

Cada variante é **idempotente** de forma independente: se um dos arquivos já
existir, ele é pulado; o Deepgram só é chamado quando falta alguma variante
solicitada.
```

- [ ] **Step 2: Atualizar a seção "Como funciona"**

No item 5 da lista "Como funciona", trocar:

```markdown
5. **Salva**: A transcrição final em `03-transcricoes/`.
```

por:

```markdown
5. **Salva**: A(s) transcrição(ões) em `03-transcricoes/` — `<nome>.txt` (sem timestamp) e/ou `<nome>-timestamps.txt` (com timestamp), conforme as flags.
```

- [ ] **Step 3: Atualizar a árvore de pastas (comentário)**

Na seção "Estrutura de pastas", trocar a linha:

```text
├── 03-transcricoes/   # Transcrições em .txt (gerado automaticamente)
```

por:

```text
├── 03-transcricoes/   # Transcrições .txt e -timestamps.txt (gerado automaticamente)
```

- [ ] **Step 4: Conferir a renderização**

Run: `python -m pytest tests/ -v` (garantir que nada quebrou) e revisar o `README.md` visualmente.
Expected: testes PASS; README com a nova seção.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: documentar flags --timestamps e --both no README"
```

---

## Self-Review (cobertura do spec)

- **Flags CLI (sem flag / `--timestamps` / `--both` / inválida)** → Task 5 (`parse_args`) + Task 8 (uso no `main`). ✔
- **Formato `[HH:MM:SS -> HH:MM:SS] texto` por frase** → Task 1 (`formatar_timestamp`) + Task 4 (`montar_texto_com_tempo`). ✔
- **Fonte dos tempos em `paragraphs.paragraphs[].sentences[]` (end da própria frase)** → Task 3/4 (`extrair_paragrafos`, `montar_frases`). ✔
- **Fallback sem `paragraphs` (linha única + aviso, fim = duração ou vazio)** → Task 7 (`construir_texto_timestamps`). ✔
- **Idempotência por variante + Deepgram só se faltar variante** → Task 8. ✔
- **Tradução sem timestamp em bloco; com timestamp frase a frase numa chamada, realinhando por posição** → Task 6/7 (`traduzir_frases`, `construir_texto_timestamps`). ✔
- **Fallback seguro quando contagem não bate** → Task 7 (bloco único com timestamps de abertura/fim + aviso). ✔
- **Refactor leve em funções pequenas** → Tasks 1, 3-7. ✔
- **README atualizado** → Task 9. ✔
- **`extrair-audio.bat` continua sem argumentos (padrão)** → inalterado; padrão de `parse_args([])` = só simples. ✔

Consistência de tipos: `montar_frases` produz `(start, end, texto)`; `montar_texto_com_tempo`, `montar_prompt_frases` e `construir_texto_timestamps` consomem exatamente essa tupla. `traduzir_frases`/`parsear_resposta_numerada` retornam `list[str] | None`, tratado em `construir_texto_timestamps`. ✔
