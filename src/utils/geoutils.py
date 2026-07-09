from shapely.geometry import Point, Polygon, LineString, shape
from shapely.ops import nearest_points
import json


def punto_desde_coords(lat: float, lon: float) -> Point:
    return Point(lon, lat)


def get_centroid(geom_json: str) -> tuple:
    geom = shape(json.loads(geom_json))
    centroid = geom.centroid
    return (centroid.y, centroid.x)


def calcular_distancia_metros(p1: tuple, p2: tuple) -> float:
    pt1 = Point(p1[1], p1[0])
    pt2 = Point(p2[1], p2[0])
    return pt1.distance(pt2) * 111111


def buffer_radio(geom_json: str, radio_metros: float) -> str:
    geom = shape(json.loads(geom_json))
    buffer = geom.buffer(radio_metros / 111111)
    return json.dumps(buffer.__geo_interface__)


def intersecta_poligono(punto: Point, poligono_json: str) -> bool:
    poligono = shape(json.loads(poligono_json))
    return poligono.contains(punto)