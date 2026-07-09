<?php
namespace Neplatic\Models;

class User
{
    private $db;
    
    public function __construct()
    {
        $this->db = Database::getInstance();
    }
    
    public function findById($id)
    {
        $sql = "SELECT u.id_usuario, u.username, u.nombres, u.apellidos, 
                       u.id_rol, r.codigo as rol_codigo, r.nombre as rol_nombre
                FROM neplatic.usuario u
                JOIN neplatic.rol_usuario r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = :id AND u.activo = true";
        
        return $this->db->fetchOne($sql, ['id' => $id]);
    }
    
    public function findByUsername($username)
    {
        $sql = "SELECT u.id_usuario, u.username, u.password_hash, u.nombres, u.apellidos, 
                       u.id_rol, r.codigo as rol_codigo, r.nombre as rol_nombre,
                       u.activo, u.bloqueado
                FROM neplatic.usuario u
                JOIN neplatic.rol_usuario r ON u.id_rol = r.id_rol
                WHERE u.username = :username";
        
        return $this->db->fetchOne($sql, ['username' => $username]);
    }
}