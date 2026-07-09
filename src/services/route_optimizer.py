from src.utils.geoutils import punto_desde_coords, calcular_distancia_metros
from typing import List


def optimizar_ruta(puntos: List[tuple]) -> List[tuple]:
    if len(puntos) <= 1:
        return puntos
    puntos_ordenados = sorted(puntos, key=lambda p: (p[0], p[1]))
    return puntos_ordenados


def calcular_distancia_ruta(puntos: List[tuple]) -> float:
    if len(puntos) < 2:
        return 0.0
    distancia = 0.0
    for i in range(len(puntos) - 1):
        distancia += calcular_distancia_metros(puntos[i], puntos[i + 1])
    return distancia