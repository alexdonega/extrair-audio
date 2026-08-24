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
                            "words": [
                                {"word": "welcome", "punctuated_word": "Welcome", "start": 0.0, "end": 0.5},
                                {"word": "to", "punctuated_word": "to", "start": 0.6, "end": 0.7},
                                {"word": "product", "punctuated_word": "product.", "start": 0.9, "end": 4.0},
                            ],
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
