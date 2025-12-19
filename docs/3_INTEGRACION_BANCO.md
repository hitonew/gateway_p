# Guía de Integración con Bancos (Connectors)

Pagoflex usa una arquitectura de adaptadores para comunicarse con bancos y PSPs.

## Interface `ConnectorIntegration`
Todo nuevo banco debe implementar la clase abstracta definida en `app/core/connectors/interface.py`.

```python
class ConnectorIntegration(ABC):
    async def build_request(self, data: PaymentData) -> Dict: ...
    async def execute_request(self, request: Dict) -> Dict: ...
    async def handle_response(self, response: Dict) -> ConnectorResponse: ...
```

## Pasos para Integrar "Banco X"

### 1. Crear el Adaptador
Crear archivo `app/connectors/banco_x.py`:

```python
from app.core.connectors.interface import ConnectorIntegration

class BancoXConnector(ConnectorIntegration):
    async def build_request(self, data: PaymentData):
        return {
            "amount": data.amount,
            "ref": str(data.payment_id),
            "callback_url": settings.WEBHOOK_BASE_URL
        }

    async def execute_request(self, request):
        # Usar httpx o similar
        async with httpx.AsyncClient() as client:
            return await client.post("https://api.bancox.com/pay", json=request)

    async def handle_response(self, response):
        status = PaymentState.FAILED
        if response["status"] == "OK":
            status = PaymentState.PENDING # Async processing
        
        return ConnectorResponse(
            status=status,
            provider_reference_id=response["id"]
        )
```

### 2. Registrar el Conector
En el factory de conectores (a implementar en `app/core/connectors/factory.py`), registrar la clave `"BANCO_X"` apuntando a esta clase.

### 3. Configurar Credenciales
Agregar a `settings.py` o base de datos de configuración cifrada:
- `BANCOX_API_KEY`
- `BANCOX_SECRET`

### 4. Implementar Webhook
El banco notificará el resultado final asíncronamente.
- Crear endpoint `POST /webhooks/bancox`
- Validar firma criptográfica del banco.
- Correlacionar `tx_id` y actualizar el estado de la `PaymentOperation`.
