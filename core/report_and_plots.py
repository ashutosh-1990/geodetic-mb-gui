import os
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pandas as pd
import re
import numpy as np
import geopandas as gpd
import rasterio
from rasterio import open as rio_open
from core import gui_plots
from geoutils import Vector
from xdem import DEM

def clean_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\(\)\[\]\s]', '', name).replace(" ", "_") + ".png"

def save_figure(fig, filepath):
    fig.tight_layout()
    canvas = FigureCanvas(fig)
    fig.savefig(filepath)
    plt.close(fig)

def save_raster(array, reference_raster_path, save_path, dtype=np.float32):
    """Save a numpy array as a GeoTIFF using a reference raster for metadata."""
    with rio_open(reference_raster_path) as ref:
        profile = ref.profile.copy()
        profile.update(dtype=dtype, count=1, compress='lzw', nodata=np.nan)

        array_to_write = np.where(np.isnan(array), ref.nodata if ref.nodata is not None else -9999, array)

        with rasterio.open(save_path, 'w', **profile) as dst:
            dst.write(array_to_write.astype(dtype), 1)

def save_all_figures_and_report(result, gui, save_dir):
    
    correction_applied = hasattr(gui, "snowfall_estimates_df")
    
    os.makedirs(save_dir, exist_ok=True)

    # Save text report
    report_path = os.path.join(save_dir, "geodetic_mass_balance_report.txt")
    with open(report_path, "w") as f:
        f.write("GEODETIC GLACIER MASS BALANCE REPORT\n")
        f.write("=" * 40 + "\n")
        f.write(f"Date Generated: {datetime.datetime.now()}\n\n")
        f.write("INPUT PARAMETERS\n")
        f.write("-" * 20 + "\n")
        f.write(f"Reference DEM: {gui.ref_dem_path.get()}\n")
        f.write(f"Aligned DEM: {gui.align_dem_path.get()}\n")
        f.write(f"Unstable Terrain: {gui.unstable_path.get()}\n")
        f.write(f"Glacier Shapefile: {gui.glacier_path.get()}\n")
        f.write(f"Reference Date: {gui.ref_date.get_date()}\n")
        f.write(f"Aligned Date: {gui.align_date.get_date()}\n")
        f.write(f"Co-registration: {gui.coreg_algo.get()}\n")
        f.write(f"Interpolation: {gui.interpolation_dropdown.get()}\n")
        f.write(f"Ice Density (Uniform): {gui.param_vars[2].get()}\n")
        f.write(f"Ice Density Uncertainty: {gui.param_vars[3].get()}\n")
        #f.write(f"Seasonality Correction: {gui.seasonality_correction.get()}\n")
        f.write(f"Heteroscedasticity: {gui.hetero_dropdown.get()}\n")
        f.write(f"Spatial Correlation: {gui.spatial_corr_dropdown.get()}\n")
        f.write(f"ELA: {gui.param_vars[4].get()}\n")
        f.write(f"Max Gain (Accumulation Zone): {gui.param_vars[5].get()}\n")
        f.write(f"Max Loss (Accumulation Zone): {gui.param_vars[6].get()}\n")
        f.write(f"Max Gain (Ablation Zone): {gui.param_vars[7].get()}\n")
        f.write(f"Max Loss (Ablation Zone): {gui.param_vars[8].get()}\n")
        f.write("\n")
        f.write("Elevation change (m) results represent total change for the entire time period of analysis \n") 
        f.write("Mass balance (m.w.e per annum) results are annual rate of change \n")
        
        if correction_applied:
            f.write("Snow bias and seasonality correction applied to individual glaciers using ERA5 data and/or manual intervention at mass balance level only.\n")
        
        try:
            if hasattr(gui, "snowfall_estimates_df"):
                factor_entry = getattr(gui, "multiplicative_bias_factor", None)
                if factor_entry is not None:
                    f.write(f"Multiplicative Bias Correction Factor applied to snow bias and seasonality correction values: {factor_entry}\n")
        except Exception as e:
            print(f"[Warning] Could not retrieve multiplicative bias factor: {e}")
            
        f.write("\n")

        f.write("GLACIER-WISE RESULTS\n")
        f.write("-" * 20 + "\n")
        df = result["data"]["df_mass_balance"]
        
        # Add topographic statistics
        from core.report_and_plots import compute_glacier_topo_stats
        topo_df = compute_glacier_topo_stats(gui.glacier_path.get(), gui.ref_dem_path.get())
        df = df.merge(topo_df, on="RGI_ID")
        
        # ✅ Compute glacier area in km² using reference DEM's CRS and consistent glacier IDs
        try:
            import rasterio
            gdf = gpd.read_file(gui.glacier_path.get())
        
            # Use CRS of reference DEM to ensure area is in meters²
            with rasterio.open(gui.ref_dem_path.get()) as src:
                dem_crs = src.crs
            gdf = gdf.to_crs(dem_crs)
            gdf["area_km2"] = gdf.geometry.area / 1e6  # m² to km²
        
            use_rgi = "rgi_id" in gdf.columns
            glacier_ids = df["RGI_ID"]
            areas = []
        
            for i, gid in enumerate(glacier_ids):
                if use_rgi:
                    area = gdf[gdf["rgi_id"] == gid]["area_km2"].values[0]
                else:
                    # Fall back to index-based match: G1 → row 0, G2 → row 1, ...
                    index = int(gid[1:]) - 1  # 'G1' → 0
                    area = gdf.iloc[index]["area_km2"]
                areas.append(area)
        
            df["Glacier_Area_km2"] = areas
        
        except Exception as e:
            print(f"[Warning] Could not add glacier area: {e}")
            df["Glacier_Area_km2"] = np.nan
    
        f.write(df.to_string(index=False))

    # Save glacier-wise results to CSV
    csv_path = os.path.join(save_dir, "glacier_mass_balance_summary.csv")
    df.to_csv(csv_path, index=False)
    # Append footnote if correction applied
    if correction_applied:
        with open(csv_path, "a") as f:
            f.write("\nNote: Snow bias and seasonality correction applied using ERA5 and/or manual intervention at mass balance level only.\n")

    # Save snowfall correction values if available
    if correction_applied:
        try:
            correction_df = gui.snowfall_estimates_df.copy()
            correction_csv_path = os.path.join(save_dir, "snowfall_correction_values.csv")
            correction_df.to_csv(correction_csv_path, index=False)
        except Exception as e:
            print(f"[Warning] Could not save snowfall correction values: {e}")

    # Save raster arrays as GeoTIFFs
    raster_map = {
        "dh_after_coreg.tif": result["data"].get("dh_after_coreg"),
        "dh_after_coreg_nmad.tif": result["data"].get("dh_after_coreg_nmad"),
        "dh_after_coreg_nmad_glacierfilter.tif": result["data"].get("dh_after_coreg_nmad_glacierfilter"),
        "dh_after_coreg_nmad_elafilter.tif": result["data"].get("dh_after_coreg_nmad_elafilter"),
        "dh_interpolated.tif": result["data"].get("dh_interpolated"),
        "sig_dh.tif": result["data"].get("sig_dh"),
        "z_dh.tif": result["data"].get("z_dh"),
    }

    for filename, array in raster_map.items():
        try:
            if array is not None:
                save_raster(array.data, gui.ref_dem_path.get(), os.path.join(save_dir, filename))
        except Exception as e:
            print(f"[Warning] Could not save raster '{filename}': {e}")

    # Save all distinct plots
    plot_map = {
        "Raw DEM Difference": lambda: _plot_raw_dem_difference(gui),
        "Reference DEM with Glacier Shapefile": lambda: gui_plots.display_image(None, gui.ref_dem_path.get(), gui.glacier_path.get(), title="Reference DEM with Glaciers", return_fig=True),
        "To-be-aligned DEM with Glacier Shapefile": lambda: gui_plots.display_image(None, gui.align_dem_path.get(), gui.glacier_path.get(), title="To-be-aligned DEM with Glaciers", return_fig=True),
        "Co-registered DEM Difference": lambda: gui_plots.plot_dh_coreg(None, result["data"]["dh_after_coreg"], gui.glacier_path.get(), "Co-registered DEM Difference", return_fig=True),
        "Filtered DEM Difference (NMAD Outlier Removal)": lambda: gui_plots.plot_dh_coreg(None, result["data"]["dh_after_coreg_nmad"], gui.glacier_path.get(), "Filtered DEM Difference (NMAD Outlier Removal)", return_fig=True),
        "Filtered DEM Difference (NMAD + Absolute Glacier Threshold)": lambda: gui_plots.plot_dh_coreg(None, result["data"]["dh_after_coreg_nmad_glacierfilter"], gui.glacier_path.get(), "Filtered DEM Difference (NMAD + Absolute Glacier Threshold)", return_fig=True),
        "Filtered DEM difference (NMAD + ELA Filter)": lambda: gui_plots.plot_dh_coreg(None, result["data"]["dh_after_coreg_nmad_elafilter"], gui.glacier_path.get(), "Filtered DEM difference (NMAD + ELA Filter)", return_fig=True),
        "Interpolated DEM Difference (Hypsometric Method)": lambda: gui_plots.plot_dh_coreg(None, result["data"]["dh_interpolated"], gui.glacier_path.get(), "Interpolated DEM Difference (Hypsometric Method)", return_fig=True),
        "Histogram of Interpolated DEM Difference (Glacier Only)": lambda: gui_plots.plot_histogram_interpolated_ddem_glacieronly(None, result["data"]["dh_interpolated"], gui.glacier_path.get(), gui.interpolation_dropdown.get(), return_fig=True),
        "Modelled Error Map (Topographic Uncertainty)": lambda: gui_plots.plot_dh_coreg(None, result["data"]["sig_dh"], gui.glacier_path.get(), "Modelled Error Map (Topographic Uncertainty)", return_fig=True),
        "Standardized Elevation Changes for Stable Terrain": lambda: gui_plots.plot_dh_coreg(None, result["data"]["z_dh"], gui.glacier_path.get(), "Standardized Elevation Changes for Stable Terrain", return_fig=True),
        "Empirical and Modelled Variogram": lambda: gui_plots.plot_variogram(None, result["data"]["df_vgm"], result["data"]["func_sum_vgm"], return_fig=True),
        "Glacier-wise Elevation Change and Uncertainty": lambda: gui_plots.plot_glacier_uncertainty(None, result["data"]["df_uncertainty"], return_fig=True),
        "Annual Glacier Mass Balance with Uncertainty": lambda: gui_plots.plot_mass_balance_with_uncertainty(None, result["data"]["df_mass_balance"], "Annual Glacier Mass Balance with Uncertainty", return_fig=True)
    }

    for name, plot_func in plot_map.items():
        try:
            fig = plot_func()
            save_figure(fig, os.path.join(save_dir, clean_filename(name)))
        except Exception as e:
            print(f"[Warning] Could not save plot for '{name}': {e}")

