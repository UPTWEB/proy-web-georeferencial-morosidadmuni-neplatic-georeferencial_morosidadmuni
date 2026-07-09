<?php
namespace Neplatic\Models;

use PDO;
use PDOException;

/**
 * Clase Singleton para manejar la conexión a PostgreSQL usando PDO.
 * Garantiza que solo exista una instancia de conexión a la base de datos
 * durante el ciclo de vida de la petición (Patrón Singleton).
 */
class Database
{
    private static $instance = null;
    private $connection;
    
    /**
     * Constructor privado para prevenir creación externa.
     * Lee las credenciales de entorno (.env) y establece la conexión PDO
     * con manejo de errores en modo Exception.
     */
    private function __construct()
    {
        $host = $_ENV['DB_HOST'];
        $port = $_ENV['DB_PORT'];
        $dbname = $_ENV['DB_NAME'];
        $user = $_ENV['DB_USER'];
        $pass = $_ENV['DB_PASS'];
        $schema = $_ENV['DB_SCHEMA'];
        
        try {
            $dsn = "pgsql:host=$host;port=$port;dbname=$dbname";
            $options = [
                PDO::ATTR_PERSISTENT => true,
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ];
            $this->connection = new PDO($dsn, $user, $pass, $options);
            $this->connection->exec("SET search_path TO $schema, public");
        } catch (PDOException $e) {
            throw new \Exception("Error de conexión PostgreSQL: " . $e->getMessage());
        }
    }
    
    /**
     * Obtiene la única instancia de la clase Database.
     * 
     * @return self Instancia Singleton
     */
    public static function getInstance(): self
    {
        if (self::$instance === null) {
            self::$instance = new Database();
        }
        return self::$instance;
    }
    
    /**
     * Devuelve el objeto PDO subyacente para realizar operaciones manuales (transacciones).
     * 
     * @return \PDO
     */
    public function getConnection(): \PDO
    {
        return $this->connection;
    }
    
    /**
     * Ejecuta una consulta SQL genérica que no devuelve resultados (INSERT, UPDATE, DELETE).
     * 
     * @param string $sql Consulta SQL
     * @param array $params Parámetros para prepared statements
     * @return \PDOStatement El statement ejecutado
     */
    public function query(string $sql, array $params = [])
    {
        $stmt = $this->connection->prepare($sql);
        $stmt->execute($params);
        return $stmt;
    }
    
    /**
     * Ejecuta una consulta SQL SELECT y retorna todos los resultados como un arreglo asociativo.
     * 
     * @param string $sql
     * @param array $params
     * @return array
     */
    public function fetchAll(string $sql, array $params = []): array
    {
        return $this->query($sql, $params)->fetchAll(PDO::FETCH_ASSOC);
    }
    
    /**
     * Ejecuta una consulta SQL SELECT y retorna un solo resultado (el primer registro).
     * Útil para búsquedas por ID o verificaciones de existencia.
     * 
     * @param string $sql
     * @param array $params
     * @return array|false Fila asociativa o false si no existe
     */
    public function fetchOne(string $sql, array $params = [])
    {
        return $this->query($sql, $params)->fetch(PDO::FETCH_ASSOC);
    }
}