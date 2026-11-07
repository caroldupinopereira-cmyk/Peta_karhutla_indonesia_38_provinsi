# Peta titik panas dan karhutla Indonesia

Proyek GeoPandas untuk memetakan titik panas, menggabungkan luas karhutla per provinsi, dan menentukan kabupaten/kota tempat setiap deteksi berada. Notebook menyediakan satu sel khusus untuk masing-masing dari 38 provinsi.

## Identifikasi tahun dan periode data

**Hasil analisis yang disimpan saat ini menggunakan tahun luas karhutla 2026 dan deteksi titik panas tanggal 7 November 2026.**

| Data | Tahun atau periode | Dasar identifikasi |
| --- | --- | --- |
| Titik panas VIIRS | 7 November 2026 (`2026-11-07`) | Kolom `acq_date` pada CSV; 1.009 deteksi pada satu tanggal |
| Luas karhutla yang dipetakan | Kolom tahun 2026 | Parameter `TAHUN = 2026` pada notebook dan `tahun_luas` pada `outputs/validasi.json` |
| Riwayat luas yang tersedia | 2018–2026 | Kolom tahun pada Excel; belum seluruhnya dipetakan |
| Batas provinsi dan kabupaten/kota | Tahun referensi batas belum diverifikasi | Jumlah wilayah pada GeoJSON tidak cukup untuk memastikan tahun penerbitan atau pemutakhiran batas |

Peringkat titik panas menunjukkan kondisi deteksi **pada 7 November 2026**, bukan akumulasi seluruh tahun 2026. Peringkat luas memakai nilai pada **kolom 2026** di Excel; tanggal pemutakhiran belum diketahui, sehingga tidak dinyatakan sebagai total satu tahun penuh. Kedua ukuran tidak memiliki periode pengamatan yang sama.

Untuk memilih tahun luas lain, ubah `TAHUN` pada bagian 2 notebook ke kolom yang tersedia. Untuk mengganti periode titik panas, gunakan CSV dengan tanggal pengamatan yang diinginkan dan ubah parameter `CSV`. Setelah alur pengolahan nasional dapat dijalankan kembali, perbarui hasil analisis dan periksa `outputs/validasi.json` agar tahun serta tanggal pada dokumentasi tetap sesuai.

## File proyek

| File | Kegunaan |
| --- | --- |
| `peta_karhutla_indonesia_38_provinsi.ipynb` | Notebook utama |
| `analisis_provinsi.py` | Pencocokan kabupaten/kota dan peta tiap provinsi |
| `fire_nrt_J1V-C2_840207.csv` | Deteksi titik panas VIIRS |
| `luas-karhutla-provinsi.xlsx` | Luas karhutla per provinsi, kolom 2018–2026 |
| `provinsi.geojson` | Batas 38 provinsi |
| `kab_kota.geojson` | Batas 514 kabupaten/kota |
| `requirements.txt` | Paket Python untuk pengolahan |
| `Readme.txt` | Tautan panduan NASA FIRMS |
| `outputs/` | Peta, tabel, GeoJSON, dan laporan validasi |

## Status setelah penghapusan file lama

Notebook masih memanggil `peta_karhutla.py` pada bagian 1 dan 4, tetapi file tersebut sudah tidak ada. Karena itu, **Run All belum dapat dijalankan dari awal**.

Agar notebook dapat berjalan dari awal, pengolahan nasional perlu dipindahkan ke notebook atau modul pengolahan yang tersedia. Bagian 9 menggunakan `analisis_provinsi.py` dan membaca hasil nasional `outputs/provinsi_karhutla.geojson` serta `outputs/titik_panas.geojson`.

## Persiapan dan membuka notebook

Jalankan terminal dari folder proyek:

```powershell
python -m pip install -r requirements.txt
python -m pip install ipykernel
code peta_karhutla_indonesia_38_provinsi.ipynb
```

Di VS Code, pasang ekstensi **Python** dan **Jupyter** dari Microsoft. Klik **Select Kernel**, lalu pilih lingkungan Python yang memiliki paket proyek. Setelah ketergantungan pengolahan nasional diperbaiki, gunakan **Run All** untuk menjalankan seluruh notebook secara berurutan.

Jika hasil nasional sudah tersedia dan hanya ingin menjalankan bagian provinsi, jalankan sel berikut terlebih dahulu:

```python
from pathlib import Path
from IPython.display import display, Image

ROOT = Path.cwd()
```

Folder kerja harus merupakan folder proyek. Jalankan sel persiapan bersama pada **bagian 9**, lalu tekan **▶** pada sel provinsi yang diinginkan. Sel provinsi memerlukan variabel `data_provinsi` dari persiapan bersama tersebut.

## Isi notebook

1. Persiapan lingkungan dan pemeriksaan file.
2. Parameter tahun luas, satuan, dan sumber CSV.
3. Pemeriksaan data sumber.
4. Pengolahan nasional dengan GeoPandas.
5. Validasi dan rekonsiliasi hasil.
6. Peta nasional titik panas dan luas karhutla.
7. Pemeriksaan titik yang belum cocok dengan provinsi.
8. Warna wilayah dan peringkat provinsi.
9. Persiapan kabupaten/kota dan 38 sel khusus provinsi.

