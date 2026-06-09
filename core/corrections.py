from tkinter import Toplevel, Label, Button, messagebox, Frame, LEFT, Entry, Canvas, Scrollbar, BOTH, RIGHT, Y
from tkcalendar import DateEntry
import datetime
import os
import geopandas as gpd
import xarray as xr
import pandas as pd
import numpy as np
import random
import glob
import matplotlib.pyplot as plt
import traceback

# def open_snow_season_dialog(gui):
#     """
#     Open a dialog for snow bias and seasonality correction dates,
#     snow density inputs, and auto-estimate snowfall for each glacier.
#     If model was run before, apply correction and refresh the mass balance plot.
#     """
#     def submit_dates():
        
#         #try:
#         #    snow_density_bias = float(entry_density_bias.get())
#         #    snow_density_season = float(entry_density_season.get())
#         #except ValueError:
#         #    messagebox.showerror("Invalid Input", "Please enter valid numeric values for both snow density inputs.")
#         #    return

#         gui.snow_season_inputs = {
#             "ref_snow_start": ref_snow_start.get_date(),
#             "ref_snow_end": ref_snow_end.get_date(),
#             "align_snow_start": align_snow_start.get_date(),
#             "align_snow_end": align_snow_end.get_date(),
#             "season_start": season_start.get_date(),
#             "season_end": season_end.get_date()
#             #"snow_density_bias": snow_density_bias,
#             #"snow_density_season": snow_density_season
#         }

#         try:
#             glacier_path = gui.glacier_path.get()
#             snowfall_df = estimate_snowfall_for_all_glaciers(
#                 glacier_path,
#                 gui.snow_season_inputs,
#                 data_dir="data/era5land_snowfall"
#             )
#             gui.snowfall_estimates_df = snowfall_df.copy()
#             show_snowfall_estimates_window(gui, snowfall_df)
#         except Exception as e:
#             messagebox.showerror("Error", f"Snowfall estimation failed:\n{e}")
#             return

#         dialog.destroy()

#     # try:
#     #     if gui.glacier_path.get():
#     #         plot_random_era5_snapshot_with_glaciers(gui.glacier_path.get())
#     # except Exception as e:
#     #     print("[ERROR] Plotting failed:", e)
#     #     traceback.print_exc()

#     dialog = Toplevel(gui.master)
#     dialog.title("Snow Bias Correction & Seasonality Correction Dates")
#     dialog.geometry("800x600")    
#     dialog.grab_set()

#     def create_labeled_entry(parent, label_text, default_date):
#         row = Frame(parent)
#         row.pack(anchor="w", pady=5, padx=15)
#         Label(row, text=label_text, width=45, anchor="w").pack(side=LEFT)
#         entry = DateEntry(row, date_pattern='dd/mm/yyyy')
#         entry.set_date(default_date)
#         entry.pack(side=LEFT)
#         return entry

#     ref_snow_start = create_labeled_entry(dialog, "Reference DEM Snow Bias Start Date:", "01/10/1999")
#     ref_snow_end = create_labeled_entry(dialog, "Reference DEM Snow Bias End Date:", "29/12/1999")
#     align_snow_start = create_labeled_entry(dialog, "Aligned DEM Snow Bias Start Date:", "01/10/2014")
#     align_snow_end = create_labeled_entry(dialog, "Aligned DEM Snow Bias End Date:", "29/12/2014")
#     season_start = create_labeled_entry(dialog, "Seasonality Correction Start Date (Ref DEM):", "29/12/1999")
#     season_end = create_labeled_entry(dialog, "Seasonality Correction End Date (Ref DEM):", "19/02/2000")

#     # row_density_bias = Frame(dialog)
#     # row_density_bias.pack(anchor="w", pady=(15, 5), padx=15)
#     # Label(row_density_bias, text="Snow Density (For Snow Bias) [kg/m³]:", width=45, anchor="w").pack(side=LEFT)
#     # entry_density_bias = Entry(row_density_bias, width=10)
#     # entry_density_bias.insert(0, "300")
#     # entry_density_bias.pack(side=LEFT)

