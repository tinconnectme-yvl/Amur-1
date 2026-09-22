"""
Unit tests for the official competition metric calculation.
"""
import pytest
import pandas as pd
import numpy as np
from evaluate_submission import evaluate

def test_metric_calculation():
    # Run evaluation on the generated submission.csv
    score = evaluate("submission.csv", "data/hydrowatch_amur")
    # Must be between 0.90 and 1.00
    assert 0.90 <= score <= 1.00
    print(f"Verified metric Score = {score:.4f}")

def test_empty_submission():
    # Test penalty on empty/missing pairs
    dummy_df = pd.DataFrame([{
        "pair_id": "flood_2019_07_amur__belogorsk",
        "flood_ha": 0.0,
        "water_pre_ha": 0.0,
        "water_peak_ha": 0.0
    }])
    dummy_path = "test_empty.csv"
    dummy_df.to_csv(dummy_path, index=False)
    score = evaluate(dummy_path, "data/hydrowatch_amur")
    assert score < 0.3 # Severe penalty for zeros/missing
    import os
    if os.path.exists(dummy_path):
        os.remove(dummy_path)
