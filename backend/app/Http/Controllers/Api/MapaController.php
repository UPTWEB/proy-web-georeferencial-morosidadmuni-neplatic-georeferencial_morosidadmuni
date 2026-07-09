<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;

class MapaController
{
    public function getSectores(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        
        $sql = "SELECT 
                    id_sector,
                    codigo_sector,
                    nombre_sector,
                    ST_AsGeoJSON(geom) as geojson,
                    total_contribuyentes_morosos,
                    total_lotes_con_deuda,
                    porcentaje_lotes_morosos,
                    total_deudas,
                    total_deudas_coactiva,
                    total_deudas_ordinaria,
                    monto_total_pendiente,
                    monto_coactiva,
                    monto_ordinaria,
                    color_predominante,
                    estado_predominante,
                    porcentaje_monto_coactiva,
                    notificaciones_30dias,
                    tasa_efectividad_notificacion
                FROM neplatic.mv_calor_sector
                ORDER BY monto_total_pendiente DESC";
        
        $sectores = $db->fetchAll($sql);
        
        foreach ($sectores as &$sector) {
            $sector['geojson'] = json_decode($sector['geojson']);
        }
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $sectores
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getManzanas(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        $sectorId = $params['sector_id'] ?? null;
        
        $sql = "SELECT 
                    id_manzana,
                    codigo_manzana,
                    id_sector,
                    codigo_sector,
                    nombre_sector,
                    ST_AsGeoJSON(geom) as geojson,
                    total_lotes,
                    total_lotes_con_deuda,
                    porcentaje_lotes_morosos,
                    total_deudas,
                    total_deudas_coactiva,
                    total_deudas_ordinaria,
                    monto_total_pendiente,
                    monto_coactiva,
                    monto_ordinaria,
                    color_predominante,
                    estado_predominante
                FROM neplatic.mv_calor_manzana";
        
        if ($sectorId) {
            $sql .= " WHERE id_sector = :sector_id";
            $manzanas = $db->fetchAll($sql, ['sector_id' => $sectorId]);
        } else {
            $manzanas = $db->fetchAll($sql);
        }
        
        foreach ($manzanas as &$manzana) {
            $manzana['geojson'] = json_decode($manzana['geojson']);
        }
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $manzanas
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getLotes(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        $manzanaId = $params['manzana_id'] ?? null;
        $sectorId = $params['sector_id'] ?? null;
        
        $sql = "SELECT 
                    id_lote,
                    codigo_lote,
                    direccion,
                    numero_municipal,
                    uso,
                    latitud,
                    longitud,
                    ST_AsGeoJSON(geom) as geojson,
                    ST_AsGeoJSON(punto) as punto_geojson,
                    area_terreno_m2,
                    id_manzana,
                    codigo_manzana,
                    id_sector,
                    codigo_sector,
                    nombre_sector,
                    total_deudas,
                    total_deudas_coactiva,
                    total_deudas_ordinaria,
                    monto_total_pendiente,
                    monto_coactiva,
                    monto_ordinaria,
                    color_predominante,
                    estado_predominante,
                    promedio_dias_mora,
                    tipos_tributo
                FROM neplatic.mv_calor_lote";
        
        $conditions = [];
        $params_array = [];
        
        if ($manzanaId) {
            $conditions[] = "id_manzana = :manzana_id";
            $params_array['manzana_id'] = $manzanaId;
        }
        
        if ($sectorId) {
            $conditions[] = "id_sector = :sector_id";
            $params_array['sector_id'] = $sectorId;
        }
        
        if (!empty($conditions)) {
            $sql .= " WHERE " . implode(" AND ", $conditions);
        }
        
        $sql .= " ORDER BY monto_total_pendiente DESC LIMIT 1000";
        
        $lotes = $db->fetchAll($sql, $params_array);
        
        foreach ($lotes as &$lote) {
            $lote['geojson'] = $lote['geojson'] ? json_decode($lote['geojson']) : null;
            $lote['punto_geojson'] = $lote['punto_geojson'] ? json_decode($lote['punto_geojson']) : null;
        }
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $lotes
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getHeatmapData(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        
        $sql = "SELECT 
                    l.id_lote,
                    l.latitud,
                    l.longitud,
                    l.monto_total_pendiente as intensidad,
                    l.estado_predominante
                FROM neplatic.mv_calor_lote l
                WHERE l.latitud IS NOT NULL AND l.longitud IS NOT NULL
                AND l.monto_total_pendiente > 0
                LIMIT 15000";
        
        $puntos = $db->fetchAll($sql);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $puntos
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}