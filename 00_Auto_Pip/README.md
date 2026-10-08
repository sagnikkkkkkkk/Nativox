# Nativox automatic pipeline

This folder runs the complete Nativox pipeline with one shared virtual
environment:

`MP4 → MP3 → Text → Keywords → Sentence → Hindi reformation → Hindi MP3 → final MP4`

## First run

In PowerShell, run:

```powershell
Set-Location "E:\Z. Code Programming\VS Code\Major Project (Nativox)\00_Auto_Pip"
& .\setup.bat
```

In Command Prompt, run:

```bat
cd /d "E:\Z. Code Programming\VS Code\Major Project (Nativox)\00_Auto_Pip"
setup.bat
```

`setup.bat` creates `venv` and installs the requirements for all stages.
Stage 01 and Stage 07 also require `ffmpeg` to be available on `PATH`.

## Start and stop

In PowerShell:

```powershell
& .\start_all.bat
& .\run_pipeline.bat "C:\path\to\video.mp4"
& .\stop_all.bat
```

In Command Prompt:

```bat
start_all.bat
run_pipeline.bat "C:\path\to\video.mp4"
stop_all.bat
```

`start_all.bat` opens all seven FastAPI services. Run the pipeline after the
seven service windows are ready. `stop_all.bat` stops all pipeline services.

Pipeline output is written to `jobs\job1` by default. To select another
directory, pass it as the second argument to `run_pipeline.bat`.

The final files include `final_dubbed_video.mp4`, `dubbed_audio.mp3`,
`transcript.txt`, `keywords.json`, and the intermediate sentence/text files.
