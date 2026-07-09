<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;
use Neplatic\Services\RedisService;

/**
 * Controlador de Soporte y TI.
 * Proporciona endpoints para revisar el estado de los servicios (Redis/PostgreSQL),
 * limpiar las cachés y visualizar a todos los usuarios del sistema.
 */
class SoporteController
{
    /**
     * Verifica que el usuario tenga rol de TI, SOPORTE o ADMIN.
     * Método auxiliar (Helper) para proteger los endpoints de esta clase.
     *
     * @param Request $request
     * @param Response $response
     * @return Response|null Devuelve una Response con error 403 si no tiene permiso, null si todo está OK.
     */
    private function checkAccess(Request $request, Response $response): ?Response
    {
        $usuario = $request->getAttribute('usuario');
        if (!in_array($usuario['rol_codigo'], ['TI', 'SOPORTE', 'ADMIN'])) {
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'No autorizado para panel de soporte']));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        return null;
    }

    /**
     * Revisa el estado de salud (Health Check) de las conexiones vitales.
     * Intenta conectarse a PostgreSQL mediante PDO y a Redis enviando un PING.
     *
     * @param Request $request
     * @param Response $response
     * @return Response JSON con el status ('ok' o 'error') de BD y Redis.
     */
    public function getEstado(Request $request, Response $response): Response
    {
        if ($err = $this->checkAccess($request, $response)) return $err;

        $estado = [
            'db_conectado' => false,
            'redis_conectado' => false,
            'tiempo_respuesta_ms' => 0
        ];

        $start = microtime(true);

        try {
            $db = Database::getInstance();
            $pdo = $db->getConnection();
            $pdo->query("SELECT 1");
            $estado['db_conectado'] = true;
        } catch (\Exception $e) {
            $estado['db_error'] = $e->getMessage();
        }

        try {
            $redis = RedisService::getInstance();
            $redis->getClient()->ping();
            $estado['redis_conectado'] = true;
        } catch (\Exception $e) {
            $estado['redis_error'] = $e->getMessage();
        }

        $estado['tiempo_respuesta_ms'] = round((microtime(true) - $start) * 1000, 2);

        $response->getBody()->write(json_encode(['success' => true, 'data' => $estado]));
        return $response->withHeader('Content-Type', 'application/json');
    }

    /**
     * Limpia completamente la caché de Redis para las claves del sistema.
     * Es útil cuando hay inconsistencias de datos (ej. rutas desactualizadas)
     * para forzar a la aplicación a consultar PostgreSQL nuevamente.
     *
     * @param Request $request
     * @param Response $response
     * @return Response JSON con el total de claves eliminadas o error 500.
     */
    public function limpiarCache(Request $request, Response $response): Response
    {
        if ($err = $this->checkAccess($request, $response)) return $err;

        try {
            $redis = RedisService::getInstance();
            $prefix = $_ENV['REDIS_PREFIX'] ?? '';
            // Peligroso pero es un botón de sistema: limpia todo lo que tenga nuestro prefijo
            $keys = $redis->getClient()->keys($prefix . '*');
            if (count($keys) > 0) {
                $redis->getClient()->del($keys);
            }
            $response->getBody()->write(json_encode(['success' => true, 'message' => 'Caché de Redis limpiada ('.count($keys).' registros eliminados)']));
        } catch (\Exception $e) {
            $response->getBody()->write(json_encode(['success' => false, 'error' => $e->getMessage()]));
            return $response->withStatus(500);
        }

        return $response->withHeader('Content-Type', 'application/json');
    }

    /**
     * Obtiene el directorio general de usuarios registrados en el sistema.
     * Junta (JOIN) las tablas `usuario` y `rol_usuario` para mostrar un listado
     * administrativo (no usado para el login).
     *
     * @param Request $request
     * @param Response $response
     * @return Response JSON con el array de usuarios.
     */
    public function getUsuarios(Request $request, Response $response): Response
    {
        if ($err = $this->checkAccess($request, $response)) return $err;

        $db = Database::getInstance();
        $sql = "SELECT u.id_usuario, u.username, u.nombres, u.apellidos, u.activo as estado, r.nombre as rol_nombre, r.codigo as rol_codigo 
                FROM neplatic.usuario u 
                JOIN neplatic.rol_usuario r ON u.id_rol = r.id_rol 
                ORDER BY r.codigo ASC, u.nombres ASC";
        
        $usuarios = $db->fetchAll($sql);

        $response->getBody()->write(json_encode(['success' => true, 'data' => $usuarios]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}
