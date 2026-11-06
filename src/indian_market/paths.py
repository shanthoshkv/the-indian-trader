"""Repo paths. One place so skills and tests do not invent locations."""

from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return repo_root() / "data"


def fixtures_dir() -> Path:
    return data_dir() / "fixtures"
