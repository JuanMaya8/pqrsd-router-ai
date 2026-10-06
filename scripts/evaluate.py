"""Measures the classifier on labelled texts the model never saw.

Usage:
  python scripts/evaluate.py                       # built-in hand-written set (tests/realistic_set.py)
  python scripts/evaluate.py --csv labelled.csv    # your own: columns text,type,dependency,urgency (any may be empty)
  python scripts/evaluate.py --feedback feedback.jsonl --synthetic 6000   # also train on feedback

IMPORTANT: scores on the synthetic corpus are meaningless (the model memorises the templates).
Only numbers measured on real, separately-labelled PQRSD tell you how it will behave in production.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import RetrainRequest  # noqa: E402
from app.service import RouterService  # noqa: E402
from app.store import FeedbackStore  # noqa: E402
from app.taxonomy import Taxonomy  # noqa: E402

HEADS = ("type", "dependency", "urgency")


def load_rows(path: str | None) -> list[dict]:
    if not path:
        from tests.realistic_set import REALISTIC

        return [{"text": t, "type": ty, "dependency": d, "urgency": u} for t, ty, d, u in REALISTIC]
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv")
    ap.add_argument("--feedback")
    ap.add_argument("--taxonomy")
    ap.add_argument("--synthetic", type=int, default=6000)
    ap.add_argument("--show-errors", action="store_true")
    args = ap.parse_args()

    svc = RouterService(taxonomy=Taxonomy.load(args.taxonomy), feedback=FeedbackStore(args.feedback), bootstrap_samples=args.synthetic)
    if args.feedback:
        svc.retrain(RetrainRequest(synthetic_samples=args.synthetic))
    rows = load_rows(args.csv)
    t0 = time.perf_counter()
    results = svc.classifier.classify_many([r["text"] for r in rows])
    ms = (time.perf_counter() - t0) * 1000 / len(rows)

    print(f"Textos evaluados: {len(rows)}   ·   {ms:.1f} ms por texto")
    wrong_rows, flagged_wrong = 0, 0
    for head in HEADS:
        scored = [(r, o) for r, o in zip(rows, results) if r.get(head)]
        if not scored:
            continue
        ok = sum(o[head]["id"] == r[head] for r, o in scored)
        print(f"  {head:<11} exactitud {ok / len(scored):.1%}  ({ok}/{len(scored)})")
    review = sum(o["needs_review"] for o in results)
    for r, o in zip(rows, results):
        bad = [h for h in HEADS if r.get(h) and o[h]["id"] != r[h]]
        if bad:
            wrong_rows += 1
            flagged_wrong += o["needs_review"]
            if args.show_errors:
                print("  ✗", ",".join(bad), "|", r["text"][:80], "→", [o[h]["id"] for h in HEADS], "review" if o["needs_review"] else "")
    print(f"  Marcados «requiere revisión»: {review}/{len(rows)}  ·  de los {wrong_rows} con algún error, {flagged_wrong} quedaron marcados")
    print("  Distribución de tipos predichos:", dict(Counter(o["type"]["id"] for o in results)))


if __name__ == "__main__":
    main()
