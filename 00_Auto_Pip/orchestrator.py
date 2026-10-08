import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

# One port per HTTP stage. Stage 04 is loaded directly from construct.py.
STAGES = {
    "mp4_to_mp3": "http://127.0.0.1:8001",
    "mp3_to_text": "http://127.0.0.1:8002",
    "text_to_kw": "http://127.0.0.1:8003",
    "kw_translation": "http://127.0.0.1:8011",
    "sentence_reformation": "http://127.0.0.1:8012",
    "text_to_mp3": "http://127.0.0.1:8013",
    "merge_mp3_mp4": "http://127.0.0.1:8014",
}

SERVICE_CONFIG = {
    "mp4_to_mp3": ("01_MP4_to_MP3\\backend", 8001, "/health"),
    "mp3_to_text": ("02_MP3_to_Text\\backend", 8002, "/api/languages"),
    "text_to_kw": ("03_Text_to_Keyword\\backend", 8003, "/api/health"),
    "kw_translation": (
        "05a_Keyword_Translation__Sagnik\\backend",
        8011,
        "/api/health",
    ),
    "sentence_reformation": (
        "05b_Sentence_Reformation__Atanu\\backend",
        8012,
        "/api/health",
    ),
    "text_to_mp3": ("06_Converted_Text_to_MP3\\backend", 8013, "/api/health"),
    "merge_mp3_mp4": ("07_Merge_MP3_with_MP4\\backend", 8014, "/api/health"),
}
STARTUP_TIMEOUT_SECONDS = 120


def wait_for_service(stage: str, health_path: str) -> None:
    """Wait until an HTTP stage accepts requests, or fail with its startup output."""
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    url = f"{STAGES[stage]}{health_path}"
    last_error = "no response"
    while time.monotonic() < deadline:
        try:
            response = requests.get(url, timeout=3)
            if response.ok:
                return
            last_error = f"HTTP {response.status_code}: {response.text[:200]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(1)
    raise SystemExit(
        f"Stage '{stage}' did not become ready at {url} within "
        f"{STARTUP_TIMEOUT_SECONDS} seconds ({last_error})."
    )


def start_services(root: Path) -> list[subprocess.Popen]:
    """Start missing HTTP stages and return only processes owned by this run."""
    owned_processes = []
    for stage, (relative_dir, port, health_path) in SERVICE_CONFIG.items():
        try:
            response = requests.get(f"{STAGES[stage]}{health_path}", timeout=2)
            if response.ok:
                print(f"[ready] {stage} is already running on port {port}")
                continue
        except requests.RequestException:
            pass

        backend_dir = root / relative_dir
        if not backend_dir.is_dir():
            raise SystemExit(f"Backend directory for '{stage}' was not found: {backend_dir}")
        print(f"[start] {stage} on port {port}")
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=backend_dir,
            env=os.environ.copy(),
        )
        owned_processes.append(process)
        try:
            wait_for_service(stage, health_path)
        except SystemExit:
            stop_services(owned_processes)
            raise
    return owned_processes


def stop_services(processes: list[subprocess.Popen]) -> None:
    """Stop only service processes started by this pipeline invocation."""
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


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


def run_pipeline(
    mp4_path: str, work_dir: str | None = None, auto_start: bool = True
) -> Path:
    input_path = Path(mp4_path).expanduser().resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input video was not found: {input_path}")

    if work_dir is None:
        work_dir = str(Path(__file__).resolve().parent / "jobs" / "job1")
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    root = Path(__file__).resolve().parent.parent
    owned_processes = start_services(root) if auto_start else []
    try:
        return _run_pipeline_steps(input_path, work, root)
    finally:
        stop_services(owned_processes)


def _run_pipeline_steps(input_path: Path, work: Path, root: Path) -> Path:
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

    # Stage 04: keywords -> grammatical sentence, loaded directly from construct.py.
    print("[04] Constructing a sentence from keywords...")
    keyword_text = ", ".join(keywords)
    stage4_dir = root / "04_Keyword_to_Sentence_Construction"
    if str(stage4_dir) not in sys.path:
        sys.path.insert(0, str(stage4_dir))
    try:
        from construct import SentenceConstructor
        constructor = SentenceConstructor(model_path=str(stage4_dir / "saved_model"))
        constructed_sentence = constructor.construct(keyword_text).strip()
    except OSError as exc:
        if exc.errno == 4551 or "c10.dll" in str(exc):
            raise SystemExit(
                "Stage 'kw_to_sentence' could not load PyTorch because Windows "
                "Application Control blocked c10.dll. Ask your administrator to "
                "approve the Python/PyTorch installation."
            ) from exc
        raise
    if not constructed_sentence:
        raise SystemExit("Stage 'kw_to_sentence' returned an empty sentence.")
    (work / "constructed_sentence.txt").write_text(
        constructed_sentence, encoding="utf-8"
    )
    print(f"     saved {work / 'constructed_sentence.txt'}")

    # Stage 05a: translate keywords for the terminology/phonetic bridge.
    print("[05a] Translating keywords for terminology support...")
    r = call(
        "kw_translation",
        "/api/translate-batch",
        json={"keywords": keywords, "target_language": "hindi"},
    )
    translation_result = json_result(r, "kw_translation")
    (work / "translated_keywords.json").write_text(
        json.dumps(translation_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"     saved {work / 'translated_keywords.json'}")

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
    auto_start = True
    args = sys.argv[2:]
    if args:
        if len(args) == 2 and args[0] == "--work-dir":
            work_dir = args[1]
        elif len(args) == 1 and args[0] == "--no-auto-start":
            auto_start = False
        else:
            raise SystemExit(
                'Usage: python orchestrator.py "path\\to\\video.mp4" '
                '[--work-dir "output\\folder"] [--no-auto-start]'
            )
    run_pipeline(input_argument, work_dir, auto_start=auto_start)