from unittest import TestCase

from itsdangerous import URLSafeTimedSerializer

from redash import settings
from redash.utils.dynamic_key import decode_token, generate_token


class TestDynamicKey(TestCase):
    def test_round_trip(self):
        token = generate_token(12, 3)

        self.assertEqual(decode_token(token), {"id": 12, "user": 3})

    def test_expired_token(self):
        token = generate_token(12, 3)

        self.assertEqual(decode_token(token, max_age=-1), {})

    def test_tampered_token(self):
        token = generate_token(12, 3)
        _, timestamp_and_signature = token.split(".", 1)
        other_payload, _ = generate_token(99, 3).split(".", 1)

        self.assertEqual(decode_token("{}.{}".format(other_payload, timestamp_and_signature)), {})

    def test_wrong_salt(self):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        token = serializer.dumps({"id": 12, "user": 3}, salt="some-other-salt")

        self.assertEqual(decode_token(token), {})

    def test_non_dict_payload(self):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        token = serializer.dumps([12, 3], salt=settings.DATASOURCE_SECRET_KEY)

        self.assertEqual(decode_token(token), {})

    def test_garbage(self):
        self.assertEqual(decode_token("not-a-token"), {})
