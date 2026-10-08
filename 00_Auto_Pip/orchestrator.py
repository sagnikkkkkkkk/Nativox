import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

# One port per stage.
STAGES = {
    "mp4_to_mp3": "http://127.0.0.1:8001",
    "mp3_to_text": "http://127.0.0.1:8002",
    "text_to_kw": "http://127.0.0.1:8003",
    "kw_to_sentence": "http://127.0.0.1:8004",
    "sentence_reformation": "http://127.0.0.1:8012",
    "text_to_mp3": "http://127.0.0.1:8013",
    "merge_mp3_mp4": "http://127.0.0.1:8014",
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


def download(stage: str, path: str) -> requests.Response:
    """Download a generated file from one stage."""
    if stage not in STAGES:
        raise ValueError(f"Unknown stage: {stage}")
    url = f"{STAGES[stage]}{path}"
    try:
        response = requests.get(url, timeout=900)
    except requests.exceptions.ConnectionError as exc:
        raise SystemExit(
            f"Stage '{stage}' is not running at {url}. Run start_all.bat first."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise SystemExit(f"Stage '{stage}' timed out while downloading {url}.") from exc

    if not response.ok:
        detail = response.text.strip().replace("\n", " ")
        raise SystemExit(
            f"Stage '{stage}' failed ({response.status_code}): {detail[:300]}"
        )
    return response


def json_result(response: requests.Response, stage: str) -> dict:
    """Parse a JSON response and report malformed stage output clearly."""
    try:
        result = response.json()
    except ValueError as exc:
        raise SystemExit(
            f"Stage '{stage}' returned invalid JSON: {response.text[:300]}"
        ) from exc
    if not isinstance(result, dict):
        raise SystemExit(f"Stage '{stage}' returned an invalid object response.")
    return result


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

    # Stage 02: audio -> text.
    print("[02] Transcribing (first run can be slow)...")
    with mp3_path.open("rb") as f:
        r = call("mp3_to_text", "/api/transcribe",
                 files={"file": ("audio.mp3", f)},
                 data={"language": "auto"})
    result = json_result(r, "mp3_to_text")
    try:
        text = str(result["text"])
        language_label = str(result["language_label"])
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'mp3_to_text' returned an invalid response: {r.text[:300]}"
        ) from exc
    (work / "transcript.txt").write_text(text, encoding="utf-8")
    print(f"     language: {language_label}, {len(text.split())} words")

    # Stage 03: text -> keywords.
    print("[03] Extracting keywords...")
    r = call("text_to_kw", "/api/extract-keywords", json={"text": text, "top_n": 15})
    result = json_result(r, "text_to_kw")
    try:
        keywords = result["keywords_in_order"]
        if not isinstance(keywords, list) or not all(isinstance(word, str) for word in keywords):
            raise TypeError("keywords_in_order must be a list of strings")
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'text_to_kw' returned an invalid response: {r.text[:300]}"
        ) from exc
    (work / "keywords.json").write_text(
        json.dumps(keywords, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"     {len(keywords)} keywords: {keywords}")

    # Stage 04: keywords -> grammatical sentence.
    print("[04] Constructing a sentence from keywords...")
    keyword_text = ", ".join(keywords)
    r = call("kw_to_sentence", "/api/construct", json={"text": keyword_text})
    result = json_result(r, "kw_to_sentence")
    try:
        constructed_sentence = str(result["output_sentence"]).strip()
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'kw_to_sentence' returned an invalid response: {r.text[:300]}"
        ) from exc
    if not constructed_sentence:
        raise SystemExit("Stage 'kw_to_sentence' returned an empty sentence.")
    (work / "constructed_sentence.txt").write_text(
        constructed_sentence, encoding="utf-8"
    )
    print(f"     saved {work / 'constructed_sentence.txt'}")

    # Stage 05b: sentence -> meaningful Hindi précis.
    print("[05b] Re-forming and compressing the sentence...")
    r = call(
        "sentence_reformation",
        "/api/pipeline",
        json={"text": constructed_sentence, "target_language": "hindi"},
    )
    result = json_result(r, "sentence_reformation")
    try:
        meaningful_hindi = str(result["step1_meaningful_hindi"]).strip()
        precise_hindi = str(result["step2_precise_hindi"]).strip()
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'sentence_reformation' returned an invalid response: {r.text[:300]}"
        ) from exc
    final_text = precise_hindi or meaningful_hindi
    if not final_text:
        raise SystemExit("Stage 'sentence_reformation' returned empty Hindi text.")
    (work / "reformed_text.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (work / "dubbed_text.txt").write_text(final_text, encoding="utf-8")
    print(f"     saved {work / 'dubbed_text.txt'}")

    # Stage 06: Hindi text -> dubbed MP3.
    print("[06] Synthesizing Hindi speech...")
    r = call(
        "text_to_mp3",
        "/api/synthesize",
        json={"text": final_text, "voice": "hi-IN-SwaraNeural"},
    )
    result = json_result(r, "text_to_mp3")
    try:
        audio_url = str(result["audio_url"])
        audio_path = urlparse(audio_url).path
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'text_to_mp3' returned an invalid response: {r.text[:300]}"
        ) from exc
    if not audio_path.startswith("/api/audio/"):
        raise SystemExit(f"Stage 'text_to_mp3' returned an unsafe audio URL: {audio_url}")
    dubbed_mp3_path = work / "dubbed_audio.mp3"
    dubbed_mp3_path.write_bytes(download("text_to_mp3", audio_path).content)
    print(f"     saved {dubbed_mp3_path}")

    # Stage 07: original MP4 + dubbed MP3 -> final MP4.
    print("[07] Merging dubbed audio with the original video...")
    with input_path.open("rb") as video_file, dubbed_mp3_path.open("rb") as audio_file:
        r = call(
            "merge_mp3_mp4",
            "/api/merge",
            files={
                "video": (input_path.name, video_file, "video/mp4"),
                "audio": ("dubbed_audio.mp3", audio_file, "audio/mpeg"),
            },
        )
    result = json_result(r, "merge_mp3_mp4")
    try:
        video_url = str(result["video_url"])
        video_path = urlparse(video_url).path
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            f"Stage 'merge_mp3_mp4' returned an invalid response: {r.text[:300]}"
        ) from exc
    if not video_path.startswith("/api/video/"):
        raise SystemExit(f"Stage 'merge_mp3_mp4' returned an unsafe video URL: {video_url}")
    final_video_path = work / "final_dubbed_video.mp4"
    final_video_path.write_bytes(download("merge_mp3_mp4", video_path).content)
    print(f"     saved {final_video_path}")

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