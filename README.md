# Neplatic - Sistema Georeferencial de Morosidad

Neplatic es un sistema web para la visualización, gestión y seguimiento de la morosidad en el distrito de Ciudad Nueva, Tacna. Permite a los gerentes y notificadores visualizar mapas de calor interactivos y gestionar rutas de notificación de deudas coactivas y ordinarias.

## Arquitectura

- **Frontend**: Vue 3 + Vite, `@arcgis/core` para visualización geoespacial de mapas.
- **Backend**: PHP 8.x con Slim Framework 4 para APIs REST.
- **Base de Datos**: PostgreSQL 15+ con extensión PostGIS para datos georeferenciados.
- **Caché / Colas**: Redis para manejo de caché (ej. rutas diarias) y procesamiento asíncrono de eventos de actualización.

## Estructura del Proyecto

```
/
├── backend/          # API REST en PHP (Slim)
│   ├── app/          # Controladores, Modelos, Servicios y Middleware
│   ├── config/       # Configuración de base de datos y Redis
│   ├── routes/       # Definición de endpoints
│   ├── scripts/      # Scripts de consumidor Redis
│   └── public/       # Punto de entrada (index.php)
├── frontend/         # SPA en Vue 3
│   ├── src/          # Componentes Vue, Vistas, Router, llamadas a API
│   └── .env          # Variables de entorno del cliente
├── docker/           # Configuración para levantar el proyecto con Docker
└── neplatic_corregido.sql # Script SQL con la estructura, vistas y datos iniciales
```

## Requisitos Previos

- PHP 8.1+ y Composer
- Node.js 18+ y npm
- PostgreSQL 15+ con extensión PostGIS
- Redis Server
- Extensiones PHP requeridas: `pdo_pgsql`, `redis`

## Instalación y Configuración

### 1. Base de Datos (Producción)
La base de datos PostgreSQL ya se encuentra alojada y configurada en producción con la extensión PostGIS habilitada.
El sistema se conecta a la base de datos `neplatic`.
Para interactuar con ella, la aplicación utiliza las credenciales definidas en el archivo `backend/.env`.
Asegúrate de que el servidor/VPS tenga acceso por puerto `5432` a dicha base de datos.

### 2. Backend (API)
1. Navega a la carpeta `backend` e instala las dependencias:
   ```bash
   cd backend
   composer install
   ```
2. Inicia el servidor de desarrollo en el puerto 8080:
   ```bash
   php -S localhost:8080 -t public/
   ```
3. *(Opcional)* Inicia el consumidor de eventos de Redis (para sincronización en tiempo real):
   ```bash
   php scripts/start-consumer.php
   ```

### 3. Frontend (Web)
1. Navega a la carpeta `frontend` e instala las dependencias:
   ```bash
   cd frontend
   npm install
   ```
2. Verifica el archivo `.env` para asegurar que apunta correctamente al backend local:
   ```env
   VITE_API_BASE_URL=http://localhost:8080/api
   ```
3. Inicia el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```

## Credenciales de Prueba

Para acceder al sistema, puedes utilizar el siguiente usuario de prueba:

- **Usuario**: `notificador2`
- **Contraseña**: `password`

## Endpoints Principales de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/login` | Autenticación y obtención de JWT |
| `GET`  | `/api/dashboard/kpis` | Métricas generales gerenciales |
| `GET`  | `/api/mapa/sectores` | Retorna el GeoJSON de los sectores para el mapa |
| `GET`  | `/api/rutas/mis-rutas`| Obtiene las rutas asignadas al notificador logueado |
| `GET`  | `/api/rutas/ubicaciones-activas` | Obtiene ubicación de notificadores (Para el mapa de monitoreo) |
| `POST` | `/api/soporte/limpiar-cache` | Limpia caché de Redis de la aplicación |
