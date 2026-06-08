import hashlib

from app.core.auth import hash_api_key


def test_api_key_hash_matches_pi_agent():
    key = "pi_test_key_for_unit_test"
    expected = hashlib.sha256(key.encode()).hexdigest()
    assert hash_api_key(key) == expected
