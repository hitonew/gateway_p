# Guía de despliegue en VPS Linux

## 1. Preparación del servidor
- Actualizar paquetes base:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```
- Instalar dependencias necesarias para Docker:
  ```bash
  sudo apt install -y ca-certificates curl gnupg lsb-release
  ```

## 2. Instalar Docker Engine
- Añadir la clave GPG oficial de Docker y el repositorio estable:
  ```bash
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt update
  ```
- Instalar Docker Engine y plugins de Compose:
  ```bash
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  ```
- Habilitar y arrancar el servicio Docker:
  ```bash
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER
  # Cerrar sesión y volver a ingresar para aplicar el grupo docker
  ```

## 3. Clonar el proyecto
- Seleccionar directorio de trabajo y clonar el repositorio:
  ```bash
  git clone <URL_DEL_REPO> billetera2026
  cd billetera2026/pagoflex/gateway_p
  ```
- Opcional: copiar archivo `.env` si existe en origen o configurarlo según necesidades.

## 4. Verificar servicios locales en conflicto
- Asegurarse de que no haya Redis ni Postgres locales ocupando los puertos 6379 y 5432:
  ```bash
  sudo systemctl stop redis-server postgresql || true
  sudo systemctl disable redis-server postgresql || true
  ss -ltnp | grep -E "(6379|5432)" || true
  ```

## 5. Construir y levantar la infraestructura Docker
- Construir imágenes y lanzar servicios:
  ```bash
  docker compose up -d --build
  ```
- Confirmar que los contenedores estén sanos:
  ```bash
  docker compose ps
  ```

## 6. Acceso a la aplicación
- API disponible en `http://<IP_VPS>:8000`.
- Postgres expuesto en el puerto 5432 (credenciales en `docker-compose.yml`).
- Redis expuesto en el puerto 6379.

## 7. Ejecutar pruebas dentro del contenedor API
- Instalar utilidades necesarias (solo la primera vez):
  ```bash
  docker compose exec api pip install pytest httpx
  ```
- Ejecutar suite de pruebas con el entorno de la aplicación:
  ```bash
  docker compose exec -e PYTHONPATH=/app api pytest tests/test_api.py
  ```

## 8. Mantenimiento básico
- Ver logs en vivo:
  ```bash
  docker compose logs -f api scheduler
  ```
- Reiniciar servicios:
  ```bash
  docker compose restart
  ```
- Detener y limpiar contenedores:
  ```bash
  docker compose down
  ```

> Nota: Si se actualiza `requirements.txt`, reconstruir la imagen con `docker compose build api scheduler` antes de volver a levantar los servicios.
