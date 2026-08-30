import csv

# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pytest

from training.feature_matrix import (
    FEATURE_COLUMNS,
    rows_to_matrix,
)


def make_row(target=1):

    row = {}

    for feature in FEATURE_COLUMNS:
        row[feature] = "1.0"

    row["target"] = str(target)

    return row


def test_rows_to_matrix_shape():

    rows = [
        make_row(1),
        make_row(0),
        make_row(1),
    ]

    X, y = rows_to_matrix(rows)

    assert X.shape == (3, 15)
    assert y.shape == (3,)


def test_features_are_numeric():

    rows = [
        make_row(1),
    ]

    X, y = rows_to_matrix(rows)

    assert X.dtype == float
    assert y.dtype == int


def test_targets_are_correct():

    rows = [
        make_row(1),
        make_row(0),
        make_row(1),
    ]

    X, y = rows_to_matrix(rows)

    assert np.array_equal(
        y,
        np.array([1, 0, 1]),
    )


def test_feature_order_is_stable():

    rows = [
        make_row(1),
    ]

    rows[0]["cuisine_match"] = "10.0"
    rows[0]["protein_match"] = "20.0"

    X, _ = rows_to_matrix(rows)

    assert X[0][0] == 10.0
    assert X[0][1] == 20.0


def test_empty_rows_rejected():

    with pytest.raises(ValueError):

        rows_to_matrix([])