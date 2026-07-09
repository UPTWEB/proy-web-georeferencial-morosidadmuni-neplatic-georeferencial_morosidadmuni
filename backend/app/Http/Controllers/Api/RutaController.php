<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;
use Neplatic\Services\RedisService;

/**
 * Controlador para la gestión de rutas y ubicación de notificadores.
 * Proporciona endpoints para asignar, listar y actualizar el estado de las visitas en campo,
 * además de rastrear la ubicación GPS en tiempo real usando Redis.
 */
class RutaController
{
    /**
     * Obtiene la ruta asignada al notificador (rol NORMAL) para una fecha específica.
     * Busca primero en caché (Redis) para reducir la carga de la BD; si no existe,
     * la consulta en la vista `v_ruta_asignada` y la almacena en caché.
     *
     * @param Request $request
     * @param Response $response
     * @return Response Retorna JSON con las deudas asignadas o un objeto vacío.
     */
    public function getMisRutas(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        $params = $request->getQueryParams();
        $fecha = $params['fecha'] ?? date('Y-m-d');
        
        // Solo usuarios con rol NORMAL pueden ver rutas
        if ($usuario['rol_codigo'] !== 'NORMAL') {
            $response->getBody()->write(json_encode([
                'success' => false,
                'error' => 'Solo notificadores pueden acceder a sus rutas'
            ]));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        // Intentar obtener de caché Redis
        $redis = RedisService::getInstance();
        $cacheKey = "rutas_usuario_{$usuarioId}_{$fecha}";
        $cachedData = $redis->get($cacheKey);
        
        if ($cachedData) {
            $response->getBody()->write(json_encode([
                'success' => true,
                'data' => $cachedData,
                'cached' => true
            ]));
            return $response->withHeader('Content-Type', 'application/json');
        }
        
        // Consultar base de datos
        $db = Database::getInstance();
        
        $sql = "SELECT * FROM neplatic.v_ruta_asignada 
                WHERE id_usuario = :usuario_id AND fecha_ruta = :fecha";
        
        $ruta = $db->fetchOne($sql, ['usuario_id' => $usuarioId, 'fecha' => $fecha]);
        
        if (!$ruta) {
            $ruta = [
                'id_ruta' => null,
                'fecha_ruta' => $fecha,
                'estado_ruta' => 'SIN_RUTA',
                'total_deudas' => 0,
                'deudas_atendidas' => 0,
                'deudas_efectivas' => 0,
                'distancia_estimada_km' => 0,
                'deudas' => []
            ];
        } else {
            $ruta['deudas'] = json_decode($ruta['deudas'], true);
        }
        
        // Guardar en caché (TTL 1 hora)
        $redis->set($cacheKey, $ruta, 3600);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $ruta,
            'cached' => false
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    /**
     * Recupera las rutas futuras (o en curso) asignadas a un notificador.
     * Se usa para previsualizar el trabajo planificado en días siguientes.
     * 
     * @param Request $request
     * @param Response $response
     * @return Response JSON con una lista de rutas planificadas.
     */
    public function getRutasFuturas(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        
        if ($usuario['rol_codigo'] !== 'NORMAL') {
            $response->getBody()->write(json_encode([
                'success' => false,
                'error' => 'Solo notificadores pueden acceder a sus rutas'
            ]));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        $db = Database::getInstance();
        
        $sql = "SELECT 
                    r.id_ruta,
                    r.fecha_ruta,
                    r.estado_ruta,
                    r.total_deudas,
                    r.deudas_atendidas,
                    r.deudas_efectivas,
                    r.distancia_estimada_km,
                    r.hora_inicio,
                    r.hora_fin,
                    CASE 
                        WHEN r.fecha_ruta = CURRENT_DATE THEN 'HOY'
                        WHEN r.fecha_ruta > CURRENT_DATE THEN 'FUTURA'
                        ELSE 'PASADA'
                    END as tipo
                FROM neplatic.ruta_notificacion r
                WHERE r.id_usuario = :usuario_id 
                AND r.fecha_ruta >= CURRENT_DATE
                AND r.estado_ruta IN ('PLANIFICADA', 'EN_CURSO')
                ORDER BY r.fecha_ruta ASC";
        
        $rutas = $db->fetchAll($sql, ['usuario_id' => $usuarioId]);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $rutas
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }

    /**
     * Registra el resultado de una visita de notificación en campo.
     * Guarda la acción en PostgreSQL, actualiza el estado de la deuda y emite
     * un evento a Redis (EDA) para que el Dashboard gerencial se actualice en vivo.
     * 
     * @param Request $request (body json: id_ruta, id_deuda, resultado, observacion)
     * @param Response $response
     * @return Response JSON de éxito o error HTTP 500 si falla la transacción.
     */
    public function notificar(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        
        if ($usuario['rol_codigo'] !== 'NORMAL') {
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'No autorizado']));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        $data = json_decode($request->getBody()->getContents(), true);
        $idRuta = $data['id_ruta'] ?? null;
        $idDeuda = $data['id_deuda'] ?? null;
        $resultado = $data['resultado'] ?? null;
        $observacion = $data['observacion'] ?? null;
        
        if (!$idRuta || !$idDeuda || !$resultado) {
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'Datos incompletos']));
            return $response->withStatus(400)->withHeader('Content-Type', 'application/json');
        }
        
        $db = Database::getInstance();
        $pdo = $db->getConnection();
        
        try {
            $pdo->beginTransaction();
            
            // Registrar notificación
            $stmt = $pdo->prepare("INSERT INTO neplatic.notificacion (id_deuda, id_usuario, resultado, observacion) VALUES (?, ?, ?, ?)");
            $stmt->execute([$idDeuda, $usuarioId, $resultado, $observacion]);
            
            // Actualizar ruta
            $stmt2 = $pdo->prepare("UPDATE neplatic.ruta_detalle SET fue_visitado = true, resultado_notificacion = ? WHERE id_ruta = ? AND id_deuda = ?");
            $stmt2->execute([$resultado, $idRuta, $idDeuda]);
            
            $pdo->commit();
            
            // Event Driven Architecture (EDA) - Publicar en Redis
            $redis = RedisService::getInstance();
            $redis->publish('neplatic_events', json_encode([
                'event_type' => 'visita_registrada',
                'id_ruta' => $idRuta,
                'id_deuda' => $idDeuda,
                'id_usuario' => $usuarioId,
                'timestamp' => date('Y-m-d H:i:s')
            ]));
            
            // Invalidate cache
            $fechaRuta = $pdo->query("SELECT fecha_ruta FROM neplatic.ruta_notificacion WHERE id_ruta = $idRuta")->fetchColumn();
            if ($fechaRuta) {
                $redis->delete("rutas_usuario_{$usuarioId}_{$fechaRuta}");
            }
            
            $response->getBody()->write(json_encode(['success' => true, 'message' => 'Notificación registrada con éxito']));
            return $response->withHeader('Content-Type', 'application/json');
            
        } catch (\Exception $e) {
            $pdo->rollBack();
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'Error al registrar: ' . $e->getMessage()]));
            return $response->withStatus(500)->withHeader('Content-Type', 'application/json');
        }
    }

    /**
     * Guarda la ubicación actual del notificador (lat, lng) recibida desde la app web móvil.
     * Los datos se almacenan exclusivamente en Redis con un TTL (tiempo de vida) de 5 minutos,
     * optimizando el rendimiento al evitar escrituras masivas en PostgreSQL.
     * 
     * @param Request $request
     * @param Response $response
     * @return Response
     */
    public function guardarUbicacion(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        
        $data = json_decode($request->getBody()->getContents(), true);
        $lat = $data['lat'] ?? null;
        $lng = $data['lng'] ?? null;
        
        if ($lat && $lng) {
            $redis = RedisService::getInstance();
            // Guardamos la ubicación con un TTL de 5 minutos
            $redis->set("ubicacion_usuario_{$usuarioId}", [
                'lat' => $lat,
                'lng' => $lng,
                'nombres' => $usuario['nombres'] ?? 'Notificador',
                'apellidos' => $usuario['apellidos'] ?? '',
                'timestamp' => time()
            ], 300);
        }
        
        $response->getBody()->write(json_encode(['success' => true]));
        return $response->withHeader('Content-Type', 'application/json');
    }

    /**
     * Extrae todas las ubicaciones activas de notificadores desde Redis.
     * Endpoint restringido a roles ADMIN y SUPERVISOR para monitoreo en vivo en el mapa principal.
     * 
     * @param Request $request
     * @param Response $response
     * @return Response JSON con array de ubicaciones (lat, lng, nombres, timestamp).
     */
    public function getUbicaciones(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        
        // Solo ADMIN o SUPERVISOR
        if (!in_array($usuario['rol_codigo'], ['ADMIN', 'SUPERVISOR'])) {
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'No autorizado']));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        $redis = RedisService::getInstance();
        $prefix = $_ENV['REDIS_PREFIX'] ?? '';
        $keys = $redis->getClient()->keys($prefix . 'ubicacion_usuario_*');
        $ubicaciones = [];
        
        foreach ($keys as $key) {
            $localKey = empty($prefix) ? $key : substr($key, strlen($prefix));
            $data = $redis->get($localKey); // get() already JSON decodes
            if ($data) {
                // Because we previously double-encoded or maybe just saved string, let's ensure it's array
                if (is_string($data)) {
                    $data = json_decode($data, true);
                }
                $ubicaciones[] = $data;
            }
        }
        
        $response->getBody()->write(json_encode(['success' => true, 'data' => $ubicaciones]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}