#     # row_density_season = Frame(dialog)
#     # row_density_season.pack(anchor="w", pady=(5, 15), padx=15)
#     # Label(row_density_season, text="Snow Density (For Seasonality Correction) [kg/m³]:", width=45, anchor="w").pack(side=LEFT)
#     # entry_density_season = Entry(row_density_season, width=10)
#     # entry_density_season.insert(0, "300")
#     # entry_density_season.pack(side=LEFT)

#     Button(dialog, text="Submit", command=submit_dates).pack(pady=(20, 10), anchor="w", padx=15)

def open_snow_season_dialog(gui):
    """
    Open a dialog for snow bias and seasonality correction dates,
    snow density inputs, and auto-estimate snowfall for each glacier.
    Minimal changes: make the dialog scrollable and keep Submit fixed.
    """
    def submit_dates():
        gui.snow_season_inputs = {
            "ref_snow_start": ref_snow_start.get_date(),
            "ref_snow_end": ref_snow_end.get_date(),
            "align_snow_start": align_snow_start.get_date(),
            "align_snow_end": align_snow_end.get_date(),
            "season_start": season_start.get_date(),
            "season_end": season_end.get_date()
        }

        try:
            glacier_path = gui.glacier_path.get()
            snowfall_df = estimate_snowfall_for_all_glaciers(
                glacier_path,
                gui.snow_season_inputs,
                data_dir="data/era5land_snowfall"
            )
            gui.snowfall_estimates_df = snowfall_df.copy()
            show_snowfall_estimates_window(gui, snowfall_df)
        except Exception as e:
            messagebox.showerror("Error", f"Snowfall estimation failed:\n{e}")
            return

        dialog.destroy()

    dialog = Toplevel(gui.master)
    dialog.title("Snow Bias Correction & Seasonality Correction Dates")
    # Limit initial size so it doesn't exceed screen; user can resize if needed
    screen_h = dialog.winfo_screenheight()
    dialog.geometry(f"800x{int(screen_h * 0.75)}")
    dialog.grab_set()
    dialog.resizable(True, True)

    # --- Scrollable area: Canvas + vertical scrollbar + inner frame ---
    canvas = Canvas(dialog)
    vscroll = Scrollbar(dialog, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vscroll.set)

    scrollable_frame = Frame(canvas)
    # update scrollregion when inner frame size changes
    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scrollable_frame.bind("<Configure>", _on_frame_configure)

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    vscroll.pack(side="right", fill="y")

    # --- keep create_labeled_entry the same, but use scrollable_frame as parent ---
    def create_labeled_entry(parent, label_text, default_date):
        row = Frame(parent)
        row.pack(anchor="w", pady=5, padx=15)
        Label(row, text=label_text, width=45, anchor="w").pack(side=LEFT)
        entry = DateEntry(row, date_pattern='dd/mm/yyyy')
        entry.set_date(default_date)
        entry.pack(side=LEFT)
        return entry

    # --- Date entries (placed inside scrollable_frame so they scroll) ---
    ref_snow_start = create_labeled_entry(scrollable_frame, "Reference DEM Snow Bias Start Date:", "01/10/1999")
    ref_snow_end = create_labeled_entry(scrollable_frame, "Reference DEM Snow Bias End Date:", "29/12/1999")
    align_snow_start = create_labeled_entry(scrollable_frame, "Aligned DEM Snow Bias Start Date:", "01/10/2014")
    align_snow_end = create_labeled_entry(scrollable_frame, "Aligned DEM Snow Bias End Date:", "29/12/2014")
    season_start = create_labeled_entry(scrollable_frame, "Seasonality Correction Start Date (Ref DEM):", "29/12/1999")
    season_end = create_labeled_entry(scrollable_frame, "Seasonality Correction End Date (Ref DEM):", "19/02/2000")

    # (commented blocks left unchanged / unused)
    # row_density_bias = Frame(dialog)
    # row_density_bias.pack(anchor="w", pady=(15, 5), padx=15)
    # Label(row_density_bias, text="Snow Density (For Snow Bias) [kg/m³]:", width=45, anchor="w").pack(side=LEFT)
    # entry_density_bias = Entry(row_density_bias, width=10)
    # entry_density_bias.insert(0, "300")
    # entry_density_bias.pack(side=LEFT)
    #
    # row_density_season = Frame(dialog)
    # row_density_season.pack(anchor="w", pady=(5, 15), padx=15)
    # Label(row_density_season, text="Snow Density (For Seasonality Correction) [kg/m³]:", width=45, anchor="w").pack(side=LEFT)
    # entry_density_season = Entry(row_density_season, width=10)
    # entry_density_season.insert(0, "300")
    # entry_density_season.pack(side=LEFT)

    # --- Fixed bottom button frame so Submit is always accessible ---
    button_frame = Frame(dialog)
    button_frame.pack(side="bottom", fill="x", padx=15, pady=10)
    Button(button_frame, text="Submit", command=submit_dates).pack(side="left")
    Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=(8, 0))

    # Optional: allow mousewheel scrolling when cursor is over canvas
    def _on_mousewheel(event):
        # Windows: event.delta (120 units); Linux may use event.num
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    # bind mousewheel for Windows and Mac
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # For Linux (wheel up/down)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

