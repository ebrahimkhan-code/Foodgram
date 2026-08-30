from pathlib import Path

from sklearn.linear_model import LogisticRegression

from training.feature_matrix import (
    FEATURE_COLUMNS,
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


def main():

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        _,
        _,
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

    print()
    print("Model Feature Importance")
    print("========================")
    print()

    coefficients = model.coef_[0]

    feature_importance = sorted(
        zip(FEATURE_COLUMNS, coefficients),
        key=lambda item: abs(item[1]),
        reverse=True,
    )

    for feature, coefficient in feature_importance:
        print(
            f"{feature:<40} "
            f"{coefficient:>10.6f}"
        )

    print()
    print("Feature Ranges")
    print("==============")
    print()

    for index, feature in enumerate(FEATURE_COLUMNS):

        values = X_train[:, index]

        print(
            f"{feature:<40} "
            f"min={values.min():>8.3f} "
            f"max={values.max():>8.3f}"
        )


if __name__ == "__main__":
    main()