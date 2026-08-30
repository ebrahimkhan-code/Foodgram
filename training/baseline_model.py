from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from training.feature_matrix import load_feature_matrices


BASE_DIR = Path(__file__).parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "synthetic"
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
        DATA_DIR / "train.csv",
        DATA_DIR / "validation.csv",
        DATA_DIR / "test.csv",
    )

    # --------------------------------------------------------
    # Scale using TRAINING data only.
    # --------------------------------------------------------

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_validation_scaled = scaler.transform(
        X_validation
    )

    X_test_scaled = scaler.transform(
        X_test
    )

    # --------------------------------------------------------
    # Train baseline.
    # --------------------------------------------------------

    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
    )

    model.fit(
        X_train_scaled,
        y_train,
    )

    # --------------------------------------------------------
    # Validation evaluation.
    # --------------------------------------------------------

    validation_predictions = model.predict(
        X_validation_scaled
    )

    validation_probabilities = (
        model.predict_proba(
            X_validation_scaled
        )[:, 1]
    )

    print("Validation Results")
    print("==================")

    print(
        f"Accuracy:  "
        f"{accuracy_score(y_validation, validation_predictions):.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_validation, validation_predictions):.4f}"
    )

    print(
        f"Recall:    "
        f"{recall_score(y_validation, validation_predictions):.4f}"
    )

    print(
        f"F1:        "
        f"{f1_score(y_validation, validation_predictions):.4f}"
    )

    print(
        f"ROC-AUC:   "
        f"{roc_auc_score(y_validation, validation_probabilities):.4f}"
    )

    # --------------------------------------------------------
    # Test evaluation.
    # --------------------------------------------------------

    test_predictions = model.predict(
        X_test_scaled
    )

    test_probabilities = (
        model.predict_proba(
            X_test_scaled
        )[:, 1]
    )

    print()
    print("Test Results")
    print("============")

    print(
        f"Accuracy:  "
        f"{accuracy_score(y_test, test_predictions):.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_test, test_predictions):.4f}"
    )

    print(
        f"Recall:    "
        f"{recall_score(y_test, test_predictions):.4f}"
    )

    print(
        f"F1:        "
        f"{f1_score(y_test, test_predictions):.4f}"
    )

    print(
        f"ROC-AUC:   "
        f"{roc_auc_score(y_test, test_probabilities):.4f}"
    )


if __name__ == "__main__":
    main()