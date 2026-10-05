#!/usr/bin/env python3
"""Free-sample question sourcing, shared by the site build and the printable magnet.

This lives in its own module for one reason: the magnet PDF must contain EXACTLY the
25 questions the page shows, in the same order, with the same shuffled options. Two
copies of this logic would drift the first time either changed, and the drift would be
silent - a subscriber would get a PDF that does not match the page they just read.
Both consumers import from here. Do not inline it back.
"""
import json, random, pathlib

ROOT     = pathlib.Path(__file__).parent
API_BANK = pathlib.Path.home() / "Documents/GitHub/API Inspector Cert Study/assets/bank_api_pool.json"
NDT_DIR  = pathlib.Path.home() / "Documents/GitHub/NDTCertStudy/assets"
N_FREE   = 25


def shuffled(qid, src):
    """Same deterministic shuffle as the PDF builder. The NDT banks put the correct
    answer at index 0 for 84-97% of questions; unshuffled that is a giveaway."""
    opts = list(src["options"])
    dis  = list(src.get("distractors") or [""] * len(opts))
    dis += [""] * (len(opts) - len(dis))
    order = list(range(len(opts)))
    random.Random("shuf-" + qid).shuffle(order)
    return {"stem": src["stem"],
            "options": [opts[i] for i in order],
            "distractors": [dis[i] for i in order],
            "answer": order.index(src["answer"]),
            "explanation": src["explanation"]}


def sample(exam):
    if exam["src"] == "api":
        pool = [q for q in json.load(open(API_BANK))
                if exam["filter"] in q.get("exams", []) and q["meta"].get("reviewStatus") == "approved"]
        rng = random.Random("free-" + exam["slug"])
        rng.shuffle(pool)
        out = []
        for q in pool[:N_FREE]:
            r = shuffled(q["id"], q["content"])
            r["topic"] = q.get("subtopic", "")
            r["ref"] = q["meta"].get("ref", "")
            out.append(r)
        return out
    # Most banks are the app's own assets. The ISO 9712 pack is composed for
    # print from overlays that no single app module owns, so it lives here.
    src_path = NDT_DIR / exam["filter"]
    if not src_path.exists():
        src_path = ROOT / "data" / exam["filter"]
    bank = json.load(open(src_path))
    pool = [q for b in bank["blocks"] for q in b["questions"]]
    rng = random.Random("free-" + exam["slug"])
    rng.shuffle(pool)
    out = []
    for q in pool[:N_FREE]:
        body = (q.get("variants") or {}).get("imperial") or q["content"]
        r = shuffled(q["id"], body)
        r["topic"] = (q.get("subtopic") or q.get("topic") or "").replace("_", " ")
        r["ref"] = ""
        out.append(r)
    return out
