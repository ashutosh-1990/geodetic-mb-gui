# -*- coding: utf-8 -*-
# core/dem_processing.py

"""
dem_processing.py
This module contains the DEM co-registration function for geodetic glacier mass balance analysis.
"""

from xdem import dDEM, DEM
from xdem.coreg import NuthKaab, ICP, VerticalShift, Deramp
import numpy as np
from xdem.spatialstats import nmad
from geoutils import Vector
import datetime
import geopandas as gpd
from rasterio.features import rasterize


def coregister_dems(ref_dem_path, align_dem_path, method):
    """
    Perform DEM co-registration using a selected pipeline and return the elevation difference raster.

    Args:
        ref_dem_path (str): Path to the reference DEM file.
        align_dem_path (str): Path to the to-be-aligned DEM file.
        method (str): Co-registration method selected from GUI. Options:
                      - "Nuth & Kaab"
                      - "ICP"
                      - "Nuth & Kaab + Deramp (polynomial order = 1)"
                      - "ICP + Nuth & Kaab"
                      - "Vertical Shift + ICP + Nuth & Kaab"

    Returns:
        xdem.DEM: DEM difference (aligned - reference) after co-registration.
    """

    ref = DEM(ref_dem_path)
    align = DEM(align_dem_path)

    # Define coregistration pipeline
    if method == "Nuth & Kaab (NK)":
        pipeline = NuthKaab()
    elif method == "Iterative Closest Point (ICP)":
        pipeline = ICP()
    elif method == "NK + Deramp (polynomial order = 1)":
        pipeline = NuthKaab() + Deramp(poly_order=1)
    elif method == "NK + Deramp (polynomial order = 2)":
        pipeline = NuthKaab() + Deramp(poly_order=2) 
    elif method == "NK + Deramp (polynomial order = 3)":
        pipeline = NuthKaab() + Deramp(poly_order=3)
    elif method == "ICP + NK":
        pipeline = ICP() + NuthKaab()
    elif method == "NK + ICP":
        pipeline = NuthKaab() + ICP()
    elif method == "Vertical Shift (VS) + NK":
        pipeline = VerticalShift() + NuthKaab()
    elif method == "VS + NK + Deramp (polynomial order = 1)":
        pipeline = VerticalShift() + NuthKaab() + Deramp(poly_order=1)
    elif method == "VS + NK + Deramp (polynomial order = 2)":
        pipeline = VerticalShift() + NuthKaab() + Deramp(poly_order=2)
    elif method == "VS + NK + Deramp (polynomial order = 3)":
        pipeline = VerticalShift() + NuthKaab() + Deramp(poly_order=3)
    elif method == "VS + ICP + NK":
        pipeline = VerticalShift() + ICP() + NuthKaab()
    elif method == "VS + ICP + NK + Deramp (polynomial order = 1)":
        pipeline = VerticalShift() + ICP() + NuthKaab() + Deramp(poly_order=1)
    elif method == "VS + ICP + NK + Deramp (polynomial order = 2)":
        pipeline = VerticalShift() + ICP() + NuthKaab() + Deramp(poly_order=2)
    elif method == "VS + ICP + NK + Deramp (polynomial order = 3)":
        pipeline = VerticalShift() + ICP() + NuthKaab() + Deramp(poly_order=3)
    else:
        raise ValueError(f"Unsupported co-registration method: {method}")

    # Fit and apply coregistration
    pipeline.fit(reference_elev=ref, to_be_aligned_elev=align)
    aligned_corrected = pipeline.apply(align)

    dh_after_coreg = aligned_corrected - ref
    return dh_after_coreg

def remove_nmad_outliers(dem_diff: DEM, nmad_factor: float = 6, glacier_shapefile: str = None) -> DEM:
    
    """
    Remove outliers beyond ±(nmad_factor × NMAD) from the elevation difference raster,
    first globally and optionally also on glacier surfaces.

    Args:
        dem_diff (xdem.DEM): DEM difference raster (e.g., after co-registration)
        nmad_factor (float): Threshold multiplier for NMAD. Default is 6.
        glacier_shapefile (str, optional): Path to glacier shapefile. If provided,
                                           glacier-specific NMAD filtering will be applied.

    Returns:
        xdem.DEM: Filtered DEM difference raster with outliers masked.
    """
    arr = dem_diff.data
    mask = np.ma.getmaskarray(arr)

    # Step 1: Global NMAD filtering
    nmad_global = nmad(arr)
    global_outliers = np.abs(arr) > (nmad_factor * nmad_global)

    # Initialize combined mask
    combined_mask = np.logical_or(mask, global_outliers)

    # Step 2: Glacier-specific NMAD filtering (if shapefile is provided)
    if glacier_shapefile is not None:
        # Read shapefile
        gdf = gpd.read_file(glacier_shapefile)
        gdf = gdf.to_crs(dem_diff.crs)  # Ensure CRS matches

        # Rasterize glacier polygons
        glacier_mask = rasterize(
            [(geom, 1) for geom in gdf.geometry if geom.is_valid],
            out_shape=dem_diff.shape,
            transform=dem_diff.transform,
            fill=0,
            dtype="uint8"
        ).astype(bool)

        # Compute NMAD only on glacier pixels
        glacier_arr = np.ma.array(arr, mask=~glacier_mask)
        nmad_glacier = nmad(glacier_arr)

        # Identify glacier outliers using glacier NMAD
        glacier_outliers = np.logical_and(
            glacier_mask,
            np.abs(arr) > (nmad_factor * nmad_glacier)
        )

        # Combine masks
        combined_mask = np.logical_or(combined_mask, glacier_outliers)

    # Apply final mask
    arr_filtered = np.ma.array(arr, mask=combined_mask)

    filtered = DEM.from_array(
        data=arr_filtered,
        transform=dem_diff.transform,
        crs=dem_diff.crs,
        nodata=np.nan
    )

    return filtered

