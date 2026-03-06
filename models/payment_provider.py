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
