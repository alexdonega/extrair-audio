# Pipeline: Extrair Audio e Transcrever

Extrai áudio de vídeos, transcreve com Deepgram (Nova-3) e traduz automaticamente para pt-BR via OpenRouter quando o idioma original não é português.

## 🚀 Guia Rápido

### 1. Coloque seus arquivos
- Se você tem **Vídeos**, **Áudios** ou ambos: basta colocar na pasta **`01-video/`**.
- O script vai extrair de vídeos automaticamente e transcrever tudo.

### 2. Escolha como Rodar (Copie e Cole)

#### Opção A: No Windows (Mais Fácil)
Basta dar um clique duplo no arquivo local na pasta:
👉 **`extrair-audio.bat`**

---

#### Opção B: No Terminal (Dentro da pasta)
Abra seu terminal na pasta e copie/cole:
```powershell
python pipeline_audio_transcricao.py
```

---

#### Opção C: De Qualquer Lugar (Caminho completo)
Copie este comando direto para rodar de qualquer terminal:
```powershell
python c:\dev\tools\extrair-audio\pipeline_audio_transcricao.py
```

---

### 3. Variantes de transcrição (timestamps)

Por padrão, o script gera a transcrição limpa em parágrafos (`<nome>.txt`).
Use uma flag para gerar também (ou apenas) a versão com marcação de tempo,
útil para edição de vídeo com IA (corte, montagem, legenda):

| Comando | Resultado |
|---|---|
| `python pipeline_audio_transcricao.py` | Só a versão **sem** timestamp (`<nome>.txt`) — padrão |
| `python pipeline_audio_transcricao.py --timestamps` | Só a versão **com** timestamp por frase (`<nome>-timestamps.txt`) |
| `python pipeline_audio_transcricao.py --words-json` | Só o JSON **palavra-a-palavra** (`<nome>-words.json`) |
| `python pipeline_audio_transcricao.py --both` | Simples + timestamps por frase |
| `python pipeline_audio_transcricao.py --all` | As **três** variantes |

A versão com timestamp tem uma frase por linha:

```text
[00:00:00 -> 00:00:04] Bem-vindo ao nosso produto.
[00:00:05 -> 00:00:13] Hoje vou mostrar como funciona.
```

A versão `--words-json` gera tempo (em segundos, precisão de ms) por **palavra**,
no mesmo formato do ElevenLabs Scribe — ideal para corte exato na fronteira da
palavra e legenda karaokê:

```json
{
  "words": [
    {"text": "Você", "start": 0.12, "end": 0.34, "type": "word"},
    {"text": " ",    "start": 0.34, "end": 0.34, "type": "spacing"},
    {"text": "já",   "start": 0.34, "end": 0.46, "type": "word"}
  ]
}
```

> ⚠️ O JSON word-level usa sempre o **idioma original** (não traduz): o
> alinhamento palavra↔tempo só é confiável na fala original. Para vídeo já em
> português, funciona direto.

Cada variante é **idempotente** de forma independente: se um dos arquivos já
existir, ele é pulado; o Deepgram só é chamado quando falta alguma variante
solicitada.

---

## 🏗️ Estrutura de pastas

```
extrair-audio/
├── 01-video/          # Coloque vídeos (.mp4, .mkv, etc.) OU áudios (.mp3, .wav) aqui
├── 02-audio/          # Áudios extraídos (gerado automaticamente)
├── 03-transcricoes/   # Transcrições .txt e -timestamps.txt (gerado automaticamente)
├── pipeline_audio_transcricao.py
├── extrair-audio.bat  # Atalho para rodar no Windows
└── .env
```

## 🛠️ Requisitos

- **Python 3.10+** (instalado e no PATH)
- **FFmpeg** instalado e disponível no PATH
- Conta no [Deepgram](https://deepgram.com/) (API key)
- Conta no [OpenRouter](https://openrouter.ai/) (API key para tradução)

## ⚙️ Setup

Instale as dependências uma única vez:
```bash
pip install requests python-dotenv
```

E configure seu arquivo `.env` na raiz:
```
DEEPGRAM_API_KEY=sua_chave_aqui
OPENROUTER_API_KEY=sua_chave_aqui
```

## 🧠 Como funciona

1. **Extrai áudio**: Se houver arquivos na pasta `01-video/`, extrai para `02-audio/` (pula se o MP3 já existir).
2. **Detecta Áudios**: Escaneia a pasta `02-audio/` por arquivos `.mp3`.
3. **Transcreve**: Cada MP3 é enviado para o Deepgram Nova-3 (pula se o `.txt` já existir).
4. **Traduz para pt-BR**: Via OpenRouter (Gemini Flash) se o idioma detectado não for português.
5. **Salva**: A(s) transcrição(ões) em `03-transcricoes/` — `<nome>.txt` (sem timestamp) e/ou `<nome>-timestamps.txt` (com timestamp), conforme as flags.

O script é inteligente e **idempotente**: se você rodar novamente, ele pula o que já foi processado. Seguro para reexecutar.
