import os
import requests

ORS_BASE_URL = 'https://api.openrouteservice.org'


def _get_api_key() -> str:
    key = os.getenv('ORS_API_KEY')
    if not key:
        raise RuntimeError(
            'Missing ORS_API_KEY environment variable. '
            'Set it before running the backend (do NOT hardcode keys).'
        )
    return key


def geocode_address(query: str) -> tuple[float, float]:
    key = _get_api_key()

    url = f'{ORS_BASE_URL}/geocode/search'
    params = {
        'text': query, 
        'size': 1,
        'boundary.country': 'SE' 
    }
    headers = {'Authorization': key}

    r = requests.get(url, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    features = data.get('features', [])
    if not features:
        raise ValueError(f'No geocoding result for: {query}')

    lon, lat = features[0]['geometry']['coordinates']
    return float(lat), float(lon)


def get_route(
    start_latlon: tuple[float, float], end_latlon: tuple[float, float]
) -> dict:
    key = _get_api_key()

    url = f'{ORS_BASE_URL}/v2/directions/driving-car/geojson'
    headers = {'Authorization': key, 'Content-Type': 'application/json'}

    start_lat, start_lon = start_latlon
    end_lat, end_lon = end_latlon

    body = {'coordinates': [[start_lon, start_lat], [end_lon, end_lat]]}

    r = requests.post(url, json=body, headers=headers, timeout=40)
    r.raise_for_status()
    data = r.json()

    if 'features' not in data or not data['features']:
        raise ValueError('No route returned (empty "features").')

    feat = data['features'][0]
    summary = feat['properties']['summary']

    coords_lonlat = feat['geometry']['coordinates']  # [[lon, lat], ...]
    polyline_latlon = [[lat, lon] for lon, lat in coords_lonlat]

    return {
        'distance_km': float(summary['distance']) / 1000.0,
        'duration_min': float(summary['duration']) / 60.0,
        'start_lat': start_lat,
        'start_lon': start_lon,
        'end_lat': end_lat,
        'end_lon': end_lon,
        'polyline_latlon': polyline_latlon,
    }
