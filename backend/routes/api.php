<?php

use Slim\Routing\RouteCollectorProxy;
use Neplatic\Http\Middleware\AuthMiddleware;

return function ($app) {
    
    // Rutas públicas
    $app->post('/api/login', [Neplatic\Http\Controllers\Api\AuthController::class, 'login']);
    
    // Rutas protegidas
    $app->group('/api', function (RouteCollectorProxy $group) {
        
        // Auth
        $group->get('/me', [Neplatic\Http\Controllers\Api\AuthController::class, 'me']);
        
        // Dashboard
        $group->get('/dashboard/kpis', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getKPIs']);
        $group->get('/dashboard/evolucion', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getEvolucion']);
        $group->get('/dashboard/top-deudores', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getTopDeudores']);
        
        // Mapa
        $group->get('/mapa/sectores', [Neplatic\Http\Controllers\Api\MapaController::class, 'getSectores']);
        $group->get('/mapa/manzanas', [Neplatic\Http\Controllers\Api\MapaController::class, 'getManzanas']);
        $group->get('/mapa/lotes', [Neplatic\Http\Controllers\Api\MapaController::class, 'getLotes']);
        $group->get('/mapa/heatmap', [Neplatic\Http\Controllers\Api\MapaController::class, 'getHeatmapData']);
        
        // Rutas (solo lectura y notificaciones para notificadores)
        $group->get('/rutas/mis-rutas', [Neplatic\Http\Controllers\Api\RutaController::class, 'getMisRutas']);
        $group->get('/rutas/futuras', [Neplatic\Http\Controllers\Api\RutaController::class, 'getRutasFuturas']);
        $group->post('/rutas/notificar', [Neplatic\Http\Controllers\Api\RutaController::class, 'notificar']);
        $group->post('/rutas/ubicacion', [Neplatic\Http\Controllers\Api\RutaController::class, 'guardarUbicacion']);
        $group->get('/rutas/ubicaciones-activas', [Neplatic\Http\Controllers\Api\RutaController::class, 'getUbicaciones']);
        
        // Notificaciones (Web)
        $group->post('/notificaciones/registrar', [Neplatic\Http\Controllers\Api\NotificacionController::class, 'registrar']);
        
        // Soporte / TI
        $group->get('/soporte/estado', [Neplatic\Http\Controllers\Api\SoporteController::class, 'getEstado']);
        $group->post('/soporte/limpiar-cache', [Neplatic\Http\Controllers\Api\SoporteController::class, 'limpiarCache']);
        $group->get('/soporte/usuarios', [Neplatic\Http\Controllers\Api\SoporteController::class, 'getUsuarios']);
        
    })->add(new AuthMiddleware());
};