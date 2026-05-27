import unittest


class MessageRulesTest(unittest.TestCase):
    def test_parse_tags_normalizes_and_deduplicates(self):
        from message_rules import parse_tags

        self.assertEqual(parse_tags(" bienvenida, Pago ,bienvenida,, Trial "), "bienvenida,pago,trial")

    def test_filter_messages_matches_title_body_and_tags(self):
        from message_rules import filter_messages

        rows = [
            type("Msg", (), {"titulo": "Bienvenida", "cuerpo": "Hola equipo", "tags": "onboarding,inicio", "categoria_key": "general"})(),
            type("Msg", (), {"titulo": "Pago pendiente", "cuerpo": "Factura vencida", "tags": "stripe,pago", "categoria_key": "pagos"})(),
        ]

        self.assertEqual([m.titulo for m in filter_messages(rows, q="factura")], ["Pago pendiente"])
        self.assertEqual([m.titulo for m in filter_messages(rows, q="inicio")], ["Bienvenida"])
        self.assertEqual([m.titulo for m in filter_messages(rows, category="pagos")], ["Pago pendiente"])

    def test_cs_pack_templates_include_operational_whatsapp_cases(self):
        from message_rules import CS_PACK_TEMPLATES

        titles = {t["titulo"] for t in CS_PACK_TEMPLATES}

        self.assertIn("Baja de enlace - intake inicial", titles)
        self.assertIn("Queja o demora - contencion con checkpoint", titles)
        self.assertIn("Soporte tecnico - acceso o dashboard", titles)


if __name__ == "__main__":
    unittest.main()