def estimate_snowfall_for_all_glaciers(glacier_path, inputs, data_dir="data/era5land_snowfall"):
    """
    Estimate total snowfall for each glacier for ref/align/seasonality periods
    by looping over GRIB files and extracting snowfall at each glacier's centroid.
    """
    gdf = gpd.read_file(glacier_path).to_crs("EPSG:4326")
    use_rgi = "rgi_id" in gdf.columns
    glacier_ids = gdf["rgi_id"].tolist() if use_rgi else [f"{i+1}" for i in range(len(gdf))]

    snowfall_ref, snowfall_align, snowfall_season = [], [], []

    for idx, row in gdf.iterrows():
        geom = row.geometry
        lon, lat = geom.centroid.x, geom.centroid.y
        #print(f"[DEBUG] Glacier {idx + 1}: Centroid at (lat={lat}, lon={lon})")

        def sum_snowfall_for_period(start_date, end_date):
            total = 0.0
            for grib_path in glob.glob(os.path.join(data_dir, "*.grib")):
                try:
                    year = int(os.path.basename(grib_path).split("_")[-1].split(".")[0])
                    if year < start_date.year or year > end_date.year:
                        continue
                    val = extract_snowfall_from_dates(grib_path, start_date, end_date, lat, lon)
                    if not np.isnan(val):
                        total += val
                except Exception as e:
                    print(f"[WARNING] Skipping {grib_path}: {e}")
            return total

        snowfall_ref.append(sum_snowfall_for_period(inputs["ref_snow_start"], inputs["ref_snow_end"]))
        snowfall_align.append(sum_snowfall_for_period(inputs["align_snow_start"], inputs["align_snow_end"]))
        snowfall_season.append(sum_snowfall_for_period(inputs["season_start"], inputs["season_end"]))

    df = pd.DataFrame({
        "Glacier": glacier_ids,
        "Snow Bias Reference DEM": snowfall_ref,
        "Snow Bias Aligned DEM": snowfall_align,
        "Seasonality Correction": snowfall_season,
    })
    df["Snow Bias Correction"] = df["Snow Bias Aligned DEM"] - df["Snow Bias Reference DEM"]
    return df


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Compute Haversine distance between two points on the Earth in meters.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    d_phi = np.radians(lat2 - lat1)
    d_lambda = np.radians(lon2 - lon1)

    a = np.sin(d_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def extract_snowfall_from_dates(grib_file, start_date, end_date, lat_pt, lon_pt):
    """
    Extract total snowfall (in meters) for the grid cell containing the given point
    between the specified start and end dates.
    """
    try:
        import numpy as np
        import xarray as xr

        ds = xr.open_dataset(grib_file, engine="cfgrib")
        ds = ds.sel(time=slice(str(start_date), str(end_date)))
        if "sf" not in ds:
            raise ValueError(f"'sf' variable not found in {grib_file}")

        sf = ds["sf"]

        lats = sf.latitude.values
        lons = sf.longitude.values

        # Ensure 1D
        if lats.ndim > 1:
            lats = lats[:, 0]
        if lons.ndim > 1:
            lons = lons[0, :]

        # Resolution
        lat_res = abs(lats[0] - lats[1])
        lon_res = abs(lons[1] - lons[0])

        # Find index where centroid lies within the grid cell boundaries
        lat_idx = np.where((lats - lat_res/2 <= lat_pt) & (lat_pt < lats + lat_res/2))[0]
        lon_idx = np.where((lons - lon_res/2 <= lon_pt) & (lon_pt < lons + lon_res/2))[0]

        if len(lat_idx) == 0 or len(lon_idx) == 0:
            print(f"[WARNING] Centroid ({lat_pt:.4f}, {lon_pt:.4f}) falls outside ERA5 grid extent in {grib_file}")
            return np.nan

        cell_lat = lats[lat_idx[0]]
        cell_lon = lons[lon_idx[0]]

        sf_cell = sf.sel(latitude=cell_lat, longitude=cell_lon)
        val = float(sf_cell.sum().values)

        if np.isnan(val) or val == 0:
            print(f"[WARNING] Snowfall = {val} at ({lat_pt:.4f}, {lon_pt:.4f}) in cell ({cell_lat:.4f}, {cell_lon:.4f}) from {grib_file}")

        #print(f"[DEBUG] Glacier centroid ({lat_pt:.4f}, {lon_pt:.4f}) → Grid cell ({cell_lat:.4f}, {cell_lon:.4f}), Snowfall: {val:.4f} m")

        return val

    except Exception as e:
        print(f"[ERROR] Failed to extract snowfall from {grib_file} for point ({lat_pt:.4f}, {lon_pt:.4f}): {e}")
        return np.nan

def show_snowfall_estimates_window(gui, df):
    import tkinter as tk
    from tkinter import Toplevel, Label, Button, messagebox, Frame, LEFT, Entry, Scrollbar

    window = Toplevel(gui.master)
    window.title("Snowfall Estimates (Editable)")
    window.geometry("1000x600")
    window.grab_set()
    window.resizable(True, True)

    # === Scrollable container ===
    container = Frame(window)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    vscroll = Scrollbar(container, orient="vertical", command=canvas.yview)
    hscroll = Scrollbar(container, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    vscroll.pack(side="right", fill="y")
    hscroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    inner = Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    inner.bind("<Configure>", _on_frame_configure)

    # === Table content goes inside 'inner' ===
    headers = list(df.columns)
    for j, header in enumerate(["Glacier"] + headers[1:]):
        Label(inner, text=header, font=("Arial", 10, "bold"), width=20).grid(row=0, column=j, padx=5, pady=5)

    gui.snowfall_entries = []
    for i, row in df.iterrows():
        row_entries = []
        Label(inner, text=row["Glacier"], width=20).grid(row=i + 1, column=0, padx=5)
        for j, col in enumerate(headers[1:], start=1):
            e = Entry(inner, width=20)
            e.insert(0, f"{row[col]:.4f}")
            e.grid(row=i + 1, column=j, padx=3, pady=1)
            row_entries.append(e)
        gui.snowfall_entries.append(row_entries)

    # --- Multiplicative Bias Correction Factor ---
    correction_applied = [False]

    bias_row = Frame(inner)
    bias_row.grid(row=len(df) + 1, column=0, columnspan=len(df.columns), pady=(10, 5), padx=10, sticky="w")
    Label(bias_row, text="Multiplicative Bias Correction Factor:", font=("Arial", 10), width=30).pack(side=LEFT)
    entry_bias_factor = Entry(bias_row, width=10)
    entry_bias_factor.insert(0, "1.0")
    entry_bias_factor.pack(side=LEFT)

    def apply_multiplicative_correction():
        if correction_applied[0]:
            messagebox.showwarning("Already Applied", "Multiplicative correction can only be applied once.")
            return
        try:
            factor = float(entry_bias_factor.get())
            gui.multiplicative_bias_factor = factor
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric correction factor.")
            return

        for col in ["Snow Bias Reference DEM", "Snow Bias Aligned DEM", "Seasonality Correction", "Snow Bias Correction"]:
            df[col] *= factor

        for i, row_entries in enumerate(gui.snowfall_entries):
            for j, entry in enumerate(row_entries):
                col_name = df.columns[j + 1]
                entry.delete(0, tk.END)
                entry.insert(0, f"{df[col_name][i]:.4f}")

        correction_applied[0] = True
        btn_correct.config(state="disabled")
        messagebox.showinfo("Success", f"Values multiplied by {factor}.")

    btn_correct = Button(bias_row, text="Correct", command=apply_multiplicative_correction, bg="orange")
    btn_correct.pack(side=LEFT, padx=10)

    # === Save & Close Button (fixed at bottom of window, not inside scroll) ===
    def save_and_close():
        for i, row_entries in enumerate(gui.snowfall_entries):
            for j, entry in enumerate(row_entries):
                try:
                    new_val = float(entry.get())
                    col_name = df.columns[j + 1]
                    gui.snowfall_estimates_df.at[i, col_name] = new_val
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Non-numeric value in row {i + 1}, column {col_name}")
                    return

        window.destroy()

        try:
            if hasattr(gui, "result") and gui.result and "df_uncertainty" in gui.result["data"]:
                from core.mass_balance import compute_geodetic_mass_balance
                df_uncertainty = gui.result["data"]["df_uncertainty"]
                updated_df = compute_geodetic_mass_balance(
                    df_uncertainty=df_uncertainty,
                    ref_date=gui.ref_date.get_date(),
                    align_date=gui.align_date.get_date(),
                    ice_density_uniform=gui.param_vars[2].get(),
                    integer_years=gui.param_vars[8].get(),
                    snowfall_estimates_df=gui.snowfall_estimates_df
                )
                gui.result["data"]["df_mass_balance"] = updated_df
                gui.plot_options.set("Annual Glacier Mass Balance with Uncertainty")
                gui.update_plot()

                if messagebox.askyesno(
                    "Save Updated Report",
                    "Mass balance has been updated with your corrections.\nWould you like to save all plots and generate the updated report?"
                ):
                    from core.report_and_plots import save_all_figures_and_report
                    from tkinter import filedialog
                    save_dir = filedialog.askdirectory(title="Select folder to save report and plots")
                    if save_dir:
                        save_all_figures_and_report(gui.result, gui, save_dir)

        except Exception as e:
            print(f"[Warning] Could not update mass balance plot: {e}")

    bottom_frame = Frame(window)
    bottom_frame.pack(side="bottom", fill="x", pady=10)
    Button(bottom_frame, text="Save & Close", command=save_and_close, bg="lightblue").pack(pady=5)

    # === Mouse wheel scrolling ===
    def _on_mousewheel(event):
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))


