# pyrefly: ignore [missing-import]
import numpy as np

from training.model_loader import (
    load_model,
    predict_probability,
)


def test_model_can_be_loaded():

    model = load_model()

    assert model is not None
    assert hasattr(model, "predict_proba")


def test_model_has_expected_feature_count():

    model = load_model()

    assert model.n_features_in_ == 15


def test_model_probability_is_valid():

    model = load_model()

    features = np.zeros(15)

    probability = predict_probability(
        model,
        features,
    )

    assert 0.0 <= probability <= 1.0