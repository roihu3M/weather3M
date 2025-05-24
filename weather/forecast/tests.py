from django.test import TestCase, Client

class GeneralTestCase(TestCase):
    
    def test_empty_query(self):
        c = Client()
        response = c.get("/search/?name=")
        self.assertEqual(response.status_code, 404)

    def test_random_query(self):
        c = Client()
        response = c.get("/search/?name=sdadasasd")
        self.assertEqual(response.status_code, 404)
        response = c.get("/search/?name=123312123")
        self.assertEqual(response.status_code, 404)
        response = c.get("/search/?name=Berlimn")
        self.assertEqual(response.status_code, 404)
        response = c.get("/search/?name=Москва")
        self.assertRaises(UnicodeEncodeError)

    def test_normal_query(self):
        c = Client()
        response = c.get("/search/?name=Moscow")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=Berlin")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=Tokyo")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=New+York")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=New York")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=None")
        self.assertEqual(response.status_code, 200)
        response = c.get("/search/?name=Brest")
        self.assertEqual(response.status_code, 200)
        