# def show_snowfall_estimates_window(gui, df):

#     import tkinter as tk
#     from tkinter import Toplevel, Label, Button, messagebox, Frame, LEFT, Entry

#     window = Toplevel(gui.master)
#     window.title("Snowfall Estimates (Editable)")
#     window.geometry("1000x500")
#     window.grab_set()

#     headers = list(df.columns)
#     for j, header in enumerate(["Glacier"] + headers[1:]):
#         Label(window, text=header, font=("Arial", 10, "bold"), width=20).grid(row=0, column=j, padx=5, pady=5)

#     gui.snowfall_entries = []
#     for i, row in df.iterrows():
#         row_entries = []
#         Label(window, text=row["Glacier"], width=20).grid(row=i+1, column=0, padx=5)
#         for j, col in enumerate(headers[1:], start=1):
#             e = Entry(window, width=20)
#             e.insert(0, f"{row[col]:.4f}")
#             e.grid(row=i+1, column=j, padx=3, pady=1)
#             row_entries.append(e)
#         gui.snowfall_entries.append(row_entries)

#     # --- Multiplicative Bias Correction Factor ---
#     correction_applied = [False]  # use mutable object to allow modification in nested scope

#     bias_row = Frame(window)
#     bias_row.grid(row=len(df) + 1, column=0, columnspan=len(df.columns), pady=(10, 5), padx=10, sticky="w")
#     Label(bias_row, text="Multiplicative Bias Correction Factor:", font=("Arial", 10), width=30).pack(side=LEFT)
#     entry_bias_factor = Entry(bias_row, width=10)
#     entry_bias_factor.insert(0, "1.0")
#     entry_bias_factor.pack(side=LEFT)

