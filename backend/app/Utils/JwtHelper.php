<?php
namespace Neplatic\Utils;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

class JwtHelper
{
    private static $secret;
    
    public static function init()
    {
        self::$secret = $_ENV['JWT_SECRET'];
    }
    
    public static function encode($payload)
    {
        $issuedAt = time();
        $expire = $issuedAt + (int)$_ENV['JWT_EXPIRES'];
        
        $tokenPayload = [
            'iat' => $issuedAt,
            'exp' => $expire,
            'data' => $payload
        ];
        
        return JWT::encode($tokenPayload, self::$secret, 'HS256');
    }
    
    public static function decode($token)
    {
        try {
            $decoded = JWT::decode($token, new Key(self::$secret, 'HS256'));
            return (array)$decoded->data;
        } catch (\Exception $e) {
            return null;
        }
    }
    
    public static function validate($token)
    {
        return self::decode($token) !== null;
    }
}

JwtHelper::init();