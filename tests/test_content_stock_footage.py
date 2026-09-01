import pytest

from poe.content.stock_footage import PexelsProvider, PixabayProvider, StockFootageError


def make_http_get(responses):
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        return responses[len(calls) - 1]

    fake_get.calls = calls
    return fake_get


PEXELS_RESPONSE = {
    "videos": [
        {
            "id": 1,
            "url": "https://pexels.com/video/1",
            "user": {"name": "Fulano"},
            "video_files": [
                {"link": "https://cdn/landscape.mp4", "width": 1920, "height": 1080, "quality": "hd"},
                {"link": "https://cdn/portrait.mp4", "width": 1080, "height": 1920, "quality": "hd"},
                {"link": "https://cdn/portrait-sd.mp4", "width": 720, "height": 1280, "quality": "sd"},
            ],
        }
    ]
}


def test_pexels_prefers_portrait_hd_file():
    http_get = make_http_get([(200, PEXELS_RESPONSE)])
    provider = PexelsProvider(api_key="fake", http_get=http_get)

    clip = provider.search("cat drinking water")

    assert clip is not None
    assert clip.url == "https://cdn/portrait.mp4"
    assert clip.source_name == "Pexels"
    assert clip.attribution == "Fulano"
    assert http_get.calls[0][1]["Authorization"] == "fake"


def test_pexels_returns_none_when_no_videos():
    http_get = make_http_get([(200, {"videos": []})])
    provider = PexelsProvider(api_key="fake", http_get=http_get)

    assert provider.search("something obscure") is None


def test_pexels_raises_on_error_status():
    http_get = make_http_get([(401, {"message": "Missing API key"})])
    provider = PexelsProvider(api_key="", http_get=http_get)

    with pytest.raises(StockFootageError, match="401"):
        provider.search("cat")


PIXABAY_RESPONSE = {
    "hits": [
        {
            "pageURL": "https://pixabay.com/videos/1",
            "user": "Ciclano",
            "videos": {
                "large": {"url": "https://cdn/large.mp4", "width": 1920, "height": 1080},
                "medium": {"url": "https://cdn/medium.mp4", "width": 1280, "height": 720},
            },
        }
    ]
}


def test_pixabay_prefers_large_quality():
    http_get = make_http_get([(200, PIXABAY_RESPONSE)])
    provider = PixabayProvider(api_key="fake", http_get=http_get)

    clip = provider.search("mop floor")

    assert clip is not None
    assert clip.url == "https://cdn/large.mp4"
    assert clip.source_name == "Pixabay"
    assert clip.attribution == "Ciclano"


def test_pixabay_returns_none_when_no_hits():
    http_get = make_http_get([(200, {"hits": []})])
    provider = PixabayProvider(api_key="fake", http_get=http_get)

    assert provider.search("something obscure") is None
