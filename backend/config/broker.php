<?php
return [
    'redis' => [
        'host' => $_ENV['REDIS_HOST'],
        'port' => (int)$_ENV['REDIS_PORT'],
        'password' => $_ENV['REDIS_PASSWORD'],
        'prefix' => $_ENV['REDIS_PREFIX'],
    ],
    'channels' => [
        'rutas' => $_ENV['REDIS_CHANNEL_RUTAS'],
    ]
];