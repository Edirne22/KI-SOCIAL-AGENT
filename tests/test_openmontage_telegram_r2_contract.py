import unittest
from scripts.openmontage_telegram_r2_contract import check_telegram_r2_contract


class FakeBoto3:
    def client(self, *args, **kwargs):
        return object()


class TelegramR2ContractTests(unittest.TestCase):
    def test_missing_secret_names_only(self):
        result = check_telegram_r2_contract(env={"R2_ACCOUNT_ID": "private"})
        self.assertFalse(result["configured"])
        self.assertNotIn("private", str(result))

    def test_configured(self):
        env = {key: "placeholder" for key in
               ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME")}
        result = check_telegram_r2_contract(env=env, boto3_module=FakeBoto3())
        self.assertTrue(result["configured"])
        self.assertNotIn("placeholder", str(result))


if __name__ == "__main__":
    unittest.main()
