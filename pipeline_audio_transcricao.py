#!/usr/bin/env python3
"""
Pipeline: Extrai MP3 de vídeos e transcreve com Deepgram
Pastas: 01-video -> 02-audio -> 03-transcricoes
"""

import os
import re
import sys
import json
import shutil
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

# Forçar UTF-8 no stdout/stderr (Windows cp1252 não suporta emojis)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

# ── Configurações ──────────────────────────────────────────────
BASE_DIR           = Path(__file__).parent.resolve()
PASTA_VIDEOS       = BASE_DIR / "01-video"
PASTA_AUDIO        = BASE_DIR / "02-audio"
PASTA_TRANSCRICOES = BASE_DIR / "03-transcricoes"

DEEPGRAM_API_KEY    = os.getenv("DEEPGRAM_API_KEY")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")

DEEPGRAM_URL      = (
    "https://api.deepgram.com/v1/listen"
    "?diarize=true&numerals=true&paragraphs=true"
    "&punctuate=true&smart_format=true&detect_language=true&model=nova-3"
)
OPENROUTER_URL    = "https://openrouter.ai/api/v1/chat/completions"
VIDEO_EXTENSOES   = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".mp3", ".wav", ".m4a"}


# ── Tradução via OpenRouter ────────────────────────────────────
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


def formatar_timestamp(segundos):
    """Converte segundos (float) em 'HH:MM:SS'."""
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


# ── Navegação no JSON do Deepgram ──────────────────────────────
def _primeira_alternativa(data):
    """Retorna o dict da 1ª alternativa do 1º canal (ou {})."""
    channels = data.get("results", {}).get("channels", [{}]) or [{}]
    alternatives = channels[0].get("alternatives", [{}]) or [{}]
    return alternatives[0]


def extrair_paragrafos(data):
    """Lista de parágrafos do Deepgram, ou [] se não houver."""
    return _primeira_alternativa(data).get("paragraphs", {}).get("paragraphs", [])


def extrair_transcript(data):
    """Transcript plano (fallback quando não há paragraphs)."""
    return _primeira_alternativa(data).get("transcript", "")


def extrair_palavras(data):
    """Lista de palavras word-level do Deepgram, ou [] se não houver.

    Cada item traz, ao menos, 'word'/'punctuated_word' e 'start'/'end' (em
    segundos, com precisão de milissegundos).
    """
    return _primeira_alternativa(data).get("words", [])


def extrair_idioma(data):
    """Idioma detectado no 1º canal, ou None."""
    channels = data.get("results", {}).get("channels", [{}])
    return channels[0].get("detected_language")


# ── Montagem de texto ──────────────────────────────────────────
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


# ── Montagem word-level (formato ElevenLabs Scribe) ────────────
def montar_words_json(words, usar_pontuacao=True):
    """Converte palavras do Deepgram em tokens no formato ElevenLabs Scribe.

    Cada palavra vira {"text", "start", "end", "type": "word"}. Entre duas
    palavras consecutivas insere um token de espaço
    {"text": " ", "start": fim_anterior, "end": inicio_proximo,
    "type": "spacing"} — reproduzindo os tokens 'spacing' do Scribe.

    usar_pontuacao=True usa 'punctuated_word' ("Você,"); False usa 'word'
    ("você"). Útil para karaokê (com pontuação) vs. corte limpo (sem).
    """
    chave = "punctuated_word" if usar_pontuacao else "word"
    tokens = []
    for i, w in enumerate(words):
        texto = w.get(chave) or w.get("word", "")
        tokens.append({
            "text": texto,
            "start": w["start"],
            "end": w["end"],
            "type": "word",
        })
        if i + 1 < len(words):
            tokens.append({
                "text": " ",
                "start": w["end"],
                "end": words[i + 1]["start"],
                "type": "spacing",
            })
    return tokens


def construir_words_json(data, usar_pontuacao=True):
    """Monta o objeto {"words": [...]} word-level a partir do JSON do Deepgram.

    Trabalha sempre no idioma ORIGINAL (não traduz): o alinhamento palavra↔tempo
    só é confiável na fala original.
    """
    words = extrair_palavras(data)
    return {"words": montar_words_json(words, usar_pontuacao)}


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


def parse_args(argv):
    """Resolve as variantes: (gerar_simples, gerar_timestamps, gerar_words).

    - sem flag       -> (True,  False, False)  # só transcrição simples (padrão)
    - --timestamps   -> (False, True,  False)  # só versão com timestamp (frases)
    - --words-json   -> (False, False, True)   # só JSON word-level (Scribe)
    - --both         -> (True,  True,  False)  # simples + timestamps
    - --all          -> (True,  True,  True)   # as três variantes
    Flag inválida    -> imprime uso e encerra com código != 0.
    """
    if not argv:
        return (True, False, False)
    if len(argv) == 1:
        if argv[0] == "--timestamps":
            return (False, True, False)
        if argv[0] == "--words-json":
            return (False, False, True)
        if argv[0] == "--both":
            return (True, True, False)
        if argv[0] == "--all":
            return (True, True, True)
    print(
        "Uso: python pipeline_audio_transcricao.py "
        "[--timestamps | --words-json | --both | --all]",
        file=sys.stderr,
    )
    sys.exit(2)


