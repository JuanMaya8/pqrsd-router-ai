"""Generalisation guard on HAND-WRITTEN texts (not generated from the training templates).

The floors are deliberately a bit below the measured values so the test catches regressions
without being flaky. They are NOT a claim of production accuracy: see README («Cómo medir»).
"""

import unittest

from tests.helpers import shared_service
from tests.realistic_set import REALISTIC

FLOORS = {"type": 0.80, "dependency": 0.70, "urgency": 0.70}


class RealisticSetTests(unittest.TestCase):
    def test_accuracy_floors(self):
        clf = shared_service().classifier
        results = clf.classify_many([r[0] for r in REALISTIC])
        for i, head in enumerate(("type", "dependency", "urgency")):
            acc = sum(o[head]["id"] == r[i + 1] for r, o in zip(REALISTIC, results)) / len(REALISTIC)
            self.assertGreaterEqual(acc, FLOORS[head], f"{head} accuracy {acc:.2f} < {FLOORS[head]}")

    def test_wrong_answers_are_mostly_flagged_for_review(self):
        clf = shared_service().classifier
        results = clf.classify_many([r[0] for r in REALISTIC])
        wrong = [o for r, o in zip(REALISTIC, results) if any(o[h]["id"] != r[i + 1] for i, h in enumerate(("type", "dependency", "urgency")))]
        flagged = sum(1 for o in wrong if o["needs_review"])
        self.assertGreaterEqual(flagged / max(1, len(wrong)), 0.5)


if __name__ == "__main__":
    unittest.main()
