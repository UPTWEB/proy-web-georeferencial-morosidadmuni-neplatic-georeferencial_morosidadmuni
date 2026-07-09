#!/usr/bin/env php
<?php

require __DIR__ . '/../vendor/autoload.php';

use Dotenv\Dotenv;
use Neplatic\Services\EventConsumer;

$dotenv = Dotenv::createImmutable(__DIR__ . '/../');
$dotenv->load();

try {
    $consumer = new EventConsumer();
    $consumer->start();
} catch (Exception $e) {
    echo " Error fatal: " . $e->getMessage() . "\n";
    exit(1);
}