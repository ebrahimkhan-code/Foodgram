from pathlib import Path

# pyrefly: ignore [missing-import]
import numpy as np
from sklearn.linear_model import LogisticRegression

from training.feature_matrix import (
    load_feature_matrices,
)


BASE_DIR = Path(__file__).parent.parent

TRAIN_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "train.csv"
)

VALIDATION_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "validation.csv"
)

TEST_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "test.csv"
)


def describe_predictions(name, probabilities):

    print()
    print(name)
    print("=" * len(name))

    print(
        f"min:    {np.min(probabilities):.6f}"
    )
    print(
        f"max:    {np.max(probabilities):.6f}"
    )
    print(
        f"mean:   {np.mean(probabilities):.6f}"
    )
    print(
        f"median: {np.median(probabilities):.6f}"
    )

    print()

    for threshold in [
        0.50,
        0.70,
        0.80,
        0.90,
        0.95,
        0.99,
    ]:

        percentage = (
            np.mean(
                probabilities >= threshold
            )
            * 100
        )

        print(
            f">= {threshold:.2f}: "
            f"{percentage:.2f}%"
        )


def main():

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    ) = load_feature_matrices(
        TRAIN_PATH,
        VALIDATION_PATH,
        TEST_PATH,
    )

    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    train_probabilities = (
        model.predict_proba(X_train)[:, 1]
    )

    validation_probabilities = (
        model.predict_proba(X_validation)[:, 1]
    )

    test_probabilities = (
        model.predict_proba(X_test)[:, 1]
    )

    describe_predictions(
        "Training Predictions",
        train_probabilities,
    )

    describe_predictions(
        "Validation Predictions",
        validation_probabilities,
    )

    describe_predictions(
        "Test Predictions",
        test_probabilities,
    )


if __name__ == "__main__":
    main()