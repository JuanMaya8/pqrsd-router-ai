import unittest

from app.rules import evaluate
from app.taxonomy import Taxonomy
from app.text import fold, normalize, strip_accents, word_count


class TextTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  ¿Cómo   ESTÁ el Niño? "), "¿como esta el nino?")
        self.assertEqual(strip_accents("canción"), "cancion")

    def test_fold_keeps_length(self):
        for s in ["Ñandú árbol", "Bogotá D.C.", "ÁÉÍÓÚ"]:
            self.assertEqual(len(fold(s)), len(s))

    def test_word_count(self):
        self.assertEqual(word_count("uno dos  tres"), 3)
        self.assertEqual(word_count(""), 0)


class RuleTests(unittest.TestCase):
    tax = Taxonomy()

    def test_denuncia_phrase(self):
        r = evaluate("Denuncio un caso de corrupción en la alcaldía", self.tax)
        self.assertGreater(r.type_scores["denuncia"], r.type_scores["peticion"])

    def test_accent_insensitive(self):
        a = evaluate("Hay una fuga de gas", self.tax).urgency_scores["critical"]
        b = evaluate("HAY UNA FUGA DE GÁS", self.tax).urgency_scores["critical"]
        self.assertEqual(a, b)
        self.assertGreaterEqual(a, 3)

    def test_prefix_rule(self):
        self.assertGreater(evaluate("el niño fue electrocutado", self.tax).urgency_scores["critical"], 0)

    def test_word_boundaries(self):
        # «bar» (seguridad keyword) must not match inside «barrio»
        r = evaluate("Vivo en el barrio centro", self.tax)
        self.assertEqual(r.dependency_scores["seguridad"], 0)

    def test_dependency_keywords(self):
        r = evaluate("El comparendo de tránsito está mal", self.tax)
        self.assertEqual(max(r.dependency_scores, key=r.dependency_scores.get), "movilidad")


if __name__ == "__main__":
    unittest.main()