#     def apply_multiplicative_correction():
#         if correction_applied[0]:
#             messagebox.showwarning("Already Applied", "Multiplicative correction can only be applied once.")
#             return

#         try:
#             factor = float(entry_bias_factor.get())
#             gui.multiplicative_bias_factor = factor  # ✅ Store factor in GUI for report
#         except ValueError:
#             messagebox.showerror("Invalid Input", "Please enter a valid numeric correction factor.")
#             return

#         for col in ["Snow Bias Reference DEM", "Snow Bias Aligned DEM", "Seasonality Correction", "Snow Bias Correction"]:
#             df[col] *= factor

#         # Refresh GUI table
#         for i, row_entries in enumerate(gui.snowfall_entries):
#             for j, entry in enumerate(row_entries):
#                 col_name = df.columns[j + 1]
#                 entry.delete(0, tk.END)
#                 entry.insert(0, f"{df[col_name][i]:.4f}")

#         correction_applied[0] = True
#         btn_correct.config(state="disabled")
#         messagebox.showinfo("Success", f"Values multiplied by {factor}.")

#     btn_correct = Button(bias_row, text="Correct", command=apply_multiplicative_correction, bg="orange")
#     btn_correct.pack(side=LEFT, padx=10)

#     def save_and_close():
#         for i, row_entries in enumerate(gui.snowfall_entries):
#             for j, entry in enumerate(row_entries):
#                 try:
#                     new_val = float(entry.get())
#                     col_name = df.columns[j + 1]
#                     gui.snowfall_estimates_df.at[i, col_name] = new_val
#                 except ValueError:
#                     messagebox.showerror("Invalid Input", f"Non-numeric value in row {i+1}, column {col_name}")
#                     return

