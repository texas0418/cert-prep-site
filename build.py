#!/usr/bin/env python3
"""Build the CertPrep Practice site: one page per exam, free sample questions, pack CTA.

Output goes to dist/ and deploys to simonbuilds.app/certprep/.
Pages carry noindex until Simon says go; flip with --live.
"""
import json, html, os, random, pathlib, sys, shutil, datetime
from questions import API_BANK, NDT_DIR, N_FREE, shuffled, sample

ROOT   = pathlib.Path(__file__).parent
DIST   = ROOT / "dist"
LIVE   = "--live" in sys.argv
CFG    = json.load(open(ROOT / "exams.json"))
BASE   = CFG["site"]["base"].rstrip("/")
CSS    = open(ROOT / "css.txt").read()
JS     = open(ROOT / "js.txt").read()
API_APP = "https://apps.apple.com/us/app/api-inspector-cert-prep/id6785875538"
NDT_APP = "https://apps.apple.com/us/app/ndt-cert-study/id6785204471"
APP_IDS = {"api": "6785875538", "ndt": "6785204471"}
APP_URLS = {"api": API_APP, "ndt": NDT_APP}
e = html.escape

# ---------- markup ----------

def render_q(i, q):
    opts = "".join(f'<button class="opt" data-i="{j}">{e(o)}</button>'
                   for j, o in enumerate(q["options"]))
    why = [f"<b>{'ABCD'[j]}</b> {e(t)}" for j, t in enumerate(q.get("distractors") or [])
           if t and j != q["answer"]]
    whyhtml = f'<div class="ref">Why the others are wrong. {" · ".join(why)}</div>' if why else ""
    ref = f'<div class="ref">Reference: {e(q["ref"])}</div>' if q.get("ref") else ""
    return f"""
<div class="q" data-answer="{q['answer']}">
  <div class="tag">Question {i}{' · ' + e(q['topic']) if q.get('topic') else ''}</div>
  <h3>{e(q['stem'])}</h3>
  {opts}
  <div class="expl"><b>Answer:</b> {e(q['options'][q['answer']])}<br>{e(q['explanation'])}{ref}{whyhtml}</div>
</div>"""

def quiz_jsonld(name, url, qs):
    return json.dumps({
        "@context": "https://schema.org/", "@type": "Quiz", "name": name, "url": url,
        # Google's practice-problem spec requires the question in "text" (GSC 2026-09-10
        # flagged "Missing field text (in hasPart)" as a critical error when it was only in
        # "name"), and recommends encodingFormat on each answer.
        "hasPart": [{"@type": "Question", "eduQuestionType": "Multiple choice",
                     "learningResourceType": "Practice problem",
                     "name": q["stem"], "text": q["stem"],
                     "suggestedAnswer": [{"@type": "Answer", "text": o, "encodingFormat": "text/plain"}
                                         for i, o in enumerate(q["options"]) if i != q["answer"]],
                     "acceptedAnswer": {"@type": "Answer", "text": q["options"][q["answer"]],
                                        "encodingFormat": "text/plain"}}
                    for q in qs[:10]]})

def nav_links(current):
    out = []
    for x in CFG["exams"][:6]:
        cls = ' class="here"' if x["slug"] == current else ""
        out.append(f'<a href="{BASE}/{x["slug"]}/"{cls}>{e(x["short"])}</a>')
    out.append(f'<a href="{BASE}/all-exams/">All exams</a>')
    return "".join(out)

def shell(title, desc, path, app, body, extra=""):
    robots = "index,follow" if LIVE else "noindex,nofollow"
    itunes = f'<meta name="apple-itunes-app" content="app-id={APP_IDS[app]}">' if app else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{BASE}{path}">
<meta name="google-site-verification" content="{CFG['site']['verification']}">
{itunes}
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<style>{CSS}
nav a.here{{color:var(--ink);font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;margin:22px 0}}
.grid a{{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:16px 18px;text-decoration:none;color:var(--ink)}}
.grid a:hover{{border-color:var(--accent)}}
.grid b{{display:block;font-size:17px;margin-bottom:3px}}
.grid span{{color:var(--muted);font-size:14px}}
.disclose{{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:10px;padding:16px 18px;margin:26px 0;font-size:15px;color:var(--muted)}}
.disclose b{{color:var(--ink)}}
</style>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="{BASE}/">Cert<span>Prep</span> Practice</a>
  <nav>{nav_links(path.strip('/'))}</nav>
