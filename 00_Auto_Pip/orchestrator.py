import json
import sys
from pathlib import Path

import requests

# One port per stage
STAGES = {
    "mp4_to_mp3": "http://127.0.0.1:8001",
    "mp3_to_text": "http://127.0.0.1:8002",
    "text_to_kw": "http://127.0.0.1:8003",
}


def call(stage: str, path: str, **kwargs) -> requests.Response:
    """Send one request to one stage, with clear error messages."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage: {stage}")
    url = f"{STAGES[stage]}{path}"
    try:
        response = requests.post(url, timeout=900, **kwargs)
    except requests.exceptions.ConnectionError as exc:
        raise SystemExit(
            f"Stage '{stage}' is not running at {url}. Run start_all.bat first."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise SystemExit(f"Stage '{stage}' timed out while calling {url}.") from exc

    if not response.ok:
        detail = response.text.strip().replace("\n", " ")
        raise SystemExit(
            f"Stage '{stage}' failed ({response.status_code}): {detail[:300]}"
        )
    return response


def run_pipeline(mp4_path: str, work_dir: str | None = None) -> Path:
    input_path = Path(mp4_path).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input video was not found: {input_path}")

    if work_dir is None:
        work_dir = str(Path(__file__).resolve().parent / "jobs" / "job1")
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    # Stage 01: video -> audio
    print("[01] Extracting audio...")
    with input_path.open("rb") as f:
        r = call("mp4_to_mp3", "/extract", files={"file": (input_path.name, f)})
    mp3_path = work / "audio.mp3"
    mp3_path.write_bytes(r.content)
    print(f"     saved {mp3_path}")

    # Stage 02: audio -> text
    print("[02] Transcribing (first run can be slow)...")
    with open(mp3_path, "rb") as f:
        r = call("mp3_to_text", "/api/transcribe",
                 files={"file": ("audio.mp3", f)},
                 data={"language": "auto"})
    try:
        result = r.json()
        text = result["text"]
        language_label = result["language_label"]
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'mp3_to_text' returned an invalid response: {r.text[:300]}"
        ) from exc
    (work / "transcript.txt").write_text(text, encoding="utf-8")
    print(f"     language: {language_label}, {len(text.split())} words")

    # Stage 03: text -> keywords
    print("[03] Extracting keywords...")
    r = call("text_to_kw", "/api/extract-keywords", json={"text": text, "top_n": 15})
    try:
        keywords = r.json()["keywords_in_order"]
    except (ValueError, KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'text_to_kw' returned an invalid response: {r.text[:300]}"
        ) from exc
    (work / "keywords.json").write_text(
        json.dumps(keywords, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"     {len(keywords)} keywords: {keywords}")

    return work


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage: python orchestrator.py "path\\to\\video.mp4" '
            '[--work-dir "output\\folder"]'
        )

    input_argument = sys.argv[1]
    work_dir = None
    if len(sys.argv) > 2:
        if len(sys.argv) != 4 or sys.argv[2] != "--work-dir":
            raise SystemExit(
                'Usage: python orchestrator.py "path\\to\\video.mp4" '
                '[--work-dir "output\\folder"]'
            )
        work_dir = sys.argv[3]
    run_pipeline(input_argument, work_dir)