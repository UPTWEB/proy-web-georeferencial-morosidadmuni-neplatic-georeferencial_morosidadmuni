<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;

class DashboardController
{
    public function getKPIs(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        
        $anio = $params['anio'] ?? date('Y');
        $periodo = $params['periodo'] ?? 'ANUAL';
        
        $dateCondition = "AND EXTRACT(YEAR FROM d.fecha_vencimiento) = :anio";
        $queryParams = ['anio' => $anio];
        
        if ($periodo === 'S1') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) <= 6";
        } elseif ($periodo === 'S2') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) > 6";
        } elseif ($periodo === 'T1') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 1 AND 3";
        } elseif ($periodo === 'T2') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 4 AND 6";
        } elseif ($periodo === 'T3') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 7 AND 9";
        } elseif ($periodo === 'T4') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 10 AND 12";
        } elseif (preg_match('/^M([1-9]|1[0-2])$/', $periodo, $matches)) {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) = " . (int)$matches[1];
        }
        
        $kpis = [];

        // Deuda Total Pendiente (estados 2: Ordinaria y 3: Coactiva)
        $sqlDeudaTotal = "SELECT COALESCE(SUM(saldo_pendiente), 0) as total FROM neplatic.deuda d WHERE d.id_estado_cobranza IN (2, 3) $dateCondition";
        $kpis['deuda_total_pendiente'] = (float) $db->fetchOne($sqlDeudaTotal, $queryParams)['total'];
        
        // Deuda Coactiva (estado 3)
        $sqlDeudaCoactiva = "SELECT COALESCE(SUM(saldo_pendiente), 0) as total FROM neplatic.deuda d WHERE d.id_estado_cobranza = 3 $dateCondition";
        $kpis['deuda_coactiva'] = (float) $db->fetchOne($sqlDeudaCoactiva, $queryParams)['total'];
        
        // Porcentaje Coactiva
        $kpis['pct_deuda_coactiva'] = $kpis['deuda_total_pendiente'] > 0 ? round(($kpis['deuda_coactiva'] / $kpis['deuda_total_pendiente']) * 100, 2) : 0;
        
        // Total Contribuyentes Morosos
        $sqlMorosos = "SELECT COUNT(DISTINCT d.id_contribuyente) as total FROM neplatic.deuda d WHERE d.id_estado_cobranza IN (2, 3) $dateCondition";
        $kpis['total_contribuyentes_morosos'] = (int) $db->fetchOne($sqlMorosos, $queryParams)['total'];

        // Calcular tasa de efectividad real: (Total de Contribuyentes con deuda - Morosos) / Total con deuda (para el periodo)
        // Para simplificar, asumimos Total Contribuyentes general vs Morosos del periodo
        $total_query = "SELECT COUNT(*) as total FROM neplatic.contribuyente";
        $total_res = $db->fetchOne($total_query);
        $total_personas = (int)($total_res['total'] ?? 0);
        
        $efectividad = 0;
        if ($total_personas > 0) {
            $efectividad = (($total_personas - $kpis['total_contribuyentes_morosos']) / $total_personas) * 100;
        }
        $kpis['tasa_efectividad_real'] = round(max(0, $efectividad), 2);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $kpis
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getEvolucion(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        $estado = $params['estado'] ?? null;
        
        $sql = "SELECT * FROM neplatic.v_evolucion_morosidad";
        $conditions = [];
        $queryParams = [];
        
        if ($estado) {
            $conditions[] = "estado = :estado";
            $queryParams['estado'] = $estado;
        }
        
        if (!empty($conditions)) {
            $sql .= " WHERE " . implode(' AND ', $conditions);
        }
        
        $sql .= " ORDER BY mes DESC LIMIT 12";
        $evolucion = $db->fetchAll($sql, $queryParams);
        $evolucion = array_reverse($evolucion);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $evolucion
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getTopDeudores(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        
        $anio = $params['anio'] ?? date('Y');
        $periodo = $params['periodo'] ?? 'ANUAL';
        $limit = min(50, (int)($params['limit'] ?? 10));
        
        $dateCondition = "EXTRACT(YEAR FROM d.fecha_vencimiento) = :anio";
        $queryParams = ['anio' => $anio];
        
        if ($periodo === 'S1') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) <= 6";
        } elseif ($periodo === 'S2') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) > 6";
        } elseif ($periodo === 'T1') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 1 AND 3";
        } elseif ($periodo === 'T2') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 4 AND 6";
        } elseif ($periodo === 'T3') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 7 AND 9";
        } elseif ($periodo === 'T4') {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) BETWEEN 10 AND 12";
        } elseif (preg_match('/^M([1-9]|1[0-2])$/', $periodo, $matches)) {
            $dateCondition .= " AND EXTRACT(MONTH FROM d.fecha_vencimiento) = " . (int)$matches[1];
        }
        
        $sql = "
            SELECT 
                c.nombres, 
                c.apellido_paterno, 
                c.numero_documento, 
                STRING_AGG(DISTINCT s.codigo, ', ') as sectores,
                SUM(d.saldo_pendiente) as deuda_total,
                ROW_NUMBER() OVER(ORDER BY SUM(d.saldo_pendiente) DESC) as ranking
            FROM neplatic.deuda d
            JOIN neplatic.contribuyente c ON d.id_contribuyente = c.id_contribuyente
            LEFT JOIN neplatic.lote l ON d.id_lote = l.id_lote
            LEFT JOIN neplatic.manzana m ON l.id_manzana = m.id_manzana
            LEFT JOIN neplatic.sector s ON m.id_sector = s.id_sector
            WHERE d.id_estado_cobranza IN (2, 3) AND $dateCondition
            GROUP BY c.id_contribuyente, c.nombres, c.apellido_paterno, c.numero_documento
            ORDER BY deuda_total DESC
            LIMIT " . (int)$limit;
            
        $deudores = $db->fetchAll($sql, $queryParams);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $deudores
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}