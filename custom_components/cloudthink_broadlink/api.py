"""Calls the houseproxy endpoint with the user's own exported mini-app session."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from urllib.request import Request, urlopen

_LOGGER = logging.getLogger(__name__)


class CloudThinkError(Exception):
    """A cloud command or state read failed."""


class CloudThinkAPI:
    def __init__(self, session_path: Path) -> None:
        self.session_path = session_path

    def call(self, name: str, device: dict, extra: dict | None = None, namespace: str = "DuerOS.ConnectedHome.Control") -> dict:
        # Reload the session for every call, so a renewed session can be copied
        # into place without restarting Home Assistant.
        session = json.loads(self.session_path.read_text(encoding="utf-8"))
        payload = {
            "cookie": session["cookie"],
            "appliance": {
                "additionalApplianceDetails": device["additionalApplianceDetails"],
                "applianceId": device["applianceId"],
            },
            "applianceId": device["applianceId"],
        }
        if extra:
            payload.update(extra)
        body = {
            "header": {
                "messageId": f"wxmini_{random.randrange(10**9, 10**10)}",
                "name": name,
                "namespace": namespace,
                "payloadVersion": "1",
            },
            "payload": payload,
        }
        request = Request(
            session["url"],
            data=json.dumps(body).encode("utf-8"),
            headers=session["headers"],
            method="POST",
        )
        try:
            # urllib verifies TLS certificates by default.
            with urlopen(request, timeout=15) as response:
                result = json.load(response)
        except Exception as exc:
            raise CloudThinkError(f"{name} request failed: {type(exc).__name__}") from exc
        response_name = result.get("header", {}).get("name", "")
        if response_name.endswith("Error") or response_name.endswith("Exception"):
            raise CloudThinkError(f"{name} returned {response_name}")
        return result

    def state(self, device: dict) -> dict:
        result = self.call("ReportStateRequest", device, namespace="DuerOS.ConnectedHome.Query")
        if result.get("header", {}).get("name") != "ReportStateConfirmation":
            raise CloudThinkError("Unexpected state response")
        return {
            attr["name"]: attr.get("value")
            for attr in result.get("payload", {}).get("attributes", [])
            if "name" in attr
        }

