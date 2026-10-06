"""Offline (re)training: builds the model from the synthetic cold-start corpus + a feedback file and saves it.

  python scripts/train.py --models-dir ./models --feedback ./data/feedback.jsonl --synthetic 6000
Equivalent to POST /v1/retrain, but without starting the HTTP service (useful in CI / batch jobs).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import RetrainRequest  # noqa: E402
from app.service import RouterService  # noqa: E402
from app.store import FeedbackStore, ModelStore  # noqa: E402
from app.taxonomy import Taxonomy  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models-dir", default="./models")
    ap.add_argument("--feedback")
    ap.add_argument("--taxonomy")
    ap.add_argument("--synthetic", type=int, default=6000)
    ap.add_argument("--feedback-weight", type=float, default=5.0)
    args = ap.parse_args()

    svc = RouterService(taxonomy=Taxonomy.load(args.taxonomy), models=ModelStore(args.models_dir), feedback=FeedbackStore(args.feedback), bootstrap_samples=300)
    info = svc.retrain(RetrainRequest(synthetic_samples=args.synthetic, feedback_weight=args.feedback_weight))
    print(json.dumps(info.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