def main():
    gerar_simples, gerar_timestamps, gerar_words = parse_args(sys.argv[1:])

    # ── Setup ──────────────────────────────────────────────────────
    PASTA_AUDIO.mkdir(parents=True, exist_ok=True)
    PASTA_TRANSCRICOES.mkdir(parents=True, exist_ok=True)

    # ── Verificação de Dependência ──────────────────────────────────
    FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"

    try:
        subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ ERRO: FFmpeg não encontrado!")
        print("O FFmpeg é necessário para extrair o áudio dos vídeos.")
        print("Instruções de instalação:")
        print("1. Baixe em: https://www.gyan.dev/ffmpeg/builds/")
        print("2. Extraia e adicione a pasta 'bin' ao seu PATH do Windows.")
        print("3. Reinicie o terminal/editor.")
        sys.exit(1)

    # ── 1. Extração de Áudio (Vídeos -> MP3) ──────────────────────
    # Processa vídeos na pasta 01-video que ainda não tenham MP3 correspondente
    videos = sorted([
        f for f in PASTA_VIDEOS.iterdir()
        if f.suffix.lower() in VIDEO_EXTENSOES
    ])

    if videos:
        print(f"\n🎥 {len(videos)} vídeo(s) encontrado(s) para extração.")
        for video in videos:
            nome     = video.stem
            mp3_path = PASTA_AUDIO / f"{nome}.mp3"

            if not mp3_path.exists():
                print(f" -> 🎵 Extraindo áudio de: {video.name}")
                result = subprocess.run(
                    [
                        FFMPEG_PATH,
                        "-i", str(video),
                        "-vn",
                        "-acodec", "libmp3lame",
                        "-q:a", "2",
                        str(mp3_path),
                        "-hide_banner",
                        "-loglevel", "error"
                    ],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f" -> ❌ Erro no FFmpeg: {result.stderr}")
            else:
                # print(f" -> Skip: Áudio já existe para {video.name}")
                pass

    # ── 2. Transcrição (MP3 -> TXT) ───────────────────────────────
    # Processa TODOS os MP3 na pasta 02-audio que ainda não tenham transcrição
    audios = sorted([
        f for f in PASTA_AUDIO.iterdir()
        if f.suffix.lower() == ".mp3"
    ])

    if not audios:
        print(f"\n❌ Nenhum arquivo MP3 encontrado em '{PASTA_AUDIO}/' para transcrever.")
        sys.exit(0)

    print(f"\n===============================================")
    print(f"  {len(audios)} arquivo(s) de áudio para processar")
    print(f"===============================================\n")

    for mp3_path in audios:
        nome       = mp3_path.stem
        txt_path   = PASTA_TRANSCRICOES / f"{nome}.txt"
        ts_path    = PASTA_TRANSCRICOES / f"{nome}-timestamps.txt"
        words_path = PASTA_TRANSCRICOES / f"{nome}-words.json"

        precisa_simples    = gerar_simples    and not txt_path.exists()
        precisa_timestamps = gerar_timestamps and not ts_path.exists()
        precisa_words      = gerar_words      and not words_path.exists()

        if not precisa_simples and not precisa_timestamps and not precisa_words:
            print(f" -> ✅ {mp3_path.name}: Já processado (variantes solicitadas existem). Pulando.")
            continue

        print(f" -> 🧠 Transcrevendo: {mp3_path.name}")
        print(f"    (Enviando para Deepgram Nova-3...)")

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/mp3",
        }

        try:
            with open(mp3_path, "rb") as f:
                audio_bytes = f.read()

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

            # Variante WORD-LEVEL JSON (formato ElevenLabs Scribe)
            if precisa_words:
                words_obj = construir_words_json(data)
                if not words_obj["words"]:
                    print(f" -> ⚠️  Aviso: Deepgram não retornou palavras para {mp3_path.name}")
                else:
                    with open(words_path, "w", encoding="utf-8") as f:
                        json.dump(words_obj, f, ensure_ascii=False, indent=2)
                    print(f" -> ✅ JSON palavra-a-palavra salvo: {words_path.name}")

        except Exception as e:
            print(f" -> ❌ Erro ao processar {mp3_path.name}: {e}")

    print(f"\n===============================================")
    print(f"  Processamento concluído!")
    print(f"===============================================\n")


if __name__ == "__main__":
    main()
