import importlib

def test_security_packages_installed():
    assert importlib.util.find_spec("axes") is not None
    assert importlib.util.find_spec("csp") is not None
