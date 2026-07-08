import unittest
from unittest.mock import patch

from room_collector import collect_product, flat_post_to_raw


class CollectProductTests(unittest.TestCase):
    def test_collect_product_respects_max_pages(self):
        responses = [
            {
                "status": "success",
                "count": 40,
                "data": [
                    {
                        "id": "1",
                        "created_at": "2026-01-01 00:00:00",
                        "likes": 10,
                        "comments": 0,
                        "recollects": 0,
                        "detail_views": 0,
                        "influence_points": 0,
                        "item": {"url": "https://item.rakuten.co.jp/aokinomori/test/"},
                        "user": {"username": "user1", "fullname": "User 1", "rank": 1},
                    }
                ],
            },
            {
                "status": "success",
                "count": 40,
                "data": [
                    {
                        "id": "2",
                        "created_at": "2026-01-02 00:00:00",
                        "likes": 20,
                        "comments": 0,
                        "recollects": 0,
                        "detail_views": 0,
                        "influence_points": 0,
                        "item": {"url": "https://item.rakuten.co.jp/aokinomori/test/"},
                        "user": {"username": "user2", "fullname": "User 2", "rank": 2},
                    }
                ],
            },
        ]

        product = {
            "item_url": "https://item.rakuten.co.jp/aokinomori/test/",
            "item_code": "test",
            "keyword": "test",
            "item_short": "test",
        }

        with patch("room_collector.api_get", side_effect=responses) as api_get:
            posts, had_error = collect_product(product, verbose=False, max_pages=2, timeout=1, sleep_between_pages=0)

        self.assertEqual(len(posts), 2)
        self.assertFalse(had_error)
        self.assertEqual(api_get.call_count, 2)

    def test_collect_product_reports_error_on_timeout(self):
        product = {
            "item_url": "https://item.rakuten.co.jp/aokinomori/test/",
            "item_code": "test",
            "keyword": "test",
            "item_short": "test",
        }

        with patch("room_collector.api_get", side_effect=TimeoutError("timed out")):
            posts, had_error = collect_product(product, verbose=False, max_pages=2, timeout=1, sleep_between_pages=0, retries=0)

        self.assertEqual(posts, [])
        self.assertTrue(had_error)


class FlatPostToRawTests(unittest.TestCase):
    def test_round_trips_fields_used_by_aggregate(self):
        flat_post = {
            "post_id": "42",
            "created_at": "2026-01-01 00:00:00",
            "username": "user1",
            "fullname": "User 1",
            "user_rank": 3,
            "price": 1000,
            "from_service": "room",
            "likes": 5,
            "comments": 1,
            "recollects": 2,
            "detail_views": 10,
            "influence_points": 7,
        }

        raw = flat_post_to_raw(flat_post)

        self.assertEqual(raw["id"], "42")
        self.assertEqual(raw["likes"], 5)
        self.assertEqual(raw["user"]["username"], "user1")
        self.assertEqual(raw["item"]["price"], 1000)


if __name__ == "__main__":
    unittest.main()
