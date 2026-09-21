"""Smoke tests using a known historical row from the supplied dataset."""

from datetime import date
from pathlib import Path

import numpy as np

from predictor import FEATURES, build_feature_row, load_assets, make_forecast_context, predict, retrieve_inputs_for_crop


BASE = Path(__file__).resolve().parent


def main() -> None:
    assets = load_assets(BASE)
    assert len(assets["crops"]) > 0
    assert list(assets["model"].feature_names_in_) == FEATURES

    # This is the first known historical row in 04_final_modelling_dataset.csv.
    context = make_forecast_context(date(2012, 4, 15))
    assert context.season == "Yala"
    assert context.forecast_date == np.datetime64("2012-04-01")
    retrieved = retrieve_inputs_for_crop(context, "Luffa", assets)
    row = build_feature_row("Luffa", context, retrieved)
    assert list(row.columns) == FEATURES
    assert retrieved.weather_source.startswith("Exact historical 2012 Yala")
    known = assets["modelling"].query("Crop == 'Luffa' and Season == 'Yala' and Year == 2012").iloc[0]
    for feature in FEATURES:
        if feature in {"Crop", "Season"}:
            assert row.iloc[0][feature] == known[feature], feature
        else:
            assert np.isclose(float(row.iloc[0][feature]), float(known[feature])), feature
    result = predict(row, assets)
    assert set(result) == {"Yield_t_ha", "NextMonthWholesalePrice_RsKg"}
    assert all(np.isfinite(value) for value in result.values())
    print("PASS: model loaded, exact nine-feature row built, and known historical row predicted.")


if __name__ == "__main__":
    main()
