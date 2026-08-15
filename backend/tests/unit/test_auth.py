from varys.auth import hash_password, validate_password, verify_password


def test_passwords_use_argon2id_and_verify_without_plaintext() -> None:
    password = "correct horse battery staple"

    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert password not in password_hash
    assert verify_password(password_hash, password) is True
    assert verify_password(password_hash, "not the password") is False


def test_password_policy_rejects_short_passwords() -> None:
    try:
        validate_password("too-short")
    except ValueError as error:
        assert str(error) == "password must be at least 12 characters"
    else:
        raise AssertionError("short password was accepted")
