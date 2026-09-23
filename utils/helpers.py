import json
from shapely.geometry import shape, mapping, Point
from geoalchemy2.shape import from_shape, to_shape

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    """Cek apakah ekstensi file diperbolehkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def geojson_to_wkbelement(geojson_data, srid=4326):
    """Konversi GeoJSON dict/string ke WKBElement untuk disimpan di PostGIS."""
    if geojson_data is None:
        return None
    try:
        if isinstance(geojson_data, str):
            geojson_data = json.loads(geojson_data)
        shapely_geom = shape(geojson_data)
        return from_shape(shapely_geom, srid=srid)
    except Exception as e:
        raise ValueError(f"Format GeoJSON tidak valid: {str(e)}")

def geometry_to_geojson(wkb_element):
    """Konversi WKBElement / Geometry dari PostGIS ke GeoJSON dict."""
    if wkb_element is None:
        return None
    try:
        shapely_geom = to_shape(wkb_element)
        return mapping(shapely_geom)
    except Exception:
        return None

def make_point_geom(latitude, longitude, srid=4326):
    """Buat Point geometry dari latitude dan longitude (GeoJSON urutan lon, lat)."""
    if latitude is None or longitude is None:
        return None
    try:
        point = Point(float(longitude), float(latitude))
        return from_shape(point, srid=srid)
    except Exception as e:
        raise ValueError(f"Koordinat tidak valid: {str(e)}")