#         window.destroy()

#         try:
#             if hasattr(gui, "result") and gui.result and "df_uncertainty" in gui.result["data"]:
#                 from core.mass_balance import compute_geodetic_mass_balance

#                 df_uncertainty = gui.result["data"]["df_uncertainty"]
#                 updated_df = compute_geodetic_mass_balance(
#                     df_uncertainty=df_uncertainty,
#                     ref_date=gui.ref_date.get_date(),
#                     align_date=gui.align_date.get_date(),
#                     ice_density_uniform=gui.param_vars[2].get(),
#                     integer_years=gui.param_vars[8].get(),    # TESTING IN PROGRESS
#                     snowfall_estimates_df=gui.snowfall_estimates_df
#                 )

#                 gui.result["data"]["df_mass_balance"] = updated_df
#                 gui.plot_options.set("Annual Glacier Mass Balance with Uncertainty")
#                 gui.update_plot()

#                 if messagebox.askyesno("Save Updated Report", "Mass balance has been updated with your corrections.\nWould you like to save all plots and generate the updated report?"):
#                     from core.report_and_plots import save_all_figures_and_report
#                     from tkinter import filedialog
#                     save_dir = filedialog.askdirectory(title="Select folder to save report and plots")
#                     if save_dir:
#                         save_all_figures_and_report(gui.result, gui, save_dir)

#         except Exception as e:
#             print(f"[Warning] Could not update mass balance plot: {e}")

#     Button(window, text="Save & Close", command=save_and_close, bg="lightblue").grid(
#         row=len(df) + 2, column=0, columnspan=len(df.columns), pady=15
#     )


# def show_snowfall_estimates_window(gui, df): # OLDEST VERSION !!
#     window = Toplevel(gui.master)
#     window.title("Snowfall Estimates (Editable)")
#     window.geometry("1000x450")
#     window.grab_set()

#     headers = list(df.columns)
#     for j, header in enumerate(["Glacier"] + headers[1:]):
#         Label(window, text=header, font=("Arial", 10, "bold"), width=20).grid(row=0, column=j, padx=5, pady=5)

#     gui.snowfall_entries = []
#     for i, row in df.iterrows():
#         row_entries = []
#         Label(window, text=row["Glacier"], width=20).grid(row=i+1, column=0, padx=5)
#         for j, col in enumerate(headers[1:], start=1):
#             e = Entry(window, width=20)
#             e.insert(0, f"{row[col]:.4f}")
#             e.grid(row=i+1, column=j, padx=3, pady=1)
#             row_entries.append(e)
#         gui.snowfall_entries.append(row_entries)

