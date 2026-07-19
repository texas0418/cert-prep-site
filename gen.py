#!/usr/bin/env python3
"""Generate the static cert-prep landing site from sampled question JSON."""
import json, html, os, pathlib

ROOT = pathlib.Path(__file__).parent
API_URL = "https://apps.apple.com/us/app/api-inspector-cert-prep/id6785875538"
NDT_URL = "https://apps.apple.com/us/app/ndt-cert-study/id6785204471"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#1a2333;--muted:#5b6678;--line:#e3e7ee;--bg:#f7f9fc;--card:#ffffff;
--accent:#0b5fff;--accent-ink:#fff;--good:#0a7d33;--good-bg:#e9f7ee;--bad:#b3261e;--bad-bg:#fdeceb}
body{font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header.site{background:var(--card);border-bottom:1px solid var(--line);padding:14px 0}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px}
.brand{font-weight:700;text-decoration:none;color:var(--ink);font-size:17px}
.brand span{color:var(--accent)}
nav a{color:var(--muted);text-decoration:none;font-size:15px;margin-left:16px}
nav a:hover{color:var(--ink)}
.hero{padding:44px 0 28px}
h1{font-size:32px;line-height:1.25;letter-spacing:-.02em;margin-bottom:12px}
.hero p.lead{font-size:19px;color:var(--muted);max-width:56ch}
.cta{display:inline-block;background:var(--accent);color:var(--accent-ink);text-decoration:none;
font-weight:600;padding:12px 22px;border-radius:10px;margin-top:18px}
.cta.secondary{background:var(--card);color:var(--accent);border:1px solid var(--accent)}
.cta:hover{filter:brightness(1.08)}
.badges{margin-top:10px;color:var(--muted);font-size:14px}
main{padding-bottom:40px}
.q{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0}
.q .tag{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}
.q h3{font-size:18px;line-height:1.45;margin-bottom:14px;font-weight:600}
.opt{display:block;width:100%;text-align:left;font:inherit;background:var(--bg);color:var(--ink);
border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0;cursor:pointer}
.opt:hover{border-color:var(--accent)}
.q.done .opt{cursor:default;opacity:.85}
.opt.correct{background:var(--good-bg);border-color:var(--good);color:var(--good);font-weight:600;opacity:1}
.opt.wrong{background:var(--bad-bg);border-color:var(--bad);color:var(--bad);opacity:1}
.expl{display:none;margin-top:12px;padding:12px 14px;background:var(--bg);border-left:3px solid var(--accent);
border-radius:0 8px 8px 0;font-size:15.5px;color:var(--ink)}
.expl .ref{color:var(--muted);font-size:14px;margin-top:4px}
.q.done .expl{display:block}
.score{position:sticky;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 0;
margin-top:26px}
.score .wrap{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.score b{font-size:17px}
.midcta{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px;margin:26px 0;text-align:center}
.midcta h2{font-size:22px;margin-bottom:8px}
.midcta p{color:var(--muted);max-width:52ch;margin:0 auto}
h2.sec{font-size:24px;margin:36px 0 6px}
.faq{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:6px 22px;margin:14px 0}
.faq details{padding:14px 0;border-bottom:1px solid var(--line)}
.faq details:last-child{border-bottom:none}
.faq summary{font-weight:600;cursor:pointer}
.faq details p{margin-top:8px;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--muted);font-size:14px}
footer a{color:var(--muted)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:22px 0}
@media(max-width:640px){.cards{grid-template-columns:1fr}h1{font-size:26px}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;display:block;
text-decoration:none;color:var(--ink)}
.card:hover{border-color:var(--accent)}
.card h3{font-size:19px;margin-bottom:6px}
.card p{color:var(--muted);font-size:15.5px}
.card .go{color:var(--accent);font-weight:600;margin-top:10px;display:inline-block}
"""

JS = """
document.querySelectorAll('.q').forEach(function(q){
  q.querySelectorAll('.opt').forEach(function(btn){
    btn.addEventListener('click', function(){
      if(q.classList.contains('done')) return;
      q.classList.add('done');
      var ans = parseInt(q.dataset.answer,10);
      var opts = q.querySelectorAll('.opt');
      opts[ans].classList.add('correct');
      var picked = parseInt(btn.dataset.i,10);
      if(picked!==ans) btn.classList.add('wrong');
      window.__score = window.__score||{right:0,total:0};
      window.__score.total++; if(picked===ans) window.__score.right++;
      var el=document.getElementById('scoreline');
      if(el) el.textContent = window.__score.right+' / '+window.__score.total+' correct';
    });
  });
});
"""

def quiz_jsonld(name, url, questions):
    return json.dumps({
        "@context": "https://schema.org/", "@type": "Quiz", "name": name, "url": url,
        "hasPart": [{
            "@type": "Question", "eduQuestionType": "Multiple choice",
            "learningResourceType": "Practice problem",
            "name": q["stem"],
            "suggestedAnswer": [{"@type": "Answer", "text": o} for i, o in enumerate(q["options"]) if i != q["answer"]],
            "acceptedAnswer": {"@type": "Answer", "text": q["options"][q["answer"]]},
        } for q in questions[:10]]
    })

def render_question(i, q, show_ref=True):
    opts = "".join(
        f'<button class="opt" data-i="{j}">{html.escape(o)}</button>'
        for j, o in enumerate(q["options"]))
    ref = f'<div class="ref">Reference: {html.escape(q["ref"])}</div>' if show_ref and q.get("ref") else ""
    topic = html.escape(q.get("topic", "").replace("_", " "))
    return f"""
