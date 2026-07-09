<?php
namespace Neplatic\Services;

use Predis\Client;

/**
 * Servicio centralizado para la gestión de Redis.
 * Maneja el almacenamiento en caché de respuestas API y actúa como
 * publicador en la arquitectura orientada a eventos (Event-Driven Architecture).
 */
class RedisService
{
    private static $instance = null;
    private $client;
    
    /**
     * Constructor privado (Patrón Singleton).
     * Configura el cliente de Predis leyendo las variables de entorno,
     * incluyendo soporte para Prefijos, optimizando múltiples apps en un mismo Redis.
     */
    private function __construct()
    {
        $this->client = new Client([
            'scheme' => 'tcp',
            'host'   => $_ENV['REDIS_HOST'],
            'port'   => (int)$_ENV['REDIS_PORT'],
            'password' => $_ENV['REDIS_PASSWORD'] ?: null,
        ], [
            'parameters' => [
                'read_write_timeout' => -1,   // ← AQUÍ está el cambio
            ]
        ]);
    }
    
    /**
     * Retorna la única instancia activa del servicio Redis.
     * @return self
     */
    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new RedisService();
        }
        return self::$instance;
    }
    
    /**
     * Proporciona acceso directo al cliente interno de Predis para comandos avanzados.
     * 
     * @return \Predis\Client
     */
    public function getClient()
    {
        return $this->client;
    }
    
    /**
     * Publica un mensaje (evento) en un canal de Redis (Pub/Sub).
     * Usado para notificar a otras aplicaciones (ej. escritorio C#) en tiempo real.
     * 
     * @param string $channel Nombre del canal
     * @param string $message Mensaje en texto/JSON
     */
    public function publish($channel, $message)
    {
        $data = json_encode($message);
        return $this->client->publish($channel, $data);
    }
    
    /**
     * Guarda un valor en Redis (caché). Lo convierte a JSON automáticamente.
     * 
     * @param string $key Clave de almacenamiento
     * @param mixed $value Datos a guardar
     * @param int $ttl Segundos de vida útil (Time To Live), por defecto 3600s
     */
    public function set($key, $value, $ttl = 3600)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $this->client->setex($fullKey, $ttl, json_encode($value));
    }
    
    /**
     * Recupera un valor almacenado y lo decodifica de JSON si corresponde.
     * 
     * @param string $key
     * @return mixed Datos decodificados o null si no existe/expiró
     */
    public function get($key)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $data = $this->client->get($fullKey);
        return $data ? json_decode($data, true) : null;
    }
    
    /**
     * Elimina una clave explícitamente, útil para invalidación de caché tras una actualización.
     * 
     * @param string $key
     */
    public function delete($key)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $this->client->del([$fullKey]);
    }
    
    public function deleteByPattern($pattern)
    {
        $fullPattern = $_ENV['REDIS_PREFIX'] . $pattern;
        $keys = $this->client->keys($fullPattern);
        if (!empty($keys)) {
            $this->client->del($keys);
        }
    }
}