"""Self-check for the alt-text scanner. Run: python utils/alt-text/test_generate_alt_text.py"""
import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("gat", Path(__file__).with_name("generate-alt-text.py"))
gat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gat)

ok = "A long enough description of a map with cities and roads."
assert gat.weak_reason(ok, set()) is None
assert gat.weak_reason("RRCHNM Logo", set()) is None            # short is fine unless --strict
assert gat.weak_reason("RRCHNM Logo", set(), strict=True) == "short"
assert gat.weak_reason(ok, {ok.lower()}, strict=True) == "duplicate"
assert gat.weak_reason("alt-text", set()) == "missing"
assert gat.weak_reason("", set()) == "missing"
assert gat.weak_reason("34final.jpg", set()) == "filename"
assert gat.weak_reason("http://thanksroy.org/Imgs/grass_d7ea60ef9d.jpg", set()) == "filename"
assert gat.weak_reason("/files/fullsize/abc.png", set()) == "filename"
assert gat.weak_reason("Photo of Roy in 1999.", set()) is None   # trailing period is not an extension

assert gat.image_key("https://x.org/files/large/ab12.jpg") == gat.image_key("https://x.org/files/square/ab12.jpg")
assert gat.image_key("/s/files/original/ab12.png") == gat.image_key("/s/files/medium/ab12.jpg")
assert gat.image_key("https://x.org/files/large/ab12.jpg") != gat.image_key("https://x.org/files/large/cd34.jpg")
assert gat.image_key("/s/img/large/ab12.jpg") == "/s/img/large/ab12.jpg"   # not Omeka: untouched

assert gat.largest_derivative("https://x.org/files/square/ab12.jpg") == "https://x.org/files/large/ab12.jpg"
assert gat.largest_derivative("/s/files/square_thumbnails/ab12.jpg") == "/s/files/fullsize/ab12.jpg"
assert gat.largest_derivative("/s/img/square/ab12.jpg") == "/s/img/square/ab12.jpg"
not_desc = "I'm not able to view the image you intended to attach—it looks like text content came through instead."
assert gat.NOT_A_DESCRIPTION_RE.search(not_desc)
assert not gat.NOT_A_DESCRIPTION_RE.search('A sign reading "Please wear a mask, I\'m vaccinated" taped to a synagogue door.')

assert gat.new_alt({"reason": "short", "alt": "Map of Paris"}, "Red dots mark bridges.") == "Map of Paris. Red dots mark bridges."
assert gat.new_alt({"reason": "filename", "alt": "x.jpg"}, "A chart.") == "A chart."

assert gat.clean('"A map of Paris"\n') == "A map of Paris."
assert gat.clean("**Alt text:** Two graphs") == "Two graphs."

assert gat.patched_tag('<img src="a.png" alt="a.png" class="c">', "html", "A cast.") == '<img src="a.png" alt="A cast." class="c">'
assert gat.patched_tag('<img src="a.png" />', "html", "A cast.") == '<img src="a.png" alt="A cast."/>'
assert gat.patched_tag('<img src="a.png">', "html", 'Say "hi"') == '<img src="a.png" alt="Say &quot;hi&quot;">'
assert gat.patched_tag("![](a.png)", "markdown", "A cast.") == "![A cast.](a.png)"
assert gat.patched_tag('![](a.png "Cast")', "markdown", "A cast.") == '![A cast.](a.png "Cast")'   # title kept
assert gat.patched_tag('<img data-alt="x" src="a.png">', "html", "A cast.") == '<img data-alt="x" src="a.png" alt="A cast.">'

