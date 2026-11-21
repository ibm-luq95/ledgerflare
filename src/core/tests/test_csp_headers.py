import pytest
from django.test import Client

@pytest.mark.django_db
def test_csp_header_is_present(client: Client):
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
    csp_header = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp_header
    assert "object-src 'none'" in csp_header
