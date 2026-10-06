import unittest
from collections import Counter

from app.corpus import generate
from app.taxonomy import Taxonomy


class CorpusTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual([s.text for s in generate(200, seed=3)], [s.text for s in generate(200, seed=3)])

    def test_labels_valid_and_balanced(self):
        tax = Taxonomy()
        samples = generate(1500)
        types = {o.id for o in tax.types}
        deps = set(tax.dependency_ids())
        urg = {o.id for o in tax.urgency}
        for s in samples:
            self.assertIn(s.type, types)
            self.assertIn(s.dependency, deps)
            self.assertIn(s.urgency, urg)
        self.assertEqual(set(Counter(s.type for s in samples)), types)
        self.assertEqual(set(Counter(s.dependency for s in samples)), deps)

    def test_no_duplicates(self):
        texts = [s.text for s in generate(1000)]
        self.assertEqual(len(texts), len(set(texts)))


if __name__ == "__main__":
    unittest.main()