def _plot_raw_dem_difference(gui):
    with rio_open(gui.ref_dem_path.get()) as ref, rio_open(gui.align_dem_path.get()) as align:
        ref_data = ref.read(1).astype(float)
        align_data = align.read(1).astype(float)
        ref_data[ref_data == ref.nodata] = np.nan
        align_data[align_data == align.nodata] = np.nan
        dh = align_data - ref_data
        extent = [ref.bounds.left, ref.bounds.right, ref.bounds.bottom, ref.bounds.top]
    gdf = gpd.read_file(gui.glacier_path.get())
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(dh, cmap='coolwarm', extent=extent, vmin=-300, vmax=300)
    gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=0.5)
    ax.set_title("Raw DEM Difference (Align - Reference)")
    fig.colorbar(im, ax=ax, label='Elevation Difference (m)')
    return fig


def compute_glacier_topo_stats(glacier_path, ref_dem_path):
    from geoutils import Vector
    from xdem import DEM
    import numpy as np
    import geopandas as gpd
    import pandas as pd

    ref = DEM(ref_dem_path)
    slope = ref.get_terrain_attribute(attribute=["slope"])
    gdf = gpd.read_file(glacier_path).to_crs(ref.crs)

    use_rgi = "rgi_id" in gdf.columns
    glacier_ids = gdf["rgi_id"].tolist() if use_rgi else [f"G{i+1}" for i in range(len(gdf))]

    topo_stats = []
    for i, geom in enumerate(gdf.geometry):
        single_gdf = gpd.GeoDataFrame(geometry=[geom], crs=gdf.crs)
        mask = Vector(single_gdf).create_mask(ref).data
        elev = ref.data[mask]
        slp = slope[mask]


        topo_stats.append({
            "RGI_ID": glacier_ids[i],
            "Median_Elev": np.nanmedian(elev),
            "Mean_Elev": np.nanmean(elev),
            "Max_Elev": np.nanmax(elev),
            "Min_Elev": np.nanmin(elev),
            "Mean_Slope": np.nanmean(slp),
            #"Mean_Aspect": np.nanmean(asp) # ASPECT removed, as the mean value cannot be taken! 
        })

    return pd.DataFrame(topo_stats)

