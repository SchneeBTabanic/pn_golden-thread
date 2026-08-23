#!/usr/bin/env python3
"""PDF / docx / HTML reduce at the boundary. Named, not ranked."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import file_read  # noqa: E402
import strip  # noqa: E402


TINY_PDF = b"""%PDF-1.1
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 20 150 Td (Hello strip) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000359 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
447
%%EOF
"""


def run():
    fails = []
    if strip.sniff(b"%PDF-1.4....") != "pdf":
        fails.append("pdf magic missed")
    if strip.sniff(b"<html><body>x</body></html>") != "html":
        fails.append("html magic missed")
    if strip.sniff(b"PK\x03\x04....", name="note.docx") != "docx":
        fails.append("docx name missed")
    if strip.sniff(b"hello world") != "bytes":
        fails.append("plain text was sniffed as a container")

    with tempfile.TemporaryDirectory() as d:
        pdf = os.path.join(d, "a.pdf")
        with open(pdf, "wb") as f:
            f.write(TINY_PDF)
        got = file_read.read_placed(pdf)
        if not got.ok:
            fails.append("pdf refused: " + repr(got.refused))
        elif "Hello strip" not in got.content:
            fails.append("pdf lost text: " + repr(got.content[:200]))
        elif "pdftotext" not in (got.reduction or ""):
            fails.append("pdf reduction unnamed: " + repr(got.reduction))

        html = os.path.join(d, "a.html")
        with open(html, "w", encoding="utf-8") as f:
            f.write(
                "<html><body><p>Hello html.</p>"
                "<span aria-hidden=\"true\">ECHO-DUP</span></body></html>\n")
        got = file_read.read_placed(html)
        if not got.ok:
            fails.append("html refused: " + repr(got.refused))
        else:
            if "Hello html" not in got.content:
                fails.append("html lost text: " + repr(got.content[:200]))
            if "ECHO-DUP" in got.content:
                fails.append("aria-hidden echo leaked into the placed text")
            if "html" not in (got.reduction or "").lower() and "pandoc" not in (
                    got.reduction or "").lower():
                fails.append("html reduction unnamed: " + repr(got.reduction))

        if shutil_pandoc():
            src = os.path.join(d, "a.md")
            docx = os.path.join(d, "a.docx")
            with open(src, "w", encoding="utf-8") as f:
                f.write("Hello from a docx body.\n")
            proc = subprocess.run(
                ["pandoc", "-f", "markdown", "-t", "docx", "-o", docx, src],
                capture_output=True)
            if proc.returncode != 0:
                fails.append("could not mint a docx fixture")
            else:
                got = file_read.read_placed(docx)
                if not got.ok:
                    fails.append("docx refused: " + repr(got.refused))
                elif "Hello from a docx body" not in got.content:
                    fails.append("docx lost text: " + repr(got.content[:200]))
                elif "docx" not in (got.reduction or ""):
                    fails.append("docx reduction unnamed: " + repr(got.reduction))

        # unknown binary still refused
        raw = os.path.join(d, "x.bin")
        with open(raw, "wb") as f:
            f.write(b"ok\x00no")
        got = file_read.read_placed(raw)
        if got.ok or "NUL" not in got.refused:
            fails.append("unknown binary not refused: " + repr(got))

        # plain text still exact
        note = os.path.join(d, "note.txt")
        body = "hello from a placed file\nsecond line\n"
        with open(note, "w", encoding="utf-8") as f:
            f.write(body)
        got = file_read.read_placed(note)
        if not got.ok or got.content != body:
            fails.append("plain file drifted: " + repr(got))
        if got.reduction:
            fails.append("plain file grew a reduction: " + repr(got.reduction))

    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("PASS — pdf/html/docx reduce at the boundary; unknown binary refused")
    return 0


def shutil_pandoc():
    import shutil
    return shutil.which("pandoc")


if __name__ == "__main__":
    sys.exit(run())
