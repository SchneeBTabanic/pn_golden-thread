#!/usr/bin/env python3
"""url: / search: / html: place whole or refuse. No page picker."""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import web  # noqa: E402
import run as runmod  # noqa: E402
import turn_record  # noqa: E402


def run():
    fails = []
    # parsers
    u, q = web.parse_url_prefix("url: https://example.org/a page?")
    if u != "https://example.org/a" or q != "page?":
        fails.append("url: split drifted: " + repr((u, q)))
    u, q = web.parse_url_prefix("fetch: https://example.org/a")
    if u != "https://example.org/a" or q != "":
        fails.append("fetch: split drifted: " + repr((u, q)))
    u, q = web.parse_url_prefix("hello")
    if u is not None:
        fails.append("bare line was parsed as url")
    s, q = web.parse_search_prefix("search: current debian")
    if s != "current debian" or q != "current debian":
        fails.append("search: split drifted: " + repr((s, q)))
    s, q = web.parse_search_prefix("search:")
    if s != "":
        fails.append("empty search not empty")
    h, q = web.parse_html_prefix("html: /tmp/x.html what")
    if h != "/tmp/x.html" or q != "what":
        fails.append("html: split drifted: " + repr((h, q)))

    empty = web.fetch_placed("")
    if empty.ok or "no url" not in empty.refused:
        fails.append("empty url was accepted: " + repr(empty))
    noturl = web.fetch_placed("just-a-path")
    if noturl.ok or "not a url" not in noturl.refused:
        fails.append("path-without-scheme was fetched: " + repr(noturl))

    noq = web.list_hits("")
    if noq.ok or "no query" not in noq.refused:
        fails.append("empty search was accepted")

    # monkeypatch: no network. A picker that auto-fetches the first hit must not exist.
    src = open(os.path.join(HERE, "web.py"), encoding="utf-8").read()
    if "SKIP_DOMAINS" in src:
        fails.append("web.py imported a domain skip-list")
    if "search_and_fetch" in src:
        fails.append("web.py grew search_and_fetch auto-pick")

    # Playwright is the JS-at-the-edge fetch, not a ranker. Static success
    # must not launch it. Static husk must name it.
    called = []

    def fake_bytes(url):
        if "husk" in url:
            return b"<html><body><div id=app></div></body></html>", "text/html", ""
        return b"<html><body><p>" + (b"word " * 40) + b"</p></body></html>", "text/html", ""

    def fake_reduce(blob, name="", prefer="auto"):
        raw = blob.decode("utf-8", errors="replace")
        if "word " in raw:
            return "word " * 40, "trafilatura main-text, not the full page"
        return None, "no extractable main text"

    def fake_dom(url):
        called.append(url)
        return (
            "<html><body><p>" + ("rendered " * 40) + "</p></body></html>",
            "",
        )

    def fake_html_main(html_text):
        if "rendered " in (html_text or ""):
            return "rendered " * 40, "trafilatura main-text, not the full page"
        return None, "no extractable main text"

    st = __import__("strip")
    real_bytes, real_dom = st.fetch_bytes, st.fetch_dom
    real_reduce, real_main = st.reduce_blob, st.reduce_html_maintext
    st.fetch_bytes = fake_bytes
    st.fetch_dom = fake_dom
    st.reduce_blob = fake_reduce
    st.reduce_html_maintext = fake_html_main
    try:
        got = web.fetch_placed("https://example.org/full")
        if not got.ok:
            fails.append("static html failed: " + repr(got.refused))
        elif called:
            fails.append("browser ran on a page the mailed HTML already placed")
        elif "trafilatura" not in (got.reduction or ""):
            fails.append("static reduction unnamed: " + repr(got.reduction))
        called[:] = []
        husk = web.fetch_placed("https://example.org/husk")
        if not husk.ok:
            fails.append("husk did not fall through to the browser: "
                         + repr(husk.refused))
        elif not called:
            fails.append("husk never asked the browser")
        elif "playwright" not in (husk.reduction or ""):
            fails.append("browser reduction unnamed: " + repr(husk.reduction))
        elif "rendered" not in husk.content:
            fails.append("browser DOM was not what got placed")
        called[:] = []
        old = os.environ.get("GT_EDGE_BROWSER")
        os.environ["GT_EDGE_BROWSER"] = "0"
        try:
            off = web.fetch_placed("https://example.org/husk")
            if called:
                fails.append("GT_EDGE_BROWSER=0 still launched")
            if off.ok:
                fails.append("husk with browser off was worn as success")
            elif "GT_EDGE_BROWSER=0" not in (off.refused or ""):
                fails.append("browser-off refuse unnamed: " + repr(off.refused))
        finally:
            if old is None:
                os.environ.pop("GT_EDGE_BROWSER", None)
            else:
                os.environ["GT_EDGE_BROWSER"] = old
    finally:
        st.fetch_bytes = real_bytes
        st.fetch_dom = real_dom
        st.reduce_blob = real_reduce
        st.reduce_html_maintext = real_main
    strip_src = open(os.path.join(HERE, "strip.py"), encoding="utf-8").read()
    if "search_and_fetch" in strip_src:
        fails.append("strip.py grew search_and_fetch")
    if "VERIFIED DATA" in src:
        fails.append("web.py injects VERIFIED DATA")
    if "def search(" in src:
        fails.append("web.py defines search() — that name is a selector")

    # list_hits: exception is named, not []
    def boom(*a, **k):
        raise RuntimeError("rate-limit-test")

    class BoomDDGS:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def text(self, *a, **k):
            raise RuntimeError("rate-limit-test")

    real_borrow = web._borrow_site
    web._borrow_site = lambda: None
    sys.modules.pop("ddgs", None)
    # inject a fake ddgs
    import types
    fake = types.ModuleType("ddgs")
    fake.DDGS = lambda *a, **k: BoomDDGS()
    sys.modules["ddgs"] = fake
    try:
        got = web.list_hits("debian")
        if got.ok:
            fails.append("failed search was worn as success")
        if "rate-limit-test" not in (got.refused or ""):
            fails.append("search exception was silent: " + repr(got.refused))
    finally:
        web._borrow_site = real_borrow
        sys.modules.pop("ddgs", None)

    # html: missing file refuses
    missing = web.html_placed("/no/such/gt-html.html")
    if missing.ok or "does not exist" not in missing.refused:
        fails.append("missing html was placed: " + repr(missing))

    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "page.html")
        with open(raw, "w", encoding="utf-8") as f:
            f.write("<html><body><p>Hello saved page.</p></body></html>\n")
        if not web.shutil_which_pandoc():
            got = web.html_placed(raw)
            if got.ok:
                fails.append("html placed without pandoc")
            elif "pandoc" not in got.refused:
                fails.append("html without pandoc: " + repr(got.refused))
        else:
            got = web.html_placed(raw)
            if not got.ok:
                fails.append("html with pandoc refused: " + repr(got))
            elif "Hello saved page" not in got.content:
                fails.append("html lost body: " + repr(got.content[:200]))
            elif "pandoc" not in got.reduction:
                fails.append("html reduction unnamed")

    # mouths exist
    for k in ("fetch", "search", "html", "refuse-fetch", "refuse-search",
              "refuse-html"):
        try:
            turn_record.known_mouth(k)
        except Exception as e:
            fails.append("mouth " + k + " missing: " + str(e))

    # HELP names the sigils; run.py still says nothing is chosen for you
    src = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "url:" not in runmod.HELP and "url:" not in src:
        fails.append("run.py HELP missing url:")
    if "search:" not in runmod.HELP:
        fails.append("run.py HELP missing search:")
    src_run = open(os.path.join(HERE, "run.py"), encoding="utf-8").read()
    if "def _window_refuse(" not in src_run:
        fails.append("run.py must refuse a prompt that will not fit n_ctx")
    if "n_ctx" not in src_run.split("def _window_refuse(", 1)[1][:800]:
        fails.append("_window_refuse must look at the face n_ctx")
    src_model = open(os.path.join(HERE, "model.py"), encoding="utf-8").read()
    http = src_model.split("def _http_json(", 1)[1].split("def _ollama_up(", 1)[0]
    if "HTTPError" not in http:
        fails.append("_http_json must name the HTTP body on 400, not only Bad Request")
    if "Nothing is searched or chosen for you" not in src:
        fails.append("file: sentence that nothing is chosen was lost")

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — url/search/html place or refuse; no page picker")
    return 0


if __name__ == "__main__":
    sys.exit(run())
