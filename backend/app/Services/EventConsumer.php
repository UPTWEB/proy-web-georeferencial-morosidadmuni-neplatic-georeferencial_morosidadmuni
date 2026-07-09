<?php
namespace Neplatic\Services;

use Neplatic\Models\Database;

class EventConsumer
{
    private $redis;
    private $db;
    
    public function __construct()
    {
        $this->redis = RedisService::getInstance();
        $this->db = Database::getInstance();
    }
    
    public function start()
    {
        $channel = $_ENV['REDIS_CHANNEL_RUTAS'];
        
        echo "\n";
        echo "╔════════════════════════════════════════════════════════════════╗\n";
        echo "║     NEPLATIC WEB - Event Consumer (Escuchando al DESKTOP)      ║\n";
        echo "╠════════════════════════════════════════════════════════════════╣\n";
        echo "║  Canal: " . str_pad($channel, 48) . "║\n";
        echo "║  Estado: ESCUCHANDO                                           ║\n";
        echo "║  Presiona Ctrl+C para detener                                  ║\n";
        echo "╚════════════════════════════════════════════════════════════════╝\n\n";
        
        $pubsub = $this->redis->getClient()->pubSubLoop();
        $pubsub->subscribe($channel);
        
        foreach ($pubsub as $message) {
            if ($message->kind === 'message') {
                $this->handleEvent($message->payload, $message->channel);
            } elseif ($message->kind === 'unsubscribe') {
                break;
            }
        }
    }
    
    private function handleEvent($message, $channel)
    {
        $timestamp = date('Y-m-d H:i:s');
        echo "[$timestamp]  Evento recibido en canal: $channel\n";
        
        $event = json_decode($message, true);
        
        if (!$event) {
            echo "[$timestamp]  Error: Evento mal formado\n";
            return;
        }
        
        echo "[$timestamp]  Tipo: " . ($event['event_type'] ?? 'desconocido') . "\n";
        echo "[$timestamp]  Aggregate ID: " . ($event['aggregate_id'] ?? 'N/A') . "\n";
        
        $eventType = $event['event_type'] ?? '';
        if ($eventType === 'RutaAsignada') {
            $this->handleRutaAsignada($event);
        } elseif ($eventType === 'MorosidadActualizada') {
            $this->handleMorosidadActualizada($event);
        }
    }
    
    private function handleMorosidadActualizada($event)
    {
        $timestamp = date('Y-m-d H:i:s');
        echo "[$timestamp]  Procesando MorosidadActualizada (Refrescando mapas)...\n";
        
        try {
            // Llamar a la función de la BD que refresca las vistas materializadas
            $this->db->query("SELECT neplatic.refrescar_mapas_calor()");
            echo "[$timestamp]  Mapas de calor refrescados exitosamente.\n";
        } catch (\Exception $e) {
            echo "[$timestamp]  Error al refrescar mapas: " . $e->getMessage() . "\n";
        }
    }
    
    private function handleRutaAsignada($event)
    {
        $payload = $event['payload'];
        $idUsuario = $payload['id_usuario'] ?? null;
        $idRuta = $payload['id_ruta'] ?? null;
        $fechaRuta = $payload['fecha_ruta'] ?? date('Y-m-d');
        
        $timestamp = date('Y-m-d H:i:s');
        echo "[$timestamp]  Procesando RutaAsignada:\n";
        echo "   ├─ ID Ruta: $idRuta\n";
        echo "   ├─ ID Usuario: $idUsuario\n";
        echo "   └─ Fecha: $fechaRuta\n";
        
        if ($idUsuario) {
            $redis = RedisService::getInstance();
            $cacheKey = "rutas_usuario_{$idUsuario}_{$fechaRuta}";
            $redis->delete($cacheKey);
            $redis->deleteByPattern("rutas_usuario_{$idUsuario}_*");
            echo "[$timestamp]  Caché invalidado para usuario $idUsuario\n";
        }
        
        echo "[$timestamp]  Evento procesado correctamente\n";
    }
}