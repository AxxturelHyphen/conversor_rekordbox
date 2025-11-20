from pathlib import Path

from conversor_rekordbox.audio.conversion import build_ffmpeg_command
from conversor_rekordbox.utils.config import AppConfig


def test_build_ffmpeg_command_mp3(tmp_path: Path) -> None:
    source = tmp_path / "sample.wav"
    dest = tmp_path / "sample.mp3"
    cmd = build_ffmpeg_command(source, dest, "mp3")
    assert "libmp3lame" in cmd
    assert "320k" in cmd


def test_build_ffmpeg_command_wav(tmp_path: Path) -> None:
    source = tmp_path / "sample.flac"
    dest = tmp_path / "sample.wav"
    cmd = build_ffmpeg_command(source, dest, "wav")
    assert "pcm_s16le" in cmd
    assert "44100" in cmd


def test_config_save_and_load(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    cfg = AppConfig(output_dir="/tmp/out", use_source_dir=False, last_format="wav")
    cfg.save(config_path)

    loaded = AppConfig.load(config_path)
    assert loaded.output_dir == "/tmp/out"
    assert loaded.use_source_dir is False
    assert loaded.last_format == "wav"
