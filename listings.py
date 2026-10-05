#!/usr/bin/env python3
"""Generate paste-ready Gumroad listing copy for every pack, from one source of truth."""
import json, pathlib, textwrap

ROOT = pathlib.Path(__file__).parent
CFG  = json.load(open(ROOT / "exams.json"))
NDT_DIR = pathlib.Path.home() / "Documents/GitHub/NDTCertStudy/assets"
OUT  = pathlib.Path.home() / "Documents/CertPacks/listings"
OUT.mkdir(exist_ok=True)

PDF = {  # slug -> built PDF filename
 "api-510-practice-questions":"api510-practice-pack.pdf",
 "api-570-practice-questions":"api570-practice-pack.pdf",
 "asnt-ut-level-2-practice-exam":"asnt-ut2-practice-pack.pdf",
 "asnt-ut-level-1-practice-exam":"asnt-ut1-practice-pack.pdf",
 "asnt-mt-level-2-practice-exam":"asnt-mt2-practice-pack.pdf",
 "asnt-mt-level-1-practice-exam":"asnt-mt1-practice-pack.pdf",
 "asnt-pt-level-2-practice-exam":"asnt-pt2-practice-pack.pdf",
 "asnt-pt-level-1-practice-exam":"asnt-pt1-practice-pack.pdf",
 "asnt-rt-level-2-practice-exam":"asnt-rt2-practice-pack.pdf",
 "asnt-rt-level-1-practice-exam":"asnt-rt1-practice-pack.pdf",
 "asnt-paut-level-2-practice-exam":"asnt-paut2-practice-pack.pdf",
 "asnt-paut-level-1-practice-exam":"asnt-paut1-practice-pack.pdf",
}
BASE = CFG["site"]["base"]
index = []

for x in CFG["exams"]:
    listed = bool(x["pack"])   # already on Gumroad: this file is an UPDATE, not a new listing
    ndt   = x["src"] == "ndt"
    name  = f'{"ASNT " if ndt else ""}{x["short"]} Practice Question Pack'
    price = x["price"].lstrip("$")
    free  = f'{BASE}/{x["slug"]}/'
    # Only the UT Level II bank actually carries reference_values. Claiming a reference
    # sheet on a pack that has none is a promise the PDF does not keep.
    refsheet = bool(json.load(open(NDT_DIR / x["filter"])).get("reference_values")) if ndt else False
    extras = ""
    if ndt:
        extras = (" Every question also carries a note on each wrong option saying which mistake "
                  "leads there, which is usually more useful than the right answer. There are also "
                  "two mock exams built only from questions held back from the topic sets, so a "
                  "mock score is a real reading and not a memory check.")
        if refsheet:
            extras += (" A reference sheet of sound velocities and trig values is included at the "
                       "front.")
    summary = (f'{x["packq"]} exam-style {"ASNT " if ndt else ""}{x["short"]} practice questions with a worked solution for '
               f'every single one. Printable PDF.')
    desc = f"""Most people who fail this exam do not fail on theory. They fail because they walked in having read about a topic instead of having worked forty questions on it.

This is {x['packq']} original multiple-choice questions written in the style of the {"ASNT " if ndt else ""}{x['short']} examination. Every one has a worked solution that either shows the arithmetic line by line or names the governing clause.{extras}

Try before you buy: 25 of these questions are free, with the full solutions, at {free} . No sign-up and no email wall.

How the questions were made: drafted with AI assistance, then reviewed and corrected by me. I have spent twenty years in oil and gas, seven as an AUT technician, three as an NDT project manager, and ten in quality assurance. These are original questions. Nothing is copied from any examination and no code or standard text is reproduced. I am not a certified inspector myself and I would rather say so than let you assume otherwise.

What this is not: not affiliated with, endorsed by, or connected to ASNT, API or ASME. It is a study aid, not a substitute for the reference documents, and it does not guarantee a result. Your employer's written practice governs your actual certification.

Refunds: if this is not what you expected, email simon@simonbuilds.app and you get your money back. No questions and no argument.

Instant download. Printable PDF, formatted for US Letter."""

    receipt = f"""Thanks. Your PDF is on your Gumroad library page and attached to this receipt.
Print it double-sided if you can, and work the topic sets before you touch the mock exams at the back.
If something in it looks wrong, or it is not what you expected, reply to this email and I will fix it or refund you. simon@simonbuilds.app
Good luck with the exam.
Simon"""

    body = f"""================================================================
{"UPDATE THE EXISTING LISTING" if listed else "NEW GUMROAD LISTING"} — {name}
{("live at " + x["pack"]) if listed else "not yet created"}
================================================================

NAME
{name}

PRICE
{price}

SUMMARY
{summary}

DESCRIPTION
{desc}

RECEIPT / CUSTOM MESSAGE  ({len(receipt)} of 500 chars)
{receipt}

FILE TO UPLOAD
~/Documents/CertPacks/{PDF[x['slug']]}

{"Re-upload the PDF too — the file changed." if listed else "AFTER PUBLISHING: paste the public URL into exams.json under pack for slug " + x["slug"] + ", then rebuild."}
================================================================
"""
    f = OUT / f'{x["slug"]}.txt'
    f.write_text(body)
    index.append((x["short"], x["price"], PDF[x["slug"]], f.name, len(receipt)))

print(f"{len(index)} listings written to {OUT}\n")
for s, p, pdf, fn, rl in index:
    flag = "  <-- RECEIPT TOO LONG" if rl > 500 else ""
    print(f"  {s:15s} {p:4s}  {pdf:30s} {fn}{flag}")
