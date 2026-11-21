"""Secure proxy media viewer view module supporting HTTP Range requests."""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, Final

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.generic import View

from core.views.mixins import (
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from document.models import DocumentProxy


ALLOWED_INLINE_MIME_TYPES: Final[set[str]] = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

CSP_VIEWER_POLICY: Final[str] = (
    "default-src 'none'; img-src 'self' data:; "
    "style-src 'unsafe-inline'; sandbox allow-same-origin;"
)


class DocumentViewerView(
    BWLoginRequiredMixin,
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    View,
):
    """Media viewer supporting HTTP 206 Range requests and sandboxed CSP."""

    permission_required = "document.can_view_list"
    object: DocumentProxy | None = None

    def get_object(self, queryset: Any = None) -> DocumentProxy:
        """Retrieve and cache the target DocumentProxy by primary key."""
        if self.object is None:
            pk = self.kwargs.get("pk")
            self.object = get_object_or_404(DocumentProxy, pk=pk)
        return self.object

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseBase:
        """Stream inline document content or force attachment download."""
        document = self.get_object()
        if not document.document_file:
            raise Http404(_("No file associated with this document"))

        try:
            file_obj = document.document_file.open("rb")
        except FileNotFoundError as err:
            raise Http404(_("Document file not found on disk")) from err

        raw_name = Path(str(document.document_file.name)).name
        clean_name = raw_name.split("_", 1)[-1] if "_" in raw_name else raw_name
        content_type, _encoding = mimetypes.guess_type(clean_name)
        resolved_content_type = content_type or "application/octet-stream"

        if resolved_content_type not in ALLOWED_INLINE_MIME_TYPES:
            response = FileResponse(
                file_obj,
                as_attachment=True,
                filename=clean_name,
                content_type=resolved_content_type,
            )
            self._apply_security_headers(response)
            return response

        total_size = getattr(file_obj, "size", None)
        if total_size is None or not isinstance(total_size, int):
            if hasattr(file_obj, "seek") and hasattr(file_obj, "tell"):
                cur = file_obj.tell()
                file_obj.seek(0, os.SEEK_END)
                total_size = file_obj.tell()
                file_obj.seek(cur)
            else:
                total_size = 0

        range_header = request.META.get("HTTP_RANGE")
        if not range_header:
            response = FileResponse(
                file_obj,
                as_attachment=False,
                filename=clean_name,
                content_type=resolved_content_type,
            )
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = str(total_size)
            self._apply_security_headers(response)
            return response

        return self._handle_range_request(
            file_obj=file_obj,
            range_header=range_header,
            total_size=total_size,
            clean_name=clean_name,
            content_type=resolved_content_type,
        )

    def _handle_range_request(
        self,
        file_obj: Any,
        range_header: str,
        total_size: int,
        clean_name: str,
        content_type: str,
    ) -> HttpResponseBase:
        if not range_header.startswith("bytes="):
            return self._range_not_satisfiable(total_size, file_obj=file_obj)

        range_val = range_header[6:].strip()
        if "," in range_val:
            return self._range_not_satisfiable(total_size, file_obj=file_obj)

        parts = range_val.split("-")
        if len(parts) != 2:
            return self._range_not_satisfiable(total_size, file_obj=file_obj)

        start_str, end_str = parts[0].strip(), parts[1].strip()
        try:
            if start_str and end_str:
                start = int(start_str)
                end = int(end_str)
            elif start_str:
                start = int(start_str)
                end = total_size - 1
            elif end_str:
                suffix = int(end_str)
                start = max(0, total_size - suffix)
                end = total_size - 1
            else:
                return self._range_not_satisfiable(total_size, file_obj=file_obj)
        except ValueError:
            return self._range_not_satisfiable(total_size, file_obj=file_obj)

        if start < 0 or start > end or start >= total_size:
            return self._range_not_satisfiable(total_size, file_obj=file_obj)

        end = min(end, total_size - 1)
        content_length = end - start + 1

        file_obj.seek(start)

        class RangedStream:
            def __init__(self, stream: Any, length: int) -> None:
                self._stream = stream
                self._remaining = length

            def read(self, size: int = -1) -> bytes:
                if self._remaining <= 0:
                    return b""
                to_read = (
                    self._remaining if size < 0 else min(size, self._remaining)
                )
                chunk = self._stream.read(to_read)
                if not chunk:
                    self._remaining = 0
                    return b""
                self._remaining -= len(chunk)
                return chunk

            def close(self) -> None:
                if hasattr(self._stream, "close"):
                    self._stream.close()

        ranged_stream = RangedStream(file_obj, content_length)
        response = FileResponse(
            ranged_stream,
            status=206,
            as_attachment=False,
            filename=clean_name,
            content_type=content_type,
        )
        response["Content-Range"] = f"bytes {start}-{end}/{total_size}"
        response["Content-Length"] = str(content_length)
        response["Accept-Ranges"] = "bytes"
        self._apply_security_headers(response)
        return response

    def _range_not_satisfiable(
        self, total_size: int, file_obj: Any = None
    ) -> HttpResponse:
        if file_obj is not None and hasattr(file_obj, "close"):
            file_obj.close()
        response = HttpResponse(status=416)
        response["Content-Range"] = f"bytes */{total_size}"
        return response

    def _apply_security_headers(self, response: HttpResponseBase) -> None:
        response["Content-Security-Policy"] = CSP_VIEWER_POLICY
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = (
            "private, no-cache, no-store, must-revalidate"
        )
        response["X-Frame-Options"] = "SAMEORIGIN"
