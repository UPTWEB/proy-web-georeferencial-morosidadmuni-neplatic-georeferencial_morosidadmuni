# Historial de Cambios (Changelog)

## Mejoras Técnicas - Migración a ArcGIS y Fixes (Reciente)

En esta actualización se realizaron tres mejoras principales al sistema Neplatic:

### 1. Migración de Mapa a ArcGIS Maps SDK
- Se reemplazó la librería `Leaflet` por el **ArcGIS Maps SDK for JavaScript 4.x**.
- **Archivo Modificado:** `frontend/index.html` (Se agregó CDN de ArcGIS).
- **Archivo Reescrito:** `frontend/src/views/MapaMorosidad.vue`. Ahora utiliza `esri/Map`, `esri/views/MapView`, `esri/Graphic` y `esri/layers/GraphicsLayer`.
- **Beneficio:** Se integró la potencia de la librería de Esri, manteniendo la misma funcionalidad de coloreo condicional (basado en morosidad coactiva/ordinaria) y visualización de popups con métricas de los sectores.

### 2. Uso de Vistas Materializadas en Backend
- Se verificó que los controladores (`DashboardController` y `MapaController`) ya estaban utilizando las vistas gerenciales (`v_dashboard_gerencial`, `v_evolucion_morosidad`, `v_top_deudores`) y vistas materializadas espaciales (`mv_calor_sector`, `mv_calor_manzana`, `mv_calor_lote`).
- **RutaController:** Se documentó que el `RutaController` aún utiliza operaciones `JOIN` debido a que no existe una vista predefinida para las rutas complejas en la BD. Esta es la recomendación a futuro para evitar alterar el esquema actual.

### 3. Solución de Reactividad en Login/Logout (Navbar Stale State)
- Se corrigió un error por el cual la barra de navegación no actualizaba el nombre del usuario después de cambiar de sesión, debido a que `App.vue` solo leía el `localStorage` una vez.
- **Archivos Modificados:** `frontend/src/views/Login.vue` y `frontend/src/App.vue`.
- **Solución implementada:** Se cambió la navegación por Vue Router (`router.push`) a redirecciones completas vía `window.location.href = '/dashboard'` (y `/login`). Esta es la opción más sencilla y robusta para garantizar que toda la SPA se recargue y tome el nuevo token/usuario del caché del navegador sin introducir más complejidad como Pinia o EventBus.

### 4. Documentación y Estandarización de Código
- Se agregaron comentarios profesionales estilo JSDoc y PHPDoc a todos los archivos críticos: `Database.php`, `RedisService.php`, `RutaController.php`, `AuthController.php`, `SoporteController.php`, `MapaMorosidad.vue`, `MisRutas.vue`, `Monitoreo.vue`, `Soporte.vue`, `router/index.js` y `api/index.js`.
- Se generó el archivo `README.md` que incluye instrucciones completas sobre arquitectura, base de datos y cómo levantar ambos entornos (frontend y backend).
- Se generó este archivo `CHANGES.md`.

### 5. Configuración de Despliegue y Enrutamiento Base
- Se corrigió el archivo `.htaccess` del backend agregando `DirectoryIndex index.html` para que el servidor web priorice la carga de la aplicación Vue (Frontend) en la raíz (`/`) del dominio, en vez de cargar el `index.php` del API.
- Se redefinió la ruta del health-check base en `backend/index.php` de `$app->get('/', ...)` a `$app->get('/api', ...)` para liberar el root path y evitar conflictos.