`TAHUN` memilih kolom luas di Excel, bukan tanggal pengamatan CSV. `SATUAN` tetap belum diverifikasi sampai satuan sumber dikonfirmasi; isi `ha` hanya jika sumber menyatakan hektare.

## Output setiap provinsi

Setiap sel menampilkan:

- Peta provinsi dan titik panas menurut confidence.
- Batas dan nomor kabupaten/kota beserta nama pada legenda.
- Informasi luas provinsi dan tahun datanya.
- Tabel kabupaten/kota yang diurutkan berdasarkan jumlah deteksi.
- Tabel koordinat setiap titik dan status pencocokan wilayah.

Warna kabupaten semakin gelap jika jumlah deteksi cocok semakin banyak. Skala warna mengikuti data tiap provinsi sehingga warna antar-peta tidak bisa dibandingkan langsung. Provinsi tanpa deteksi tetap ditampilkan dengan keterangan sesuai tanggal data.

Peta dan tabel disimpan di `outputs/provinsi/`:

- `<kode>_<nama_provinsi>.png`: peta.
- `<kode>_<nama_provinsi>_ringkasan.csv`: jumlah deteksi per kabupaten/kota.
- `<kode>_<nama_provinsi>_titik.csv`: rincian lokasi titik panas.

## Hasil nasional dan pemeriksaan lokasi

| File di `outputs/` | Isi |
| --- | --- |
| `peta_karhutla.png` | Dua panel peta titik panas dan luas karhutla |
| `peta_warna_provinsi.png` | Warna dan nomor untuk mengenali provinsi |
| `peringkat_provinsi.png` dan `peringkat_provinsi.csv` | Perbandingan luas dan jumlah deteksi |
| `ringkasan_provinsi.csv` | Luas dan jumlah deteksi tiap provinsi |
| `provinsi_karhutla.geojson` | Batas provinsi yang diperbaiki dan hasil penggabungan |
| `titik_panas.geojson` dan `titik_panas_dengan_provinsi.csv` | Deteksi dan status provinsi |
| `hasil_pencocokan_spasial.csv` | Hasil mentah pencocokan provinsi |
| `koordinat_tidak_valid.csv` dan `validasi.json` | Pemeriksaan data dan rekonsiliasi |
| `titik_panas_dengan_kabupaten.csv` | Deteksi dan status kabupaten/kota |
| `pencocokan_kabupaten_mentah.csv` | Hasil mentah pencocokan kabupaten/kota |

Menjalankan ulang pengolahan memperbarui hasil terkait. Data sumber tidak diubah.

Folder `outputs/` ikut disimpan di repositori GitHub agar peta dan tabel dapat dilihat atau diunduh tanpa menjalankan notebook. Hasil yang tersimpan merupakan snapshot pengolahan sebelumnya. Setelah mengubah data atau parameter, jalankan ulang analisis lalu commit hasil yang diperbarui.

## Metode dan interpretasi

Koordinat menggunakan EPSG:4326, longitude sebagai X dan latitude sebagai Y. Geometri diperbaiki dengan `make_valid`, bagian nonpoligon dibuang, dan bagian poligon digabung kembali berdasarkan kode wilayah. Excel digabungkan ke provinsi memakai kode wilayah. Angka seperti `1.284,70` dibaca sebagai `1284.70`; baris Total tidak dianggap sebagai provinsi.

Spatial join menggunakan `intersects`. Titik yang cocok dengan beberapa wilayah ditandai ambigu. Kabupaten hanya diterima jika konsisten dengan provinsi titik tersebut. Titik yang belum cocok tetap disimpan tanpa dipindahkan ke wilayah terdekat.

CSV awal memuat 1.009 deteksi pada 7 November 2026. Pemeriksaan sebelumnya menghasilkan 1.000 titik cocok dengan provinsi dan 998 titik cocok dengan kabupaten/kota. Dua titik memiliki provinsi tetapi belum cocok dengan kabupaten; sembilan titik belum cocok dengan provinsi. Hasil dapat berubah jika data atau batas diperbarui.

Jumlah deteksi bukan jumlah kejadian kebakaran atau luas terbakar. Titik panas belum membuktikan kebakaran pada tutupan hutan; analisis itu memerlukan data tutupan lahan. Data luas kabupaten tidak tersedia, sehingga perbandingan kabupaten menggunakan jumlah deteksi pada tanggal CSV.

Satuan dan tanggal pemutakhiran luas belum dikonfirmasi dari tabel Excel. Kolom 2026 tidak otomatis berarti data satu tahun penuh. Nol deteksi pada satu tanggal tidak berarti bebas kebakaran. Nilai nol pada sumber tetap dipertahankan; perbandingan historis perlu memperhatikan pemekaran dan perubahan batas provinsi.

## Referensi metode

- [GeoPandas make_valid](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.make_valid.html)
- [GeoPandas spatial join](https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html)