</div></header>
{body}
<footer><div class="wrap">
  <p><b>Independent study aids.</b> Not affiliated with, endorsed by, or connected to the American
  Petroleum Institute, ASNT, or ASME. Nothing here is copied from any examination and no code or
  standard text is reproduced. Always confirm current requirements with the certifying body.</p>
  <p style="margin-top:8px">Written and reviewed by Simon Shih, twenty years in oil and gas.
  Questions? <a href="mailto:simon@simonbuilds.app">simon@simonbuilds.app</a></p>
  <p style="margin-top:8px">Free apps: <a href="{API_APP}">API Inspector Cert Prep</a> ·
  <a href="{NDT_APP}">NDT Cert Study</a></p>
</div></footer>
{extra}
<script>{JS}</script>
</body>
</html>"""

# ---------- pages ----------

def pdf_line(exam):
    """Secondary offer: the instant PDF, for pages that lead with the paperback.

    Not every paperback has a Gumroad twin; newer packs go straight to KDP.
    """
    if not exam.get("pack"):
        return ""
    return (f'<div class="badges">Want it now? The same pack as an '
            f'<a href="{exam["pack"]}">instant PDF download</a> '
            f'({e(exam["price"])}), with a 30-day no-questions refund.</div>')


def hero_cta(exam):
    """Top-of-page button. Same channel order as the mid-page CTA."""
    if exam.get("amazon"):
        return (f'<a class="cta" href="{exam["amazon"]}">Get all {exam["packq"]} '
                f'questions in paperback — {e(exam["amazon_price"])}</a>')
    if exam["pack"]:
        return (f'<a class="cta" href="{exam["pack"]}">Get all {exam["packq"]} '
                f'questions — {e(exam["price"])}</a>')
    return f'<a class="cta" href="{APP_URLS[exam["app"]]}">Practise free in the app</a>'


def cta(exam, heading, para):
    if exam.get("amazon"):
        return f"""<div class="midcta">
  <h2>{e(heading)}</h2><p>{para}</p>
  <a class="cta" href="{exam['amazon']}">Get the {e(exam['short'])} pack on Amazon — {e(exam['amazon_price'])}</a>
  <div class="badges">Paperback · {exam['packq']} questions · a worked solution for every one</div>
  {pdf_line(exam)}
</div>"""
    if exam["pack"]:
        return f"""<div class="midcta">
  <h2>{e(heading)}</h2><p>{para}</p>
  <a class="cta" href="{exam['pack']}">Get the {e(exam['short'])} pack — {e(exam['price'])}</a>
  <div class="badges">Instant PDF download · {exam['packq']} questions · 30-day no-questions refund</div>
</div>"""
    return f"""<div class="midcta">
  <h2>{e(heading)}</h2><p>{para}</p>
  <a class="cta" href="{APP_URLS[exam['app']]}">Practise free in the app</a>
  <div class="badges">The printable {e(exam['short'])} pack ({exam['packq']} questions) is finished.
  Email <a href="mailto:simon@simonbuilds.app?subject={e(exam['short'])}%20pack">simon@simonbuilds.app</a>
  and I will send you the link.</div>
</div>"""

DISCLOSE = """<div class="disclose">
<b>How these questions were made.</b> They were drafted with AI assistance and then reviewed and
corrected by me. I have spent twenty years in oil and gas: seven as an AUT technician, three as an
NDT project manager, and ten in quality assurance. They are original questions written in the style
of the exam. They are not real exam questions and nothing here is copied from one. I am not a
certified inspector myself, and I would rather say so than let you assume otherwise. What I have is
twenty years of writing and reviewing this work, and no patience for a practice question that
teaches you the wrong thing.
</div>"""

DIST.exists() and shutil.rmtree(DIST)
DIST.mkdir()
urls = []

for exam in CFG["exams"]:
    if exam.get("host"):
        continue  # published on its own host by the standalone build below
    qs = sample(exam)
    path = f"/{exam['slug']}/"
    half = len(qs) // 2
    body = f"""
