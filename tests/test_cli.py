from pathlib import Path
import sys
import types

from m3u_to_crates.cli import (
    convert_playlist_to_crate,
    format_serato_track_path,
    normalize_m3u_entry,
    parse_m3u,
    sanitize_crate_name,
)


def test_parse_m3u_returns_non_comment_tracks(tmp_path):
    playlist = tmp_path / "sample.m3u"
    playlist.write_text(
        "#EXTM3U\n\n#EXTINF:123,Artist - Track\nMusic/track.mp3\n",
        encoding="utf-8",
    )

    assert parse_m3u(playlist) == ["Music/track.mp3"]


def test_sanitize_crate_name_replaces_windows_unsafe_characters():
    assert sanitize_crate_name('Bad:Name/Here?.') == "Bad_Name_Here_"
    assert sanitize_crate_name("...") == "Imported"


def test_normalize_m3u_entry_strips_leading_slash_before_windows_drive():
    assert str(normalize_m3u_entry("/D:/Music/song.mp3")) == "D:\\Music\\song.mp3"
    assert str(normalize_m3u_entry(r"\D:\Music\song.mp3")) == "D:\\Music\\song.mp3"


def test_normalize_m3u_entry_decodes_file_urls():
    assert str(normalize_m3u_entry("file:///D:/My%20Music/song.mp3")) == (
        "D:\\My Music\\song.mp3"
    )


def test_normalize_m3u_entry_collapses_embedded_windows_drive():
    assert str(normalize_m3u_entry(r"D:\D:\Music\song.mp3")) == (
        "D:\\Music\\song.mp3"
    )
    assert str(normalize_m3u_entry(r"D:\Playlists\D:\Music\song.mp3")) == (
        "D:\\Music\\song.mp3"
    )


def test_format_serato_track_path_uses_slash_prefixed_windows_drive():
    assert format_serato_track_path(Path(r"D:\Music\song.mp3")) == "/D:/Music/song.mp3"


def test_convert_playlist_adds_track_objects(tmp_path, monkeypatch):
    playlist = tmp_path / "sample.m3u"
    track = tmp_path / "track.mp3"
    serato_root = tmp_path / "_Serato_"
    playlist.write_text("track.mp3\n", encoding="utf-8")
    track.write_bytes(b"")
    serato_root.mkdir()

    added_tracks = []
    saved = {}

    class FakeTrack:
        def __init__(self, path):
            self.path = path

        @staticmethod
        def from_path(path):
            return FakeTrack(path)

    class FakeCrate:
        def __init__(self, name):
            self.name = name

        def add_track(self, track_obj):
            added_tracks.append(track_obj)

    class FakeBuilder:
        def save(self, crate, save_path, overwrite=False):
            saved["crate"] = crate
            saved["save_path"] = save_path
            saved["overwrite"] = overwrite

    pyserato = types.ModuleType("pyserato")
    builder = types.ModuleType("pyserato.builder")
    model = types.ModuleType("pyserato.model")
    crate = types.ModuleType("pyserato.model.crate")
    track_module = types.ModuleType("pyserato.model.track")
    util = types.ModuleType("pyserato.util")
    builder.Builder = FakeBuilder
    crate.Crate = FakeCrate
    track_module.Track = FakeTrack
    util.serato_encode = lambda value: value.encode()

    monkeypatch.setitem(sys.modules, "pyserato", pyserato)
    monkeypatch.setitem(sys.modules, "pyserato.builder", builder)
    monkeypatch.setitem(sys.modules, "pyserato.model", model)
    monkeypatch.setitem(sys.modules, "pyserato.model.crate", crate)
    monkeypatch.setitem(sys.modules, "pyserato.model.track", track_module)
    monkeypatch.setitem(sys.modules, "pyserato.util", util)

    crate_name, added, skipped = convert_playlist_to_crate(playlist, serato_root)

    assert crate_name == "sample"
    assert added == 1
    assert skipped == 0
    assert added_tracks[0].path == track.resolve()
    assert saved["save_path"] == serato_root
    assert saved["overwrite"] is True
