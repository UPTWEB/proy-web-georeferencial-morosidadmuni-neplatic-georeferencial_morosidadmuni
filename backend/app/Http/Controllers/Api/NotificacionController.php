<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;

class NotificacionController
{
    public function registrar(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        
        $data = json_decode($request->getBody()->getContents(), true);
        $idLote = $data['id_lote'] ?? null;
        $idEstadoNotif = $data['id_estado_notif'] ?? null;
        $observacion = $data['observaciones'] ?? '';
        
        if (!$idLote || !$idEstadoNotif) {
            $response->getBody()->write(json_encode(['success' => false, 'error' => 'Faltan datos']));
            return $response->withStatus(400)->withHeader('Content-Type', 'application/json');
        }
        
        $db = Database::getInstance();
        $pdo = $db->getConnection();
        
        try {
            $pdo->beginTransaction();
            
            // Buscar deudas activas para este lote
            $stmtDeudas = $pdo->prepare("SELECT id_deuda FROM neplatic.deuda WHERE id_lote = ? AND activo = TRUE AND saldo_pendiente > 0");
            $stmtDeudas->execute([$idLote]);
            $deudas = $stmtDeudas->fetchAll(\PDO::FETCH_ASSOC);
            
            if (empty($deudas)) {
                $pdo->rollBack();
                $response->getBody()->write(json_encode(['success' => false, 'error' => 'El lote no tiene deudas activas']));
                return $response->withStatus(404)->withHeader('Content-Type', 'application/json');
            }
            
            // Registrar notificación para cada deuda del lote
            $stmtInsert = $pdo->prepare("INSERT INTO neplatic.notificacion (id_deuda, id_usuario, id_estado_notif, observacion) VALUES (?, ?, ?, ?)");
            
            foreach ($deudas as $deuda) {
                $stmtInsert->execute([$deuda['id_deuda'], $usuarioId, $idEstadoNotif, $observacion]);
            }
            
            $pdo->commit();
            
            $response->getBody()->write(json_encode(['success' => true, 'mensaje' => 'Notificación registrada']));
            return $response->withHeader('Content-Type', 'application/json');
            
        } catch (\Exception $e) {
            $pdo->rollBack();
            $response->getBody()->write(json_encode(['success' => false, 'error' => $e->getMessage()]));
            return $response->withStatus(500)->withHeader('Content-Type', 'application/json');
        }
    }
}
