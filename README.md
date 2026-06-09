# Geodetic Glacier Mass Balance Tool

A standalone Python-based GUI tool to estimate geodetic glacier mass balance using satellite-derived Digital Elevation Models (DEMs). The tool supports DEM co-registration, elevation change analysis, uncertainty modeling, and mass balance estimation — all through an intuitive graphical interface.

This tool is built on top of the [xDEM](https://github.com/GlacioHack/xdem) open-source package — a Python library developed by the GlacioHack community for the analysis of digital elevation models, providing robust methods for DEM co-registration, elevation change analysis, and uncertainty quantification. [![xDEM GitHub](https://img.shields.io/badge/built%20on-xDEM-4c9be8)](https://github.com/GlacioHack/xdem?tab=readme-ov-file)
[![xDEM Docs](https://img.shields.io/badge/docs-xDEM-brightgreen)](https://xdem.readthedocs.io/en/stable/)

## 🛠️ Requirements
- Python version: **3.12.10**
- All required packages are listed in `requirements.txt`

## 📦 Features
- Interactive GUI for input selection and parameter configuration
- DEM co-registration pipelines: Nuth & Kääb, ICP, Deramp, Vertical Shift
- Elevation difference filtering: NMAD, ELA, absolute threshold
- Glacier masking using shapefiles and unstable terrain exclusion
- Hypsometric interpolation of missing values
- Terrain-based heteroscedasticity modeling (slope, aspect, curvature)
- Spatial error estimation using empirical variograms
- Glacier-wise mass balance calculation with uncertainty (in m w.e./yr)
- Real-time visualization of elevation changes, uncertainty maps, histograms, and scatter plots

## 💾 Installation

1. Ensure Python 3.12.10 is available (preferably via Anaconda)
2. Create and activate a virtual environment:
    ```bash
    conda create -n geodetic_model_env python=3.12.10 -c conda-forge -y
    conda activate geodetic_model_env
    ```
3. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4. Install the tool locally using `setup.py`:
    ```bash
    pip install .
    ```
This registers the tool as a command-line application named `geodetic-model`

## ▶️ Running the GUI via Anaconda Prompt

Once the installation is complete, you can launch the graphical interface using the Anaconda Prompt:

### Step-by-step:
1. **Open Anaconda Prompt**  
   From the Start Menu, search and open **Anaconda Prompt**.
2. **Activate the environment**  
   ```bash
   conda activate geodetic_model_env
   ```
3. **Navigate to the project directory**  
   If you installed it from a folder like `D:\GlacierProject`, run:
   ```bash
   cd D:\GlacierProject
   ```
4. **Run the GUI**  
   Either of the following will launch the tool:
   ```bash
   python run_gui.py
   ```
   or (if `setup.py` installed the console script correctly):
   ```bash
   geodetic-model
   ```
This will open the Geodetic Glacier Mass Balance Tool in a standalone window.

## 📝 Additional Notes 

[1] The user needs to create a folder called "__data__" which should further contain 2 sub-folders: (i) era5land_2m_temperature (ii) era5land_snowfall. The user should download in "GRIB" format data for these variables for their study region. I have attached a screen shot for the same below for your reference. Each of the individual files were quite large (approx 40-60 MB), so I didn't upload them. Downloading these files is optional if the end user do not wish to perform seasonality correction. Or the user can perform the seasonality correction manually using their own algorithm after the inital mass balance results are derived. 

<p align="center">
  <table>
    <tr>
      <td><img width="100%" src="https://github.com/user-attachments/assets/c4c137b1-fb95-43fc-aff7-5a63a47c48f4" /></td>
      <td><img width="100%" src="https://github.com/user-attachments/assets/a6c5228a-446c-4e23-9778-e2c8d7b3ed2c" /></td>
    </tr>
    <tr>
      <td align="center"><b>Figure 1</b> <em>Sample ERA5Land 2m temperature Variable files</em></td>
      <td align="center"><b>Figure 2</b> <em>Sample ERA5Land Snowfall Variable files</em></td>
    </tr>
  </table>
</p>

