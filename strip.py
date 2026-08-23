"""
strip.py — reduce a named source to inert text at the placement boundary.

The human named a file or a URL. What crosses inward is text, or a named
refusal. HTML / PDF / docx / odt / epub are reduced by the doorway tools
Claude Code already proved (scribe capture_html, pdftotext, pandoc).
Unknown binary is still refused. Nothing is ranked. A lossy reduction is
named, never silent.

This is not Thermai-Pylai (that tree never shipped the edge). It is not
GTPS-Agent. Playwright is not a second stripper: it is the browser that
runs JavaScript at the edge so a JS-only page has a DOM to strip. The
strip itself is still scribe capture_html. Used only when the mailed HTML
placed nothing. GT_EDGE_BROWSER=0 turns that fetch off.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIBE_PY = os.environ.get(
    "GT_SCRIBE",
    os.path.normpath(os.path.join(HERE, "..", "pn_scribe-wb", "scribe.py")))
WEB_SITE = os.environ.get(
    "GT_WEB_SITE",
    "/home/schnee/vessel-env/lib/python3.13/site-packages")
SOURCE_MAX = int(os.environ.get("GT_SOURCE_MAX_BYTES", "8000000"))
MIN_EXTRACT = 50
FETCH_TIMEOUT = int(os.environ.get("GT_FETCH_TIMEOUT", "20"))


def _borrow_site():
    if WEB_SITE and os.path.isdir(WEB_SITE) and WEB_SITE not in sys.path:
        sys.path.insert(0, WEB_SITE)


def sniff(blob, name=""):
    """Name the container. Magic first, then the filename he typed."""
    b = blob[:8] if blob else b""
    lower = (name or "").lower()
    if b.startswith(b"%PDF"):
        return "pdf"
    if lower.endswith(".pdf"):
        return "pdf"
    if b.startswith(b"PK"):
        if lower.endswith(".docx"):
            return "docx"
        if lower.endswith(".odt"):
            return "odt"
        if lower.endswith(".epub"):
            return "epub"
        head = blob[:8192]
        if b"word/" in head:
            return "docx"
        if b"opendocument" in head:
            return "odt"
        if b"mimetype" in blob[:256] and b"epub" in blob[:256]:
            return "epub"
        return "zip"
    head = (blob[:256] if blob else b"").lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
        return "html"
    if lower.endswith(".html") or lower.endswith(".htm") or lower.endswith(".xhtml"):
        return "html"
    if lower.endswith(".docx"):
        return "docx"
    if lower.endswith(".odt"):
        return "odt"
    if lower.endswith(".epub"):
        return "epub"
    return "bytes"


def _which(name):
    import shutil
    return shutil.which(name)


def reduce_pdf(blob):
    if not _which("pdftotext"):
        return None, "pdftotext not on PATH — PDF reduction refused rather than guessed"
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        tmp.write(blob)
        tmp.close()
        proc = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", "-layout", tmp.name, "-"],
            capture_output=True)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        return None, "pdftotext failed" + ((" — " + err) if err else "")
    text = (proc.stdout or b"").decode("utf-8", errors="replace")
    text = text.replace("\x0c", "\n").strip()
    if not text:
        return None, "pdftotext produced no extractable text"
    return text, "pdftotext layout, not the PDF binary — layout may be lossy"


def reduce_office(blob, kind):
    if not _which("pandoc"):
        return None, "pandoc not on PATH — " + kind + " reduction refused rather than soup-scraped"
    ext = {"docx": ".docx", "odt": ".odt", "epub": ".epub"}.get(kind, ".bin")
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        tmp.write(blob)
        tmp.close()
        proc = subprocess.run(
            ["pandoc", "-f", kind, "-t", "gfm-raw_html", "--wrap=none", tmp.name],
            capture_output=True)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        return None, "pandoc failed on " + kind + ((" — " + err) if err else "")
    text = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
    if not text:
        return None, "pandoc produced empty markdown from " + kind
    return text, "pandoc gfm from " + kind + ", not the office binary"


def reduce_html(html_text):
    if not _which("pandoc"):
        return None, "pandoc not on PATH — HTML reduction refused rather than soup-scraped"
    scribe_dir = os.path.dirname(SCRIBE_PY)
    if scribe_dir not in sys.path:
        sys.path.insert(0, scribe_dir)
    import scribe
    try:
        body, annotations = scribe.capture_html(html_text)
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e)
    body = (body or "").strip()
    if not body:
        return None, "pandoc produced empty markdown from HTML"
    try:
        audited, findings = scribe.loss_check(body, annotations=annotations)
    except Exception:
        audited, findings = body, []
    n = len(findings or [])
    note = "scribe capture --html (aria-hidden stripped, pandoc gfm)"
    if n:
        note += "; " + str(n) + " loss marker(s) named in-band"
    return audited, note


def reduce_html_maintext(html_text):
    """trafilatura main-text. Small windows. Named, not a ranker."""
    _borrow_site()
    try:
        import trafilatura
    except ImportError:
        return None, "trafilatura not installed"
    try:
        text = trafilatura.extract(
            html_text, include_comments=False, include_tables=True) or ""
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e)
    text = text.strip()
    if len(text) < MIN_EXTRACT:
        return None, "no extractable main text"
    return text, "trafilatura main-text, not the full page"


def reduce_blob(blob, name="", prefer="auto"):
    """Return (text, reduction) or (None, refuse). prefer: auto|maintext|faithful."""
    kind = sniff(blob, name)
    if kind == "pdf":
        return reduce_pdf(blob)
    if kind in ("docx", "odt", "epub"):
        return reduce_office(blob, kind)
    if kind == "html":
        html = blob.decode("utf-8", errors="replace")
        if prefer == "faithful":
            return reduce_html(html)
        text, note = reduce_html_maintext(html)
        if text:
            return text, note
        # main-text failed: fall through to the faithful HTML path
        text, note = reduce_html(html)
        if text:
            return text, note
        return None, (note or "no extractable main text (pdf, empty, or script-only)")
    if kind == "zip":
        return None, "zip archive — name a .docx / .odt / .epub, or extract a file yourself"
    return None, None  # caller treats as ordinary bytes


def fetch_bytes(url):
    """One download. Returns (blob, content-type, refuse)."""
    import urllib.error
    import urllib.request
    target = (url or "").strip()
    if not target:
        return b"", "", "no url given"
    if "://" not in target:
        return b"", "", "not a url — name http(s)://…"
    req = urllib.request.Request(
        target,
        headers={"User-Agent": "golden-thread-place/1"},
        method="GET")
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
            blob = resp.read(SOURCE_MAX + 1)
    except Exception as e:
        return b"", "", type(e).__name__ + ": " + str(e)
    if len(blob) > SOURCE_MAX:
        return b"", ctype, (
            str(len(blob)) + " source bytes exceeds cap " + str(SOURCE_MAX)
            + ". Set GT_SOURCE_MAX_BYTES. Nothing was placed.")
    if not blob:
        return b"", ctype, "download returned empty"
    return blob, ctype, ""


def browser_wanted():
    """Fallback browser is on unless he turns it off. Not a second architecture."""
    return os.environ.get("GT_EDGE_BROWSER", "1") != "0"


def fetch_dom(url):
    """Ephemeral headless Chromium. JS runs here. Only an HTML string returns.

    Public pages, no profile, no login. The page is thrown away with the
    browser. Same wall as Thermai-Pylai, this scale.
    """
    target = (url or "").strip()
    if not target:
        return None, "no url given"
    if "://" not in target:
        return None, "not a url"
    if not browser_wanted():
        return None, "browser off (GT_EDGE_BROWSER=0)"
    _borrow_site()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "playwright not installed"
    timeout_ms = FETCH_TIMEOUT * 1000
    html = ""
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(target, timeout=timeout_ms, wait_until="load")
                html = page.content() or ""
            finally:
                browser.close()
    except Exception as e:
        return None, type(e).__name__ + ": " + str(e)
    if not html.strip():
        return None, "playwright returned empty DOM"
    return html, ""
