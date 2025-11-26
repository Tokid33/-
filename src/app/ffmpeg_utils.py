from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple


def run_ffmpeg(cmd: List[str]) -> None:
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with code {process.returncode}: {process.stdout}")


def detect_silence(input_file: Path) -> List[Tuple[float, float]]:
    cmd = [
        "ffmpeg",
        "-i",
        str(input_file),
        "-af",
        "silencedetect=noise=-30dB:d=0.5",
        "-f",
        "null",
        "-",
    ]
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"Silence detection failed: {process.stdout}")

    boundaries: List[float] = [0.0]
    for line in process.stdout.splitlines():
        if "silence_start" in line:
            boundaries.append(float(line.split("silence_start:")[1].strip()))
        if "silence_end" in line:
            end = float(line.split("silence_end:")[1].split(" ")[0].strip())
            boundaries.append(end)
    return list(zip(boundaries, boundaries[1:]))


def export_scene(input_file: Path, start: float, end: float, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-ss",
        f"{start}",
        "-to",
        f"{end}",
        "-c",
        "copy",
        str(destination),
    ]
    run_ffmpeg(cmd)
    return destination


def render_vertical(
    clip: Path,
    subtitles: Path,
    font_path: Path,
    output_path: Path,
    target_width: int,
    target_height: int,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2,"
        f"boxblur=luma_radius=min(h\,w)/20:luma_power=1:chroma_radius=min(h\,w)/20:chroma_power=1,"
        f"setsar=1:1[bg];"
        f"[0:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"subtitles={subtitles}:fontsdir=/usr/share/fonts/truetype/dejavu:force_style=\"Fontname=DejaVu Sans,Fontsize=36,PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=1,Shadow=0,Alignment=2\""
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(clip),
        "-filter_complex",
        filter_complex,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path
