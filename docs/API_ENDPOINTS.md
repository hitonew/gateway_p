# Catálogo de Endpoints

Este documento resume los endpoints HTTP disponibles en la plataforma actual. Se agrupan según el servicio FastAPI que los expone dentro del proyecto.

## 1. Servicio `app.main` (Pagoflex Middleware)

> Estado actual: Desde el 26/12/2025 el `docker-compose` del entorno (`services.api.command`) levanta esta aplicación, por lo que los endpoints siguientes están disponibles en `http://localhost:8000`.

| Método | Ruta | Descripción | Entrada principal | Respuesta (HTTP 200) |
|--------|------|-------------|-------------------|----------------------|
| GET | /health | Verificación de estado del servicio. | — | `{ "status": "ok" }` |
| POST | /api/v1/payments | Crea un pago en memoria y devuelve su representación. | JSON: `{ "amount": float, "currency": str }` | Objeto `Payment` con campos `id`, `amount`, `currency`, `status`, `created_at`, `updated_at`.
| POST | /api/v1/payments/{payment_id}/process | Procesa el pago indicado utilizando el mock gateway. | Ruta: `payment_id` (UUID) | Mismo objeto `Payment` con estado actualizado (`COMPLETED` si monto < 1000, `FAILED` en caso contrario).
| GET | /api/v1/payments/{payment_id} | Recupera un pago específico almacenado en memoria. | Ruta: `payment_id` (UUID) | Objeto `Payment` correspondiente o error 404 si no existe.

### Notas operativas
- El repositorio activo es en memoria (`InMemoryPaymentRepository`), por lo que los datos persisten solo mientras el contenedor `api` está en ejecución.
- El procesamiento simula una pasarela mediante `MockPaymentGateway`; no hay interacción con proveedores externos reales.
- Ejemplo real (26/12/2025): `POST /api/v1/payments` con `{ "amount": 100.0, "currency": "USD" }` devolvió el pago `5decdb50-25d3-4850-ba84-c5de1e41c278` con estado `PENDING`; `GET /api/v1/payments/5decdb50-25d3-4850-ba84-c5de1e41c278` confirmó el mismo estado.

## 2. Servicio `app.api_server.main` (API Server Modular)

| Método | Ruta | Descripción | Respuesta (HTTP 200) |
|--------|------|-------------|----------------------|
| GET | /health | Verificación de estado del API modular. | `{ "status": "ok", "service": "api_server" }` |
| GET | /payments/ | Placeholder informativo del módulo de pagos. | `{ "message": "Payments module" }` |
| GET | /kyc/ | Placeholder informativo del módulo KYC. | `{ "message": "KYC module" }` |

### Notas operativas
- Ambos endpoints (`/payments/` y `/kyc/`) son placeholders y no ofrecen lógica de negocio aún.
- Para exponer este servicio se debe iniciar el módulo `app.api_server.main` (no forma parte del `docker compose` por defecto).

## 3. Futuras extensiones
- Cuando se incorporen repositorios persistentes o conectores reales, actualizar este documento con los nuevos endpoints y sus contratos.
- Añadir ejemplos curl/postman y códigos de estados adicionales (400, 404, 500) en futuras iteraciones.
