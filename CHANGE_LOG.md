# Change Log

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
_________________________________________________________________________
## 2026-07-14

### Summary
>
> - Repository restructured into an installable Python package (`vitals`) via `pyproject.toml`, in addition to the existing standalone notebooks
> - Added new PACE & EMIT tutorial series
> - Various fixes and improvements to shared Python modules, notebooks, and documentation

### Added

> - `pyproject.toml` for building/installing the repository as the `vitals` package
> - PACE & EMIT Tutorials
>   - `01_Colocate_PACE_EMIT_Data.ipynb`
>   - `02_Process_PACE_EMIT_Data.ipynb`
> - `src/vitals/pace_tools.py` and `src/vitals/utils.py` modules
> - `citation.cff`
> - Static figures for interactive plots across notebooks
> - Sample output data from interactive visualizations (e.g. `clicked_values.csv`, `dangermond_default_polygons.geojson`)

### Changed

> - Moved shared Python modules from `python/modules/` to `src/vitals/` and renamed `python/EMIT_NEON/` to `python/emit_neon/`
> - Replaced `earthaccess.collection_query` with `earthaccess.search_datasets` and removed pinned `earthaccess` version (fixes #59)
> - Improved `merge_emit` granule ID retrieval when `earthaccess` file handlers are passed to `emit_xarray` in `emit_tools.py`
> - Updated NEON notebooks for new filepaths, token handling, and `neonutilities` version
> - Updated README with a full table of contents, citation guidance, and related resources
> - Updated setup instructions, `environment.yml`, and web-book Quarto files (`_quarto.yml`, `index.qmd`)
> - Updated contract numbers in notebook footers where applicable

## 2025-12-05

### Summary
>
> - Moved EMIT + NEON notebooks and supporting files out of community_contributed directory
> - Moved EMIT + ECOSTRESS into new directory
> - Updated filepaths in notebooks to reflect new directory structure
> - Updated workshop powerpoint links to new google docs locations
> - Update PACE_OCI_L2_SFRFL search to version 3.1 in `Exploring_PACE_OCI_L2_SFRFL.ipynb`

## 2025-07-20

### Summary
>
> - Added VSWIR-TIR Handbook Workshop Contents
>   - `Exploring_ECOSTRESS_L2T_LSTE.ipynb`
>   - `Exploring_EMIT_L2A_RFL.ipynb`
>   - `Exploring_PACE_OCI_L2_SFRFL.ipynb`
> - Updated quarto files
>   - `vitals.qmd`
>   - `_quarto.yml`
>   - `index.qmd`
>   - `2025_sbg_workshop.qmd`
> - Updated readme
> 

## 2025-05-19

### Summary
>
> - Added SBG-TIM2025 contents
>   - `Finding_Coincident_Airborne_and_Orbital_Data.ipynb`
> - Updated setup instructions and python environment
> - Updated `01_Finding_Concurrent_Data.ipynb`
> - Updated the quarto file 
> - Added 2025 markdown file
> - Added new logos



## 2024-09-09

### Summary
>
> Change name of 'user_contributed' directory to 'community_contributed'
> Updated `contribute.md` to reflect the change
>

## 2024-09-03

### Summary
>
> - Added community contributed notebooks and associated figures:
>   -  `01_Finding_Co-located_NEON_and_EMIT_Data_NIWO.ipynb`
>   -  `02_Exploring_NEON_and_EMIT Reflectance_Data_NIWO.ipynb`
> 

## 2024-05-24

### Summary
>
> - Add streaming functionality to notebooks 2 and 3
> - Add ECOSTRESS ET example to notebook 2
> - Update some text
> - Add SBG workshop contents
> - minor changes to notebook 4
> - update to newest `emit_tools.py`
>

## 2024-01-31

### Summary
>
> - Fixed some typos
> - Resize slides in `slides.md`
>

## 2024-01-24

> ### Summary
>
> - Updated earthaccess search to use concept-id for Notebook 1
> - Implemented downloading of required scenes for Notebooks 2-5 into a cell in Notebook 1
> - Corrected projection/crs arguments for plotting of EMIT and ECOSTRESS imagery
> - Made minor changes to Notebook 5 to fix cloud/local compatibility issues
> - Fixed implementation of ewt_detection_limit threshold in ewt_calc.py
> - Improved description of ewt_detection_limit in Notebook 3
> - misc typos/syntax fixes
>
>
> ### Added
>
> - Local environment support and setup instructions  
> - Added EWT and ET cloud-optimized GeoTIFFs generated for the workshop to repository
> - Added list of required granules/scenes to execute notebooks
> - Added workshop slides.md
>

## 2023-10-10

> ### Summary
>
> - Improved Finding Concurrent Data Notebook text/instructions
> - Renamed contribute.md
> - added repo description
>
> ### Added
>
> - Repository description
>

## 2023-09-28

> ### Summary
>
> Updated notebook ROI to Carpinteria Salt Marsh
>
> ### Added
>
> - Added landcover.geojson
>

## 2023-09-22

> ### Summary
>
> Updated contribute.md and added `user contributed` directory
>
> ### Added
>
> - Added `user_contributed` directory

## 2023-09-20

> ### Summary
>
>This is the first update.
>
> ### Added
>
> - [Finding Concurrent Data Notebook](python/emit_ecostress/01_Finding_Concurrent_Data.ipynb)
