"""Convert M3U playlists into Serato crates."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import traceback
from urllib.parse import unquote, urlparse


WINDOWS_DRIVE_PATH = re.compile(r"^[\\/]+([A-Za-z]:[\\/].*)$")


def parse_m3u(m3u_path: Path) -> list[str]:
    """Parse .m3u/.m3u8 and return non-comment track lines."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = m3u_path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Could not decode playlist: {m3u_path}")

    tracks = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tracks.append(line)
    return tracks


def sanitize_crate_name(name: str) -> str:
    """Return a Windows-safe and Serato-friendly crate file name."""
    bad = '<>:"/\\|?*'
    cleaned = "".join("_" if c in bad else c for c in name).strip().rstrip(".")
    return cleaned or "Imported"


def normalize_m3u_entry(entry: str) -> Path:
    """Normalize an M3U track entry into a local filesystem path."""
    parsed = urlparse(entry)
    if parsed.scheme == "file":
        entry = unquote(parsed.path)

    match = WINDOWS_DRIVE_PATH.match(entry)
    if match:
        entry = match.group(1)

    return Path(entry)


def convert_playlist_to_crate(
    m3u_path: Path, serato_root: Path, skip_missing: bool = True
) -> tuple[str, int, int]:
    from pyserato.builder import Builder
    from pyserato.model.crate import Crate
    from pyserato.model.track import Track

    crate_name = sanitize_crate_name(m3u_path.stem)
    crate = Crate(crate_name)
    added = 0
    skipped = 0

    for entry in parse_m3u(m3u_path):
        track_path = normalize_m3u_entry(entry)

        # Relative paths in M3U are relative to the playlist file.
        if not track_path.is_absolute():
            track_path = (m3u_path.parent / track_path).resolve()

        if not track_path.exists():
            if skip_missing:
                skipped += 1
                print(f"    [skip missing] {track_path}")
                continue
            raise FileNotFoundError(track_path)

        try:
            crate.add_track(Track.from_path(track_path))
            added += 1
        except Exception as e:
            # pyserato may raise duplicate-track errors or path-related issues.
            skipped += 1
            print(f"    [skip error] {track_path} -> {e}")

    builder = Builder()
    builder.save(crate, save_path=serato_root, overwrite=True)

    return crate_name, added, skipped


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage:")
        print("  m3u-to-crates <playlist_folder> <serato_root>")
        print(r'Example: m3u-to-crates "D:\Playlists" "D:\_Serato_"')
        return 1

    playlist_folder = Path(sys.argv[1]).expanduser().resolve()
    serato_root = Path(sys.argv[2]).expanduser().resolve()

    if not playlist_folder.exists() or not playlist_folder.is_dir():
        print(f"[ERROR] Playlist folder not found: {playlist_folder}")
        return 1

    if not serato_root.exists() or not serato_root.is_dir():
        print(f"[ERROR] Serato root not found: {serato_root}")
        print("Expected something like: D:\\_Serato_")
        return 1

    m3u_files = sorted(
        list(playlist_folder.glob("*.m3u")) + list(playlist_folder.glob("*.m3u8"))
    )
    if not m3u_files:
        print(f"[INFO] No .m3u or .m3u8 files found in: {playlist_folder}")
        return 0

    print(f"[INFO] Found {len(m3u_files)} playlist(s) in {playlist_folder}")
    print(f"[INFO] Saving crates into {serato_root}")
    print("-" * 60)

    total_added = 0
    total_skipped = 0
    success = 0
    failed = 0

    for m3u in m3u_files:
        print(f"[PROCESS] {m3u.name}")
        try:
            crate_name, added, skipped = convert_playlist_to_crate(
                m3u, serato_root, skip_missing=True
            )
            print(f"    [OK] Crate: {crate_name} | added={added} skipped={skipped}")
            total_added += added
            total_skipped += skipped
            success += 1
        except Exception as e:
            failed += 1
            print(f"    [FAILED] {e}")
            traceback.print_exc()

    print("-" * 60)
    print(f"[DONE] playlists={len(m3u_files)} success={success} failed={failed}")
    print(f"       total tracks added={total_added}, skipped={total_skipped}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
