# -*- coding: utf-8 -*-
# main_controller.py

"""
This module connects the GUI to the backend geodetic glacier mass balance pipeline.
It performs input logging, error handling, and module-level orchestration.
"""

import logging
import os
from core.dem_processing import coregister_dems, remove_nmad_outliers, remove_nmad_outliers_elev_binned, glacier_abs_filter, glacier_ela_filter, interpolate_missing_values
from core.dh_and_uncertainty import estimate_uncertainty
from geoutils import Vector
from xdem import DEM
from core.mass_balance import compute_geodetic_mass_balance

def run_geodetic_pipeline(ref_dem, align_dem, unstable_shp, glacier_shp,
                          ref_date, align_date, coreg_algo, params,
                          heteroscedasticity, spatial_correlation,
                          interpolation_algo, glacier_filter_type,
                          canvas_frame=None, view_option=None, progress_callback=None, snowfall_estimates_df=None): #seasonality (removed for now)

    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "geodetic_pipeline.log")

    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )

    logging.info("=== Geodetic Mass Balance Pipeline Called ===")
    logging.info(f"Reference DEM: {ref_dem}")
    logging.info(f"To-be-aligned DEM: {align_dem}")
    logging.info(f"Coregistration Algorithm: {coreg_algo}")
    logging.info(f"Unstable Terrain Shapefile: {unstable_shp}")
    logging.info(f"Glacier Shapefile: {glacier_shp}")
    logging.info(f"Reference Date: {ref_date}")
    logging.info(f"Aligned Date: {align_date}")
    logging.info(f"Model Parameters: {params}")
    #logging.info(f"Seasonality Correction: {seasonality}")
    logging.info(f"Elevation Heteroscedasticity: {heteroscedasticity}")
    logging.info(f"Spatial Correlation: {spatial_correlation}")
    logging.info(f"Interpolation Algorithm: {interpolation_algo}")
    logging.info(f"Glacier Filter Type for Interpolation: {glacier_filter_type}")
    logging.info(f"View Option: {view_option}")
    logging.info(f"Canvas Frame: {'Available' if canvas_frame else 'None'}")
    logging.info("=== End Input Log ===")

    try:
        if progress_callback: progress_callback(20, "Co-registering the DEMs...")
        dh_after_coreg = coregister_dems(ref_dem, align_dem, coreg_algo)
        logging.info("✅ DEM co-registration completed.")

        try:
            nmad_factor = float(params[0]) if params[0].strip() else 6.0
        except Exception:
            logging.warning(f"⚠️ Invalid NMAD value '{params[0]}'. Defaulting to 6.0.")
            nmad_factor = 6.0

        #if progress_callback: progress_callback(40, "Filtering elevation changes...")
        #dh_after_coreg_nmad = remove_nmad_outliers(dh_after_coreg, nmad_factor=nmad_factor, glacier_shapefile=glacier_shp)
        #logging.info(f"✅ NMAD filtering applied (factor = {nmad_factor})")
        
        if progress_callback: progress_callback(40, "Filtering elevation changes...")
        #NOTES -->                                            (dem_diff: DEM, elevation_dem, glacier_shapefile: str, global_nmad_factor: float = 6.0, glacier_nmad_factor: float = 5.0, bin_size: float = 100.0)
        dh_after_coreg_nmad = remove_nmad_outliers_elev_binned(dh_after_coreg, ref_dem, glacier_shapefile=glacier_shp, global_nmad_factor=nmad_factor, glacier_nmad_factor=nmad_factor)
        logging.info(f"✅ NMAD filtering applied (factor = {nmad_factor})")        


        

        # Absolute threshold filtering
        try:
            abs_threshold = float(params[1]) if params[1].strip() else None
        except ValueError:
            logging.warning(f"⚠️ Invalid absolute threshold value '{params[1]}'. Skipping glacier absolute filter.")
            abs_threshold = None
        
        if abs_threshold is not None:
            dh_after_coreg_nmad_glacierfilter = glacier_abs_filter(dh_after_coreg_nmad, glacier_shp, abs_threshold)
            logging.info(f"✅ Glacier absolute filter applied (threshold = {abs_threshold})")
        else:
            dh_after_coreg_nmad_glacierfilter = None
            logging.info("ℹ️ Glacier absolute filtering skipped due to missing/invalid threshold value.")


        # ELA and zone thresholds with explicit validation
        try:
            ela = float(params[3]) if params[3].strip() else None
            gain_accum = float(params[4]) if params[4].strip() else None
            loss_accum = float(params[5]) if params[5].strip() else None
            gain_ablation = float(params[6]) if params[6].strip() else None
            loss_ablation = float(params[7]) if params[7].strip() else None
        
            ela_filter_inputs = [ela, gain_accum, loss_accum, gain_ablation, loss_ablation]
        
            if any(val is None for val in ela_filter_inputs):
                raise ValueError("One or more parameters for ELA-based filtering of glacier surface dh values are not numeric")
        
        except Exception as e:
            logging.warning(f"⚠️ Skipping ELA filter due to invalid input: {e}")
            ela = None
        
        if ela is not None:
            dh_after_coreg_nmad_elafilter = glacier_ela_filter(
                dh_after_coreg_nmad,
                glacier_shp,
                ref_dem,
                ela,
                gain_accum,
                loss_accum,
                gain_ablation,
                loss_ablation
            )
            logging.info(f"✅ ELA-based glacier filter applied (ELA = {ela})")
        else:
            dh_after_coreg_nmad_elafilter = None
            logging.info("ℹ️ ELA filtering skipped due to missing/invalid ELA value")
            

        glacier_vector = Vector(glacier_shp)
        
        if glacier_filter_type == "absolute threshold filter":
            dh_for_interp = dh_after_coreg_nmad_glacierfilter
        elif glacier_filter_type == "ela filter":
            dh_for_interp = dh_after_coreg_nmad_elafilter
        else:
            logging.warning("Unknown glacier filter type. Falling back to NMAD filtered raster only.")
            dh_for_interp = dh_after_coreg_nmad
        
        ref_dem_obj = DEM(ref_dem)
        
        if progress_callback: progress_callback(60, "Interpolating missing values...")
        dh_interpolated = interpolate_missing_values(
            dh=dh_for_interp,
            ref_dem=ref_dem_obj,
            glacier_mask=glacier_vector,
            method=interpolation_algo,
            start_date=ref_date,
            end_date=align_date)
        
        hetero_vars = [v.strip() for v in heteroscedasticity.split(",")]
        spatial_models = [m.strip() for m in spatial_correlation.split(",")]
        
        
        if progress_callback: progress_callback(80, "Estimating uncertainty in mass balance ...")
        sig_dh, z_dh, df_vgm, func_sum_vgm, df_uncertainty = estimate_uncertainty(
            dh_interpolated,
            ref_dem,
            unstable_shp,
            glacier_shp,
            hetero_vars,
            spatial_models
        )
        
        if progress_callback: progress_callback(95, "Estimating mass balance of glaciers ...")
        df_mass_balance = compute_geodetic_mass_balance(
            df_uncertainty=df_uncertainty,
            ref_date=ref_date,
            align_date=align_date,
            ice_density_uniform=params[2],
            integer_years=params[8],
            snowfall_estimates_df=snowfall_estimates_df  # ✅ Pass correctly here
        )

    except Exception as e:
        logging.error(f"❌ DEM processing failed: {e}")
        return {
            "status": "error",
            "message": f"DEM processing failed: {e}",
            "data": None
        }

    logging.info("✅ Pipeline completed successfully.\n")
    return {
        "status": "success",
        "message": "Mass balance estimation complete!",
        "data": {
            "dh_after_coreg": dh_after_coreg,
            "dh_after_coreg_nmad": dh_after_coreg_nmad,
            "dh_after_coreg_nmad_glacierfilter": dh_after_coreg_nmad_glacierfilter,
            "dh_after_coreg_nmad_elafilter": dh_after_coreg_nmad_elafilter,
            "nmad_factor": nmad_factor,
            "abs_threshold": abs_threshold,
            "ela": ela,
            "dh_interpolated": dh_interpolated,
            "sig_dh": sig_dh,
            "z_dh": z_dh,
            "df_vgm": df_vgm,
            "func_sum_vgm": func_sum_vgm,
            "df_uncertainty": df_uncertainty,
            "df_mass_balance": df_mass_balance

        }
    }
