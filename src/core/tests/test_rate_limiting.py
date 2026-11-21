import pytest
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import View
from django.http import HttpResponse
from core.api.throttling import AuthEndpointRateThrottle, ExportDataRateThrottle
from core.views.mixins import ThrottledViewMixin

class DummyAuthAPIView(APIView):
    permission_classes = []
    throttle_classes = [AuthEndpointRateThrottle]
    
    def post(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class DummyThrottledCBV(ThrottledViewMixin, View):
    throttle_classes = [AuthEndpointRateThrottle]

    def get(self, request):
        return HttpResponse("OK", status=200)

class DummyExportCBV(ThrottledViewMixin, View):
    throttle_classes = [ExportDataRateThrottle]

    def get(self, request):
        return HttpResponse("OK", status=200)

from django.core.cache import cache

@pytest.mark.django_db
def test_auth_endpoint_rate_limiting_api(rf):
    cache.clear()
    view = DummyAuthAPIView.as_view()
    
    for _ in range(5):
        request = rf.post("/dummy-auth/")
        response = view(request)
        assert response.status_code == 200

    request = rf.post("/dummy-auth/")
    response = view(request)
    assert response.status_code == 429

@pytest.mark.django_db
def test_auth_endpoint_cbv_throttling(rf):
    cache.clear()
    view = DummyThrottledCBV.as_view()

    for _ in range(5):
        request = rf.get("/dummy-cbv/")
        response = view(request)
        assert response.status_code == 200

    request = rf.get("/dummy-cbv/")
    response = view(request)
    assert response.status_code == 429

@pytest.mark.django_db
def test_export_data_cbv_throttling(rf):
    cache.clear()
    view = DummyExportCBV.as_view()

    for _ in range(10):
        request = rf.get("/dummy-export/")
        response = view(request)
        assert response.status_code == 200

    request = rf.get("/dummy-export/")
    response = view(request)
    assert response.status_code == 429