<div class="q" data-answer="{q['answer']}">
  <div class="tag">Question {i} · {topic}</div>
  <h3>{html.escape(q['stem'])}</h3>
  {opts}
  <div class="expl"><b>Answer:</b> {html.escape(q['options'][q['answer']])}<br>{html.escape(q['explanation'])}{ref}</div>
</div>"""

def page(title, desc, canonical_path, app_id, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://texas0418.github.io/cert-prep-site{canonical_path}">
<meta name="google-site-verification" content="YW7uUkw2l_VQy3eMgVtYelKT14MrHSl70VHYWL93Fjg">
<meta name="apple-itunes-app" content="app-id={app_id}">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap">
  <a class="brand" href="../index.html">Cert<span>Prep</span> Practice</a>
  <nav>
    <a href="../api-510-practice-questions/index.html">API 510</a>
    <a href="../asnt-ut-level-2-practice-exam/index.html">UT Level II</a>
  </nav>
</div></header>
{body}
<footer><div class="wrap">
  <p>Independent study aids. Not affiliated with or endorsed by the American Petroleum Institute (API) or ASNT.
  Always confirm current exam requirements with the certifying body.</p>
  <p style="margin-top:8px">Apps: <a href="{API_URL}">API Inspector Cert Prep</a> ·
  <a href="{NDT_URL}">NDT Cert Study</a></p>
</div></footer>
<script>{JS}</script>
</body>
</html>"""