#     def save_and_close():
#         for i, row_entries in enumerate(gui.snowfall_entries):
#             for j, entry in enumerate(row_entries):
#                 try:
#                     new_val = float(entry.get())
#                     col_name = df.columns[j + 1]
#                     gui.snowfall_estimates_df.at[i, col_name] = new_val
#                 except ValueError:
#                     messagebox.showerror("Invalid Input", f"Non-numeric value in row {i+1}, column {col_name}")
#                     return
    
#         window.destroy()
#         #messagebox.showinfo("Saved", "Snowfall estimates updated successfully.")
    
#         # ✅ Recompute mass balance using updated snowfall estimates
#         try:
#             if hasattr(gui, "result") and gui.result and "df_uncertainty" in gui.result["data"]:
#                 from core.mass_balance import compute_geodetic_mass_balance
    
#                 df_uncertainty = gui.result["data"]["df_uncertainty"]
#                 updated_df = compute_geodetic_mass_balance(
#                     df_uncertainty=df_uncertainty,
#                     ref_date=gui.ref_date.get_date(),
#                     align_date=gui.align_date.get_date(),
#                     ice_density_uniform=gui.param_vars[2].get(),
#                     snowfall_estimates_df=gui.snowfall_estimates_df
#                 )
    
#                 gui.result["data"]["df_mass_balance"] = updated_df
#                 gui.plot_options.set("Annual Glacier Mass Balance with Uncertainty")
#                 gui.update_plot()
    
#                 # Ask user if they want to save updated report
#                 if messagebox.askyesno("Save Updated Report", "Mass balance has been updated with your corrections.\nWould you like to save all plots and generate the updated report?"):
#                     from core.report_and_plots import save_all_figures_and_report
#                     from tkinter import filedialog
#                     save_dir = filedialog.askdirectory(title="Select folder to save report and plots")
#                     if save_dir:
#                         save_all_figures_and_report(gui.result, gui, save_dir)
    
#         except Exception as e:
#             print(f"[Warning] Could not update mass balance plot: {e}")


#     Button(window, text="Save & Close", command=save_and_close, bg="lightblue").grid(
#         row=len(df) + 2, column=0, columnspan=len(df.columns), pady=15
#     )


def plot_random_era5_snapshot_with_glaciers(glacier_shapefile_path, grib_folder="data/era5land_snowfall", max_attempts=25):
    import os, random, glob
    import xarray as xr
    import geopandas as gpd
    import matplotlib
    matplotlib.use("TkAgg", force=True)  # Force interactive backend
    import matplotlib.pyplot as plt

    os.environ["CFGRIB_INDEX_PATH"] = ""  # Avoid index errors
    grib_files = glob.glob(os.path.join(grib_folder, "*.grib"))
    if not grib_files:
        print("[ERROR] No GRIB files found.")
        return

    random.shuffle(grib_files)
    attempts = 0

    for grib_file in grib_files:
        if attempts >= max_attempts:
            print("[ERROR] Too many invalid GRIB files. Aborting.")
            break
        attempts += 1

        try:
            print(f"[INFO] Trying file: {grib_file}")
            ds = xr.open_dataset(grib_file, engine="cfgrib")

            # Pick variable and collapse 'step' if needed
            var_name = list(ds.data_vars)[0]
            da = ds[var_name]
            if "step" in da.dims:
                da = da.isel(step=0)

            if "time" not in da.coords or len(da.time) == 0:
                continue

            random_time = random.choice(da.time.values)
            da2d = da.sel(time=random_time)

            gdf = gpd.read_file(glacier_shapefile_path).to_crs("EPSG:4326")

            fig, ax = plt.subplots(figsize=(9, 7))
            da2d.plot.imshow(ax=ax, cmap="Blues", cbar_kwargs={'label': f'{var_name} (m)'})
            gdf.boundary.plot(ax=ax, edgecolor="red", linewidth=1)
            ax.set_title(f"Random ERA5 Snapshot — {str(random_time)}")
            plt.tight_layout()
            plt.show()
            return

        except Exception as e:
            print(f"[WARNING] Could not plot from {grib_file}: {e}")

    print("[ERROR] No valid GRIB file found for plotting.")
