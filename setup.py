from setuptools import setup, find_packages

setup(
    name='geodetic_model',
    version='0.1.0',
    description='GUI tool for geodetic glacier mass balance estimation using xDEM',
    author='Ashutosh Kulkarni',
    author_email='ashutoshk@ncpor.res.in',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'scipy',
        'pytransform3d',
        'geopandas',
        'rasterio',
        'xdem==0.1.4',
	    'opencv-contrib-python',
        'geoutils',
        'tkcalendar',
        'Pillow'
    ],
    classifiers=[
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    python_requires='==3.12.10',
    entry_points={
        'gui_scripts': [
            'geodetic-model = run_gui:main'
        ]
    }
)