# ---------- API 510 page ----------
api_qs = json.load(open(ROOT / "api510_sample.json"))
api_body = f"""
<div class="hero"><div class="wrap">
<h1>Free API 510 Practice Questions — Pressure Vessel Inspector Exam</h1>
<p class="lead">20 free, SME-reviewed practice questions for the API 510 Pressure Vessel Inspector
certification exam — corrosion-rate and remaining-life calculations, inspection intervals, CMLs,
rerating, repairs, and more. Tap an answer to check it and see the full explanation with the code reference.</p>
<a class="cta" href="{API_URL}">Get the full 323-question bank — free app</a>
<div class="badges">iPhone &amp; iPad · timed mock exams · per-topic readiness scores · works offline</div>
</div></div>
<main><div class="wrap">
{''.join(render_question(i+1, q) for i, q in enumerate(api_qs[:10]))}
<div class="midcta">
  <h2>Want the other 300+ questions?</h2>
  <p>API Inspector Cert Prep has the full SME-approved API 510 bank, timed mock exams that mirror
  the real thing, and a readiness score per topic — so you know exactly what to drill before exam day.
  API 570 and 653 modules included.</p>
  <a class="cta" href="{API_URL}">Download free on the App Store</a>
</div>
{''.join(render_question(i+11, q) for i, q in enumerate(api_qs[10:20]))}
<div class="score"><div class="wrap"><b id="scoreline">Tap answers to track your score</b>
<a class="cta secondary" href="{API_URL}">Continue in the app →</a></div></div>
<h2 class="sec">API 510 exam FAQ</h2>
<div class="faq">
<details><summary>What does the API 510 exam cover?</summary>
<p>The API 510 Pressure Vessel Inspector exam covers inspection, repair, alteration, and rerating
of in-service pressure vessels, drawing on API 510 itself plus related documents in the published
Body of Knowledge (including API RP 571, 572, 576, 577 and ASME code sections). Check
api.org for the current Body of Knowledge and exam format.</p></details>
<details><summary>How hard are the calculation questions?</summary>
<p>Calculations — corrosion rate, remaining life, inspection intervals, required thickness, static
head — are where most candidates win or lose points. They aren't conceptually hard, but you need
the formulas to be automatic under time pressure. That's why this sample leans heavily on them.</p></details>
<details><summary>Is this an official API resource?</summary>
<p>No. These questions are an independent study aid written and reviewed by subject-matter reviewers.
They are not actual exam questions and this site is not affiliated with or endorsed by API.</p></details>
<details><summary>Does the app cover API 570 and API 653 too?</summary>
<p>Yes — the app includes modules for API 570 (Piping Inspector) and API 653 (Aboveground Storage
Tanks), with dedicated banks growing over time.</p></details>
</div>
</div></main>
<script type="application/ld+json">{quiz_jsonld("API 510 Practice Questions", "https://texas0418.github.io/cert-prep-site/api-510-practice-questions/", api_qs)}</script>
"""

# ---------- UT Level II page ----------
ut_qs = json.load(open(ROOT / "ut2_sample.json"))
ut_body = f"""
<div class="hero"><div class="wrap">
<h1>Free ASNT UT Level II Practice Exam Questions — Ultrasonic Testing</h1>
<p class="lead">20 free practice questions for the ASNT UT Level II (conventional ultrasonic testing)
written exam — sound-path and skip-distance calculations, physics, calibration, angle-beam techniques,
flaw detection, and API 1104 acceptance basics. Tap an answer to check it and read the full rationale.</p>
<a class="cta" href="{NDT_URL}">Get the full 355-question bank — free app</a>
<div class="badges">iPhone &amp; iPad · timed mock exams · weak-topic-first review · imperial &amp; metric · offline</div>
</div></div>
<main><div class="wrap">
{''.join(render_question(i+1, q, show_ref=False) for i, q in enumerate(ut_qs[:10]))}
<div class="midcta">
  <h2>335 more questions in the app</h2>
  <p>NDT Cert Study has the full SME-reviewed UT Level II bank with an explanation for every answer
  choice, timed mock exams with per-topic breakdowns, and a review system that serves your weakest
  topics first. Free to download.</p>
  <a class="cta" href="{NDT_URL}">Download free on the App Store</a>
</div>
{''.join(render_question(i+11, q, show_ref=False) for i, q in enumerate(ut_qs[10:20]))}
<div class="score"><div class="wrap"><b id="scoreline">Tap answers to track your score</b>
<a class="cta secondary" href="{NDT_URL}">Continue in the app →</a></div></div>
<h2 class="sec">UT Level II exam FAQ</h2>
<div class="faq">
<details><summary>What's on the UT Level II written exam?</summary>
<p>Employer-administered Level II exams under SNT-TC-1A typically include a general exam (UT physics,
equipment, calibration, techniques) and a specific exam based on the employer's procedures and
applicable codes. Content varies by employer and specification — always study to your written practice.</p></details>
<details><summary>Are the calculation questions in imperial or metric?</summary>
<p>Both. The app lets you toggle every dual-unit question between imperial and metric; the samples on
this page use imperial units.</p></details>
<details><summary>Is this an official ASNT resource?</summary>
<p>No. These are independent practice questions reviewed by subject-matter reviewers. They are not
actual exam questions, and this site is not affiliated with or endorsed by ASNT.</p></details>
<details><summary>Does the app cover other NDT methods?</summary>
<p>The architecture supports additional method modules (PT, MT, RT, PAUT and more) that roll out as
their banks pass review — UT Level II conventional is the flagship module today.</p></details>
</div>
</div></main>
<script type="application/ld+json">{quiz_jsonld("ASNT UT Level II Practice Exam Questions", "https://texas0418.github.io/cert-prep-site/asnt-ut-level-2-practice-exam/", ut_qs)}</script>
"""

