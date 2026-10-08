# Nativox automatic pipeline

This folder runs stages 01–03 with one shared virtual environment.

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

`setup.bat` creates `venv` and installs the requirements for the three
stages. Stage 01 also requires `ffmpeg` to be available on `PATH`.

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

`start_all.bat` opens all three FastAPI services. Run the pipeline after the
three service windows are ready. `stop_all.bat` stops services listening on
ports 8001–8003.

Pipeline output is written to `jobs\job1` by default. To select another
directory, pass it as the second argument to `run_pipeline.bat`.
