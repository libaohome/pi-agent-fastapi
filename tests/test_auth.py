import hashlib

from app.core.auth import hash_api_key


def test_api_key_hash_matches_pi_agent():
    key = "pi_Zu3IRzpFdRN6ktgK8YWsTiJ268ZYIx6w"
    expected = hashlib.sha256(key.encode()).hexdigest()
    assert hash_api_key(key) == expected
