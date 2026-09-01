# Industrial Predictive Maintenance — Real Data Edition

This edition bundles real experimental UCI hydraulic measurements and automatically downloads the large NASA IMS bearing and MIMII pump-audio datasets during setup. It preserves RAG, citations, Ollama, Bluetooth, bookings, technician ratings, work orders, approvals, inventory, alerts and analytics.

## Data integrity

- UCI Hydraulic Systems: 2,205 bundled real test-rig cycles, CC BY 4.0.
- NASA IMS Bearings: downloaded from NASA's official archive.
- MIMII DUE pump audio: downloaded from Zenodo; CC BY-NC-SA 4.0.
- UCI model metrics are calculated from a 75/25 stratified holdout and are not hard-coded.
- NASA vibration features are RMS, peak and kurtosis calculated from each recording.
- MIMII features are audio RMS and zero-crossing rate; labels are derived from official normal/anomaly paths.
- UCI has no sound channel, so no sound values are invented.

## VS Code CMD setup

Extract the ZIP and open the inner project folder in VS Code. Run:

~~~bat
setup.cmd
~~~

Setup installs dependencies, tests the application, then downloads and processes NASA IMS and MIMII. The external downloads require roughly 1.5 GB or more plus extraction space and can take a long time.

If an external download is interrupted, run:

~~~bat
setup_external_real_data.cmd
~~~

The downloader reuses completed archives and validates the published MIMII pump MD5 checksum.

Set .env:

~~~dotenv
USE_OLLAMA=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
VECTOR_BACKEND=tfidf
~~~

Terminal 1:

~~~bat
run_backend.cmd
~~~

Terminal 2:

~~~bat
run_dashboard.cmd
~~~

Open http://localhost:8501 and select **Real dataset replay** or **Model health**.

## Reproducibility

The official UCI raw archive can be transformed again with:

~~~bat
.venv\Scripts\python.exe scripts\import_uci_hydraulic.py PATH_TO_UCI_FILES
~~~

External dataset sources:

- UCI DOI: https://doi.org/10.24432/C5CW21
- NASA IMS: https://data.nasa.gov/dataset/ims-bearings
- MIMII DUE: https://doi.org/10.5281/zenodo.4740355

Synthetic demonstration screens from the earlier edition remain available only for backward-compatible UI workflows. The real-data research results, dataset replay and model metrics are explicitly labelled and never mix synthetic and recorded measurements.
