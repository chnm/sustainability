"""Self-check for the alt-text scanner. Run: python utils/alt-text/test_generate_alt_text.py"""
import importlib.util
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

assert gat.new_alt({"reason": "short", "alt": "Map of Paris"}, "Red dots mark bridges.") == "Map of Paris. Red dots mark bridges."
assert gat.new_alt({"reason": "filename", "alt": "x.jpg"}, "A chart.") == "A chart."

assert gat.clean('"A map of Paris"\n') == "A map of Paris."
assert gat.clean("**Alt text:** Two graphs") == "Two graphs."

assert gat.patched_tag('<img src="a.png" alt="a.png" class="c">', "html", "a.png", "A cast.") == '<img src="a.png" alt="A cast." class="c">'
assert gat.patched_tag('<img src="a.png" />', "html", "a.png", "A cast.") == '<img src="a.png" alt="A cast."/>'
assert gat.patched_tag('<img src="a.png">', "html", "a.png", 'Say "hi"') == '<img src="a.png" alt="Say &quot;hi&quot;">'
assert gat.patched_tag("![](a.png)", "markdown", "a.png", "A cast.") == "![A cast.](a.png)"

with tempfile.TemporaryDirectory() as tmp:
    site = Path(tmp)
    (site / "files").mkdir()
    (site / "files" / "x.png").write_bytes(b"png")
    (site / "items").mkdir()
    page = site / "items" / "1.html"
    page.write_text('<img src="../files/x.png" alt="">\n<img src="/files/x.png" alt="x.png">\n'
                    '<img src="/files/missing.png" alt="">\n<img src="/files/x.png" alt="A fine cast.">\n'
                    "<img src=\"'+d.thumb+'\" alt=\"'+d.title+'\">")
    (site / "node_modules").mkdir()
    (site / "node_modules" / "skip.html").write_text('<img src="x.png">')
    entries = gat.find_weak(site, strict=False)
    assert [e["reason"] for e in entries] == ["missing", "filename", "missing"], entries
    assert gat.resolve_image_path(site, page, "../files/x.png") == site / "files" / "x.png"
    assert gat.resolve_image_path(site, page, "/files/x.png?v=2") == site / "files" / "x.png"
    assert gat.resolve_image_path(site, page, "/files/missing.png") is None
    assert gat.resolve_image_path(site, page, "'+d.thumb+'") is None
    assert gat.resolve_image_path(site, page, "/files/missing.png", "https://x.org/") == "https://x.org/files/missing.png"
    assert gat.resolve_image_path(site, page, "../files/missing.png", "https://x.org") == "https://x.org/files/missing.png"
    assert gat.resolve_image_path(site, page, "../../outside.png", "https://x.org") is None
    assert gat.resolve_image_path(site, page, "/files/x.png", "https://x.org") == site / "files" / "x.png"
    gat.patch(entries[0], "A cast.")
    assert page.read_text().startswith('<img src="../files/x.png" alt="A cast.">')
print("ok")
