from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

from training.feature_matrix import load_feature_matrices


BASE_DIR = Path(__file__).parent.parent

TRAIN_PATH = BASE_DIR / "data" / "synthetic" / "train.csv"
VALIDATION_PATH = BASE_DIR / "data" / "synthetic" / "validation.csv"
TEST_PATH = BASE_DIR / "data" / "synthetic" / "test.csv"


def evaluate_model(model, X, y):
    """Calculate classification metrics for a trained model."""

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    return {
        "accuracy": accuracy_score(y, predictions),
        "precision": precision_score(y, predictions, zero_division=0),
        "recall": recall_score(y, predictions, zero_division=0),
        "f1": f1_score(y, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y, probabilities),
    }


def print_results(title, results):
    print()
    print(title)
    print("=" * len(title))
    print(f"Accuracy:  {results['accuracy']:.4f}")
    print(f"Precision: {results['precision']:.4f}")
    print(f"Recall:    {results['recall']:.4f}")
    print(f"F1:        {results['f1']:.4f}")
    print(f"ROC-AUC:   {results['roc_auc']:.4f}")


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

    # Best configuration selected using validation data.
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=42,
    )

    print("Training tuned Logistic Regression...")

    model.fit(
        X_train,
        y_train,
    )

    validation_results = evaluate_model(
        model,
        X_validation,
        y_validation,
    )

    test_results = evaluate_model(
        model,
        X_test,
        y_test,
    )

    print_results(
        "Validation Results",
        validation_results,
    )

    print_results(
        "Test Results",
        test_results,
    )


if __name__ == "__main__":
    main()