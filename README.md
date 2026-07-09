# Neplatic Desktop – Sistema de Administración de Morosidad Tributaria

**Neplatic Desktop** es la aplicación de administración del sistema georreferencial de morosidad de la Municipalidad Distrital de Ciudad Nueva (Tacna).  
Este programa (desarrollado en Python + Tkinter) es el **único componente con capacidad de escritura** en la base de datos y se encarga de:

- Ejecutar el proceso ETL desde Oracle a PostgreSQL.
- Gestionar usuarios y roles.
- Segmentar contribuyentes morosos.
- Generar rutas de notificación optimizadas (algoritmo de priorización).
- Publicar eventos de rutas asignadas a través de un **broker Redis**.
- Producir reportes en PDF y Excel.

> **Nota:** El sistema web (lectura de mapas y dashboards) es independiente; este repositorio contiene solo la aplicación de escritorio.

---

## 📋 Requerimientos funcionales (basados en FD03)

| ID     | Descripción                                                                 | Prioridad |
|--------|-----------------------------------------------------------------------------|-----------|
| RF-01  | Módulo ETL automatizado que extraiga datos desde Oracle (solo lectura) y los cargue en PostgreSQL/PostGIS. | Alta |
| RF-05  | Segmentación de contribuyentes morosos por monto, tipo de tributo, antigüedad y etapa de cobranza. | Alta |
| RF-06  | Algoritmo configurable de priorización para generar rutas de notificación optimizadas según concentración geográfica de morosidad. | Media |
| RF-09  | Generación y descarga de reportes en PDF y Excel (listados de deudores, KPIs, rutas). | Media |
| RF-11  | Gestión de usuarios: crear, modificar, desactivar cuentas y asignar roles (Administrador / Normal). | Alta |
| RF-12  | Autenticación obligatoria (usuario+contraseña) y control de acceso por rol. | Alta |

---

## ⚙️ Requerimientos no funcionales (relevantes para el desktop)

| ID     | Descripción                                                                 | Relevancia |
|--------|-----------------------------------------------------------------------------|------------|
| RNF-01 | Seguridad: cifrado de contraseñas con bcrypt, consultas parametrizadas, comunicación segura con el broker. | Crítica |
| RNF-05 | Integración con Oracle **exclusivamente en modo lectura**; nunca modificar el sistema legacy. | Crítica |
| RNF-06 | Proyecto debe completarse en máximo 4 meses (16/03/2026 – 24/06/2026). | Alta |
| RNF-07 | Presupuesto de desarrollo no mayor a S/ 30,000. | Alta |

---

## 📜 Reglas de negocio implementadas

1. La base de datos Oracle es la **fuente oficial**; el desktop solo realiza consultas `SELECT` sobre ella.
2. El proceso ETL debe registrar logs de ejecución y errores en la tabla `log_sistema`.
3. Solo los usuarios con rol `Administrador` pueden generar reportes, modificar parámetros de segmentación y gestionar usuarios.
4. La desactivación de usuarios no elimina registros históricos (se usa columna `activo` en lugar de `DELETE`).
5. Después de crear una ruta de notificación, el desktop **publica un evento** en el broker Redis para notificar al sistema web.

---

## 🔌 Broker de mensajería (Redis)

El desktop utiliza **Redis Pub/Sub** como broker de eventos. Cada vez que un administrador genera y asigna una ruta, se publica un evento en el canal `neplatic.rutas`.

### Configuración de Redis (acceso remoto)

| Parámetro       | Valor                    |
|----------------|--------------------------|
| Host           | `149.34.48.115`          |
| Puerto         | `6379`                   |
| Contraseña     | `Upt2026`                |

