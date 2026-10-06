import unittest

from tests.helpers import shared_service


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clf = shared_service().classifier

    def test_output_shape(self):
        r = self.clf.classify("Solicito copia del contrato de obra 345 de 2024 del barrio Santa Lucía.")
        for k in ("type", "dependency", "urgency", "entities", "needs_review", "review_reasons", "model_version", "latency_ms", "word_count"):
            self.assertIn(k, r)
        for head in ("type", "dependency", "urgency"):
            self.assertTrue(0.0 <= r[head]["confidence"] <= 1.0)
            self.assertTrue(r[head]["reasons"])
        self.assertEqual(r["type"]["id"], "peticion")
        self.assertEqual(r["subtype"]["id"], "information")

    def test_subtype_only_for_peticion(self):
        r = self.clf.classify("Sugiero que instalen más canecas de reciclaje en el parque principal del barrio.")
        self.assertEqual(r["type"]["id"], "sugerencia")
        self.assertIsNone(r["subtype"])

    def test_life_risk_is_escalated_to_critical(self):
        r = self.clf.classify("Hay una fuga de gas en el edificio de la calle 10 #5-20, huele muy fuerte desde esta mañana.")
        self.assertEqual(r["urgency"]["id"], "critical")
        self.assertGreaterEqual(r["urgency"]["priority_score"], 85)

    def test_ordinary_request_is_not_critical(self):
        r = self.clf.classify("Quisiera saber cuáles son los horarios de atención de la oficina para radicar documentos.")
        self.assertNotEqual(r["urgency"]["id"], "critical")
        self.assertLess(r["urgency"]["priority_score"], 60)

    def test_priority_orders_urgency(self):
        crit = self.clf.classify("Hay un cable de alta tensión caído frente al colegio y hay niños cerca, es una emergencia.")
        low = self.clf.classify("Sugiero con calma que a futuro pongan más bancas en el parque del barrio.")
        self.assertGreater(crit["urgency"]["priority_score"], low["urgency"]["priority_score"])

    def test_very_short_text_needs_review(self):
        r = self.clf.classify("ayuda")
        self.assertTrue(r["needs_review"])

    def test_gibberish_goes_to_fallback_or_review(self):
        r = self.clf.classify("asdf qwer zxcv lorem ipsum dolor sit amet")
        self.assertTrue(r["needs_review"] or r["dependency"]["routed_to_fallback"])

    def test_redaction_flag(self):
        t = "Mi cédula es 1.020.304.050 y solicito copia de mi historia clínica en la clínica del norte."
        self.assertIsNone(self.clf.classify(t)["redacted_text"])
        self.assertNotIn("1.020.304.050", self.clf.classify(t, with_redaction=True)["redacted_text"])

    def test_batch_equals_single(self):
        texts = ["Denuncio que un funcionario me pidió dinero para agilizar mi trámite.", "El semáforo de la calle 30 está dañado hace días."]
        batch = self.clf.classify_many(texts)
        for t, b in zip(texts, batch):
            s = self.clf.classify(t)
            self.assertEqual((s["type"]["id"], s["dependency"]["id"], s["urgency"]["id"]), (b["type"]["id"], b["dependency"]["id"], b["urgency"]["id"]))

    def test_confidences_are_distributions(self):
        r = self.clf.classify("Mi hijo no tiene cupo escolar y las clases ya empezaron.", top_k=6)
        total = r["type"]["confidence"] + sum(a["confidence"] for a in r["type"]["alternatives"])
        self.assertAlmostEqual(total, 1.0, places=1)


if __name__ == "__main__":
    unittest.main()
