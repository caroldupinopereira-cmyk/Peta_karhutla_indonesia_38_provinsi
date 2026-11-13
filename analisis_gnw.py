"""Peta tahunan kehilangan tutupan pohon akibat kebakaran Global Nature Watch."""
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from elemen_peta import tambah_elemen_peta

SOURCE_URL = 'https://globalnaturewatch.org/dashboards/country/IDN/?category=fires&lang=id&map=eyJjYW5Cb3VuZCI6dHJ1ZX0%3D'
FOLDER = 'Wilayah dengan kehilangan tutupan pohon terbanyak akibat kebakaran di Indonesia'


def analisis_kehilangan_pohon(root):
    root = Path(root)
    folder = root / 'All Dataset' / FOLDER
    table = pd.read_csv(folder / 'treecover_loss_from_fires_by_region__ha.csv', dtype={'adm1': str})
    names = pd.read_csv(folder / 'adm1_metadata.csv', dtype={'adm1__id': str}).rename(columns={'adm1__id': 'adm1'})
    year = int(table.umd_tree_cover_loss__year.max())
    latest = table[table.umd_tree_cover_loss__year.eq(year)].merge(names, on='adm1', validate='one_to_one')
    latest = latest.rename(columns={'name': 'nama_gnw', 'umd_tree_cover_loss_from_fires__ha': 'kehilangan_akibat_api_ha'})
    prov = gpd.read_file(root / 'outputs/provinsi_karhutla.geojson')[['name', 'geometry']].to_crs(4326)
    # Cakupan tabel GNW 34 wilayah: kelompokkan geometri provinsi pemekaran.
    mapping = {
        'Papua Selatan': 'Papua', 'Papua Tengah': 'Papua', 'Papua Pegunungan': 'Papua',
        'Papua Barat Daya': 'Papua Barat',
        'Kepulauan Bangka Belitung': 'Bangka Belitung',
        'Daerah Khusus Ibukota Jakarta': 'Jakarta Raya',
        'Daerah Istimewa Yogyakarta': 'Yogyakarta',
    }
    prov['nama_gnw'] = prov.name.replace(mapping)
    grouped = prov[['nama_gnw', 'geometry']].dissolve(by='nama_gnw', as_index=False)
    if set(grouped.nama_gnw) != set(names.name):
        raise ValueError('Nama wilayah GNW belum cocok dengan kelompok batas provinsi.')
    geo = grouped.merge(latest[['nama_gnw', 'kehilangan_akibat_api_ha']], on='nama_gnw', how='left', validate='one_to_one')
    out = root / 'outputs'
    geo['tahun'] = year
    geo.drop(columns='geometry').sort_values('kehilangan_akibat_api_ha', ascending=False).to_csv(out / 'kehilangan_pohon_gnw_provinsi.csv', index=False)
    geo.to_file(out / 'kehilangan_pohon_gnw_34_wilayah.geojson', driver='GeoJSON')
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='#f5f7fa')
    ax.set_facecolor('#e7f0f5')
    geo.plot(ax=ax, column='kehilangan_akibat_api_ha', cmap='YlOrRd', edgecolor='#7d8c99', linewidth=0.5,
             legend=True, legend_kwds={'label': 'Kehilangan tutupan pohon akibat kebakaran (ha)', 'shrink': 0.7},
             missing_kwds={'color': '#bfc7cd', 'label': 'Data tidak tersedia'})
    ax.set_xlim(94, 142)
    ax.set_ylim(-12, 7)
    ax.set_xlabel('Bujur')
    ax.set_ylabel('Lintang')
    ax.set_title(f'Kehilangan tutupan pohon akibat kebakaran di Indonesia | {year}', loc='left', fontsize=17, pad=15)
    tambah_elemen_peta(ax)
    fig.text(0.06, 0.035, 'Sumber: Global Nature Watch / UMD-GLAD. Tahun terakhir dalam CSV lokal; ambang tutupan tajuk 30%.\nCakupan statistik 34 wilayah. Batas provinsi pemekaran Papua digabung untuk visualisasi; ketelitian historis batas perlu diperhatikan.', fontsize=9)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    path = out / 'peta_kehilangan_pohon_gnw.png'
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return {'peta': path, 'tahun': year, 'tabel': geo.drop(columns='geometry'),
            'metode_batas': 'Penggabungan geometri 38 provinsi menjadi 34 kelompok nama GNW',
            'sumber': SOURCE_URL}
