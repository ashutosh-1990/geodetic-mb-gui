# -*- coding: utf-8 -*-

# core/dh_and_uncertainty.py

import numpy as np
import pandas as pd
import xdem
from xdem import DEM, dDEM
from geoutils import Vector

def compute_df_h(dh, ref_dem_path, unstable_path, variables):
    ref = DEM(ref_dem_path)
    slope, aspect, curvature = ref.get_terrain_attribute(attribute=["slope", "aspect", "curvature"])

    if unstable_path:
        mask = ~Vector(unstable_path).create_mask(ref).data
    else:
        mask = np.ones_like(ref.data, dtype=bool)

    dh_arr = dh.data[mask]
    var_map = {"slope": slope[mask], "aspect": aspect[mask], "curvature": curvature[mask]}
    bins = {
        "slope": np.linspace(0, 90, 10),
        "aspect": np.linspace(0, 360, 10),
        "curvature": np.linspace(-10, 10, 10)
    }

    list_var = [var_map[v] for v in variables]
    list_bins = [bins[v] for v in variables]

    df_h = xdem.spatialstats.nd_binning(
        dh_arr,
        list_var=list_var,
        list_var_names=variables,
        statistics=["count", xdem.spatialstats.nmad],
        list_var_bins=list_bins
    )

    return df_h

def estimate_uncertainty(dh, ref_dem_path, unstable_path, glacier_shp, hetero_variables, spatial_models):
    """
    Estimate elevation uncertainty using topographic variables and empirical variograms.

    Compatible with xdem version 0.1.4.
    """

    # Step 1: Get terrain attributes
    slope, aspect, curvature = DEM(ref_dem_path).get_terrain_attribute(attribute=["slope", "aspect", "curvature"])

    # Step 2: Compute ND-binned NMAD per topo variable combination
    def compute_df_h():
        ref = DEM(ref_dem_path)
        if unstable_path:
            mask = ~Vector(unstable_path).create_mask(ref).data
        else:
            mask = np.ones_like(ref.data, dtype=bool)

        dh_arr = dh.data[mask]
        var_map = {"slope": slope[mask], "aspect": aspect[mask], "curvature": curvature[mask]}
        bins = {
            "slope": np.linspace(0, 90, 10),
            "aspect": np.linspace(0, 360, 10),
            "curvature": np.linspace(-10, 10, 10)
        }

        list_var = [var_map[v] for v in hetero_variables]
        list_bins = [bins[v] for v in hetero_variables]

        return xdem.spatialstats.nd_binning(
            dh_arr,
            list_var=list_var,
            list_var_names=hetero_variables,
            statistics=["count", xdem.spatialstats.nmad],
            list_var_bins=list_bins
        )

    df_h = compute_df_h()

    # Step 3: Interpolate standard deviation field
    sig_dh_func = xdem.spatialstats.interp_nd_binning(df_h, list_var_names=hetero_variables)
    topo_data = {"slope": slope.data, "aspect": aspect.data, "curvature": curvature.data}
    input_list = [topo_data[v].ravel() for v in hetero_variables]
    
    # Ensure correct shape for interpolation input
    if len(input_list) == 1:
        xi = input_list[0][:, np.newaxis]  # shape (N, 1)
    else:
        xi = np.stack(input_list, axis=-1)  # shape (N, D)
    
    # Interpolate and reshape back to raster shape
    sig_dh_flat = sig_dh_func(xi)
    sig_dh_arr = sig_dh_flat.reshape(dh.shape)

    # ✅ Use dh.copy (xdem 0.1.4 safe)
    sig_dh = dh.copy(new_array=sig_dh_arr)

    # Step 4: Standardize dh
    z_dh_arr = dh.data / sig_dh.data
    z_dh = dh.copy(new_array=z_dh_arr)

    if unstable_path:
        mask = ~Vector(unstable_path).create_mask(dh).data
        z_dh.set_mask(~mask)

    # Step 5: Empirical variogram from stable terrain
    df_vgm = xdem.spatialstats.sample_empirical_variogram(
        z_dh, subsample=500, n_variograms=5, random_state=42
    )
    func_sum_vgm, params_variogram_model = xdem.spatialstats.fit_sum_model_variogram(
        list_models=spatial_models,
        empirical_variogram=df_vgm
    )

    # Step 6: Glacier-wise uncertainty estimate
    gvec = Vector(glacier_shp)
    ds = gvec.ds
    use_rgi = "rgi_id" in ds.columns
    glacier_ids = ds["rgi_id"].tolist() if use_rgi else [f"G{i+1}" for i in range(len(ds))]

    rgi_ids, elevation_changes, uncertainties = [], [], []

    for k, gid in enumerate(glacier_ids):
        outline = Vector(ds[ds["rgi_id"] == gid]) if use_rgi else Vector(ds.iloc[[k]])
        mask = outline.create_mask(dh)

        mean_sig = np.nanmean(sig_dh[mask])
        neff = xdem.spatialstats.number_effective_samples(
            area=outline, params_variogram_model=params_variogram_model, rasterize_resolution=50
        )
        sig_dh_brom = mean_sig / np.sqrt(neff)
        dh_brom = np.nanmean(dh[mask])

        rgi_ids.append(gid)
        elevation_changes.append(dh_brom)
        uncertainties.append(sig_dh_brom)

    df_uncertainty = pd.DataFrame({
        "RGI_ID": rgi_ids,
        "Elevation_Change": elevation_changes,
        "Uncertainty": uncertainties
    })

    return sig_dh, z_dh, df_vgm, func_sum_vgm, df_uncertainty
