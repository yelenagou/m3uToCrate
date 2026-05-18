from m3u_to_crates.cli import parse_m3u, sanitize_crate_name


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
