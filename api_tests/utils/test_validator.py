from server.utils.validator import validate_resource_name


def test_validate_resource_name() -> None:
    assert validate_resource_name("") is False
    assert validate_resource_name("_aaHDrfds11") is False
    assert validate_resource_name("1esdf24343") is False
    assert validate_resource_name("adeDh2_dfd") is True
    assert validate_resource_name("Adfdfn345d_") is True
    assert validate_resource_name("fds23dff-") is True
    assert validate_resource_name("-") is False
