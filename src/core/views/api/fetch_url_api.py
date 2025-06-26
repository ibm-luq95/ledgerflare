# -*- coding: utf-8 -*-#
import traceback

from django.urls import reverse_lazy
from rest_framework import permissions
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import get_formatted_logger

logger = get_formatted_logger()


class FetchUrlApiView(APIView):
    """
    API view for fetching URL paths based on input data.

    Permissions:
        - IsAuthenticated: Users must be authenticated to access this view.

    Methods:
        post(request: Request, *args, **kwargs) -> Response: Processes a POST request to fetch URL paths.

    Returns:
        Response: JSON response containing the fetched URL path and status code.

    """

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request: Request, *args, **kwargs):
        """
        Processes a POST request to fetch URL paths based on input data.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: JSON response containing the fetched URL path and status code.

        """
        serializer = ""
        try:
            data = request.data
            url_name = data.get("urlName")
            pk = data.get("pk", None)
            if pk is not None:
                url_path = reverse_lazy(url_name, kwargs={"pk": pk})
            else:
                url_path = reverse_lazy(url_name)
            return Response(
                {"urlPath": url_path},
                status=status.HTTP_200_OK,
            )
        except APIException as ex:
            logger.error(traceback.format_exc())
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "user_error_msg": ex.default_detail,
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.error(traceback.format_exc())
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "error": str(ex),
                "user_error_msg": "Error while fetching URL path!",
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
