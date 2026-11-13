"""Unduh snapshot VIIRS NOAA-20 24 jam dari NASA FIRMS untuk Indonesia."""
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import json
import urllib.request
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'All Dataset'
URL = 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_24h.csv'


def main():
    with urllib.request.urlopen(URL, timeout=60) as response:
        content = response.read()
    raw = pd.read_csv(BytesIO(content), dtype={'acq_time': str})
    required = {'latitude', 'longitude', 'acq_date', 'acq_time', 'confidence'}
    if not required.issubset(raw.columns) or raw.empty:
        raise ValueError('Respons NASA tidak memuat tabel deteksi yang diharapkan.')
    valid = raw.latitude.between(-90, 90) & raw.longitude.between(-180, 180)
    if not valid.all():
        raise ValueError('Unduhan NASA memuat koordinat tidak valid.')
    boundary = gpd.read_file(DATA_DIR / 'provinsi.geojson').to_crs(4326)
    boundary.geometry = boundary.geometry.make_valid()
    points = gpd.GeoDataFrame(raw, geometry=gpd.points_from_xy(raw.longitude, raw.latitude), crs=4326)
    inside = gpd.sjoin(points, boundary[['geometry']], predicate='intersects', how='inner')
    selected = raw.loc[inside.index.unique()].copy()
    if selected.empty:
        raise ValueError('Tidak ada deteksi di dalam batas Indonesia pada snapshot ini.')
    selected = selected.rename(columns={'bright_ti4': 'brightness', 'bright_ti5': 'bright_t31'})
    selected['confidence'] = selected.confidence.replace({'low': 'l', 'nominal': 'n', 'high': 'h'})
    selected['instrument'] = 'VIIRS'
    selected['acq_time'] = selected.acq_time.str.zfill(4)
    observed = pd.to_datetime(selected.acq_date)
    metadata = {
        'source': 'NASA FIRMS VIIRS NOAA-20 NRT', 'url': URL,
        'landing_page': 'https://firms.modaps.eosdis.nasa.gov/active_fire/',
        'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
        'window': 'rolling 24 hours as provided by NASA',
        'acq_date_min': observed.min().strftime('%Y-%m-%d'),
        'acq_date_max': observed.max().strftime('%Y-%m-%d'),
        'acq_time_timezone': 'UTC', 'regional_rows': len(raw), 'indonesia_rows': len(selected),
        'selection': 'intersects with repaired local Indonesia province boundaries; duplicate boundary matches removed',
        'crs': 'EPSG:4326', 'confidence_mapping': {'low': 'l', 'nominal': 'n', 'high': 'h'},
        'brightness_mapping': 'bright_ti4 -> brightness; bright_ti5 -> bright_t31 (legacy column names in this project)',
    }
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / 'firms_noaa20_southeast_asia_24h.csv').write_bytes(content)
    selected.to_csv(DATA_DIR / 'firms_noaa20_indonesia_24h.csv', index=False)
    (DATA_DIR / 'firms_noaa20_indonesia_24h_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
