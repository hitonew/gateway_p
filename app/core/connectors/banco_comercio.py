from typing import Any, Dict
from uuid import uuid4

import httpx

from app.core.connectors.interface import ConnectorIntegration
from app.core.payments.types import (
    ConnectorResponse,
    PaymentData,
    PaymentState,
    TransferBody,
)
from config.settings import settings


class BancoComercioConnector(ConnectorIntegration):
    """Connector for Banco de Comercio transfer API."""

    auth_path = "/auth"
    transfer_path = "/movements/transfer-request"

    async def build_request(self, data: PaymentData) -> Dict[str, Any]:
        if not data.source or not data.destination or not data.transfer_body:
            raise ValueError("Transfer data incomplete; source, destination and body are required")

        body: TransferBody = data.transfer_body
        request = {
            "originId": data.origin_id or str(uuid4()),
            "from": data.source.model_dump(by_alias=True),
            "to": data.destination.model_dump(by_alias=True),
            "body": {
                "currencyId": self._map_currency(body.currency),
                "amount": float(body.amount),
                "description": body.description,
                "concept": body.concept,
            },
        }
        return request

    async def execute_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        token = await self._get_token()
        payload = {k: v for k, v in request.items() if v is not None}
        signature = self._calculate_signature(self.transfer_path, payload)

        headers = {
            "Authorization": f"Bearer {token}",
            "X-SIGNATURE": signature,
        }

        async with httpx.AsyncClient(base_url=settings.bdc_base_url, timeout=30) as client:
            response = await client.post(self.transfer_path, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def handle_response(self, response: Dict[str, Any]) -> ConnectorResponse:
        status_code = response.get("statusCode")
        status = PaymentState.FAILED
        if status_code == 0:
            status = PaymentState.AUTHORIZED

        provider_reference = response.get("dest_ori_trx_id")
        if not provider_reference:
            provider_reference = response.get("data", {}).get("request", {}).get("originId")

        return ConnectorResponse(
            status=status,
            provider_reference_id=provider_reference,
            raw_response=response,
        )

    async def _get_token(self) -> str:
        payload = {
            "clientId": settings.bdc_client_id,
            "clientSecret": settings.bdc_client_secret,
        }
        async with httpx.AsyncClient(base_url=settings.bdc_base_url, timeout=10) as client:
            response = await client.post(self.auth_path, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["data"]["accessToken"]

    def _calculate_signature(self, path: str, payload: Dict[str, Any]) -> str:
        import json
        import hmac
        import hashlib

        compact_body = json.dumps(payload, separators=(",", ":"))
        uri = f"[{path.strip('/')}]"
        message = f"{uri}{compact_body}".encode()
        secret = settings.bdc_secret_key.encode()
        signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
        return signature

    def _map_currency(self, currency_alpha: str) -> str:
        mapping = {
            "ARS": "032",
            "USD": "840",
        }
        return mapping.get(currency_alpha.upper(), currency_alpha)
