# core/gui_plots.py

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import rasterio
from rasterio.plot import show
import geopandas as gpd
import numpy as np
import xdem
from rasterio import open as rio_open
from geoutils import Vector
from xdem import DEM
from xdem.spatialstats import nmad
import logging

def display_image(canvas_frame, raster_path=None, shapefile_path=None, title="", return_fig=False):
    fig, ax = plt.subplots(figsize=(7, 6))

    if raster_path and os.path.exists(raster_path):
        with rasterio.open(raster_path) as src:
            show(src, ax=ax, title=title)
    else:
        ax.set_title("Raster file not found.")

    if shapefile_path and os.path.exists(shapefile_path):
        gdf = gpd.read_file(shapefile_path)
        gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=0.5)

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_dh_coreg(canvas_frame, raster_obj, glacier_shp_path, plot_title="Raster Plot", return_fig=False):
    fig, ax = plt.subplots(figsize=(8, 6))

    data = raster_obj.data
    extent = [
        raster_obj.bounds.left,
        raster_obj.bounds.right,
        raster_obj.bounds.bottom,
        raster_obj.bounds.top
    ]

    vmin = np.nanmin(data)
    vmax = np.nanmax(data)
    #vmin = -300
    #vmax = 300
    img = ax.imshow(data, cmap="coolwarm", extent=extent, origin="upper", vmin=vmin, vmax=vmax)

    try:
        glacier_gdf = gpd.read_file(glacier_shp_path)
        glacier_gdf.boundary.plot(ax=ax, edgecolor="black", linewidth=0.8)
    except Exception as e:
        print(f"[WARNING] Failed to load glacier shapefile: {e}")

    ax.set_title(plot_title)
    fig.colorbar(img, ax=ax, label="Value")

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
def plot_dh_coreg2(canvas_frame, raster_obj, glacier_shp_path, plot_title="Raster Plot", return_fig=False):
    fig, ax = plt.subplots(figsize=(8, 6))

    data = raster_obj.data
    extent = [
        raster_obj.bounds.left,
        raster_obj.bounds.right,
        raster_obj.bounds.bottom,
        raster_obj.bounds.top
    ]

    vmin = -300
    vmax = 300
    img = ax.imshow(data, cmap="coolwarm", extent=extent, origin="upper", vmin=vmin, vmax=vmax)

    try:
        glacier_gdf = gpd.read_file(glacier_shp_path)
        glacier_gdf.boundary.plot(ax=ax, edgecolor="black", linewidth=0.8)
    except Exception as e:
        print(f"[WARNING] Failed to load glacier shapefile: {e}")

    ax.set_title(plot_title)
    fig.colorbar(img, ax=ax, label="Value")

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_histogram_interpolated_ddem_glacieronly(canvas_frame, dem, glacier_path, interpolation_algo, bins=100, return_fig=False):
    gdf = gpd.read_file(glacier_path)
    glacier_mask = Vector(gdf).create_mask(dem)
    data = dem.data.filled(np.nan)
    masked_data = data[glacier_mask.data]
    valid_values = masked_data[np.isfinite(masked_data)]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(valid_values, bins=bins, color="lightgreen", edgecolor="black")
    ax.set_title(f"Histogram of Interpolated DEM Difference (Glacier Only)\n({interpolation_algo})")
    ax.set_xlabel("Elevation Change (m)")
    ax.set_ylabel("Frequency")

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_elevation_heteroscedasticity(canvas_frame, dh, ref_dem_path, unstable_path, variables, return_fig=False):
    ref = DEM(ref_dem_path)
    slope, aspect, curvature = ref.get_terrain_attribute(attribute=["slope", "aspect", "curvature"])

    if unstable_path:
        mask = ~Vector(unstable_path).create_mask(ref).data
    else:
        mask = np.ones_like(ref.data, dtype=bool)

    dh_arr = dh.data[mask]
    var_arrs = {"slope": slope[mask], "aspect": aspect[mask], "curvature": curvature[mask]}

    bins = {
        "slope": np.linspace(0, 90, 10),
        "aspect": np.linspace(0, 360, 10),
        "curvature": np.linspace(-10, 10, 10)
    }

    list_var = [var_arrs[v] for v in variables]
    list_bins = [bins[v] for v in variables]

    df = xdem.spatialstats.nd_binning(
        dh_arr,
        list_var=list_var,
        list_var_names=variables,
        statistics=["count", xdem.spatialstats.nmad],
        list_var_bins=list_bins
    )

    fig, ax = plt.subplots(figsize=(7, 5))

    if len(variables) == 1:
        v = variables[0]
        xdem.spatialstats.plot_1d_binning(df, v, "nmad", v.capitalize(), "NMAD of dh (m)", ax=ax)
        fig.suptitle(f"NMAD vs {v.capitalize()}")
    elif len(variables) == 2:
        v1, v2 = variables
        xdem.spatialstats.plot_2d_binning(df, v1, v2, "nmad", v1.capitalize(), v2.capitalize(), "NMAD of dh (m)", ax=ax)
        fig.suptitle(f"NMAD: {v1.capitalize()} vs {v2.capitalize()}")

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_glacier_uncertainty(canvas_frame, df, return_fig=False):
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(df))

    ax.errorbar(x, df["Elevation_Change"], yerr=df["Uncertainty"], fmt='o', ecolor='red', capsize=7)
    ax.axhline(y=0, color='blue', linestyle='--', linewidth=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels(df["RGI_ID"], rotation=90)
    ax.set_ylabel("Elevation Change (m)")
    ax.set_title("Glacier-wise Elevation Change with Uncertainty")
    ax.grid(True)
    fig.tight_layout()

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_mass_balance_with_uncertainty(canvas_frame, df, plot_title, return_fig=False):
    import matplotlib.patheffects as path_effects

    fig, ax = plt.subplots(figsize=(5, 6))
    x = np.arange(len(df))
    ax.errorbar(
        x, df["Mass_Balance"],
        yerr=df["MB_Uncertainty"],
        fmt='o', ecolor='red', capsize=8,
        label="Annual Mass Balance ± uncertainty"
    )
    ax.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(df["RGI_ID"], rotation=90)
    ax.set_ylabel("Mass Balance (m w.e. / year)")
    ax.set_title(plot_title)
    ax.legend()
    ax.grid(True)

    for i, rgi_id in enumerate(df["RGI_ID"]):
        annotation = ax.annotate(
            f"{df['Mass_Balance'][i]:.2f}",
            xy=(x[i], df["Mass_Balance"][i]),
            xytext=(20, 10),
            textcoords='offset points',
            ha='center', fontsize=10, color='blue'
        )
        annotation.set_path_effects([
            path_effects.Stroke(linewidth=10, foreground='yellow'),
            path_effects.Normal()
        ])

    fig.tight_layout()

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

def plot_variogram(canvas_frame, df_vgm, func_sum_vgm, return_fig=False):
    fig, ax = plt.subplots(figsize=(7, 5))
    xdem.spatialstats.plot_variogram(
        df_vgm, [func_sum_vgm], ["Sum of Gaussian and Spherical"], xscale="log", ax=ax
    )
    ax.set_title("Empirical and Fitted Variogram")
    ax.grid(True)
    fig.tight_layout()

    if return_fig:
        return fig
    else:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


def plot_zdh_histogram(z_dh, unstable_shp=None, canvas_frame=None, return_fig=False):
    """
    Plot histogram of standardized elevation change (z_dh) over stable terrain.
    """
    from geoutils import Vector

    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    from xdem.spatialstats import nmad

    # Create mask for stable terrain
    if unstable_shp:
        mask = ~Vector(unstable_shp).create_mask(z_dh).data
    else:
        mask = np.ones_like(z_dh.data, dtype=bool)

    data = z_dh.data[mask]
    data = data[np.isfinite(data)]

    mean_val = np.nanmean(data)
    nmad_val = nmad(data)

    import logging
    logging.info(f"[Stable Terrain z_dh Stats] Mean: {mean_val:.3f}, NMAD: {nmad_val:.3f}")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(data, bins=60, color="steelblue", edgecolor="black", alpha=0.8)
    ax.set_title("Histogram of Standardized Elevation Change (z_dh)")
    ax.set_xlabel("z_dh")
    ax.set_ylabel("Pixel count")
    ax.axvline(mean_val, color='red', linestyle='--', label=f"Mean: {mean_val:.4f}")
    ax.axvline(mean_val + nmad_val, color='orange', linestyle='--', label=f"NMAD: ±{nmad_val:.4f}")
    ax.axvline(mean_val - nmad_val, color='orange', linestyle='--')
    ax.legend()

    if return_fig:
        return fig

    if canvas_frame:
        # Embed into GUI
        for widget in canvas_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    else:
        plt.tight_layout()
        plt.show()

def plot_dh_interpolated_histogram(dh_interpolated, unstable_shp=None, canvas_frame=None, return_fig=False):
    """
    Plot histogram of interpolated elevation difference (dh) over stable terrain.
    """
    from geoutils import Vector
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from xdem.spatialstats import nmad
    import logging

    # Mask unstable terrain
    if unstable_shp:
        mask = ~Vector(unstable_shp).create_mask(dh_interpolated).data
    else:
        mask = np.ones_like(dh_interpolated.data, dtype=bool)

    data = dh_interpolated.data[mask]
    data = data[np.isfinite(data)]

    mean_val = np.nanmean(data)
    nmad_val = nmad(data)

    logging.info(f"[Stable Terrain dh Stats] Mean: {mean_val:.3f} m, NMAD: {nmad_val:.3f} m")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(data, bins=60, color="mediumseagreen", edgecolor="black", alpha=0.8)
    ax.set_title("Histogram of Interpolated DEM Difference (Stable Terrain Only)")
    ax.set_xlabel("Elevation Difference (m)")
    ax.set_ylabel("Pixel Count")
    ax.axvline(mean_val, color='red', linestyle='--', label=f"Mean: {mean_val:.2f}")
    ax.axvline(mean_val + nmad_val, color='orange', linestyle='--', label=f"NMAD: ±{nmad_val:.2f}")
    ax.axvline(mean_val - nmad_val, color='orange', linestyle='--')
    ax.legend()

    if return_fig:
        return fig

    if canvas_frame:
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    else:
        plt.tight_layout()
        plt.show()
