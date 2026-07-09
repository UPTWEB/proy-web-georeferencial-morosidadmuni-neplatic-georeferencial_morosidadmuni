<?php
require 'vendor/autoload.php';
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();
$db = \Neplatic\Models\Database::getInstance();
echo "deuda:\n";
print_r($db->fetchAll("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'neplatic' AND table_name = 'deuda'"));
