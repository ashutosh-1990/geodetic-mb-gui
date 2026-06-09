# -*- coding: utf-8 -*-

# core/mass_balance.py

import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import numpy as np
import datetime

def compute_geodetic_mass_balance(
    df_uncertainty,
    ref_date,
    align_date,
    ice_density_uniform,
    integer_years,
    snowfall_estimates_df=None  # Optional: includes snow corrections
):
    """
    Compute annual glacier mass balance using geodetic method and uniform density.
    Optionally subtracts snow bias and seasonality corrections per glacier.

    Args:
        df_uncertainty (DataFrame): Must include "Elevation_Change", "Uncertainty"
        ref_date, align_date (datetime.date): DEM acquisition dates
        ice_density_uniform (float or str): Density in kg/m³
        snowfall_estimates_df (optional DataFrame): Must match glacier order, include:
            - "Snow Bias Correction"
            - "Seasonality Correction"

    Returns:
        df_uncertainty (DataFrame): Adds "Mass_Balance" and "MB_Uncertainty" columns
    """
    no_of_years = (align_date - ref_date).days / 365.25

    density = float(ice_density_uniform)
    df_uncertainty["cumulative_Mass_Balance"] = (df_uncertainty["Elevation_Change"] * (density / 1000)) 
    df_uncertainty["cumulative_MB_Uncertainty"] = (df_uncertainty["Uncertainty"] * (density / 1000)) 
    i=0
    if snowfall_estimates_df is not None:
        try:
            df_uncertainty["cumulative_Mass_Balance"] -= (
                snowfall_estimates_df["Snow Bias Correction"] +
                snowfall_estimates_df["Seasonality Correction"]
            )

        except Exception as e:
            print(f"[Warning] Could not apply snow corrections to mass balance: {e}")
            
        i+=1
        
    if i==0:
        df_uncertainty["Mass_Balance"] = df_uncertainty["cumulative_Mass_Balance"] / no_of_years
        df_uncertainty["MB_Uncertainty"] = df_uncertainty["cumulative_MB_Uncertainty"] / no_of_years
    else:
        df_uncertainty["Mass_Balance"] = df_uncertainty["cumulative_Mass_Balance"] / float(integer_years)
        df_uncertainty["MB_Uncertainty"] = df_uncertainty["cumulative_MB_Uncertainty"] / float(integer_years)
        
    return df_uncertainty
