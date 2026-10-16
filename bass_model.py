#!/usr/bin/env python3
"""Fit a Bass model to smart-speaker ownership and forecast Lotus Ring adoption."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "smart_speaker_data.csv"
IMG_DIR = ROOT / "img"

PURPLE = "#6D28D9"
PURPLE_DARK = "#4C1D95"
PURPLE_LIGHT = "#A78BFA"
GRAY = "#6B7280"
GRID = "#E5E7EB"


def bass_cumulative(t: float, p: float, q: float, market: float) -> float:
    """Return cumulative adoption at time t."""
    exp_term = math.exp(-(p + q) * t)
    return market * (1 - exp_term) / (1 + (q / p) * exp_term)


def fit_bass(times: list[float], observed: list[float]) -> tuple[float, float, float]:
    """Estimate p, q, and M with a small deterministic coordinate search."""
    params = [0.03, 0.70, 37.0]
    steps = [0.02, 0.30, 10.0]

    def loss(values: list[float]) -> float:
        p, q, market = values
        if p <= 0 or q <= 0 or market < max(observed) or market > 100:
            return float("inf")
        return sum(
            (bass_cumulative(t, p, q, market) - actual) ** 2
            for t, actual in zip(times, observed)
        )

    for _ in range(10000):
        current_loss = loss(params)
        improved = False
        for index in range(3):
            for direction in (-1, 1):
                candidate = params.copy()
                candidate[index] += direction * steps[index]
                candidate_loss = loss(candidate)
                if candidate_loss < current_loss:
                    params = candidate
                    current_loss = candidate_loss
                    improved = True
        if not improved:
            steps = [step / 2 for step in steps]
            if max(steps) < 1e-10:
                break
    return tuple(params)


def make_chart(
    path: Path,
    title: str,
    x_values: list[float],
    series: list[tuple[str, list[float], str, bool]],
    y_max: float,
    y_label: str,
) -> None:
    """Create one minimal purple line chart."""
    width, height = 900, 480
    left, right, bottom, top = 85, 35, 65, 62
    plot_width = width - left - right
    plot_height = height - bottom - top
    image = Image.new("RGB", (width, height), "#FFFFFF")
    drawing = ImageDraw.Draw(image)

    try:
        regular = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
        bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20, index=1)
    except OSError:
        regular = small = bold = ImageFont.load_default()

    drawing.text((left, 18), title, font=bold, fill=PURPLE_DARK)
    drawing.text((left, height - 28), "Year", font=regular, fill=GRAY)
    drawing.text((8, 12), y_label, font=small, fill=GRAY)

    x_min, x_max = min(x_values), max(x_values)

    def scale_x(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * plot_width

    def scale_y(value: float) -> float:
        return height - bottom - value / y_max * plot_height

    for step in range(6):
        value = y_max * step / 5
        y = scale_y(value)
        drawing.line((left, y, width - right, y), fill=GRID, width=1)
        drawing.text((left - 42, y - 7), f"{value:.0f}", font=small, fill=GRAY)

    chart_bottom = height - bottom
    drawing.line((left, top, left, chart_bottom), fill=GRAY, width=1)
    drawing.line((left, chart_bottom, width - right, chart_bottom), fill=GRAY, width=1)

    for year in x_values:
        x = scale_x(year)
        drawing.line((x, chart_bottom, x, chart_bottom + 5), fill=GRAY, width=1)
        drawing.text((x - 15, chart_bottom + 8), str(int(year)), font=small, fill=GRAY)

    legend_x = width - right - 250
    legend_y = 48
    for name, values, color, points in series:
        coordinates = [
            (scale_x(x_value), scale_y(y_value))
            for x_value, y_value in zip(x_values, values)
        ]
        drawing.line(coordinates, fill=color, width=4, joint="curve")
        if points:
            for x_value, y_value in zip(x_values, values):
                x, y = scale_x(x_value), scale_y(y_value)
                drawing.ellipse(
                    (x - 5, y - 5, x + 5, y + 5),
                    fill="#FFFFFF",
                    outline=color,
                    width=3,
                )
        drawing.line((legend_x, legend_y, legend_x + 24, legend_y), fill=color, width=4)
        drawing.text((legend_x + 32, legend_y - 7), name, font=small, fill=GRAY)
        legend_x += 125

    image.save(path, format="PNG", dpi=(140, 140))


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    years = [int(row["year"]) for row in rows]
    times = [float(row["years_since_2014_launch"]) for row in rows]
    ownership = [float(row["us_population_12plus_owning_percent"]) for row in rows]

    p, q, market_percent = fit_bass(times, ownership)
    fitted = [bass_cumulative(t, p, q, market_percent) for t in times]
    rmse = math.sqrt(
        sum((actual - estimate) ** 2 for actual, estimate in zip(ownership, fitted))
        / len(ownership)
    )
    average = sum(ownership) / len(ownership)
    r_squared = 1 - (
        sum((actual - estimate) ** 2 for actual, estimate in zip(ownership, fitted))
        / sum((actual - average) ** 2 for actual in ownership)
    )

    lotus_market = 8.0
    forecast_years = list(range(2026, 2038))
    cumulative: list[float] = []
    annual: list[float] = []
    previous = 0.0
    for year in forecast_years:
        total = bass_cumulative(year - 2025, p, q, lotus_market)
        cumulative.append(total)
        annual.append(total - previous)
        previous = total

    make_chart(
        IMG_DIR / "bass_model_fit.png",
        "U.S. smart-speaker ownership: observed and Bass fit",
        years,
        [
            ("Observed", ownership, PURPLE_DARK, True),
            ("Bass fit", fitted, PURPLE_LIGHT, False),
        ],
        40,
        "Ownership (%)",
    )
    make_chart(
        IMG_DIR / "lotus_ring_forecast.png",
        "Lotus Ring base-case diffusion in the United States",
        forecast_years,
        [
            ("Cumulative", cumulative, PURPLE_DARK, False),
            ("New each year", annual, PURPLE_LIGHT, True),
        ],
        8.5,
        "Adopters (millions)",
    )

    print(f"p = {p:.4f}")
    print(f"q = {q:.4f}")
    print(f"Smart-speaker M = {market_percent:.2f}%")
    print(f"RMSE = {rmse:.2f} percentage points")
    print(f"R-squared = {r_squared:.3f}")
    print(f"Lotus cumulative adoption in 2030 = {cumulative[4]:.3f} million")
    print(f"Peak annual adoption year = {forecast_years[annual.index(max(annual))]}")


if __name__ == "__main__":
    main()