def to_xdem_dem(elev_input, like_dem: DEM):
    """
    Convert elevation input to an xdem.DEM object.

    Accepts:
      - xdem.DEM  (returned unchanged)
      - filepath string
      - rasterio dataset
      - numpy array (requires same transform & CRS as like_dem)
    """
    if isinstance(elev_input, DEM):
        return elev_input

    # If filepath is given
    if isinstance(elev_input, str):
        return DEM(elev_input)

    # If rasterio dataset is given
    if isinstance(elev_input, rasterio.io.DatasetReader):
        return DEM.from_array(
            data=elev_input.read(1),
            transform=elev_input.transform,
            crs=elev_input.crs,
            nodata=elev_input.nodata,
        )

    # If NumPy array is given
    if isinstance(elev_input, np.ndarray):
        return DEM.from_array(
            data=elev_input,
            transform=like_dem.transform,  # adopt same grid as dem_diff
            crs=like_dem.crs,
            nodata=np.nan
        )

    raise ValueError("Unsupported input type for elevation_dem.")

def remove_nmad_outliers_elev_binned(
    dem_diff: DEM,
    elevation_dem,
    glacier_shapefile: str,
    global_nmad_factor: float = 6.0,
    glacier_nmad_factor: float = 5.0,
    bin_size: float = 100.0,
) -> DEM:
    """
    Filter dh raster using:
      - Stable terrain: global NMAD threshold
      - Glaciers: per-elevation-band NMAD (100 m bins × 5 NMAD)
    """

    # --- Convert elevation input to DEM ---
    elevation_dem = to_xdem_dem(elevation_dem, like_dem=dem_diff)

    # Extract arrays
    arr = np.ma.array(dem_diff.data, copy=True)
    elev_arr = np.ma.array(elevation_dem.data, copy=False)

    # Existing masks
    base_mask = np.ma.getmaskarray(arr)
    elev_mask = np.ma.getmaskarray(elev_arr)

    # Combined initial mask
    common_invalid = np.logical_or(base_mask, elev_mask)
    arr.mask = common_invalid
    elev_arr.mask = common_invalid

    # Rasterize glacier polygons
    gdf = gpd.read_file(glacier_shapefile).to_crs(dem_diff.crs)

    glacier_mask = rasterize(
        [(geom, 1) for geom in gdf.geometry if geom.is_valid],
        out_shape=dem_diff.shape,
        transform=dem_diff.transform,
        fill=0,
        dtype="uint8",
    ).astype(bool)

    glacier_valid = np.logical_and(glacier_mask, ~common_invalid)
    stable_mask = np.logical_and(~glacier_mask, ~common_invalid)

    # ----------------------------------------------------------------------
    # 1) GLOBAL NMAD ON STABLE TERRAIN
    # ----------------------------------------------------------------------
    global_outliers = np.zeros(arr.shape, bool)

    if np.any(stable_mask):
        stable_dh = np.ma.array(arr, mask=~stable_mask)
        nmad_stable = nmad(stable_dh)

        if not (np.ma.is_masked(nmad_stable) or np.isnan(nmad_stable) or nmad_stable == 0):
            global_outliers = np.logical_and(
                stable_mask, np.abs(arr) > (global_nmad_factor * nmad_stable)
            )

    combined_mask = np.logical_or(common_invalid, global_outliers)

    # ----------------------------------------------------------------------
    # 2) GLACIER FILTERING: 100 m elevation bins × 5 NMAD
    # ----------------------------------------------------------------------
    glacier_outliers = np.zeros(arr.shape, bool)

    if np.any(glacier_valid):

        glacier_elev = np.ma.array(elev_arr, mask=~glacier_valid)
        min_elev = float(np.floor(glacier_elev.min() / bin_size) * bin_size)
        max_elev = float(np.ceil(glacier_elev.max() / bin_size) * bin_size)
        bins = np.arange(min_elev, max_elev + bin_size, bin_size)

        for z0, z1 in zip(bins[:-1], bins[1:]):
            bin_mask = np.logical_and.reduce((
                glacier_valid,
                elev_arr >= z0,
                elev_arr < z1
            ))

            if not np.any(bin_mask):
                continue

            dh_bin = np.ma.array(arr, mask=~bin_mask)
            nmad_bin = nmad(dh_bin)

            if np.ma.is_masked(nmad_bin) or np.isnan(nmad_bin) or nmad_bin == 0:
                continue

            glacier_outliers |= np.logical_and(
                bin_mask,
                np.abs(arr) > glacier_nmad_factor * nmad_bin
            )

    combined_mask |= glacier_outliers

    # --- Final output ---
    filtered = DEM.from_array(
        data=np.ma.array(arr, mask=combined_mask),
        transform=dem_diff.transform,
        crs=dem_diff.crs,
        nodata=np.nan
    )

    return filtered

