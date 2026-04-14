from django.test import TestCase, Client
import json


class CategoriesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_categories_success(self):
        res = self.client.get("/api/categories/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("categories", data)
        self.assertIn("restaurant", data["categories"])

    def test_categories_not_empty(self):
        res = self.client.get("/api/categories/")
        data = res.json()
        self.assertTrue(len(data["categories"]) > 0)

    def test_categories_post_not_allowed(self):
        res = self.client.post("/api/categories/")
        self.assertEqual(res.status_code, 405)


class SearchValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/api/search/"

    # --- Success ---
    def test_valid_request_returns_200(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertIn(res.status_code, [200, 502])

    # --- Missing fields ---
    def test_missing_body(self):
        res = self.client.post(self.url, content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_latitude(self):
        res = self.client.post(self.url, json.dumps({
            "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_longitude(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_category(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Invalid data ---
    def test_invalid_category(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "spaceship"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_latitude_too_high(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 999, "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_latitude_too_low(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": -999, "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_longitude_too_high(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 999, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_radius_too_small(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "restaurant", "radius": 10
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_radius_too_large(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "restaurant", "radius": 99999
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_string_latitude(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": "abc", "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_null_latitude(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": None, "longitude": 49.8671, "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Manipulation ---
    def test_invalid_json(self):
        res = self.client.post(self.url, "not json at all", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_empty_json(self):
        res = self.client.post(self.url, json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_extra_fields_ignored(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "restaurant",
            "hack": "drop table", "admin": True
        }), content_type="application/json")
        self.assertIn(res.status_code, [200, 502])

    def test_sql_injection_in_category(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "'; DROP TABLE--"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_xss_in_category(self):
        res = self.client.post(self.url, json.dumps({
            "latitude": 40.4093, "longitude": 49.8671, "category": "<script>alert('xss')</script>"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- HTTP methods ---
    def test_get_not_allowed(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 405)

    def test_put_not_allowed(self):
        res = self.client.put(self.url)
        self.assertEqual(res.status_code, 405)

    def test_delete_not_allowed(self):
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, 405)


class CountriesTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_countries(self):
        res = self.client.get("/api/countries/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("countries", data)
        codes = [c["code"] for c in data["countries"]]
        self.assertIn("AZ", codes)

    def test_countries_has_multiple(self):
        res = self.client.get("/api/countries/")
        data = res.json()
        self.assertTrue(len(data["countries"]) >= 10)

    def test_countries_post_not_allowed(self):
        res = self.client.post("/api/countries/")
        self.assertEqual(res.status_code, 405)


class LocationsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_locations_az(self):
        res = self.client.get("/api/locations/AZ/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("areas", data)
        self.assertIn("metro", data["areas"])
        self.assertIn("cadde", data["areas"])
        self.assertIn("rayon", data["areas"])

    def test_metro_count_az(self):
        res = self.client.get("/api/locations/AZ/")
        data = res.json()
        self.assertEqual(len(data["areas"]["metro"]), 10)

    def test_cadde_count_az(self):
        res = self.client.get("/api/locations/AZ/")
        data = res.json()
        self.assertEqual(len(data["areas"]["cadde"]), 10)

    def test_rayon_count_az(self):
        res = self.client.get("/api/locations/AZ/")
        data = res.json()
        self.assertEqual(len(data["areas"]["rayon"]), 10)

    def test_invalid_country(self):
        res = self.client.get("/api/locations/XX/")
        self.assertEqual(res.status_code, 404)

    def test_lowercase_country(self):
        res = self.client.get("/api/locations/az/")
        self.assertEqual(res.status_code, 200)

    def test_empty_metro_mugla(self):
        res = self.client.get("/api/locations/TR_MUG/")
        data = res.json()
        self.assertEqual(len(data["areas"]["metro"]), 0)

    def test_location_has_coordinates(self):
        res = self.client.get("/api/locations/AZ/")
        data = res.json()
        metro = data["areas"]["metro"][0]
        self.assertIn("latitude", metro)
        self.assertIn("longitude", metro)
        self.assertIsInstance(metro["latitude"], float)
        self.assertIsInstance(metro["longitude"], float)

    def test_us_nyc_exists(self):
        res = self.client.get("/api/locations/US_NYC/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["areas"]["metro"]), 10)

    def test_locations_post_not_allowed(self):
        res = self.client.post("/api/locations/AZ/")
        self.assertEqual(res.status_code, 405)


class SearchByAreaValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = "/api/search/area/"

    # --- Success ---
    def test_valid_request(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro",
            "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertIn(res.status_code, [200, 502])

    # --- Missing fields ---
    def test_missing_all_fields(self):
        res = self.client.post(self.url, json.dumps({}), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_country_code(self):
        res = self.client.post(self.url, json.dumps({
            "area_type": "metro", "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_area_type(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_area_name(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_missing_category(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro", "area_name": "28 May"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Invalid data ---
    def test_invalid_area_type(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "highway",
            "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_area_name(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro",
            "area_name": "Fake Station", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_country(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "XX", "area_type": "metro",
            "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_category(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro",
            "area_name": "28 May", "category": "spaceship"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- Manipulation ---
    def test_sql_injection_area_name(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "AZ", "area_type": "metro",
            "area_name": "'; DROP TABLE--", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_xss_in_country_code(self):
        res = self.client.post(self.url, json.dumps({
            "country_code": "<script>alert(1)</script>", "area_type": "metro",
            "area_name": "28 May", "category": "restaurant"
        }), content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_json(self):
        res = self.client.post(self.url, "not json", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    # --- HTTP methods ---
    def test_get_not_allowed(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 405)

    def test_put_not_allowed(self):
        res = self.client.put(self.url)
        self.assertEqual(res.status_code, 405)