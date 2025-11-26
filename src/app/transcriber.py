from __future__ import annotations

from pathlib import Path
from typing import List

from openai import OpenAI


def transcribe_audio(client: OpenAI, audio_file: Path) -> str:
    with audio_file.open("rb") as f:
        transcript = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=f, response_format="text")
    return transcript


def build_srt(text: str, duration: float, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = text.strip().split()
    if not lines:
        destination.write_text("")
        return destination
    words_per_line = 8
    segments: List[str] = []
    chunk_count = (len(lines) + words_per_line - 1) // words_per_line
    seconds_per_chunk = max(duration / chunk_count, 1.0)
    for idx in range(chunk_count):
        start = idx * seconds_per_chunk
        end = min((idx + 1) * seconds_per_chunk, duration)
        chunk_words = lines[idx * words_per_line : (idx + 1) * words_per_line]
        payload = " ".join(chunk_words)
        segments.append(
            f"{idx + 1}\n"
            f"{format_timestamp(start)} --> {format_timestamp(end)}\n"
            f"{payload}\n\n"
        )
    destination.write_text("".join(segments), encoding="utf-8")
    return destination


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")
