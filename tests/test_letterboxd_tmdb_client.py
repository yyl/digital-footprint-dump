from src.letterboxd.tmdb_client import TMDBClient


def test_tmdb_client_prefers_exact_title_and_year_match():
    client = TMDBClient(access_token="token")
    client._make_request = lambda path, params=None: {  # type: ignore[method-assign]
        "results": [
            {"id": 1, "title": "The Substance", "original_title": "The Substance", "release_date": "2024-09-07"},
            {"id": 2, "title": "The Substance", "original_title": "The Substance", "release_date": "2025-01-01"},
        ]
    } if path == "/search/movie" else {"runtime": 141}

    match = client.get_runtime(title="The Substance", year=2024)

    assert match == (1, 141)


def test_tmdb_client_rejects_fuzzy_title_matches():
    client = TMDBClient(access_token="token")
    client._make_request = lambda path, params=None: {  # type: ignore[method-assign]
        "results": [
            {"id": 1, "title": "Substance", "original_title": "Substance", "release_date": "2024-09-07"},
        ]
    } if path == "/search/movie" else {"runtime": 141}

    match = client.get_runtime(title="The Substance", year=2024)

    assert match is None


def test_tmdb_client_allows_one_year_release_fallback_for_exact_title():
    client = TMDBClient(access_token="token")

    def fake_request(path, params=None):  # type: ignore[no-untyped-def]
        if path != "/search/movie":
            return {"runtime": 102}
        if params == {"query": "Synchronic", "year": 2019}:
            return {"results": []}
        if params == {"query": "Synchronic"}:
            return {
                "results": [
                    {"id": 10, "title": "Synchronic", "original_title": "Synchronic", "release_date": "2020-10-23"}
                ]
            }
        return {"results": []}

    client._make_request = fake_request  # type: ignore[method-assign]

    match = client.get_runtime(title="Synchronic", year=2019)

    assert match == (10, 102)


def test_tmdb_client_rejects_large_year_gap_even_on_fallback():
    client = TMDBClient(access_token="token")

    def fake_request(path, params=None):  # type: ignore[no-untyped-def]
        if path != "/search/movie":
            return {"runtime": 90}
        if params == {"query": "The Blackening", "year": 2022}:
            return {"results": []}
        if params == {"query": "The Blackening"}:
            return {
                "results": [
                    {
                        "id": 20,
                        "title": "The Blackening",
                        "original_title": "The Blackening",
                        "release_date": "2024-01-01",
                    }
                ]
            }
        return {"results": []}

    client._make_request = fake_request  # type: ignore[method-assign]

    match = client.get_runtime(title="The Blackening", year=2022)

    assert match is None
