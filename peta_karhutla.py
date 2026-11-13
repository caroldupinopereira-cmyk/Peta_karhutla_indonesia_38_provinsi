"""Peta awal karhutla Indonesia dengan GeoPandas. Jalankan: python peta_karhutla.py."""
from pathlib import Path
import argparse
import json

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "All Dataset"


def angka_indonesia(value):
    """Pertahankan angka asli, ubah teks seperti 1.284,70 menjadi 1284.70."""
    if pd.isna(value) or str(value).strip() in {"", "-"}:
        return float("nan")
    if isinstance(value, str):
        return float(value.strip().replace(".", "").replace(",", "."))
    return float(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tahun", type=int, default=2026)
    parser.add_argument("--csv", type=Path, default=DATA_DIR / "fire_nrt_J1V-C2_840207.csv")
    parser.add_argument("--satuan", default="ha")
    args = parser.parse_args()
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)

    prov = gpd.read_file(DATA_DIR / "provinsi.geojson")
    if prov.crs is None:
        raise ValueError("GeoJSON tidak memiliki CRS.")
    prov = prov.to_crs(4326)
    invalid = int((~prov.is_valid).sum())
    prov.geometry = prov.geometry.make_valid()
    # make_valid dapat menghasilkan GeometryCollection: simpan hanya bagian poligon.
    prov = prov.explode(index_parts=False)
    prov = prov[prov.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    prov = prov.dissolve(by="code", as_index=False)
    prov["code"] = prov["code"].astype(str).str.zfill(2)
    if not prov.is_valid.all() or prov.geometry.is_empty.any() or prov.code.duplicated().any():
        raise ValueError("Batas provinsi belum memenuhi validasi.")

    luas = pd.read_excel(DATA_DIR / "luas-karhutla-provinsi.xlsx", sheet_name="data")
    luas.columns = luas.columns.map(str)
    year = str(args.tahun)
    if year not in luas:
        raise ValueError(f"Tahun {year} tidak tersedia di Excel.")
    total_source = luas.loc[luas["Provinsi"].eq("Total"), year].map(angka_indonesia)
    luas = luas[luas["Kode Wilayah"].notna()].copy()
    luas["code"] = luas["Kode Wilayah"].astype(int).astype(str).str.zfill(2)
    luas["luas_karhutla"] = luas[year].map(angka_indonesia)
    if luas.code.duplicated().any():
        raise ValueError("Kode wilayah Excel duplikat.")
    unknown = sorted(set(luas.code) - set(prov.code))
    if unknown:
        raise ValueError(f"Kode Excel tidak ada di batas provinsi: {unknown}")
    prov = prov.merge(luas[["code", "luas_karhutla"]], on="code", how="left", validate="one_to_one")
    prov["tahun_luas"] = args.tahun

    raw = pd.read_csv(args.csv, dtype={"acq_time": str})
    raw["id_deteksi"] = range(1, len(raw) + 1)
    for col in ["longitude", "latitude"]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    valid = raw.longitude.between(-180, 180) & raw.latitude.between(-90, 90)
    raw.loc[~valid].to_csv(out / "koordinat_tidak_valid.csv", index=False)
    points = gpd.GeoDataFrame(raw[valid].copy(), geometry=gpd.points_from_xy(raw.loc[valid, "longitude"], raw.loc[valid, "latitude"]), crs=4326)
    joined = gpd.sjoin(points, prov[["code", "name", "geometry"]], how="left", predicate="intersects")
    # Titik di batas/overlap tidak boleh dihitung dua kali atau dipilih sembarang.
    ambiguous = joined.loc[joined.id_deteksi.duplicated(keep=False), "id_deteksi"].unique()
    joined.drop(columns="geometry").to_csv(out / "hasil_pencocokan_spasial.csv", index=False)
    assigned = joined[~joined.id_deteksi.isin(ambiguous)].copy()
    assigned["status_wilayah"] = assigned.code.notna().map({True: "cocok", False: "di luar batas poligon"})
    if len(ambiguous):
        amb = points[points.id_deteksi.isin(ambiguous)].copy()
        amb["status_wilayah"] = "ambigu: lebih dari satu provinsi"
        assigned = pd.concat([assigned, amb], ignore_index=True)
    counts = assigned[assigned.status_wilayah.eq("cocok")].groupby("code").size()
    prov["jumlah_deteksi"] = prov.code.map(counts).fillna(0).astype(int)
    if len(assigned) != len(points):
        raise ValueError("Rekonsiliasi jumlah deteksi gagal.")
    prov.drop(columns="geometry").to_csv(out / "ringkasan_provinsi.csv", index=False)
    assigned.drop(columns=["geometry", "index_right"], errors="ignore").to_csv(out / "titik_panas_dengan_provinsi.csv", index=False)
    prov.to_file(out / "provinsi_karhutla.geojson", driver="GeoJSON")
    assigned.drop(columns="index_right", errors="ignore").to_file(out / "titik_panas.geojson", driver="GeoJSON")

    dates = sorted(points.acq_date.unique())
    period = " sampai ".join([dates[0], dates[-1]]) if len(dates) > 1 else dates[0]
    fig, axes = plt.subplots(2, 1, figsize=(16, 12), facecolor="#f5f7fa")
    colors = {"l": "#f6bd60", "n": "#ed6a24", "h": "#b51025"}
    for ax in axes:
        ax.set_facecolor("#e7f0f5")
        ax.set_xlim(94, 142)
        ax.set_ylim(-12, 7)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=8, colors="#526477")
        ax.set_xlabel("Bujur", fontsize=9)
        ax.set_ylabel("Lintang", fontsize=9)
        for spine in ax.spines.values():
            spine.set_color("#cad5de")
    prov.plot(ax=axes[0], color="#ffffff", edgecolor="#8594a2", linewidth=0.4)
    for conf, color in colors.items():
        subset = points[points.confidence.eq(conf)]
        if len(subset):
            subset.plot(ax=axes[0], color=color, markersize=8, alpha=0.75)
    axes[0].set_title(f"Deteksi titik panas VIIRS | {period} | {len(points):,} deteksi", loc="left", fontsize=13, pad=12)
    axes[0].legend(handles=[Line2D([], [], marker="o", linestyle="", color=c, label=l, markersize=5) for c, l in zip(colors.values(), ["Confidence rendah", "Confidence nominal", "Confidence tinggi"])], loc="lower left", fontsize=8)
    prov.plot(ax=axes[1], column="luas_karhutla", cmap="YlOrRd", edgecolor="#8594a2", linewidth=0.4, legend=True, legend_kwds={"label": f"Nilai luas ({args.satuan})", "shrink": 0.65}, missing_kwds={"color": "#c4cbd2", "label": "Data tidak tersedia"})
    axes[1].set_title(f"Luas karhutla per provinsi | kolom tahun {args.tahun}", loc="left", fontsize=13, pad=12)
    fig.suptitle("Titik panas dan karhutla Indonesia", x=0.07, ha="left", fontsize=23, fontweight="bold", color="#192d40")
    fig.text(0.07, 0.025, "Sumber: CSV NASA FIRMS, Excel luas karhutla, dan GeoJSON lokal. Titik panas bukan konfirmasi kebakaran hutan.\nLuas mengikuti periode pada Excel; tanggal pemutakhiran dan satuan perlu dikonfirmasi. Kedua panel memiliki periode berbeda.", fontsize=9, color="#526477")
    fig.subplots_adjust(top=0.91, bottom=0.10, hspace=0.30, left=0.07, right=0.94)
    fig.savefig(out / "peta_karhutla.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    # Warna kategori membedakan wilayah, bukan tingkat keparahan.
    from matplotlib.colors import to_hex
    import colorsys
    palette = [to_hex(colorsys.hsv_to_rgb((i * 0.61803398875) % 1, 0.40 + (i % 2) * 0.18, 0.92)) for i in range(len(prov))]
    fig, ax = plt.subplots(figsize=(18, 10), facecolor="#f5f7fa")
    ax.set_facecolor("#e7f0f5")
    prov.plot(ax=ax, color=palette, edgecolor="#455363", linewidth=0.45)
    for number, (_, row) in enumerate(prov.iterrows(), start=1):
        label = row.geometry.representative_point()
        ax.text(label.x, label.y, str(number), fontsize=7, ha="center", va="center", bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.8))
    ax.set_xlim(94, 142)
    ax.set_ylim(-12, 7)
    ax.set_title("Wilayah 38 provinsi Indonesia", loc="left", fontsize=20, pad=15)
    handles = [Line2D([], [], marker="s", linestyle="", color=color, label=f"{i}. {name}") for i, (color, name) in enumerate(zip(palette, prov.name), start=1)]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.025))
    fig.text(0.08, 0.32, "Warna membedakan provinsi. Nomor merujuk ke legenda; tingkat dampak ditampilkan pada grafik peringkat.", fontsize=9)
    fig.subplots_adjust(left=0.06, right=0.97, top=0.93, bottom=0.35)
    fig.savefig(out / "peta_warna_provinsi.png", dpi=160)
    plt.close(fig)

    ranked = prov[["code", "name", "luas_karhutla", "jumlah_deteksi"]].copy()
    ranked["peringkat_luas"] = ranked.luas_karhutla.rank(method="min", ascending=False).astype("Int64")
    ranked["peringkat_deteksi"] = ranked.jumlah_deteksi.rank(method="min", ascending=False).astype("Int64")
    ranked.sort_values("luas_karhutla", ascending=False).to_csv(out / "peringkat_provinsi.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(18, 13), facecolor="#f5f7fa")
    for ax, field, title, color in zip(axes, ["luas_karhutla", "jumlah_deteksi"], [f"Luas karhutla | {args.tahun}", f"Deteksi titik panas | {period}"], ["#cb422e", "#267e9c"]):
        ordered = ranked.sort_values(field, ascending=True, na_position="first")
        bars = ax.barh(ordered.name, ordered[field], color=color, height=0.7)
        ax.bar_label(bars, labels=[f"{v:,.2f}" if field == "luas_karhutla" else f"{v:,}" for v in ordered[field]], padding=3, fontsize=7)
        ax.set_title(title, fontsize=13, loc="left")
        ax.set_xlabel(args.satuan if field == "luas_karhutla" else "Jumlah deteksi yang cocok dengan provinsi")
        ax.tick_params(axis="y", labelsize=8)
        ax.set_xlim(0, max(ordered[field].max() * 1.25, 1))
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Perbandingan dampak karhutla per provinsi", fontsize=21, x=0.04, ha="left")
    fig.text(0.04, 0.025, "Luas dan deteksi memiliki periode berbeda. Peringkat menunjukkan nilai absolut, bukan persentase wilayah terbakar.\nDeteksi satelit bukan jumlah kejadian kebakaran. Titik di luar poligon dan titik ambigu tidak masuk peringkat provinsi.", fontsize=9)
    fig.tight_layout(rect=(0.01, 0.06, 1, 0.96), w_pad=4)
    fig.savefig(out / "peringkat_provinsi.png", dpi=160)
    plt.close(fig)
    report = {"tahun_luas": args.tahun, "satuan": args.satuan, "periode_titik_panas": period, "provinsi": len(prov), "geometri_awal_tidak_valid": invalid, "baris_csv": len(raw), "koordinat_valid": len(points), "status_wilayah": assigned.status_wilayah.value_counts().to_dict(), "provinsi_tanpa_luas": prov.loc[prov.luas_karhutla.isna(), "name"].tolist(), "jumlah_luas_provinsi": float(prov.luas_karhutla.sum()), "total_luas_excel": float(total_source.iloc[0]) if len(total_source) else None}
    (out / "validasi.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Hasil disimpan di {out}")


if __name__ == "__main__":
    main()
