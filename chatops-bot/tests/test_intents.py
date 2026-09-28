"""Coverage for the explicit Day 5 intent allowlist."""

import unittest

from app.intents import Intent, classify_question


class IntentTests(unittest.TestCase):
    def test_api_health_variants(self):
        self.assertEqual(classify_question("<@U1> api healthy?"), Intent.API_HEALTH)
        self.assertEqual(classify_question("InsightHub có healthy không?"), Intent.API_HEALTH)

    def test_ingestion_today_variants(self):
        self.assertEqual(classify_question("ingest count today?"), Intent.INGESTION_TODAY)
        self.assertEqual(classify_question("Hôm nay ingest bao nhiêu doc?"), Intent.INGESTION_TODAY)

    def test_failing_pods_variants(self):
        self.assertEqual(classify_question("which pods failing?"), Intent.FAILING_PODS)
        self.assertEqual(classify_question("Pod nào đang lỗi?"), Intent.FAILING_PODS)

    def test_unknown_question_is_not_an_infrastructure_command(self):
        self.assertIsNone(classify_question("scale api to 5"))
