<?php
namespace Neplatic\Http;

class Kernel
{
    /**
     * Middleware globales (se ejecutan en todas las rutas)
     */
    protected $middleware = [
        \Neplatic\Http\Middleware\CorsMiddleware::class,
    ];
    
    /**
     * Middleware para rutas (se asignan a grupos específicos)
     */
    protected $routeMiddleware = [
        'auth' => \Neplatic\Http\Middleware\AuthMiddleware::class,
    ];
}