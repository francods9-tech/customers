import unittest


class AppRoutesTest(unittest.TestCase):
    def test_healthz_is_public(self):
        from app import app

        client = app.test_client()
        response = client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_colabs_route_requires_login(self):
        from app import app

        client = app.test_client()
        response = client.get("/colabs")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_colab_creator_create_requires_login(self):
        from app import app

        client = app.test_client()
        response = client.post("/colabs/creadores", data={"nombre": "Creator"})

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_bajas_route_requires_login(self):
        from app import app

        client = app.test_client()
        response = client.get("/bajas")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)


if __name__ == "__main__":
    unittest.main()
