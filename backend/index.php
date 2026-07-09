<?php
use Slim\Factory\AppFactory;
use Slim\Routing\RouteCollectorProxy;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

require __DIR__ . '/vendor/autoload.php';

// Cargar variables de entorno
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

// Crear app
$app = AppFactory::create();

// Configurar CORS
$app->add(function (Request $request, $handler) {
    $response = $handler->handle($request);
    
    $allowedOrigins = explode(',', $_ENV['ALLOWED_ORIGINS']);
    $origin = $request->getHeaderLine('Origin');
    
    if (in_array($origin, $allowedOrigins)) {
        $response = $response->withHeader('Access-Control-Allow-Origin', $origin);
    }
    
    return $response
        ->withHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        ->withHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        ->withHeader('Access-Control-Allow-Credentials', 'true');
});

// Manejar OPTIONS preflight
$app->options('/{routes:.+}', function (Request $request, Response $response) {
    return $response;
});

// Cargar rutas
$routes = require __DIR__ . '/routes/api.php';
$routes($app);

// Ruta de información del sistema
$app->get('/api', function (Request $request, Response $response) {
    $response->getBody()->write(json_encode([
        'name' => 'Neplatic Web API',
        'version' => '2.0.0',
        'architecture' => 'Event-Driven Architecture (EDA)',
        'role' => 'SOLO LECTURA',
        'status' => 'running'
    ]));
    return $response->withHeader('Content-Type', 'application/json');
});

// Manejar 404
$app->map(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], '/{routes:.+}', function (Request $request, Response $response) {
    $response->getBody()->write(json_encode(['error' => 'Ruta no encontrada']));
    return $response->withStatus(404)->withHeader('Content-Type', 'application/json');
});

$app->run();