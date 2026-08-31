from pathlib import Path

# pyrefly: ignore [missing-import]
from xgboost import XGBClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

from training.feature_matrix import load_feature_matrices


BASE_DIR = Path(__file__).parent.parent

DATA_DIR = (
    BASE_DIR
    / "data"
    / "synthetic"
)


def evaluate_model(
    model,
    X,
    y,
    name,
):
    predictions = model.predict(X)

    probabilities = model.predict_proba(X)[:, 1]

    print()
    print(name)
    print("=" * len(name))

    print(
        f"Accuracy:  "
        f"{accuracy_score(y, predictions):.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y, predictions):.4f}"
    )

    print(
        f"Recall:    "
        f"{recall_score(y, predictions):.4f}"
    )

    print(
        f"F1:        "
        f"{f1_score(y, predictions):.4f}"
    )

    print(
        f"ROC-AUC:   "
        f"{roc_auc_score(y, probabilities):.4f}"
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

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )

    print("Training XGBoost...")

    model.fit(
        X_train,
        y_train,
    )

    print()
    print("Feature Importance")
    print("==================")

    from training.feature_matrix import FEATURE_COLUMNS

    for feature, importance in sorted(
        zip(
           FEATURE_COLUMNS,
           model.feature_importances_,
        ),
        key=lambda x: x[1],
        reverse=True,
    ):
        print(
        f"{feature:35s} {importance:.4f}")

    evaluate_model(
        model,
        X_validation,
        y_validation,
        "Validation Results",
    )

    evaluate_model(
        model,
        X_test,
        y_test,
        "Test Results",
    )


if __name__ == "__main__":
    main()