<div class="hero"><div class="wrap">
<h1>{e(exam['h1'])}</h1>
<p class="lead">{e(exam['lead'])}</p>
{hero_cta(exam)}
<div class="badges">{N_FREE} questions free on this page · no sign-up · worked solutions</div>
</div></div>
<main><div class="wrap">
{''.join(render_q(i + 1, q) for i, q in enumerate(qs[:half]))}
{cta(exam, f"The other {exam['packq'] - N_FREE} questions", f"The full {e(exam['short'])} pack is {exam['packq']} questions with a worked solution for every one, grouped into topic sets so a weak area shows up as a cluster rather than a vague feeling.")}
{''.join(render_q(i + half + 1, q) for i, q in enumerate(qs[half:]))}
<div class="score"><div class="wrap"><b id="scoreline">Tap answers to track your score</b></div></div>
{DISCLOSE}
{cta(exam, "Ready for the full pack?", f"{exam['packq']} questions, every one with the arithmetic worked through or the governing clause named. Amazon handles the printing, the shipping and the returns.")}
</div></main>"""
    (DIST / exam["slug"]).mkdir(parents=True)
    (DIST / exam["slug"] / "index.html").write_text(shell(
        exam["title"], exam["desc"], path, exam["app"], body,
        f'<script type="application/ld+json">{quiz_jsonld(exam["h1"], BASE + path, qs)}</script>'))
    urls.append(path)

# index + all-exams
cards = "".join(
    f'<a href="{("https://" + x["host"]) if x.get("host") else (BASE + "/" + x["slug"])}/">'
    f'<b>{e(x["short"])}</b>'
    f'<span>{N_FREE} free questions · full pack {x["packq"]}</span></a>'
    for x in CFG["exams"])
home_body = f"""
<div class="hero"><div class="wrap">
<h1>Free practice questions for API and NDT certification exams</h1>
<p class="lead">Twenty-five free questions for each of fourteen exams, every one with the arithmetic
worked through or the governing clause named. No sign-up, no email wall, nothing to install.</p>
</div></div>
<main><div class="wrap">
<div class="grid">{cards}</div>
{DISCLOSE}
<h2 class="sec">Why these exist</h2>
<p>Most free practice questions for these exams are scanned photocopies of somebody's course
handout, with an answer letter and no explanation. That tells you whether you were right. It does
not tell you why, which is the only part that changes your score.</p>
<p>Every question here shows the working. On the NDT exams each wrong option also carries a note
saying which mistake leads there, because on a multiple-choice test the distractors are chosen to
catch a specific error, and recognising the error is worth more than recognising the answer.</p>
</div></main>"""
(DIST / "index.html").write_text(shell(
    "Free API & NDT Certification Practice Questions | CertPrep Practice",
    "Free practice questions for API 510, API 570, API 653 and ten ASNT exams: UT, MT, PT, RT and PAUT, Levels I and II. Worked solutions on every question. No sign-up.",
    "/", "", home_body))
urls.insert(0, "/")

(DIST / "all-exams").mkdir()
(DIST / "all-exams" / "index.html").write_text(shell(
    "All API and NDT Practice Exams | CertPrep Practice",
    "Every free practice exam on CertPrep: API 510, API 570, and ASNT UT, MT, PT, RT and PAUT at Levels I and II.",
    "/all-exams/", "", f'<div class="hero"><div class="wrap"><h1>All exams</h1>'
    f'<p class="lead">Fourteen exams, {N_FREE} free questions each.</p></div></div>'
    f'<main><div class="wrap"><div class="grid">{cards}</div></div></main>'))
urls.append("/all-exams/")

today = datetime.date.today().isoformat()
(DIST / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{BASE}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    + "</urlset>\n")
(DIST / "robots.txt").write_text(
    ("User-agent: *\nAllow: /\n\nSitemap: " + BASE + "/sitemap.xml\n") if LIVE
    else "User-agent: *\nDisallow: /\n")
(DIST / CFG["site"]["verification"].join(["google", ".html"])).write_text(
    "google-site-verification: google" + CFG["site"]["verification"] + ".html")

print(f"{'LIVE' if LIVE else 'STAGED (noindex)'} — {len(urls)} pages")
for u in urls: print("  ", BASE + u)


# ---------- tell IndexNow (Bing, Yandex, Seznam) on every live build ----------
if LIVE:
    import urllib.request, urllib.error
    key = (ROOT / "indexnow_key.txt").read_text().strip()
    body = json.dumps({"host": "simonbuilds.app", "key": key,
                       "keyLocation": f"https://simonbuilds.app/{key}.txt",
                       "urlList": [BASE + u for u in urls]}).encode()
    try:
        req = urllib.request.Request("https://api.indexnow.org/IndexNow", data=body,
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        print("IndexNow:", urllib.request.urlopen(req, timeout=45).status)
    except urllib.error.HTTPError as ex:
        print("IndexNow:", ex.code)
    except Exception as ex:
        print("IndexNow failed (not fatal):", ex)

# ---------- standalone subdomain build ----------
# The loop above publishes every exam as a page under /certprep/. A book that
# gets its own host needs the same page emitted as a site in its own right, so
# the canonical points at the host serving it rather than at a copy elsewhere.
# Run: SUBDOMAIN_SLUG=<slug> SUBDOMAIN_HOST=<host> python3 build.py [--live]
SUB_SLUG = os.environ.get("SUBDOMAIN_SLUG")
if SUB_SLUG:
    SUB_HOST = os.environ["SUBDOMAIN_HOST"]
    exam = next(x for x in CFG["exams"] if x["slug"] == SUB_SLUG)
    BASE = f"https://{SUB_HOST}"
    CERTPREP = "https://simonbuilds.app/certprep"

    def nav_links(current):  # noqa: F811 - one host, one page, so the nav points home
        return f'<a href="{CERTPREP}/all-exams/">All the other packs</a>'

    qs = sample(exam)
    half = len(qs) // 2
    body = f"""
