from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    openai_api_key: str
    postgres_dsn: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str

    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    work_dir: Path = Path("workspace")

    min_scene_seconds: float = 3.0
    max_scene_seconds: float = 40.0
    top_scenes: int = 5

    target_height: int = 1920
    target_width: int = 1080
    font_path: Path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

    class Config:
        extra = "ignore"

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        return cls(
            openai_api_key=env.get("OPENAI_API_KEY", ""),
            postgres_dsn=env.get("POSTGRES_DSN", "postgresql://media:media@localhost:5432/media"),
            minio_endpoint=env.get("MINIO_ENDPOINT", "http://localhost:9000"),
            minio_access_key=env.get("MINIO_ACCESS_KEY", "minio"),
            minio_secret_key=env.get("MINIO_SECRET_KEY", "minio123"),
            minio_bucket=env.get("MINIO_BUCKET", "shorts"),
            input_dir=Path(env.get("INPUT_DIR", "input")),
            output_dir=Path(env.get("OUTPUT_DIR", "output")),
            work_dir=Path(env.get("WORK_DIR", "workspace")),
            min_scene_seconds=float(env.get("MIN_SCENE_SECONDS", 3)),
            max_scene_seconds=float(env.get("MAX_SCENE_SECONDS", 40)),
            top_scenes=int(env.get("TOP_SCENES", 5)),
            target_height=int(env.get("TARGET_HEIGHT", 1920)),
            target_width=int(env.get("TARGET_WIDTH", 1080)),
            font_path=Path(env.get("FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")),
        )
