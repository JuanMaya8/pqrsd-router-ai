import unittest
from datetime import date

from app.entities import extract_entities, redact


def by_type(text, ref=None):
    out = {}
    for e in extract_entities(text, ref):
        out.setdefault(e.type, []).append(e)
    return out


class EntityTests(unittest.TestCase):
    def test_absolute_date(self):
        d = by_type("El 15 de marzo de 2025 radiqué mi solicitud")["date"][0]
        self.assertEqual(d.value, "2025-03-15")

    def test_relative_dates(self):
        ref = date(2025, 6, 10)
        self.assertEqual(by_type("Ocurrió ayer", ref)["date"][0].value, "2025-06-09")
        self.assertEqual(by_type("Hace 3 días me atendieron", ref)["date"][0].value, "2025-06-07")

    def test_amount(self):
        a = by_type("Me cobraron $1.850.000 de más")["amount"][0]
        self.assertEqual(a.value, "1850000")

    def test_document_and_email_flagged_pii(self):
        e = by_type("Soy Juan Pérez, C.C. 52.123.456, correo juan@correo.com, cel 3001234567")
        for k in ("document_id", "email", "phone"):
            self.assertTrue(e[k][0].pii, k)

    def test_address_and_place(self):
        e = by_type("Vivo en la calle 45 #12-30 del barrio Santa Lucía en Medellín")
        self.assertIn("address", e)
        self.assertTrue(any(p.text.lower().startswith("barrio") for p in e["place"]))

    def test_procedure(self):
        self.assertIn("procedure", by_type("Necesito la licencia de construcción y el paz y salvo"))

    def test_redact_removes_pii_but_keeps_places(self):
        text = "Mi cédula es 1.020.304.050, escríbanme a ana@x.co. Vivo en Cali."
        out = redact(text, extract_entities(text))
        self.assertNotIn("1.020.304.050", out)
        self.assertNotIn("ana@x.co", out)
        self.assertIn("Cali", out)

    def test_offsets_match_original_text(self):
        text = "Él pagó $2.000 en Bogotá el 3 de abril de 2024."
        for e in extract_entities(text):
            self.assertEqual(text[e.start:e.end], e.text)

    def test_no_overlap(self):
        ents = sorted(extract_entities("Llamen al 3001234567 o escriban a ana@x.co, calle 10 #5-20"), key=lambda e: e.start)
        for a, b in zip(ents, ents[1:]):
            self.assertLessEqual(a.end, b.start)


if __name__ == "__main__":
    unittest.main()


class PersonNameTests(unittest.TestCase):
    def test_soy_requires_two_capitalised_words(self):
        self.assertIn("person", by_type("Hola, soy Ana Pérez y vivo en Cali"))
        self.assertNotIn("person", by_type("Soy Madre de tres niños y no tengo agua"))

    def test_sign_off(self):
        self.assertIn("person", by_type("Gracias por su atención.\nAtentamente, Juan Carlos Rojas"))