def glacier_abs_filter(dem_diff: DEM, glacier_shapefile: str, abs_threshold: float) -> DEM:
    """
    Mask all values inside glacier outlines that exceed the absolute threshold.

    Args:
        dem_diff (xdem.DEM): The input elevation difference raster (e.g., NMAD filtered).
        glacier_shapefile (str): Path to glacier outline shapefile.
        abs_threshold (float): Threshold (e.g., 80 m). Values |dh| > threshold inside glacier will be masked.

    Returns:
        xdem.DEM: DEM with extreme glacier values removed.
    """

    # Copy to avoid in-place edits
    filtered_dh = dem_diff.copy()
    filtered_dh.nodata = np.nan

    # Load glacier outlines using geoutils
    glacier_vector = Vector(glacier_shapefile)

    # Create mask where True = inside glacier
    glacier_mask = glacier_vector.create_mask(filtered_dh).data.data

    # Apply masking: remove values beyond threshold inside glacier only
    mask_neg_extreme = glacier_mask & (filtered_dh.data.data < -abs_threshold)
    filtered_dh.data.data[mask_neg_extreme] = np.nan

    mask_pos_extreme = glacier_mask & (filtered_dh.data.data > abs_threshold)
    filtered_dh.data.data[mask_pos_extreme] = np.nan

    # Restore original nodata mask
    filtered_dh.data.mask = dem_diff.data.mask.copy()

    return filtered_dh

def glacier_ela_filter(dem_diff: DEM, glacier_shapefile: str, ref_dem_path: str, ela: float,
                        gain_accum: float, loss_accum: float,
                        gain_ablation: float, loss_ablation: float) -> DEM:
    """
    Apply elevation-based filter on DEM difference values inside glacier outlines using ELA.

    Args:
        dem_diff (DEM): Filtered DEM difference raster after NMAD.
        glacier_shapefile (str): Path to glacier outlines.
        ref_dem_path (str): Path to reference DEM.
        ela (float): Equilibrium Line Altitude.
        gain_accum (float): Max gain allowed in accumulation zone.
        loss_accum (float): Max loss allowed in accumulation zone.
        gain_ablation (float): Max gain allowed in ablation zone.
        loss_ablation (float): Max loss allowed in ablation zone.

    Returns:
        DEM: DEM after ELA-based elevation change filtering.
    """
    filtered_dh = dem_diff.copy()
    filtered_dh.nodata = np.nan

    ref_dem = DEM(ref_dem_path)
    glacier_vector = Vector(glacier_shapefile)
    glacier_mask = glacier_vector.create_mask(filtered_dh).data.data
    elevation = ref_dem.data.data

    accumulation_zone = (elevation > ela)
    ablation_zone = (elevation <= ela)

    inside_accum = glacier_mask & accumulation_zone
    inside_ablation = glacier_mask & ablation_zone

    dh = filtered_dh.data.data

    dh[inside_accum & (dh < -loss_accum)] = -loss_accum
    dh[inside_accum & (dh > gain_accum)] = gain_accum

    dh[inside_ablation & (dh < -loss_ablation)] = -loss_ablation
    dh[inside_ablation & (dh > gain_ablation)] = gain_ablation

    filtered_dh.data.mask = dem_diff.data.mask.copy()
    return filtered_dh

def interpolate_missing_values(dh: DEM, ref_dem: DEM, glacier_mask: Vector, method: str, start_date: datetime.date, end_date: datetime.date) -> dDEM:
    """
    Interpolate missing values in a DEM difference raster using hypsometric interpolation.

    Args:
        dh (DEM): DEM difference after filtering.
        ref_dem (DEM): Reference elevation raster (needed for hypsometric bins).
        glacier_mask (Vector): Glacier shapefile as geoutils.Vector.
        method (str): "regional_hypsometric" or "local_hypsometric".

    Returns:
        xdem.dDEM: Interpolated dDEM object.
    """
    if method not in ["regional_hypsometric", "local_hypsometric"]:
        raise ValueError(f"Unsupported interpolation method: {method}")

    # Create a dDEM from the filtered DEM difference
    ddem_obj = dDEM(dh, start_time=start_date, end_time=end_date)

    # Perform interpolation and return a new copy with the updated array
    interpolated = ddem_obj.interpolate(method=method, reference_elevation=ref_dem, mask=glacier_mask)

    return ddem_obj.copy(new_array=interpolated)
