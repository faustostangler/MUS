"""Unit tests for OllamaMetadataTagger adapter with fallback heuristics."""

from mus.stem_separation.infrastructure.ollama_metadata_tagger import (
    OllamaMetadataTagger,
    parse_fallback_title,
)


def test_parse_fallback_title_heuristics() -> None:
    # "Artist - Track" format
    meta1 = parse_fallback_title("Frank Sinatra - My Way")
    assert meta1.artist == "Frank Sinatra"
    assert meta1.track == "My Way"

    # Title with parenthetical noise
    meta2 = parse_fallback_title("Simon & Garfunkel - The Sound of Silence (Official Audio)")
    assert meta2.artist == "Simon & Garfunkel"
    assert meta2.track == "The Sound of Silence"


def test_ollama_metadata_tagger_offline_fallback() -> None:
    # Points to non-existent port to force fallback heuristics
    tagger = OllamaMetadataTagger(ollama_host="http://localhost:59999")
    meta = tagger.tag("John Denver - Take Me Home, Country Roads [Official Video]")
    assert meta.artist == "John Denver"
    assert "Country Roads" in meta.track
