from __future__ import annotations

from json import JSONDecodeError as StdJSONDecodeError
from typing import Tuple

from requests import Response

try:
    from simplejson.errors import JSONDecodeError as SimpleJSONDecodeError  # type: ignore
except Exception:  # pragma: no cover - fallback when simplejson is unavailable
    SimpleJSONDecodeError = StdJSONDecodeError

from odoo import _, models

JSON_ERRORS: Tuple[type[Exception], ...] = (
    SimpleJSONDecodeError,
    StdJSONDecodeError,
    ValueError,
)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    def _send_api_request(
        self, method, endpoint, *, params=None, data=None, json=None, reference=None, **kwargs
    ):
        """Inherit to ensure a ValidationError is raised on JSONDecodeError.

        The core test 'test_parsing_non_json_response_falls_back_to_text_response'
        expects a ValidationError, while environment-specific JSON/Requests
        versions can raise a JSONDecodeError.
        """
        try:
            return super()._send_api_request(
                method, endpoint, params=params, data=data, json=json, reference=reference, **kwargs
            )
        except JSON_ERRORS as e:
            from odoo.exceptions import ValidationError
            raise ValidationError(str(e))

    def _parse_response_error(self, response: Response) -> str:
        """Fallback to response text when JSON parsing fails.

        Odoo's payment test suite expects a ValidationError when the provider
        returns a non-JSON payload. Some environments bubble a JSONDecodeError
        instead; we normalize by returning the raw text (or a minimal reason)
        so the calling code raises the expected ValidationError.
        """
        try:
            return super()._parse_response_error(response)
        except JSON_ERRORS:
            text = (getattr(response, "text", "") or "").strip()
            if text:
                return text
            reason = getattr(response, "reason", None)
            status = getattr(response, "status_code", None)
            return str(reason or status or _("Unable to parse provider response."))
