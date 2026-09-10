# Geodetic Glacier Mass Balance Tool

A standalone Python-based GUI tool to estimate geodetic glacier mass balance using satellite-derived Digital Elevation Models (DEMs). The tool supports DEM co-registration, elevation change analysis, uncertainty modeling, and mass balance estimation — all through an intuitive graphical interface.

This tool is built on top of the [xDEM](https://github.com/GlacioHack/xdem) open-source package — a Python library developed by the GlacioHack community for the analysis of digital elevation models, providing robust methods for DEM co-registration, elevation change analysis, and uncertainty quantification. 

[![xDEM GitHub](https://img.shields.io/badge/built%20on-xDEM-4c9be8)](https://github.com/GlacioHack/xdem?tab=readme-ov-file)
[![xDEM Docs](https://img.shields.io/badge/docs-xDEM-brightgreen)](https://xdem.readthedocs.io/en/stable/)
[![Paper](https://img.shields.io/badge/paper-IEEE-blue)](https://ieeexplore.ieee.org/abstract/document/9815885)

<p align="center">
  <table width="50%">
    <tr>
      <td align="center" style="border: 3px solid white; padding: 8px;">
        <img width="78%" alt="image"
             src="https://github.com/user-attachments/assets/52bdfcb7-3bd9-42d9-95d9-670d41591681" />
        <br><br>
        <em>Python based graphical user interface for rapid estimation of geodetic glacier mass balance, based on open source <a href="https://github.com/GlacioHack/xdem">xDEM</a> package.</em>
      </td>
    </tr>
  </table>
</p>

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
5. ALTERNATE METHOD (Try this First !) There could be conflict in versions of various packages being installed and their dependencies. You can directly create a new environment in 'Anaconda Prompt' using the 'environment.yml' file. This will install the exact versions required. One caveat, in the last line of 'environment.yml' file make sure you give the correct path to your 'env' folder (check where your Anaconda is installed)
   ```bash
   conda env create -f environment.yml
   ```
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

### 1. Notes on ERA5Land Data Download and Seasonality Correction

The user needs to create a folder called "__data__" which should further contain 2 sub-folders: "__era5land_2m_temperature__" and "__era5land_snowfall__". The user should download in "__GRIB__" format data for these variables for their study region. I have attached a screen shot for the same below for your reference. Each of the individual files were quite large (approx. 40-60 MB), so they were not uploaded. Downloading the era5land data is optional if the end user do not wish to perform seasonality correction. Or the user can perform the seasonality correction manually using their own algorithm after the inital mass balance results are derived. 

<p align="center">
  <table>
    <tr>
      <td><img width="100%" src="https://github.com/user-attachments/assets/c4c137b1-fb95-43fc-aff7-5a63a47c48f4" /></td>
      <td><img width="100%" src="https://github.com/user-attachments/assets/a6c5228a-446c-4e23-9778-e2c8d7b3ed2c" /></td>
    </tr>
    <tr>
      <td align="center"><b>Figure 1</b> <em>Sample ERA5Land 2m-temperature variable files</em></td>
      <td align="center"><b>Figure 2</b> <em>Sample ERA5Land Snowfall variable files</em></td>
    </tr>
  </table>
</p>

### 2. Detailed notes on how to operate the tool with an example

*This section is under development, will be updated shortly .......*
