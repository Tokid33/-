from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

from app.config import Settings
from app.ffmpeg_utils import detect_silence, export_scene, render_vertical
from app.scoring import score_transcripts
from app.transcriber import build_srt, transcribe_audio

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Автопайплайн нарезки и сборки шортсов")
    parser.add_argument("--watch", action="store_true", help="Запуск в режиме watch: опрашивает input директорию")
    parser.add_argument("--once", action="store_true", help="Единовременный запуск для всех файлов в input")
    parser.add_argument("--file", type=str, help="Обработать конкретный файл")
    return parser.parse_args()


@dataclass
class Scene:
    start: float
    end: float
    path: Path
    transcript: str | None = None
    score: float | None = None


class Pipeline:
    def __init__(self, settings: Settings, client: OpenAI):
        self.settings = settings
        self.client = client
        self.settings.input_dir.mkdir(exist_ok=True)
        self.settings.output_dir.mkdir(exist_ok=True)
        self.settings.work_dir.mkdir(exist_ok=True)

    def process_file(self, video_path: Path) -> None:
        logger.info("Обрабатываем %s", video_path)
        scenes = self._split_scenes(video_path)
        filtered = [s for s in scenes if self.settings.min_scene_seconds <= (s.end - s.start) <= self.settings.max_scene_seconds]
        logger.info("Отфильтровано %s сцен", len(filtered))

        transcripts = []
        for scene in tqdm(filtered, desc="Транскрипция"):
            transcript = transcribe_audio(self.client, scene.path)
            scene.transcript = transcript
            transcripts.append(transcript)

        scores = score_transcripts(self.client, transcripts)
        for scene, score in zip(filtered, scores):
            scene.score = score
        best = sorted(filtered, key=lambda s: s.score or 0, reverse=True)[: self.settings.top_scenes]
        logger.info("Выбрано топ сцен: %s", len(best))

        for idx, scene in enumerate(best, start=1):
            duration = scene.end - scene.start
            srt_path = self.settings.work_dir / f"{video_path.stem}_scene{idx:02d}.srt"
            build_srt(scene.transcript or "", duration, srt_path)
            out_path = self.settings.output_dir / f"{video_path.stem}_short{idx:02d}.mp4"
            render_vertical(
                clip=scene.path,
                subtitles=srt_path,
                font_path=self.settings.font_path,
                output_path=out_path,
                target_width=self.settings.target_width,
                target_height=self.settings.target_height,
            )
            logger.info("Готов шорт: %s (score=%.2f)", out_path, scene.score or 0)

    def _split_scenes(self, video_path: Path) -> List[Scene]:
        boundaries = detect_silence(video_path)
        scenes: List[Scene] = []
        for idx, (start, end) in enumerate(boundaries):
            clip_path = self.settings.work_dir / f"{video_path.stem}_scene{idx:02d}.mp4"
            export_scene(video_path, start, end, clip_path)
            scenes.append(Scene(start=start, end=end, path=clip_path))
        return scenes



def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    if not settings.openai_api_key:
        logger.error("Укажите OPENAI_API_KEY в .env")
        raise SystemExit(1)

    client = OpenAI(api_key=settings.openai_api_key)
    args = parse_args()
    pipeline = Pipeline(settings=settings, client=client)

    if args.file:
        pipeline.process_file(Path(args.file))
        return

    if args.once or args.watch:
        logger.info("Стартуем мониторинг input: %s", settings.input_dir)
        seen = set()
        while True:
            for video in settings.input_dir.glob("*.mp4"):
                if video not in seen:
                    pipeline.process_file(video)
                    seen.add(video)
            if not args.watch:
                break
            time.sleep(5)
        return

    logger.error("Не указан режим. Используйте --once или --watch или --file")


if __name__ == "__main__":
    main()
