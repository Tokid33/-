# Готовый конвейер для шортсов из «Мажора»

Проект собирает вертикальные шортсы из локально скачанных серий: режет по тишине, фильтрует сцены, транскрибирует, оценивает «хайп», рендерит вертикальные ролики с субтитрами и блюром и может крутиться в Docker вместе с Postgres, MinIO и n8n.

## Что входит
- Python-сервис с CLI `python -m app.main` (нарезка, транскрипция, скоринг, рендер).
- Dockerfile + docker-compose (app + Postgres + MinIO + n8n).
- Пример `.env.example` с настройками.
- Пример workflow `workflows/majora-shorts.json` для n8n (cron → запуск пайплайна).

## Быстрый старт (Docker)
1. Скопируйте `.env.example` → `.env` и впишите ключ OpenAI:
   ```bash
   cp .env.example .env
   # отредактируйте OPENAI_API_KEY
   ```
2. Подготовьте каталоги и положите серии в `./input` (mp4):
   ```bash
   mkdir -p input output workspace
   ```
3. Запустите стек:
   ```bash
   docker compose up --build
   ```
   - Сервис `app` будет мониторить `./input` (флаг `--watch`).
   - Готовые шорты появятся в `./output`.
   - n8n доступен на http://localhost:5678 (workflow уже лежит в volume `./workflows`).

## Ручной запуск без Docker
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # добавить OPENAI_API_KEY
python -m app.main --file input/episode01.mp4
```
- `--once` — обработать все mp4 в `INPUT_DIR` один раз.
- `--watch` — мониторить каталог и обрабатывать новые файлы.

## Как работает пайплайн
1. **Детект тишины** — `ffmpeg` (`silencedetect`) строит интервалы и режет кандидатов в `workspace/`.
2. **Фильтр по длине** — пропускает только отрезки `MIN_SCENE_SECONDS..MAX_SCENE_SECONDS`.
3. **Транскрипция** — OpenAI `gpt-4o-transcribe` по каждому клипу.
4. **Скоринг** — `gpt-4o-mini` возвращает число 0–100, сортируем и берём `TOP_SCENES`.
5. **Субтитры** — генерация простого SRT по тексту и длительности сцены.
6. **Вертикальный рендер** — FFmpeg: блюр фона + центрированный кадр 9:16 + сабы. Результат в `output/`.

## Ключевые файлы
- `src/app/main.py` — точка входа CLI, мониторинг папки, управление пайплайном.
- `src/app/ffmpeg_utils.py` — обёртки FFmpeg: детект тишины, вырезка, рендер вертикали.
- `src/app/transcriber.py` — транскрипция и сборка SRT.
- `src/app/scoring.py` — промпт и вызов LLM для оценки хайпа.
- `docker-compose.yml` — сервисы app/Postgres/MinIO/n8n.
- `workflows/majora-shorts.json` — cron → ExecuteCommand (`python -m app.main --once`).

## Настройки (.env)
- `OPENAI_API_KEY` — ключ для транскрипции и скоринга.
- `POSTGRES_DSN` — строка подключения (Postgres поднимается внутри compose).
- `MINIO_*` — точка входа и креды (для будущего хранения исходников/рендеров).
- `MIN_SCENE_SECONDS` / `MAX_SCENE_SECONDS` — фильтр длины сцен.
- `TOP_SCENES` — сколько лучших сцен собирать в шорты.
- `TARGET_WIDTH` / `TARGET_HEIGHT` — разрешение финального видео (по умолчанию 1080×1920).
- `FONT_PATH` — путь до шрифта для сабов (по умолчанию DejaVu Sans в контейнере).

## Что дальше можно подключить
- Заливку исходников и готовых роликов в MinIO/S3.
- Запись метрик в Postgres (таблицы `episodes`, `scenes`, `renders`).
- HTTP-эндпоинт или Webhook для запуска пайплайна из n8n/YouTube-бота.
- Добавление оверлея (плашки) через дополнительный вход `-i badge.png` и `overlay` в `render_vertical`.