### Estructura del evento (JSON)
```json
{
  "event_type": "RutaAsignada",
  "aggregate_id": "ruta_123",
  "payload": {
    "id_ruta": 123,
    "id_usuario": 5,
    "fecha_ruta": "2026-05-27",
    "deudas": [101, 102, 103]
  }
}
Conexión desde Python (publicación)
python
import redis
import json

r = redis.Redis(
    host='149.34.48.115',
    port=6379,
    password='Upt2026',
    decode_responses=True
)

evento = {
    "event_type": "RutaAsignada",
    "aggregate_id": "ruta_123",
    "payload": {
        "id_ruta": 123,
        "id_usuario": 5,
        "fecha_ruta": "2026-05-27",
        "deudas": [101, 102, 103]
    }
}
r.publish('neplatic.rutas', json.dumps(evento))
Verificación de conectividad desde el VPS
bash
redis-cli -h 149.34.48.115 -p 6379 -a Upt2026 PING
# Respuesta esperada: PONG
🗄️ Base de datos PostgreSQL (acceso remoto)
Parámetros de conexión
Parámetro	Valor
Host	178.238.228.92
Puerto	5432
Base de datos	neplatic
Esquema	neplatic
Usuarios y permisos
Usuario	Contraseña	Permisos	Uso principal
neplatic_app	Upt2026	Lectura/escritura (CRUD)	Desktop (administración, ETL, generación de rutas)
neplatic_readonly	Upt2026	Solo lectura (SELECT)	Sistema web (dashboards, consultas públicas)
Prueba de conexión desde línea de comandos
bash
psql -h 178.238.228.92 -p 5432 -U neplatic_app -d neplatic
# Contraseña: Upt2026
Conexión desde Python (psycopg2)
python
import psycopg2

conn = psycopg2.connect(
    host="178.238.228.92",
    port=5432,
    dbname="neplatic",
    user="neplatic_app",
    password="Upt2026"
)
Variables de entorno (archivo .env del desktop)
ini
# PostgreSQL
DB_HOST=178.238.228.92
DB_PORT=5432
DB_NAME=neplatic
DB_USER=neplatic_app
DB_PASS=Upt2026

# Oracle (sistema legacy, solo lectura)
ORACLE_DSN=localhost/orcl
ORACLE_USER=readonly_user
ORACLE_PASS=********

# Redis
REDIS_HOST=149.34.48.115
REDIS_PORT=6379
REDIS_PASSWORD=Upt2026
🗃️ Estructura completa de la base de datos (neplatic)
La base de datos utiliza PostgreSQL 15+ con la extensión PostGIS. A continuación se describen todas las tablas, vistas y vistas materializadas.

Tablas de soporte (catálogos)
Tabla	Descripción
estado_cobranza	Etapas de cobranza con color asignado (sin_proceso → azul, ordinaria → guinda, coactiva → rojo).
tipo_tributo	Clasificación de tributos (Arbitrios, Predial, Alcabala, Otros).
rol_usuario	Roles de acceso (ADMIN, SUPERVISOR, NORMAL, TI).
estado_notificacion	Resultados de visita (Notificado, Ausente, Dirección errónea, etc.).
tipo_documento	Tipos de documento de identidad (DNI, RUC, Carnet de Extranjería).
Tablas geográficas
Tabla	Descripción
sector	Sectores geográficos del distrito (polígonos).
manzana	Manzanas catastrales asociadas a un sector.
lote	Lotes/predios catastrales con geometría, dirección, uso y punto central.
via	Vías principales (líneas).
Tablas maestras del negocio
Tabla	Descripción
contribuyente	Contribuyentes registrados (persona natural o jurídica).
contribuyente_lote	Relación muchos a muchos entre contribuyentes y lotes.
deuda	Deudas tributarias replicadas desde Oracle (monto, saldo, fechas, estado de cobranza).
historial_estado_deuda	Seguimiento de cambios de etapa en cada deuda.
Tablas de operación del sistema
Tabla	Descripción
usuario	Usuarios del sistema Neplatic (hash de contraseña, rol, sector asignado).
sesion_usuario	Registro de sesiones activas (tokens, IP, user-agent).
ruta_notificacion	Rutas diarias de notificación asignadas a cada notificador.
ruta_detalle	Detalle ordenado de deudas a visitar en una ruta.
notificacion	Registro de visitas en campo (geolocalización, resultado, evidencia).
outbox_evento	Tabla para entrega confiable de eventos de dominio (patrón Outbox).
log_sistema	Registro de eventos y errores del sistema.
parametro	Parámetros configurables (versión, radios, intentos, etc.).
Vistas no materializadas
Vista	Descripción
v_morosidad_sector	Morosidad agregada por sector (deuda total, colores, efectividad de notificaciones).
v_morosidad_manzana	Morosidad a nivel de manzana.
v_morosidad_lote	Morosidad detallada por lote/predio.
v_evolucion_morosidad	Evolución mensual de la morosidad por etapa (para gráficos).
v_top_deudores	Ranking de los mayores contribuyentes morosos.
v_dashboard_gerencial	KPIs principales para el dashboard ejecutivo.
Vistas materializadas (para rendimiento en mapas de calor)
Vista materializada	Descripción
mv_calor_sector	Datos de morosidad por sector (refrescable).
mv_calor_manzana	Datos de morosidad por manzana (refrescable).
mv_calor_lote	Datos de morosidad por lote (refrescable).
Función para refrescar vistas materializadas:

sql
SELECT refrescar_mapas_calor();
🧪 Estructura del código (Python + Tkinter)
text
neplatic-desktop/
├── src/
│   ├── main.py
│   ├── controllers/
│   │   ├── auth_controller.py
│   │   ├── ruta_controller.py
│   │   └── usuario_controller.py
│   ├── models/
│   │   ├── database.py
│   │   ├── deuda.py
│   │   └── usuario.py
│   ├── services/
│   │   ├── route_optimizer.py      # RF-06
│   │   ├── event_publisher.py      # publica eventos Redis
│   │   ├── report_generator.py     # RF-09
│   │   └── etl/                    # RF-01
│   ├── views/
│   │   ├── login_view.py
│   │   ├── usuarios_view.py
│   │   └── rutas_view.py
│   └── utils/
│       ├── config.py
│       └── logger.py
├── requirements.txt
└── setup.py
Librerías necesarias (requirements.txt)
text
psycopg2-binary
cx_Oracle
redis
bcrypt
reportlab
openpyxl
Pillow
pandas
tkinter

---

## Empaquetado Windows y publicacion en GitHub Releases

La aplicacion de escritorio puede distribuirse como un ejecutable para Windows usando PyInstaller.
No se debe subir el archivo `.env` al repositorio porque contiene credenciales reales.

### Generar el ejecutable

```powershell
cd C:\Users\USUARIO\Documents\NEPLATIC_GP
.\.venv\Scripts\Activate.ps1
.\scripts\build_windows_release.ps1
```

El paquete listo para publicar queda en:

```text
release\NeplaticDesktop-Windows.zip
```

### Publicar como release en GitHub

1. Subir los cambios del codigo fuente al repositorio.
2. Entrar al repositorio en GitHub.
3. Ir a `Releases`.
4. Crear un nuevo release, por ejemplo `v1.0.0-windows`.
5. Adjuntar el archivo `release\NeplaticDesktop-Windows.zip` en `Assets`.
6. Publicar el release.

El archivo `.zip` incluye `NeplaticDesktop.exe`, `.env.example` y `README-WINDOWS.md`.
Cada equipo debe crear su propio `.env` a partir de `.env.example`.
