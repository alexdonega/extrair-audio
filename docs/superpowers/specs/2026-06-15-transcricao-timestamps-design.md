# Design: duas versões de transcrição (com e sem timestamp)

**Data:** 2026-06-15
**Arquivo afetado:** `pipeline_audio_transcricao.py`

## Objetivo

Permitir gerar a transcrição em duas variantes, escolhidas por flag de linha de comando:

1. **Sem timestamp** — texto limpo em parágrafos (comportamento atual).
2. **Com timestamp** — uma frase por linha, prefixada pelo intervalo `[início -> fim]`, voltada para edição de vídeo com IA (corte automático, montagem por trecho, geração de legenda).

## Comportamento (flags de CLI)

| Comando | Resultado |
|---|---|
| `python pipeline_audio_transcricao.py` | Só versão **sem** timestamp (padrão, igual hoje) |
| `python pipeline_audio_transcricao.py --timestamps` | Só versão **com** timestamp |
| `python pipeline_audio_transcricao.py --both` | As **duas** versões |

- A extração de áudio (vídeo → MP3) não é afetada pelas flags; ocorre sempre.
- `extrair-audio.bat` continua chamando o script sem argumentos (padrão = sem timestamp).
- Flags inválidas: imprimir mensagem de uso e sair com código ≠ 0.

## Arquivos gerados (em `03-transcricoes/`)

| Variante | Nome do arquivo |
|---|---|
| Sem timestamp | `<nome>.txt` (como hoje) |
| Com timestamp | `<nome>-timestamps.txt` |

- **Idempotência:** cada variante é pulada individualmente se o arquivo correspondente já existir. Ex.: com `--both`, se `<nome>.txt` existe mas `<nome>-timestamps.txt` não, só a versão com tempo é gerada.
- A chamada ao Deepgram só acontece se pelo menos uma das variantes solicitadas ainda estiver faltando (evita gasto de API à toa).

## Formato da versão com timestamp

Uma frase por linha, no formato:

```
[00:00:00 -> 00:00:04] Bem-vindo ao nosso produto.
[00:00:05 -> 00:00:13] Hoje vou mostrar como funciona.
[00:00:14 -> 00:00:18] O primeiro passo é se cadastrar.
```

- Tempo no formato `HH:MM:SS`.
- Fonte dos tempos: `results.channels[0].alternatives[0].paragraphs.paragraphs[].sentences[]`, onde cada frase já tem `start` e `end` (em segundos, float). O `end` usado é o da própria frase.
- **Fallback** (quando o Deepgram não retorna `paragraphs`): se só houver `transcript` plano, sem frases segmentadas, a versão com timestamp grava o transcript inteiro em uma linha única com `[00:00:00 -> HH:MM:SS]` (fim = duração total disponível, ou sem fim se indisponível) e registra um aviso no console. A versão sem timestamp já tem esse fallback hoje.

## Tradução mantendo o tempo (idioma detectado ≠ pt)

Hoje, quando o idioma não é `pt*`, o texto inteiro é traduzido em uma única chamada ao OpenRouter. Mantemos isso para a versão **sem** timestamp.

Para a versão **com** timestamp, traduzir o bloco inteiro quebraria o alinhamento frase↔tempo. Solução:

1. Coletar a lista de frases na ordem original.
2. Fazer **uma** chamada ao OpenRouter enviando as frases numeradas:
   ```
   1. Welcome to our product.
   2. Today I'll show how it works.
   ```
   com instrução de devolver a tradução na **mesma estrutura numerada**, uma por linha, sem comentários.
3. Parsear a resposta de volta para uma lista e realinhar cada tradução com o `[início -> fim]` da frase original (por posição/número).
4. **Fallback seguro:** se o número de linhas retornadas não bater com o número de frases enviadas, registrar aviso e usar a tradução em bloco único (texto traduzido sem segmentação por frase, mas ainda com timestamps de parágrafo/abertura), garantindo que o arquivo nunca fique vazio ou desalinhado silenciosamente.

- Se o idioma já for `pt*`, nenhuma tradução ocorre (frases originais com seus tempos).

## Refactor leve (organização)

O script hoje é um corpo procedural único. Extrair funções pequenas e testáveis, sem alterar o fluxo geral:

- `parse_args()` → resolve quais variantes gerar (`gerar_simples`, `gerar_timestamps`).
- `formatar_timestamp(segundos: float) -> str` → `HH:MM:SS`.
- `extrair_paragrafos(data) -> list` → isola a navegação no JSON do Deepgram.
- `montar_texto_simples(paragraphs) -> str` → texto em parágrafos (lógica atual).
- `montar_frases(paragraphs) -> list[(start, end, texto)]` → lista de frases com tempos.
- `montar_texto_com_tempo(frases) -> str` → linhas `[início -> fim] texto`.
- `traduzir_para_ptbr(texto)` → mantém (versão sem timestamp).
- `traduzir_frases(frases) -> list[texto_traduzido]` → tradução numerada em 1 chamada, com fallback.

O loop principal decide, por arquivo, quais variantes faltam e grava cada uma.

## Não-objetivos (YAGNI)

- Sem exportação SRT/VTT nesta versão (pode virar flag futura).
- Sem timestamps por palavra.
- Sem identificação de locutor no arquivo de saída (mesmo com `diarize=true` ativo na URL).
- Sem mudança na etapa de extração de áudio.

## Testes / verificação

- Rodar sem flag → gera só `<nome>.txt` (inalterado vs. hoje).
- Rodar com `--timestamps` → gera só `<nome>-timestamps.txt` no formato esperado.
- Rodar com `--both` → gera ambos; rodar de novo pula ambos.
- Caso idioma ≠ pt: conferir que `<nome>-timestamps.txt` tem frases traduzidas com tempos preservados e mesma quantidade de linhas que frases.
- Caso fallback (sem `paragraphs`): conferir aviso e arquivo não-vazio.