with tempfile.TemporaryDirectory() as tmp:
    site = Path(tmp)
    (site / "files").mkdir()
    (site / "files" / "x.png").write_bytes(b"png")
    (site / "items").mkdir()
    page = site / "items" / "1.html"
    page.write_text('<img src="../files/x.png" alt="">\n<img src="/files/x.png" alt="x.png">\n'
                    '<img src="/files/missing.png" alt="">\n<img src="/files/x.png" alt="A fine cast.">\n'
                    "<img src=\"'+d.thumb+'\" alt=\"'+d.title+'\">\n"
                    '<img src="&#x2F;files&#x2F;x.png" alt="">')   # Omeka S entity-encodes src
    (site / "node_modules").mkdir()
    (site / "node_modules" / "skip.html").write_text('<img src="x.png">')
    entries = gat.find_weak(site, strict=False)
    assert [e["reason"] for e in entries] == ["missing", "filename", "missing", "missing"], entries
    assert entries[3]["img_ref"] == "/files/x.png"
    assert gat.resolve_image_path(site, page, "../files/x.png") == site / "files" / "x.png"
    assert gat.resolve_image_path(site, page, "/files/x.png?v=2") == site / "files" / "x.png"
    assert gat.resolve_image_path(site, page, "/files/missing.png") is None
    assert gat.resolve_image_path(site, page, "'+d.thumb+'") is None
    assert gat.resolve_image_path(site, page, "/files/missing.png", "https://x.org/") == "https://x.org/files/missing.png"
    assert gat.resolve_image_path(site, page, "../files/missing.png", "https://x.org") == "https://x.org/files/missing.png"
    assert gat.resolve_image_path(site, page, "../../outside.png", "https://x.org") is None
    assert gat.resolve_image_path(site, page, "/files/x.png", "https://x.org") == site / "files" / "x.png"
    req = gat.openai_request(site / "files" / "x.png", "Describe.", "llava", "http://localhost:11434/v1/", "k")
    body = json.loads(req.data)
    assert req.full_url == "http://localhost:11434/v1/chat/completions"
    assert req.get_header("Authorization") == "Bearer k"
    assert body["model"] == "llava" and body["messages"][0]["content"][0]["text"] == "Describe."
    assert body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert gat.build_prompt("Look at the attached image.", "").startswith("Look at the attached image. Describe it")
    assert "Map of Paris" in gat.build_prompt("Read the image at /x.png.", "Map of Paris")
    content = gat.anthropic_content(site / "files" / "x.png", "Describe.")
    assert content[0]["source"] == {"type": "base64", "media_type": "image/png", "data": "cG5n"}
    assert content[1] == {"type": "text", "text": "Describe."}
    cache = site / "cache"; cache.mkdir()
    gat.urllib.request.urlopen = lambda url, timeout: __import__("io").BytesIO(url.encode())  # no network
    a, b = gat.fetch("https://x.org/a/thumb.jpg", cache), gat.fetch("https://x.org/b/thumb.jpg", cache)
    assert a != b and a.suffix == ".jpg" and a.read_bytes().endswith(b"/a/thumb.jpg")
    sq = site / "files" / "square"; sq.mkdir(parents=True); (sq / "p.jpg").write_bytes(b"s")
    assert gat.load(sq / "p.jpg", cache) == (sq / "p.jpg", str(sq / "p.jpg"))      # no large copy on disk
    (site / "files" / "large").mkdir(); (site / "files" / "large" / "p.jpg").write_bytes(b"l")
    assert gat.load(sq / "p.jpg", cache)[0] == site / "files" / "large" / "p.jpg"
    png = cache / "default.png%3Fv=3.1.0"; png.write_bytes(b"\x89PNG\r\n\x1a\n....")
    assert gat.image_mime(png) == "image/png"
    def boom(url, timeout): raise OSError("404")
    gat.urllib.request.urlopen = boom
    try:
        gat.fetch("https://x.org/gone.jpg", cache); raise AssertionError("fetch should raise")
    except gat.ImageFailed as exc:
        assert "gone.jpg" in str(exc) and "404" in str(exc)
    seen = []
    gat.fetch = lambda url, d: seen.append(url) or (_ for _ in ()).throw(gat.ImageFailed("404")) if "/large/" in url else Path(url)
    assert gat.load("https://x.org/files/square/q.jpg", cache) == (Path("https://x.org/files/square/q.jpg"), "https://x.org/files/square/q.jpg")
    assert seen == ["https://x.org/files/large/q.jpg"]                              # tried large first, fell back
    log = site / "logs" / "runs.jsonl"
    gat.write_log(log, status="ok", alt="A cast.")
    gat.write_log(log, status="error", error="404")
    assert [json.loads(line)["status"] for line in log.read_text().splitlines()] == ["ok", "error"]
    gat.patch(entries[0], "A cast.")
    assert page.read_text().startswith('<img src="../files/x.png" alt="A cast.">')
print("ok")
