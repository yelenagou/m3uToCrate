# m3uToCrates

Convert `.m3u` and `.m3u8` playlists into Serato crate files.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Run

```powershell
m3u-to-crates "D:\Playlists" "D:\_Serato_"
```

## Test

```powershell
pytest
```

## Build Windows Executable

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --name m3u-to-crates --paths src src\m3u_to_crates\cli.py
```

The executable will be created at `dist\m3u-to-crates.exe`.
