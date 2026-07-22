import pytest

from app.utils.chunking import split_text


def test_split_text_returns_overlapping_chunks() -> None:
    chunks = split_text(
        "abcdefghijklmnopqrstuvwxyz",
        chunk_size=10,
        chunk_overlap=2,
    )

    assert chunks == [
        "abcdefghij",
        "ijklmnopqr",
        "qrstuvwxyz",
    ]


def test_split_text_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        split_text("hello", chunk_size=5, chunk_overlap=5)
