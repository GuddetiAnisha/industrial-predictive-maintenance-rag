# Industrial Predictive Maintenance and RAG Digital Twin

## What this project is about

Industrial machines give off signs when something is not working normally. A hydraulic pump might start leaking internally, a valve might respond more slowly, or a cooler might lose efficiency. Sensor measurements can help us notice these problems before they become bigger.

I built this project to bring equipment-condition prediction and maintenance support into one application. The machine-learning part uses sensor information to classify component conditions. The application then presents those predictions in a dashboard and connects them to maintenance information.

**The main goal is condition monitoring and fault diagnosis.** This version does not claim to predict exactly how many hours a component has left before failure. That would require suitable run-to-failure data and a separate Remaining Useful Life (RUL) model.

## Why I worked on it

Unexpected equipment problems can interrupt industrial operations and increase maintenance costs. In a traditional reactive approach, technicians often respond after something has gone wrong. Condition monitoring gives them earlier information about what might need attention.

I wanted to understand the complete path from measurements to a useful maintenance decision: collect or replay data, prepare it, predict component condition, check model performance, and present understandable supporting information.

## The datasets

### 1. UCI Hydraulic Systems — main component-condition dataset

This is real experimental data from a hydraulic test rig, rather than data recorded from a production truck. It contains **2,205 operating cycles**. Each cycle covers approximately **60 seconds**, with measurements such as temperature, pressure, flow and vibration. The official dataset contains signals sampled at different frequencies, as well as known condition labels.

The project focuses on four condition targets:

| Component | What its condition label represents |
| --- | --- |
| Cooler | Cooling performance or degradation |
| Valve | Switching condition |
| Pump | Internal leakage condition |
| Accumulator | Pressure condition |

The processed cycle-level CSV created by `scripts/import_uci_hydraulic.py` has eight columns: `cycle`, the four component labels, `stable_flag`, `temperature_mean`, and `vibration_max`.

The import script calculates mean temperature from the `TS1.txt` measurements and maximum vibration from `VS1.txt` for each cycle. This is a compact feature representation; it is **not** the same as retaining every signal channel from the original UCI dataset.

**Why mean temperature?** It gives a simple picture of the thermal conditions during the cycle, rather than reacting to every small fluctuation.

**Why maximum vibration?** It preserves the strongest positive vibration reading in the cycle, which may reveal short-lived mechanical events that an average could hide. A high reading is not automatically proof of a fault—it may also come from operating conditions or noise. Peak absolute vibration and RMS are alternative features worth comparing.

These features are useful starting points, but they cannot capture every pressure, flow or time-dependent fault pattern.

### 2. NASA IMS Bearings — vibration analysis

The repository documents a workflow for downloading the NASA IMS Bearing data. Bearing vibration recordings can be summarised using **RMS**, **peak** and **kurtosis**:

- **RMS** describes the overall strength of a vibration signal.
- **Peak** captures its largest amplitude.
- **Kurtosis** helps describe the occurrence of unusually large signal values or impacts.

These indicators can be useful for studying mechanical degradation. Full RUL claims would still require an appropriate run-to-failure evaluation, not just extracting features.

### 3. MIMII DUE — machine sound

The repository also describes downloading MIMII DUE pump-audio data. The sound workflow calculates **audio RMS** and **zero-crossing rate**, and uses the dataset's normal/anomaly structure.

This explores a different way to observe machine condition: sound rather than hydraulic or vibration measurements. The UCI dataset does **not** have an audio channel, so the project does not present invented UCI sound readings.

## How the system works

```text
Experimental sensor measurements
             |
             v
Cycle-level preparation and features
             |
             v
Random Forest condition classifiers
             |
             v
Predicted cooler / valve / pump / accumulator conditions
             |
             +----> Model evaluation
             |
             v
Dashboard and maintenance information
             |
             v
Inspection or follow-up decisions by a person
```

The model predicts conditions; it does not automatically establish a physical cause or decide that a component must be replaced.

## Why Random Forest?

I used **Random Forest** as a practical approach for numerical, structured features. A Random Forest builds several decision trees and combines their predictions. One tree may rely on a particular threshold or pattern; combining many trees usually produces a more stable classifier.

It is a useful baseline because it can learn nonlinear patterns, works without requiring every feature to be scaled, and can provide feature-importance indicators. Feature importance, however, should not be confused with a proven physical cause.

