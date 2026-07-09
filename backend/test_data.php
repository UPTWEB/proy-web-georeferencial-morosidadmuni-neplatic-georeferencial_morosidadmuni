<?php
require 'vendor/autoload.php';
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();
$db = \Neplatic\Models\Database::getInstance();

echo "--- Evolucion Morosidad ---\n";
print_r($db->fetchAll("SELECT * FROM neplatic.v_evolucion_morosidad LIMIT 5"));

echo "\n--- Total Contribuyentes ---\n";
print_r($db->fetchAll("SELECT COUNT(*) as total FROM neplatic.contribuyente"));
