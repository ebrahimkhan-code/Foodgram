from pathlib import Path
import pickle

from sklearn.linear_model import LogisticRegression


BASE_DIR = Path(__file__).parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "logistic_regression.pkl"
)


def load_model() -> LogisticRegression:
    """
    Load the trained Logistic Regression model.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    with open(MODEL_PATH, "rb") as file:
        model = pickle.load(file)

    if not isinstance(model, LogisticRegression):
        raise TypeError(
            "Saved model is not a LogisticRegression model."
        )

    return model


def predict_probability(
    model: LogisticRegression,
    features,
) -> float:
    """
    Return probability that a food interaction
    will be positive.
    """

    probability = model.predict_proba(
        [features]
    )[0][1]

    return float(probability)