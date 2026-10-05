#!/usr/bin/env python3
"""Build the printable magnet: the SAME 25 free questions each exam page shows,
laid out for paper, with the worked solutions at the back.

Why this exists: the 25 questions are already free and ungated on the page, so a PDF
of "free questions" is only worth an email address because of the FORMAT. People
sitting an inspection exam study on paper, which is also why they buy the paperback.
So the magnet is a format shift, not new content, and it is honest about that.

Questions come from questions.py, the same module build.py uses, so the PDF can never
drift from the page. Output: magnets/<slug>-25-free.pdf

Usage: python3 build_magnet.py            # all 14
       python3 build_magnet.py api-510-practice-questions   # one
PDF engine is headless Chrome, the same one the paid packs use. Nothing to install.
"""
import json, html, pathlib, subprocess, sys, datetime
from questions import sample, N_FREE

ROOT = pathlib.Path(__file__).parent
OUT  = ROOT / "magnets"
CFG  = json.load(open(ROOT / "exams.json"))
SITE = CFG["site"]["base"].rstrip("/")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LETTERS = "ABCDEFGH"
e = html.escape

CSS = """
@page { size: letter; margin: 0.75in 0.7in 0.6in 0.7in; }
* { box-sizing: border-box; }
body { font: 11.5pt/1.5 Georgia, "Times New Roman", serif; color: #14181d; margin: 0; }
h1 { font: 700 21pt/1.2 Georgia, serif; margin: 0 0 2pt; }
h2 { font: 700 14pt/1.3 Georgia, serif; margin: 22pt 0 8pt; padding-bottom: 4pt;
     border-bottom: 1.5pt solid #14181d; break-after: avoid; }
.sub { font-size: 12pt; color: #4a5560; margin: 0 0 14pt; }
.rule { border: 0; border-top: 2.5pt solid #14181d; margin: 0 0 16pt; }
.howto { background: #f2f0ea; border-left: 3pt solid #8a7a52; padding: 9pt 11pt;
         font-size: 10.5pt; margin: 0 0 16pt; }
.q { break-inside: avoid; margin: 0 0 13pt; }
.stem { margin: 0 0 5pt; }
.n { font-weight: 700; }
.topic { font-size: 8.5pt; letter-spacing: .06em; text-transform: uppercase;
         color: #6b7681; margin: 0 0 3pt; }
ol.opts { list-style: none; margin: 0; padding: 0 0 0 16pt; }
ol.opts li { margin: 0 0 2pt; }
ol.opts li b { display: inline-block; width: 15pt; }
.sol { break-inside: avoid; margin: 0 0 11pt; font-size: 10.5pt; }
.sol .ans { font-weight: 700; }
.ref { color: #6b7681; font-style: italic; }
.cta { break-inside: avoid; margin: 20pt 0 0; padding: 11pt 13pt;
       border: 2pt solid #14181d; background: #f7f6f2; }
.cta b { font-size: 12.5pt; }
.foot { margin-top: 16pt; padding-top: 7pt; border-top: 1pt solid #c9ccd1;
        font-size: 8.5pt; color: #6b7681; }
.pb { break-before: page; }
"""


def pack_line(x):
    """Same channel priority the site uses: Amazon first, then Gumroad."""
    if x.get("amazon"):
        return (f'<b>The other {x["packq"] - N_FREE} questions.</b><br>'
                f'The full {e(x["short"])} pack is all {x["packq"]} questions, every one with a '
                f'worked solution, as a paperback on Amazon for {e(x["amazon_price"])}. '
                f'Amazon handles the printing, the shipping and the returns.<br>'
                f'<span class="ref">{e(x["amazon"])}</span>')
    if x.get("pack") and x.get("price"):
        return (f'<b>The other {x["packq"] - N_FREE} questions.</b><br>'
                f'The full {e(x["short"])} pack is {x["packq"]} questions as a PDF for '
                f'{e(x["price"])}.<br><span class="ref">{e(x["pack"])}</span>')
    return (f'<b>The other {x["packq"] - N_FREE} questions.</b><br>'
            f'The full {e(x["short"])} pack has all {x["packq"]}. '
            f'<span class="ref">{SITE}/{x["slug"]}/</span>')


def build(x):
    qs = sample(x)
    page_url = f'{SITE}/{x["slug"]}/'

    questions = "".join(
        f'<div class="q">'
        + (f'<div class="topic">{e(q["topic"])}</div>' if q.get("topic") else "")
        + f'<p class="stem"><span class="n">{i}.</span> {e(q["stem"])}</p>'
        + '<ol class="opts">'
        + "".join(f'<li><b>{LETTERS[j]}</b>{e(o)}</li>' for j, o in enumerate(q["options"]))
        + "</ol></div>"
        for i, q in enumerate(qs, 1))

    solutions = "".join(
        f'<div class="sol"><span class="ans">{i}. {LETTERS[q["answer"]]}</span> '
        f'{e(q["explanation"])}'
        + (f' <span class="ref">{e(q["ref"])}</span>' if q.get("ref") else "")
        + "</div>"
        for i, q in enumerate(qs, 1))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{e(x["short"])} - {N_FREE} Free Practice Questions</title>
<style>{CSS}</style></head><body>
<h1>{e(x["short"])}: {N_FREE} Practice Questions</h1>
<p class="sub">{e(x["sub"])} · printable edition with worked solutions</p>
<hr class="rule">
<div class="howto">These are the same {N_FREE} questions as
{e(page_url)}, laid out for paper. Answers and worked solutions start on the
last pages, so nothing is given away while you work. Options are shuffled, so the
answer is not in a predictable position.</div>
<h2>Questions</h2>
{questions}
<div class="pb"></div>
<h2>Answers and worked solutions</h2>
{solutions}
<div class="cta">{pack_line(x)}</div>
<div class="foot">CertPrep Practice · {e(SITE)} · not affiliated with, endorsed by or
licensed by API, ASNT, ISO or any certifying body. Practice questions only.</div>
</body></html>"""

    OUT.mkdir(exist_ok=True)
    tmp = OUT / f'{x["slug"]}-25-free.html'
    pdf = OUT / f'{x["slug"]}-25-free.pdf'
    tmp.write_text(doc)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + str(tmp.resolve())],
                   check=True, capture_output=True)
    tmp.unlink()
    return pdf, len(qs)


if __name__ == "__main__":
    want = sys.argv[1:]
    todo = [x for x in CFG["exams"] if not want or x["slug"] in want]
    if not todo:
        sys.exit(f"no exam matched {want}")
    for x in todo:
        pdf, n = build(x)
        print(f'{x["short"]:<14} {n:>2} questions -> {pdf.name} '
              f'({pdf.stat().st_size // 1024} KB)')
