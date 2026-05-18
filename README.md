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
