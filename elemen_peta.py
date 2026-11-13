"""Elemen bersama untuk peta geografis EPSG:4326 dengan utara di atas."""


def tambah_elemen_peta(ax):
    ax.annotate('U', xy=(0.95, 0.90), xytext=(0.95, 0.76),
                xycoords='axes fraction', ha='center', va='center',
                fontsize=12, fontweight='bold',
                arrowprops={'arrowstyle': '-|>', 'color': '#172b3b', 'lw': 1.8},
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.8})
    ax.text(0.01, 0.01, 'WGS 84 / EPSG:4326', transform=ax.transAxes,
            fontsize=8, va='bottom',
            bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.85})