<div class="hero"><div class="wrap">
<h1>{e(exam['h1'])}</h1>
<p class="lead">{e(exam['lead'])}</p>
{hero_cta(exam)}
<div class="badges">{N_FREE} questions free on this page · no sign-up · worked solutions</div>
</div></div>
<main><div class="wrap">
{''.join(render_q(i + 1, q) for i, q in enumerate(qs[:half]))}
{cta(exam, f"The other {exam['packq'] - N_FREE} questions", f"The full {e(exam['short'])} pack is {exam['packq']} questions with a worked solution for every one, grouped into topic sets so a weak area shows up as a cluster rather than a vague feeling.")}
{''.join(render_q(i + half + 1, q) for i, q in enumerate(qs[half:]))}
<div class="score"><div class="wrap"><b id="scoreline">Tap answers to track your score</b></div></div>
{DISCLOSE}
{cta(exam, "Ready for the full pack?", f"{exam['packq']} questions, every one with the arithmetic worked through or the governing clause named. Amazon handles the printing, the shipping and the returns.")}
<div class="disclose"><b>Doing a method exam too?</b> The method packs, UT, MT, PT, RT and PAUT at
both levels, are separate books and live over at
<a href="{CERTPREP}/all-exams/">CertPrep Practice</a>. This one is the scheme and the standards;
it does not repeat method fundamentals.</div>
</div></main>"""

    SUBDIST = ROOT / f"dist-{SUB_SLUG}"
    SUBDIST.exists() and shutil.rmtree(SUBDIST)
    SUBDIST.mkdir()
    (SUBDIST / "index.html").write_text(shell(exam["title"], exam["desc"], "/", exam["app"], body))
    (SUBDIST / "robots.txt").write_text(
        (f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n") if LIVE
        else "User-agent: *\nDisallow: /\n")
    (SUBDIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"<url><loc>{BASE}/</loc></url>\n</urlset>\n")
    print(f"standalone: {SUB_HOST} -> dist-{SUB_SLUG}/ ({'LIVE' if LIVE else 'noindex'})")
