from __future__ import annotations

from typing import List
from openai import OpenAI

PROMPT = """Ты редактор клипов. Оцени интересность сцены сериала по транскрипту.
Выставь одно число от 0 до 100 где 100 — максимальный хайп для вертикального шорта.
Возвращай только число без текста.
"""


def score_transcripts(client: OpenAI, transcripts: List[str]) -> List[float]:
    scores: List[float] = []
    for text in transcripts:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": text},
            ],
            max_output_tokens=10,
        )
        content = resp.output_text.strip()
        try:
            scores.append(float(content))
        except ValueError:
            scores.append(0.0)
    return scores
