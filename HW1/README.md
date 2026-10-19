# Lotus Ring Bass Model

This folder contains the files for my Bass model homework on the Lotus Ring.

## Files

- `report/report.pdf` - final written report
- `report/report_source.md` - editable report text
- `bass_model.py` - fits the Bass model and creates the two charts
- `Lotus_Ring_Bass_Model.xlsx` - model calculations, forecast, sources, and an editable chart
- `data/smart_speaker_data.csv` - historical U.S. smart-speaker ownership data
- `img/bass_model_fit.png` - observed smart-speaker ownership and fitted Bass curve
- `img/lotus_ring_forecast.png` - Lotus Ring annual and cumulative adoption forecast
- `references/references.md` - full source list

## How to run the model

Open a terminal in this folder and run:

```bash
python3 -m pip install pillow
python3 bass_model.py
```

The script reads `data/smart_speaker_data.csv`, estimates the Bass parameters, prints the results, and recreates both files in `img/`.

## Main assumptions

- Historical comparison: U.S. smart-speaker ownership, 2017-2023
- Smart-speaker launch year used for timing: 2014
- Lotus Ring U.S. market potential: 8.0 million adopters
- Lotus Ring forecast begins in 2026

The Lotus Ring market size is a Fermi estimate, so the forecast should be read as a scenario rather than a precise sales target.