Other models, including gradient boosting and neural networks, could also be investigated. A 1D CNN would be particularly relevant when working directly with raw sensor sequences rather than only cycle-level summaries.

## How I evaluate the predictions

The repository documents UCI model evaluation using a **75/25 stratified holdout**. Stratification helps preserve the representation of target classes in the two partitions.

The model evaluation includes:

| Metric | What it tells me |
| --- | --- |
| Accuracy | The overall share of correct classifications |
| Precision | How many predicted faults are actually faults |
| Recall | How many real faults the system detects |
| F1-score | A balance between precision and recall |
| False-alarm rate | How often normal examples are incorrectly flagged |
| Confusion matrix | Which classes are confused with one another |

For maintenance applications, accuracy alone is not enough. Missing a serious fault and raising an unnecessary alarm can have very different consequences.

A stratified holdout can test the classifier on withheld cycles, but it does not by itself prove that the model will generalise to completely different machines, sites or operating conditions.

## What about overfitting?

Overfitting happens when a model learns its training examples too closely and performs less well on unseen examples.

Separating training and test data helps **detect** overfitting. Random Forest combines many trees, which can reduce variance compared with one tree. Additional steps could include limiting tree depth, setting a minimum number of samples per leaf, and testing on independent operating conditions.

Those hyperparameter controls are possible improvements; the project documentation does not establish that each one was tuned in the final run.

## What does uncertainty mean here?

A fault classifier may assign different probabilities to different condition categories. Those values can be useful as preliminary indicators of prediction confidence, but raw Random Forest probabilities are **not automatically calibrated uncertainty estimates**.

A more rigorous uncertainty study would check whether predicted probabilities match actual frequencies on independent data, and examine how performance changes with noisy or unfamiliar measurements.

This matters because technicians should not treat every model prediction as equally reliable.

## What is retrieval, and why add RAG?

Predicting a condition such as pump leakage is only part of the maintenance workflow. A technician may also want to know what to inspect next.

**Retrieval** means searching available information, such as maintenance guidance, for passages relevant to the predicted condition or the technician's question.

**RAG (Retrieval-Augmented Generation)** then uses retrieved information to help produce a natural-language response. The repository describes maintenance-oriented retrieval, citations and an optional Ollama integration. Retrieved passages and citations should be checked, and generated guidance is not a replacement for approved safety procedures or technician judgement.

The difference is simple:

- **Random Forest:** What condition does the sensor data suggest?
- **Retrieval/RAG:** What relevant maintenance information can help a person investigate that condition?

## Application and interface

The documented application includes a **FastAPI backend** and **Streamlit dashboard**, with workflows for viewing real dataset replay, model health and maintenance-related information. The repository also describes bookings, work orders, approvals, inventory and alerts.

The dashboard makes predictions easier to inspect. It should not be confused with a physics-based model that continuously reproduces every internal state of a real machine.

## What I learned

This project helped me connect several ideas:

1. Understanding the engineering meaning of sensor measurements matters before building the model.
2. Summarising time-series data can make a first classifier manageable, but useful information may be lost.
3. Good evaluation needs more than one metric, particularly when missed faults and false alarms have different costs.
4. Predictions are more useful when users can inspect supporting maintenance information.
5. Strong results on one experimental dataset are not a guarantee of reliable performance on every industrial machine.

## Current limitations and next steps

The most important limitations are:

- The UCI experiment primarily provides **component-condition labels**, not complete component failure lifetimes.
- Two cycle-level summary features cannot capture every fault signature in the original multichannel time series.
- Results from a test rig should not be presented as validated performance on production equipment.
- The documented holdout does not prove transfer to new machine populations.
- Reliable probability calibration and RUL uncertainty estimation would require dedicated evaluation.

My next steps would be to compare richer pressure, temperature and vibration features; test generalisation to new operating conditions; evaluate probability calibration; and investigate a dedicated RUL model using run-to-failure datasets such as NASA bearing or engine-degradation data.


## Data sources

- [UCI Condition Monitoring of Hydraulic Systems](https://doi.org/10.24432/C5CW21)
- [NASA IMS Bearings](https://data.nasa.gov/dataset/ims-bearings)
- [MIMII DUE](https://doi.org/10.5281/zenodo.4740355)

## Running this repository

See the main [README](README.md) for installation, download scripts, environment settings, startup commands and reproducibility notes. The large NASA and MIMII datasets are downloaded separately.

---