# ---------- index ----------
index_body = f"""
<div class="hero"><div class="wrap">
<h1>Free Practice Questions for Inspection &amp; NDT Certification Exams</h1>
<p class="lead">SME-reviewed multiple-choice practice for API inspector and NDT certification exams,
with worked explanations on every question. Try 20 free questions per exam — no sign-up.</p>
</div></div>
<main><div class="wrap">
<div class="cards">
  <a class="card" href="api-510-practice-questions/index.html">
    <h3>API 510 — Pressure Vessel Inspector</h3>
    <p>Corrosion-rate, remaining-life and interval calculations, CMLs, rerating, repairs, RBI.</p>
    <span class="go">20 free questions →</span>
  </a>
  <a class="card" href="asnt-ut-level-2-practice-exam/index.html">
    <h3>ASNT UT Level II — Ultrasonic Testing</h3>
    <p>Sound-path calcs, physics, calibration, angle-beam techniques, flaw detection, API 1104.</p>
    <span class="go">20 free questions →</span>
  </a>
</div>
<div class="midcta">
  <h2>Study the full banks on your phone</h2>
  <p><a href="{API_URL}">API Inspector Cert Prep</a> (323 SME-approved API 510 questions, plus 570/653)
  and <a href="{NDT_URL}">NDT Cert Study</a> (355 UT Level II questions) are free on the App Store,
  with timed mock exams and per-topic readiness tracking.</p>
</div>
</div></main>
"""

pages = [
    ("index.html",
     "Free API & NDT Certification Practice Questions | CertPrep Practice",
     "Free SME-reviewed practice questions for API 510 and ASNT UT Level II certification exams, with full explanations. Try 20 questions per exam, no sign-up.",
     "/", "6785875538", index_body),
    ("api-510-practice-questions/index.html",
     "API 510 Practice Questions — 20 Free Pressure Vessel Inspector Exam Questions",
     "20 free SME-reviewed API 510 practice questions with answers, explanations, and code references. Corrosion rate, remaining life, inspection intervals, and more.",
     "/api-510-practice-questions/", "6785875538", api_body),
    ("asnt-ut-level-2-practice-exam/index.html",
     "ASNT UT Level II Practice Exam — 20 Free Ultrasonic Testing Questions",
     "20 free UT Level II practice questions with full rationale: sound-path calculations, calibration, angle-beam techniques, flaw detection, and API 1104.",
     "/asnt-ut-level-2-practice-exam/", "6785204471", ut_body),
]
for path, title, desc, canon, app_id, body in pages:
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    content = page(title, desc, canon, app_id, body)
    if path == "index.html":  # root page: fix relative nav links
        content = content.replace('href="../', 'href="')
    out.write_text(content)
    print("wrote", path, len(content), "bytes")
