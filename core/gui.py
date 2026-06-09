import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from core import gui_plots
import datetime
import rasterio
from core.main_controller import run_geodetic_pipeline
from core.corrections import open_snow_season_dialog
import subprocess
import sys
import os

def restart_gui():
    import tkinter as tk
    from tkinter import messagebox
    import sys
    import subprocess
    import os

    # Ask for confirmation
    root = tk.Tk()
    root.withdraw()
    confirm = messagebox.askyesno("Confirm Restart", "Are you sure you want to close and restart the application?")
    root.destroy()

    if confirm:
        try:
            # Get full path to run_gui.py
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run_gui.py"))

            # Launch new process
            subprocess.Popen([sys.executable, script_path], close_fds=True)

        except Exception as e:
            messagebox.showerror("Restart Failed", f"Could not restart GUI:\n{e}")
            return

        # Forcefully terminate current process
        os._exit(0)


class Geodetic_MB_GUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Geodetic Glacier Mass Balance Tool")
        self.master.state('zoomed')
        self.pane = tk.PanedWindow(master, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.pane.pack(fill=tk.BOTH, expand=True)
        
        # Centered progress overlay (initially hidden)
        self.center_progress_frame = tk.Frame(master)
        self.center_progress_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.center_progress_label = tk.Label(self.center_progress_frame, text="Running model...", fg="blue", font=("Helvetica", 14, "italic"))
        self.center_progress_label.pack()
        self.center_progress_bar = ttk.Progressbar(self.center_progress_frame, mode="determinate", length=500)
        self.center_progress_bar.pack(pady=10)
        self.center_progress_frame.place_forget()  # hide initially
        
        self.left_frame = tk.Frame(self.pane, width=980)
        self.right_frame = tk.Frame(self.pane)
        self.pane.add(self.left_frame, minsize=900)
        self.pane.add(self.right_frame)
        self.result = None  # Store output from run_model for use in plotting
        self.input_entries = {}  # Track entries using string keys
        self.build_left_pane()
        self.build_right_pane()

    def update_progress(self, percent, message=""):
        self.center_progress_bar["value"] = percent
        if message:
            self.center_progress_label.config(text=message)
        self.master.update_idletasks()

    def add_placeholder(self, entry, placeholder):
        entry.insert(0, placeholder)
        entry.config(fg="gray")
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="black")
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="gray")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def build_left_pane(self):
        row = 0
        top_frame = tk.Frame(self.left_frame)
        top_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(5, 10))
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "ncpor_logo.png"))
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((130, 130), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(top_frame, image=self.logo_img).pack(side=tk.LEFT, padx=(0, 10))
            except Exception as e:
                tk.Label(top_frame, text=f"Logo error: {e}").pack(side=tk.LEFT)
        tk.Label(top_frame, text="Geodetic Glacier Mass Balance Tool", font=("Helvetica", 22, "bold")).pack(side=tk.LEFT)
        row += 1
        self.ref_dem_path = tk.StringVar()
        self.align_dem_path = tk.StringVar()
        self.unstable_path = tk.StringVar()
        self.glacier_path = tk.StringVar()
        file_inputs = [
            ("Reference DEM (Raster File)", self.ref_dem_path, "Enter the reference DEM file path (Ref. Help, Sec. 5) ", "reference"),
            ("To-be-aligned DEM (Raster File)", self.align_dem_path, "Enter the to-be-aligned DEM file path", "to-be-aligned"),
            ("Unstable Terrain (Shapefile)", self.unstable_path, "Enter the unstable terrain shape file path", "unstable"),
            ("Glaciers (Shapefile)", self.glacier_path, "Enter the glacier shape file path (Ref. Help, Section 2)", "glaciers"),
        ]
        for text, var, placeholder, key in file_inputs:
            tk.Label(self.left_frame, text=text).grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
            entry = tk.Entry(self.left_frame, textvariable=var, width=45)
            entry.grid(row=row, column=1, sticky="w")
            self.input_entries[key] = entry
            self.add_placeholder(entry, placeholder)
            def on_key(event, e=entry):
                e.config(fg="blue")
            entry.bind("<KeyRelease>", on_key)
            tk.Button(self.left_frame, text="Browse", command=lambda v=var, k=key: self.browse_file(v, k)).grid(row=row, column=2, sticky="w")
            row += 1

        tk.Label(self.left_frame, text="Reference DEM Date").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.ref_date = DateEntry(self.left_frame, date_pattern='dd/mm/yyyy', year=2000,
                                  mindate=datetime.date(1970, 1, 1), maxdate=datetime.date(2100, 12, 31))
        self.ref_date.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(self.left_frame, text="To-be-aligned DEM Date").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.align_date = DateEntry(self.left_frame, date_pattern='dd/mm/yyyy', year=2014,
                                    mindate=datetime.date(1970, 1, 1), maxdate=datetime.date(2100, 12, 31))
        self.align_date.grid(row=row, column=1, sticky="w")
        row += 1

        tk.Label(self.left_frame, text="Co-registration Pipeline").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.coreg_algo = ttk.Combobox(self.left_frame, values=[
            "Nuth & Kaab (NK)",
            "Iterative Closest Point (ICP)",
            "NK + Deramp (polynomial order = 1)",
            "NK + Deramp (polynomial order = 2)", 
            "NK + Deramp (polynomial order = 3)",
            "ICP + NK",
            "NK + ICP",
            "Vertical Shift (VS) + NK",
            "VS + NK + Deramp (polynomial order = 1)",
            "VS + NK + Deramp (polynomial order = 2)",
            "VS + NK + Deramp (polynomial order = 3)",
            "VS + ICP + NK",
            "VS + ICP + NK + Deramp (polynomial order = 1)",
            "VS + ICP + NK + Deramp (polynomial order = 2)",
            "VS + ICP + NK + Deramp (polynomial order = 3)"
        ], state="readonly", width=42)
        self.coreg_algo.set("Nuth & Kaab (NK)")
        self.coreg_algo.grid(row=row, column=1, columnspan=2, sticky="w")
        row += 1

        entries = [
            ("NMAD Filtering", "6"),
            ("Absolute threshold filter value (meters)", "FILTERING OPTION 1/2 (Ref. Help, Section 7)"),
            ("Ice Density (Uniform, Kg/m3)", "850"),
            ("ELA Value (meters a.s.l)", "FILTERING OPTION 2/2 (Can be skipped)"),
            ("Max ice thickness gain (Accumulation Zone, meters)", "USER INPUT REQUIRED (related to filtering option 2)"),
            ("Max ice thickness loss (Accumulation Zone, meters)", "0 (related to filtering option 2)"),
            ("Max ice thickness gain (Ablation Zone, meters)", "0 (related to filtering option 2)"),
            ("Max ice thickness loss (Ablation Zone, meters)", "USER INPUT REQUIRED (related to filtering option 2)"),
            ("Integer Number of Years","15"),
            #("Ice Density (Accumulation Zone, Kg/m3)", "550"),
            #("Ice Density (Ablation Zone, Kg/m3)", "900"),
        ]

        self.param_vars = []
        for text, default in entries:
            var = tk.StringVar()
            self.param_vars.append(var)
            tk.Label(self.left_frame, text=text).grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
            entry = tk.Entry(self.left_frame, textvariable=var, width=45)
            entry.grid(row=row, column=1, columnspan=2, sticky="w")
            self.add_placeholder(entry, default)
            row += 1

        # --- Additional Parameters ---

        # [1] Seasonality Correction
        # self.seasonality_correction = tk.StringVar()
        # tk.Label(self.left_frame, text="Seasonality Correction (m.w.e)").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        # entry_seasonality = tk.Entry(self.left_frame, textvariable=self.seasonality_correction, width=45)
        # entry_seasonality.grid(row=row, column=1, columnspan=2, sticky="w")
        # self.add_placeholder(entry_seasonality, "-0.101")
        # row += 1
        
        # [2] Elevation Heteroscedasticity (Dropdown)
        tk.Label(self.left_frame, text="Elevation Heteroscedasticity").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.hetero_dropdown = ttk.Combobox(self.left_frame, values=[
            "slope",
            "aspect",
            "curvature",
            "slope, aspect",
            "slope, curvature",
            "aspect, curvature",
            "slope, aspect, curvature"
        ], state="readonly", width=42)
        self.hetero_dropdown.set("slope, aspect")  # Default value
        self.hetero_dropdown.grid(row=row, column=1, columnspan=2, sticky="w")
        row += 1
        
        # [3] Spatial Correlations (Dropdown)
        tk.Label(self.left_frame, text="Spatial Correlations").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.spatial_corr_dropdown = ttk.Combobox(self.left_frame, values=[
            "Gaussian, Spherical"
        ], state="readonly", width=42)
        self.spatial_corr_dropdown.set("Gaussian, Spherical")
        self.spatial_corr_dropdown.grid(row=row, column=1, columnspan=2, sticky="w")
        
        row += 1
        
        # [4] Interpolation Algorithm (Dropdown)
        tk.Label(self.left_frame, text="Interpolation Algorithm").grid(row=row, column=0, sticky="w", pady=4, padx=(10, 5))
        self.interpolation_dropdown = ttk.Combobox(self.left_frame, values=[
            "regional_hypsometric, absolute threshold filter",
            "regional_hypsometric, ela filter",
            "local_hypsometric, absolute threshold filter",
            "local_hypsometric, ela filter"
        ], state="readonly", width=42)
        self.interpolation_dropdown.set("regional_hypsometric, absolute threshold filter")  # ✅ New default
        self.interpolation_dropdown.grid(row=row, column=1, columnspan=2, sticky="w")
        row += 1
        
        button_frame = tk.Frame(self.left_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(10, 5), sticky="w")
        tk.Button(button_frame, text="RUN MODEL", width=15, command=self.run_model).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Help", width=18, command=self.show_info).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Case Study", width=15, command=self.load_case_study).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="DEM Similarity Test", width=20, command=self.dem_similarity_test).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="LICENSE", width=12, command=self.show_license).pack(side=tk.LEFT, padx=5)
        
        # New row for View Log button
        row += 1
        #tk.Button(self.left_frame, text="View Log File", width=14, command=self.open_log_file).grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))
        #tk.Button(self.left_frame, text="Snow Bias Correction & Seasonality Correction", command=lambda: open_snow_season_dialog(self.master)).grid(row=row, column=1, columnspan=2, sticky="we", padx=(0, 10), pady=(0, 10))
    
        button_row = tk.Frame(self.left_frame)
        button_row.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))
        tk.Button(button_row, text="View Log File", width=14, command=self.open_log_file).pack(side=tk.LEFT, padx=(0, 10))

        def open_correction_dialog_if_ready():
            if hasattr(self, "result") and self.result and self.result.get("data"):
                from core.corrections import open_snow_season_dialog
                open_snow_season_dialog(self)
            else:
                messagebox.showwarning("Run Model First", "Please run the model at least once before applying snowfall correction.")
        
        self.snow_correction_button = tk.Button(
            button_row,
            text="Snow Bias Correction & Seasonality Correction",
            command=open_correction_dialog_if_ready,
            state="disabled"  # 🚫 disabled initially
        )
        self.snow_correction_button.pack(side=tk.LEFT)

        tk.Button(button_row,text="Close & Restart",command=restart_gui,width=16).pack(side=tk.LEFT, padx=(10, 0))
    
    def build_right_pane(self):
        # --- Top Frame for Dropdown ---
        dropdown_frame = tk.Frame(self.right_frame)
        dropdown_frame.pack(fill="x", pady=(10, 5))
        
        tk.Label(dropdown_frame, text="Select View:").pack(side=tk.LEFT, padx=(10, 5))
        self.plot_options = ttk.Combobox(dropdown_frame, values=[
            "Welcome Image",
            "Reference DEM with Glacier Shapefile",
            "To-be-aligned DEM with Glacier Shapefile",
            "Raw DEM Difference",
            "Co-registered DEM Difference",
            "Filtered DEM Difference (NMAD Outlier Removal)",
            "Histogram Plot (NMAD Filtered DEM Difference)",
            "Histogram Plot (NMAD Filtered over Glacier Surface)",
            "Filtered DEM Difference (NMAD + Absolute Glacier Threshold)",
            "Histogram Plot (Absolute Glacier Threshold - Glacier Surface)",
            "Filtered DEM difference (NMAD + ELA Filter)",
            "Histogram Plot (ELA Filter - Glacier Surface)",
            "Hypsometric Plot (Absolute Glacier Threshold)",
            "Hypsometric Plot (ELA Filtered)",
            "Interpolated DEM Difference (Hypsometric Method)",
            "Histogram of Interpolated DEM Difference (Glacier Only)",
            "Histogram of Interpolated DEM Difference (Stable Terrain Only)",
            "Visualize Elevation Heteroscedasticity (SLOPE)",
            "Visualize Elevation Heteroscedasticity (ASPECT)",
            "Visualize Elevation Heteroscedasticity (CURVATURE)",
            "Visualize Elevation Heteroscedasticity (SLOPE, ASPECT)",
            "Visualize Elevation Heteroscedasticity (SLOPE, CURVATURE)",
            "Visualize Elevation Heteroscedasticity (ASPECT, CURVATURE)",
            "Modelled Error Map (Topographic Uncertainty)",
            "Standardized Elevation Changes for Stable Terrain",
            "Histogram of z_dh for Stable Terrain",
            "Empirical and Modelled Variogram",
            "Glacier-wise Elevation Change and Uncertainty",
            "Annual Glacier Mass Balance with Uncertainty"
        ], state="readonly", width=60)
        self.plot_options.set("Welcome Image")
        self.plot_options.pack(side=tk.LEFT, padx=(0, 10))
        self.plot_options.bind("<<ComboboxSelected>>", self.update_plot)
        # --- Bottom Frame for Plot Area ---
        self.canvas_frame = tk.Frame(self.right_frame)
        self.canvas_frame.pack(fill="both", expand=True)
        self.master.after(200, self.show_welcome_image)

    def show_welcome_image(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        welcome_img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "welcome_img.png"))
        if not os.path.exists(welcome_img_path):
            tk.Label(self.canvas_frame, text="Welcome image not found.").pack()
            return

        try:
            img = Image.open(welcome_img_path)
            w, h = self.right_frame.winfo_width(), self.right_frame.winfo_height()
            if w == 1 or h == 1:
                w, h = 700, 600
            max_width = w - 60
            max_height = int((h - 100) * 0.85)
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            self._welcome_img_ref = ImageTk.PhotoImage(img)
            label = tk.Label(self.canvas_frame, image=self._welcome_img_ref)
            label.image = self._welcome_img_ref
            label.pack(pady=10, expand=True)
        except Exception as e:
            tk.Label(self.canvas_frame, text=f"Image error: {e}").pack()

    def update_plot(self, event=None):
        selection = self.plot_options.get()
    
        if selection == "Welcome Image":
            self.show_welcome_image()
    
        elif selection == "Reference DEM with Glacier Shapefile":
            gui_plots.display_image(
                self.canvas_frame, self.ref_dem_path.get(), self.glacier_path.get(),
                title="Reference DEM with Glaciers"
            )
    
        elif selection == "To-be-aligned DEM with Glacier Shapefile":
            gui_plots.display_image(
                self.canvas_frame, self.align_dem_path.get(), self.glacier_path.get(),
                title="To-be-aligned DEM with Glaciers"
            )
    
        elif selection == "Raw DEM Difference":
            self.plot_raw_dem_difference()
    
        elif selection == "Co-registered DEM Difference":
            if self.result and self.result.get("data") and "dh_after_coreg" in self.result["data"]:
                from core.gui_plots import plot_dh_coreg2
                plot_dh_coreg2(self.canvas_frame, self.result["data"]["dh_after_coreg"], self.glacier_path.get(),"Co-registered DEM Difference")
            else:
                messagebox.showerror("Error", "No co-registered DEM available. Please check the input and run the model again. Check the logbook for details.")    
    
        elif selection == "Filtered DEM Difference (NMAD Outlier Removal)":
            self.plot_filtered_dem_difference()
            
        elif selection == "Histogram Plot (NMAD Filtered DEM Difference)":
            self.plot_histogram_filtered_dem()
            
        elif selection == "Histogram Plot (NMAD Filtered over Glacier Surface)":
            self.plot_histogram_glacier_masked()
  
        elif selection == "Filtered DEM Difference (NMAD + Absolute Glacier Threshold)":
            if self.result and self.result.get("data") and "dh_after_coreg_nmad_glacierfilter" in self.result["data"]:
                from core.gui_plots import plot_dh_coreg
                plot_dh_coreg(self.canvas_frame, self.result["data"]["dh_after_coreg_nmad_glacierfilter"], self.glacier_path.get(),"Filtered DEM Difference (NMAD + Absolute Glacier Threshold)")
            else:
                messagebox.showerror("Error", "No filtered DEM available. Please check the input and run the model again. Check the logbook for details.")
                
        elif selection == "Filtered DEM difference (NMAD + ELA Filter)":
            if self.result and self.result.get("data") and "dh_after_coreg_nmad_elafilter" in self.result["data"] and self.result["data"]["dh_after_coreg_nmad_elafilter"] is not None:
                from core.gui_plots import plot_dh_coreg
                plot_dh_coreg(self.canvas_frame, self.result["data"]["dh_after_coreg_nmad_elafilter"], self.glacier_path.get(), "Filtered DEM difference (NMAD + ELA Filter)")
            else:
                messagebox.showerror("Error", "No ELA-filtered DEM available or Ivalid input parameters. Please check the input and run the model again. Check the logbook for details.")

        elif selection == "Histogram Plot (Absolute Glacier Threshold - Glacier Surface)":
            self.plot_histogram("dh_after_coreg_nmad_glacierfilter", "Absolute Glacier Threshold", glacier_only=True)

        elif selection == "Histogram Plot (ELA Filter - Glacier Surface)":
            self.plot_histogram("dh_after_coreg_nmad_elafilter", "ELA Filter", glacier_only=True)
                
        elif selection == "Hypsometric Plot (Absolute Glacier Threshold)":
            self.plot_hypsometric_curve("dh_after_coreg_nmad_glacierfilter")

        elif selection == "Hypsometric Plot (ELA Filtered)":
            self.plot_hypsometric_curve("dh_after_coreg_nmad_elafilter")
            
        elif selection == "Interpolated DEM Difference (Hypsometric Method)":
            if self.result and self.result.get("data") and "dh_interpolated" in self.result["data"]:
                from core.gui_plots import plot_dh_coreg
        
                interp_method = self.interpolation_dropdown.get()
                plot_title = f"dDEM interpolation raster \n({interp_method})"
        
                plot_dh_coreg(
                    self.canvas_frame,
                    self.result["data"]["dh_interpolated"],
                    self.glacier_path.get(),
                    plot_title=plot_title)
            else:
                messagebox.showerror("Error", "Interpolated DEM not available. Please run the model first.")

        elif selection == "Histogram of Interpolated DEM Difference (Glacier Only)":
            if self.result and "dh_interpolated" in self.result["data"]:
                from core.gui_plots import plot_histogram_interpolated_ddem_glacieronly
                algo = self.interpolation_dropdown.get()
                plot_histogram_interpolated_ddem_glacieronly(self.canvas_frame, self.result["data"]["dh_interpolated"], self.glacier_path.get(), algo)
        
        elif selection == "Histogram of Interpolated DEM Difference (Stable Terrain Only)":
            from core.gui_plots import plot_dh_interpolated_histogram
            plot_dh_interpolated_histogram(
                self.result["data"]["dh_interpolated"],
                unstable_shp=self.unstable_path.get(),
                canvas_frame=self.canvas_frame
            )
        
        elif selection.startswith("Visualize Elevation Heteroscedasticity"):
            from core.gui_plots import plot_elevation_heteroscedasticity
        
            if not self.result or "dh_interpolated" not in self.result["data"]:
                messagebox.showerror("Error", "Interpolated DEM not available. Please run the model first.")
                return
        
            ref_dem = self.ref_dem_path.get()
            unstable_path = self.unstable_path.get()
            dh = self.result["data"]["dh_interpolated"]
        
            # Parse dropdown label to decide variable(s)
            if "SLOPE, ASPECT" in selection:
                plot_vars = ["slope", "aspect"]
            elif "SLOPE, CURVATURE" in selection:
                plot_vars = ["slope", "curvature"]
            elif "ASPECT, CURVATURE" in selection:
                plot_vars = ["aspect", "curvature"]
            elif "SLOPE" in selection:
                plot_vars = ["slope"]
            elif "ASPECT" in selection:
                plot_vars = ["aspect"]
            elif "CURVATURE" in selection:
                plot_vars = ["curvature"]
            else:
                plot_vars = []
    
            plot_elevation_heteroscedasticity(self.canvas_frame, dh, ref_dem, unstable_path, plot_vars)

        elif selection == "Modelled Error Map (Topographic Uncertainty)":
            from core.gui_plots import plot_dh_coreg
            plot_dh_coreg(self.canvas_frame, self.result["data"]["sig_dh"], self.glacier_path.get(), plot_title="Modelled Error Map (σ_dh)")
        
        elif selection == "Standardized Elevation Changes for Stable Terrain":
            from core.gui_plots import plot_dh_coreg
            plot_dh_coreg(self.canvas_frame, self.result["data"]["z_dh"], self.glacier_path.get(), plot_title="Standardized Elevation Changes (z_dh)")
        
        elif selection == "Histogram of z_dh for Stable Terrain":
            from core.gui_plots import plot_zdh_histogram
            plot_zdh_histogram(
                self.result["data"]["z_dh"],
                unstable_shp=self.unstable_path.get(),
                canvas_frame=self.canvas_frame
            )
             
        elif selection == "Empirical and Modelled Variogram":
            from core.gui_plots import plot_variogram
            plot_variogram(
                self.canvas_frame,
                self.result["data"]["df_vgm"],
                self.result["data"]["func_sum_vgm"]
            )
            
        elif selection == "Glacier-wise Elevation Change and Uncertainty":
            from core.gui_plots import plot_glacier_uncertainty
            plot_glacier_uncertainty(self.canvas_frame, self.result["data"]["df_uncertainty"])

        elif selection == "Annual Glacier Mass Balance with Uncertainty":
            from core.gui_plots import plot_mass_balance_with_uncertainty
        
            plot_title = (
                "GEODETIC GLACIER MASS BALANCE \n"
                f"(Coregistration Algorithm: {self.coreg_algo.get()},\n Interpolation & Filter Algo: {self.interpolation_dropdown.get()},\n "
                f"Ice Density: {self.param_vars[2].get()},"
                f"Heteroscedasticity: {self.hetero_dropdown.get()},\n Spatial Correlation: {self.spatial_corr_dropdown.get()})"
            )
        
            plot_mass_balance_with_uncertainty(
                self.canvas_frame,
                self.result["data"]["df_mass_balance"],
                plot_title
            )
        
    def display_single_plot(self, plot_func, df):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    
        # Clear previous canvas contents
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
    
        # Create new plot
        fig, ax = plt.subplots(figsize=(7, 5))  # You can adjust the size here
        plot_func(ax, df)
    
        # Embed in Tkinter canvas
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)  
        
    def browse_file(self, var, key):
        file_path = filedialog.askopenfilename()
        if file_path:
            var.set(file_path)
            if key in self.input_entries:
                self.input_entries[key].config(fg="blue")
                
            # Auto plot Raw DEM Difference if both DEMs are selected
            if self.ref_dem_path.get() and self.align_dem_path.get():
                self.plot_options.set("Raw DEM Difference")
                self.plot_raw_dem_difference()
    

    def run_model(self):
        self.center_progress_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.update_progress(10, "Starting model...")
    
        try:
            interpolation_value = self.interpolation_dropdown.get()
            try:
                interpolation_method, glacier_filter_type = interpolation_value.split(", ")
            except ValueError:
                interpolation_method = interpolation_value
                glacier_filter_type = None
    
            self.update_progress(20, "Running coregistration...")
    
            # 🧼 Remove any existing snowfall correction before re-running
            if hasattr(self, "snowfall_estimates_df"):
                del self.snowfall_estimates_df
    
            self.result = run_geodetic_pipeline(
                ref_dem=self.ref_dem_path.get(),
                align_dem=self.align_dem_path.get(),
                unstable_shp=self.unstable_path.get(),
                glacier_shp=self.glacier_path.get(),
                ref_date=self.ref_date.get_date(),
                align_date=self.align_date.get_date(),
                coreg_algo=self.coreg_algo.get(),
                params=[v.get() for v in self.param_vars],
                #seasonality=self.seasonality_correction.get(),
                heteroscedasticity=self.hetero_dropdown.get(),
                spatial_correlation=self.spatial_corr_dropdown.get(),
                interpolation_algo=interpolation_method,
                glacier_filter_type=glacier_filter_type,
                canvas_frame=self.canvas_frame,
                view_option=self.plot_options.get(),
                progress_callback=self.update_progress,  # ✅ pass callback
                snowfall_estimates_df=getattr(self, "snowfall_estimates_df", None),  # ✅ pass from self
            )
    
            self.update_progress(100, "Finalizing...")
    
            if isinstance(self.result, dict) and self.result.get("status") == "success":
                # ✅ Enable snowfall correction button after successful model run
                if hasattr(self, "snow_correction_button"):
                    self.snow_correction_button.config(state="normal", bg="lightgreen")
            
                messagebox.showinfo("Success", self.result.get("message", "Mass balance estimation complete!"))
                self.plot_options.set("Annual Glacier Mass Balance with Uncertainty")
                self.update_plot()
            
                if messagebox.askyesno("Save Report", "Do you want to save all figures and generate a report?"):
                    save_dir = filedialog.askdirectory(title="Select directory to save report and images")
                    if save_dir:
                        from core.report_and_plots import save_all_figures_and_report
                        save_all_figures_and_report(self.result, self, save_dir)

            else:
                messagebox.showerror("Error", f"{self.result.get('message', 'An error occurred.')} \n\nPlease check the log for details.")
                #self.open_log_file()
    
        except Exception as e:
            messagebox.showerror("Error", f"A critical error occurred:\n{e}\n\nPlease check the log for more details.")
            self.open_log_file()
    
        finally:
            self.center_progress_bar["value"] = 0
            self.center_progress_frame.place_forget()

    def show_info(self):
        message = (
            "This GUI tool is used to estimate glacier mass balance using the geodetic method.\n\n"
            "Key Information for end users:\n\n"
            "1. The readme document contains installation instructions.\n\n"
            "2. The glacier shapefile input can contain 'rgi_id' as an attribute, however this is optional.\n\n"
            "3. The modules for co-registration and uncertainty estimation is taken as is from xDEM package (https://xdem.readthedocs.io/en/stable/about_xdem.html).\n\n"
            "4. Research Paper Reference (related to xDEM) - https://ieeexplore.ieee.org/document/9815885/ \n\n"
            "5. In case of DEM generated via microwave data, for e.g., SRTM - snow penetration correction is assumed \n\n"
            "6. For detailed instructions on various parameters - a manual is being developed for step-by-step procedure - will be released in next version \n\n"
            "7. Write an arbitary HIGH default value here, e.g., 10000, if no specific value is chosen for absolute threshold filter \n\n"
            "8. Make sure all files are projected in their appropriate UTM zones \n\n"
        )
        messagebox.showinfo("Help", message)

    def load_case_study(self):
        import tkinter as tk
    
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test"))
        self.ref_dem_path.set(os.path.join(base_path, "reference_dem.tif"))
        self.align_dem_path.set(os.path.join(base_path, "to_be_aligned_dem.tif"))
        self.unstable_path.set(os.path.join(base_path, "unstable_terrain.shp"))
        self.glacier_path.set(os.path.join(base_path, "glaciers.shp"))
        self.ref_date.set_date("11/02/2000")
        self.align_date.set_date("02/11/2014")
    
        for key in ["reference", "to-be-aligned", "unstable", "glaciers"]:
            if key in self.input_entries:
                self.input_entries[key].config(fg="blue")
    
        try:
            self.param_vars[1].set("80")     # Absolute threshold
            self.param_vars[3].set("5836")   # ELA
            self.param_vars[4].set("20")     # Max gain in accumulation zone
            self.param_vars[7].set("100")    # Max loss in ablation zone
        except IndexError:
            messagebox.showwarning("Warning", "One or more parameters could not be set. Check param_vars index.")
    
        # ✅ Custom auto-closing message box
        splash = tk.Toplevel(self.master)
        splash.title("Case Study Loaded")
        splash.geometry("400x120")
        splash_label = tk.Label(splash, text="✅ Case study data and parameters loaded.\n\nRunning the model now...", font=("Helvetica", 11))
        splash_label.pack(expand=True, fill="both", padx=20, pady=20)
        splash.after(2500, splash.destroy)  # Close after 2.5 seconds
    
        # ✅ Delay model run slightly so user sees message
        self.master.after(3000, self.run_model)

        
    def show_license(self):
        license_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "LICENSE"))
        if not os.path.exists(license_path):
            messagebox.showerror("Error", "LICENSE file not found.")
            return
    
        try:
            with open(license_path, "r", encoding="utf-8") as file:
                content = file.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read LICENSE file:\n{e}")
            return
    
        # Show license content in a scrollable popup
        license_window = tk.Toplevel(self.master)
        license_window.title("License Agreement")
        license_window.geometry("1000x800")
    
        text_area = tk.Text(license_window, wrap=tk.WORD)
        text_area.insert(tk.END, content)
        text_area.config(state=tk.DISABLED)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        scrollbar = tk.Scrollbar(text_area, command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.config(yscrollcommand=scrollbar.set)

    def dem_similarity_test(self):
        ref_path = self.ref_dem_path.get()
        align_path = self.align_dem_path.get()
    
        if not os.path.exists(ref_path) or not os.path.exists(align_path):
            messagebox.showerror("Error", "Please provide valid DEM file paths.")
            return
    
        try:
            with rasterio.open(ref_path) as ref_src, rasterio.open(align_path) as align_src:
                crs_match = ref_src.crs == align_src.crs
                shape_match = ref_src.shape == align_src.shape
                transform_match = ref_src.transform == align_src.transform
    
            results = {
                "CRS": crs_match,
                "Shape": shape_match,
                "Transform": transform_match
            }
    
            summary = "DEM Similarity Test Results:\n\n"
            for key, passed in results.items():
                status = "✓ OK" if passed else "✗ Mismatch"
                summary += f"{key}: {status}\n"
    
            messagebox.showinfo("DEM Similarity Test", summary)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open DEM files:\n{e}")

    def plot_raw_dem_difference(self):
        from rasterio import open as rio_open
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import geopandas as gpd
    
        ref_path = self.ref_dem_path.get()
        align_path = self.align_dem_path.get()
        glacier_path = self.glacier_path.get()
    
        if not (os.path.exists(ref_path) and os.path.exists(align_path) and os.path.exists(glacier_path)):
            return
    
        try:
            with rio_open(ref_path) as ref, rio_open(align_path) as align:
                ref_data = ref.read(1).astype(float)
                align_data = align.read(1).astype(float)
    
                ref_data[ref_data == ref.nodata] = np.nan
                align_data[align_data == align.nodata] = np.nan
    
                dh = align_data - ref_data
    
                extent = [ref.bounds.left, ref.bounds.right, ref.bounds.bottom, ref.bounds.top]
    
            gdf = gpd.read_file(glacier_path)
    
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
    
            fig, ax = plt.subplots(figsize=(7, 6))
            im = ax.imshow(dh, cmap='coolwarm', extent=extent, vmin=-300, vmax=300)
            gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=0.5)
            ax.set_title("Raw DEM Difference (Align - Reference)")
            fig.colorbar(im, ax=ax, label='Elevation Difference (m)')
    
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compute or display DEM difference:\n{e}")
            
    def plot_filtered_dem_difference(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import geopandas as gpd
    
        try:
            if not self.result or "dh_after_coreg_nmad" not in self.result["data"]:
                messagebox.showwarning("No Data", "Filtered DEM Difference not available. Please run the model first.")
                return
    
            dh = self.result["data"]["dh_after_coreg_nmad"]
            glacier_path = self.glacier_path.get()
    
            if not os.path.exists(glacier_path):
                messagebox.showerror("Error", "Valid glacier shapefile not found.")
                return
    
            gdf = gpd.read_file(glacier_path)
            extent = [dh.bounds.left, dh.bounds.right, dh.bounds.bottom, dh.bounds.top]
    
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
    
            fig, ax = plt.subplots(figsize=(7, 6))
            im = ax.imshow(dh.data, cmap='coolwarm', extent=extent, vmin=-300, vmax=300)
            gdf.boundary.plot(ax=ax, edgecolor='black', linewidth=0.5)
            ax.set_title("Filtered DEM Difference (NMAD Outlier Removal)")
            fig.colorbar(im, ax=ax, label='Elevation Difference (m)')
    
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot filtered DEM difference:\n{e}")
            
    def plot_histogram_filtered_dem(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        #import numpy as np
    
        if not self.result or "dh_after_coreg_nmad" not in self.result["data"]:
            messagebox.showerror("Error", "Filtered DEM not available. Please run the model first.")
            return
    
        dh = self.result["data"]["dh_after_coreg_nmad"]
        dh_values = dh.data.compressed()  # Remove NaNs or masked pixels
    
        if len(dh_values) == 0:
            messagebox.showerror("Error", "No valid data in filtered DEM raster.")
            return
    
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
    
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.hist(dh_values, bins=100, color='skyblue', edgecolor='black')
        ax.set_title("Histogram of Elevation Change (NMAD Filtered)")
        ax.set_xlabel("Elevation Change (m)")
        ax.set_ylabel("Pixel Count")
        ax.grid(True)
    
        plt.tight_layout()
    
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_histogram_glacier_masked(self):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np
        import geopandas as gpd
        from rasterio import features
        import rasterio
        import os
    
        if not self.result or "dh_after_coreg_nmad" not in self.result["data"]:
            messagebox.showerror("Error", "Filtered DEM not available. Please run the model first.")
            return
    
        dh = self.result["data"]["dh_after_coreg_nmad"]
        glacier_path = self.glacier_path.get()
        ref_path = self.ref_dem_path.get()
    
        if not os.path.exists(glacier_path) or not os.path.exists(ref_path):
            messagebox.showerror("Error", "Valid glacier shapefile or reference DEM not found.")
            return
    
        try:
            # Rasterize glacier mask
            glacier_outlines = gpd.read_file(glacier_path)
            with rasterio.open(ref_path) as src:
                glacier_mask = features.rasterize(
                    [(geom, 1) for geom in glacier_outlines.geometry],
                    out_shape=src.shape,
                    transform=src.transform,
                    fill=0,
                    dtype="uint8"
                ).astype(bool)
    
            # Mask non-glacier pixels
            masked_data = np.ma.masked_array(dh.data, mask=~glacier_mask)
    
            valid_values = masked_data.compressed()
            if len(valid_values) == 0:
                messagebox.showwarning("Warning", "No valid glacier pixels found in raster.")
                return
    
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
    
            fig, ax = plt.subplots(figsize=(7, 5))
            ax.hist(valid_values, bins=100, color='lightcoral', edgecolor='black')
            ax.set_title("Histogram of Elevation Change (Glacier Surface Only)")
            ax.set_xlabel("Elevation Change (m)")
            ax.set_ylabel("Pixel Count")
            ax.grid(True)
    
            plt.tight_layout()
    
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot histogram:\n{e}")

    def plot_histogram(self, raster_key, title_suffix, glacier_only=False):
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np
        import geopandas as gpd
        from rasterio import features
        import rasterio
        import os
    
        if not self.result or raster_key not in self.result["data"]:
            messagebox.showerror("Error", f"Raster '{raster_key}' not available. Please run the model first.")
            return
    
        dh = self.result["data"][raster_key]
        glacier_path = self.glacier_path.get()
        ref_path = self.ref_dem_path.get()
    
        # Apply glacier mask if needed
        if glacier_only:
            if not os.path.exists(glacier_path) or not os.path.exists(ref_path):
                messagebox.showerror("Error", "Valid glacier shapefile or reference DEM not found.")
                return
    
            try:
                glacier_outlines = gpd.read_file(glacier_path)
                with rasterio.open(ref_path) as src:
                    glacier_mask = features.rasterize(
                        [(geom, 1) for geom in glacier_outlines.geometry],
                        out_shape=src.shape,
                        transform=src.transform,
                        fill=0,
                        dtype="uint8"
                    ).astype(bool)
    
                masked_data = np.ma.masked_array(dh.data, mask=~glacier_mask)
                values = masked_data.compressed()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply glacier mask:\n{e}")
                return
        else:
            values = dh.data.compressed()
    
        if len(values) == 0:
            messagebox.showwarning("Warning", f"No valid data found for: {title_suffix}")
            return
    
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
    
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.hist(values, bins=100, color='mediumseagreen' if glacier_only else 'steelblue', edgecolor='black')
        ax.set_title(f"Histogram of Elevation Change\n({title_suffix})")
        ax.set_xlabel("Elevation Change (m)")
        ax.set_ylabel("Pixel Count")
        ax.grid(True)
    
        plt.tight_layout()
    
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    def open_log_file(self):
        import subprocess
        import platform
        import os
    
        log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs", "geodetic_pipeline.log"))
    
        if not os.path.exists(log_path):
            messagebox.showerror("Error", "Log file not found.")
            return
    
        try:
            if platform.system() == "Windows":
                os.startfile(log_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", log_path])
            else:  # Linux and others
                subprocess.call(["xdg-open", log_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open log file:\n{e}")

    def plot_hypsometric_curve(self, raster_key):
        import matplotlib.pyplot as plt
        import numpy as np
        import geopandas as gpd
        import xdem
        from rasterio import features
        import rasterio
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import warnings
        import os
    
        if not self.result or raster_key not in self.result["data"] or self.result["data"][raster_key] is None:
            messagebox.showerror("Error", f"Selected raster '{raster_key}' is not available. Please run the model first.")
            return
    
        dh2 = self.result["data"][raster_key]
        ref_path = self.ref_dem_path.get()
        glacier_path = self.glacier_path.get()
    
        if not os.path.exists(ref_path) or not os.path.exists(glacier_path):
            messagebox.showerror("Error", "Reference DEM or glacier shapefile not found.")
            return
    
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
    
                ref_dem = xdem.DEM(ref_path)
                start_date = self.ref_date.get_date()
                end_date = self.align_date.get_date()
    
                n_years = (end_date - start_date).days / 365.25
                if n_years <= 0:
                    messagebox.showerror("Error", "DEM date range must be greater than 0.")
                    return
    
                ddem = xdem.dDEM(dh2.copy(), start_time=start_date, end_time=end_date)
                ddem.data /= n_years
    
                glacier_outlines = gpd.read_file(glacier_path)
                with rasterio.open(ref_path) as src:
                    glacier_mask = features.rasterize(
                        [(geom, 1) for geom in glacier_outlines.geometry],
                        out_shape=src.shape,
                        transform=src.transform,
                        fill=0,
                        dtype="uint8"
                    ).astype(bool)
    
                ddem_bins = xdem.volume.hypsometric_binning(ddem[glacier_mask], ref_dem[glacier_mask])
                stds = xdem.volume.hypsometric_binning(ddem[glacier_mask], ref_dem[glacier_mask], aggregation_function=np.std)
    
                for widget in self.canvas_frame.winfo_children():
                    widget.destroy()
    
                fig, ax = plt.subplots(figsize=(8, 8))
                ax.grid(zorder=0)
                ax.axvline(x=0, color="black", linestyle="-", linewidth=1.5, zorder=1)
                ax.plot(ddem_bins["value"], ddem_bins.index.mid, linestyle="--", zorder=1)
    
                ela = self.result["data"].get("ela", None)
                is_ela_filtered = "elafilter" in raster_key.lower() and ela is not None
    
                for bin in ddem_bins.index:
                    bin_mid = bin.mid
                    bin_mean = ddem_bins.loc[bin, "value"]
                    bin_std = stds.loc[bin, "value"]
                    bin_top = bin.left
                    bin_bottom = bin.right
    
                    height = bin_top - bin_bottom
                    left = bin_mean - bin_std / 2
                    right = bin_mean + bin_std / 2
    
                    # Base bar: light gray
                    ax.barh(
                        y=bin_mid,
                        width=right - left,
                        left=left,
                        height=height,
                        zorder=2,
                        edgecolor="black",
                        color="lightgray"
                    )
    
                    # ELA-specific logic: red above ELA if dh < 0; green below ELA if dh > 0
                    if is_ela_filtered:
                        if bin_mid > ela and left < 0:
                            red_width = min(right, 0) - left
                            ax.barh(
                                y=bin_mid,
                                width=red_width,
                                left=left,
                                height=height,
                                zorder=3,
                                color="red"
                            )
                        elif bin_mid < ela and right > 0:
                            green_left = max(left, 0)
                            green_width = right - green_left
                            ax.barh(
                                y=bin_mid,
                                width=green_width,
                                left=green_left,
                                height=height,
                                zorder=3,
                                color="red"
                            )
    
                for bin in ddem_bins.index:
                    ax.vlines(ddem_bins.loc[bin, "value"], bin.left, bin.right, color="black", zorder=3)
    
                # ELA horizontal dashed line and annotation
                if is_ela_filtered:
                    ax.axhline(y=ela, color="black", linestyle="--", linewidth=2, zorder=4)
                    y_min, y_max = ax.get_ylim()
                    x_min, x_max = ax.get_xlim()
                    ax.text(
                        x_max, ela - (y_max - y_min) * 0.01,
                        f"ELA = {int(ela)}m",
                        color="black", fontsize=8,
                        ha="right", va="top", style="italic"
                    )
    
                ax.set_xlabel("Elevation change (m / a)")
                ax.set_ylabel("Elevation (m a.s.l.)")
    
                ax2 = ax.twiny()
                ax2.barh(
                    y=ddem_bins.index.mid,
                    width=ddem_bins["count"] / ddem_bins["count"].sum(),
                    left=0,
                    height=(ddem_bins.index.left - ddem_bins.index.right),
                    zorder=2,
                    alpha=0.2,
                )
                ax2.set_xlabel("Normalized area distribution (hypsometry)")
    
                plt.tight_layout()
    
                canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate hypsometric plot:\n{e}")

