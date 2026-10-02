import json
import unittest

from server import get_restaurant_info, get_review, recommend_by_vibe


class ServerToolsTests(unittest.TestCase):
    def test_finds_restaurant_by_name(self):
        result = json.loads(get_restaurant_info("The Gilded Artichoke"))
        self.assertEqual(result["status"], "found")
        self.assertGreaterEqual(result["count"], 1)

    def test_finds_restaurant_with_accented_spanish_vibe(self):
        result = json.loads(recommend_by_vibe("romántico"))
        names = {item["name"] for item in result["structured_matches"]}
        self.assertIn("Velvet & Vine", names)

    def test_returns_review(self):
        result = json.loads(get_review("The Gilded Artichoke"))
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["restaurant"], "The Gilded Artichoke")

    def test_reports_unknown_restaurant(self):
        result = json.loads(get_restaurant_info("No existe este restaurante"))
        self.assertEqual(result["status"], "not_found")


if __name__ == "__main__":
    unittest.main()