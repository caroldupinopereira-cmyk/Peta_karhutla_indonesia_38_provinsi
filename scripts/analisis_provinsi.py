"""Peta dan rincian titik panas per provinsi untuk notebook."""
from pathlib import Path
import re
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from elemen_peta import tambah_elemen_peta


def siapkan_data(root):
    root = Path(root)
    prov = gpd.read_file(root / 'outputs/provinsi_karhutla.geojson').to_crs(4326)
    points = gpd.read_file(root / 'outputs/titik_panas.geojson').to_crs(4326)
    kab = gpd.read_file(root / 'All Dataset' / 'kab_kota.geojson').to_crs(4326)
    kab['kode_kab'] = kab['code'].astype(str)
    kab['kode_provinsi'] = kab.kode_kab.str.split('.').str[0]
    kab = kab.rename(columns={'name': 'kabupaten_kota'})
    kab.geometry = kab.geometry.make_valid()
    kab = kab.explode(index_parts=False)
    kab = kab[kab.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()
    kab = kab.dissolve(by='kode_kab', as_index=False)
    if not kab.is_valid.all() or kab.geometry.is_empty.any():
        raise ValueError('Geometri kabupaten belum valid.')
    points = points.drop(columns='index_right', errors='ignore')
    joined = gpd.sjoin(points, kab[['kode_kab', 'kode_provinsi', 'kabupaten_kota', 'geometry']], how='left', predicate='intersects')
    # Hanya gunakan kecocokan kabupaten yang konsisten dengan hasil provinsi.
    matches = joined[joined.status_wilayah.eq('cocok') & joined.code.eq(joined.kode_provinsi)].copy()
    ambiguous = matches.loc[matches.id_deteksi.duplicated(keep=False), 'id_deteksi'].unique()
    unique = matches[~matches.id_deteksi.isin(ambiguous)].drop(columns=['geometry', 'index_right'])
    detail = points.merge(unique[['id_deteksi', 'kode_kab', 'kabupaten_kota']], on='id_deteksi', how='left', validate='one_to_one')
    detail['status_kabupaten'] = 'tidak cocok dengan batas kabupaten dalam provinsi'
    detail.loc[detail.kode_kab.notna(), 'status_kabupaten'] = 'cocok'
    detail.loc[detail.id_deteksi.isin(ambiguous), 'status_kabupaten'] = 'ambigu: lebih dari satu kabupaten'
    detail.loc[~detail.status_wilayah.eq('cocok'), 'status_kabupaten'] = 'provinsi belum dapat ditentukan'
    if len(detail) != len(points) or detail.id_deteksi.duplicated().any():
        raise ValueError('Rekonsiliasi titik kabupaten gagal.')
    detail.drop(columns='geometry').to_csv(root / 'outputs/titik_panas_dengan_kabupaten.csv', index=False)
    joined.drop(columns='geometry').to_csv(root / 'outputs/pencocokan_kabupaten_mentah.csv', index=False)
    return {'root': root, 'provinsi': prov, 'kabupaten': kab, 'titik': detail}


def tampilkan_provinsi(data, nama):
    prov = data['provinsi']
    selected = prov[prov.name.eq(nama)]
    if len(selected) != 1:
        raise ValueError(f'Nama provinsi tidak unik atau tidak ditemukan: {nama}')
    row = selected.iloc[0]
    kab = data['kabupaten'][data['kabupaten'].kode_provinsi.eq(str(row.code))].sort_values('kabupaten_kota').copy()
    titik = data['titik'][data['titik'].code.eq(row.code) & data['titik'].status_wilayah.eq('cocok')].copy()
    counts = titik[titik.status_kabupaten.eq('cocok')].groupby('kode_kab').size()
    kab['jumlah_deteksi'] = kab.kode_kab.map(counts).fillna(0).astype(int)
    kab['nomor_peta'] = range(1, len(kab) + 1)
    assert int(kab.jumlah_deteksi.sum()) + int(titik.kode_kab.isna().sum()) == len(titik)
    fig, (ax, legend_ax) = plt.subplots(1, 2, figsize=(15, max(7, len(kab) * 0.18)), gridspec_kw={'width_ratios': [2.4, 1]}, facecolor='#f5f7fa')
    ax.set_facecolor('#e7f0f5')
    selected.plot(ax=ax, color='#f1f3ed', edgecolor='#354d60', linewidth=1)
    if len(kab):
        kab.plot(ax=ax, column='jumlah_deteksi', cmap='YlOrBr', edgecolor='#7d8c99', linewidth=0.55, vmin=0, vmax=max(1, kab.jumlah_deteksi.max()))
        for _, area in kab.iterrows():
            p = area.geometry.representative_point()
            ax.text(p.x, p.y, str(area.nomor_peta), fontsize=7, ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1))
    colors = {'l': '#f1c232', 'n': '#ed6927', 'h': '#b10f2e'}
    for conf, color in colors.items():
        subset = titik[titik.confidence.eq(conf)]
        if len(subset):
            subset.plot(ax=ax, color=color, markersize=24, edgecolor='#fff', linewidth=0.3, alpha=0.85)
    bounds = selected.total_bounds
    margin = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) * 0.07
    ax.set_xlim(bounds[0] - margin, bounds[2] + margin)
    ax.set_ylim(bounds[1] - margin, bounds[3] + margin)
    ax.set_xlabel('Bujur')
    ax.set_ylabel('Lintang')
    tambah_elemen_peta(ax)
    fig.colorbar(ScalarMappable(norm=Normalize(vmin=0, vmax=max(1, kab.jumlah_deteksi.max())), cmap='YlOrBr'),
                 ax=ax, shrink=0.6, pad=0.02, label='Jumlah deteksi per kabupaten/kota')
    ax.set_title(f'{nama}\n{len(titik):,} deteksi titik panas', loc='left', fontsize=18)
    ax.legend(handles=[Line2D([], [], marker='o', linestyle='', color=c, label=l) for c, l in zip(colors.values(), ['Confidence rendah', 'Confidence nominal', 'Confidence tinggi'])], loc='best', fontsize=8)
    if not len(titik):
        ax.text(0.5, 0.04, 'Tidak ada deteksi pada tanggal data', transform=ax.transAxes, ha='center', fontsize=10, bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))
    legend_ax.axis('off')
    legend_ax.set_title('Kabupaten/kota (nomor pada peta)', fontsize=10, loc='left')
    for i, (_, area) in enumerate(kab.iterrows()):
        legend_ax.text(0, 0.97 - i * (0.91 / max(1, len(kab))), f'{area.nomor_peta}. {area.kabupaten_kota} ({area.jumlah_deteksi})', fontsize=8, va='top')
    period = ', '.join(sorted(pd.to_datetime(data['titik'].acq_date).dt.strftime('%Y-%m-%d').unique()))
    unassigned = int(titik.kode_kab.isna().sum())
    fig.text(0.04, 0.035, f'Tanggal deteksi: {period}. Angka dalam kurung pada legenda adalah jumlah deteksi.\nArsir semakin gelap: semakin banyak deteksi cocok. Titik tanpa kabupaten pasti: {unassigned}.\nTitik panas bukan konfirmasi kebakaran hutan. Luas kabupaten terbakar tidak tersedia pada sumber.', fontsize=9)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    folder = data['root'] / 'outputs' / 'provinsi'
    folder.mkdir(exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '_', nama.lower()).strip('_')
    path = folder / f'{row.code}_{slug}.png'
    fig.savefig(path, dpi=135)
    plt.close(fig)
    summary = kab[['nomor_peta', 'kode_kab', 'kabupaten_kota', 'jumlah_deteksi']].sort_values('jumlah_deteksi', ascending=False)
    summary.to_csv(folder / f'{row.code}_{slug}_ringkasan.csv', index=False)
    locations = titik.drop(columns='geometry')[['id_deteksi', 'latitude', 'longitude', 'acq_date', 'acq_time', 'confidence', 'kabupaten_kota', 'status_kabupaten']]
    locations.to_csv(folder / f'{row.code}_{slug}_titik.csv', index=False)
    info = pd.DataFrame([{'provinsi': nama, 'tahun_luas': row.tahun_luas, 'luas_karhutla_ha': row.luas_karhutla, 'jumlah_deteksi': len(titik), 'deteksi_tanpa_kabupaten_pasti': unassigned}])
    return {'peta': path, 'informasi': info, 'ringkasan': summary, 'titik': locations}
