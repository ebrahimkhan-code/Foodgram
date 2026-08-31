from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from training.feature_matrix import load_feature_matrices


BASE_DIR = Path(__file__).parent.parent

TRAIN_PATH = BASE_DIR / "data" / "synthetic" / "train.csv"
VALIDATION_PATH = BASE_DIR / "data" / "synthetic" / "validation.csv"
TEST_PATH = BASE_DIR / "data" / "synthetic" / "test.csv"


C_VALUES = [
    0.01,
    0.03,
    0.1,
    0.3,
    1.0,
    3.0,
    10.0,
]


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

    results = []

    print("Logistic Regression tuning")
    print("==========================")

    for c in C_VALUES:

        model = LogisticRegression(
            C=c,
            max_iter=1000,
            random_state=42,
        )

        model.fit(
            X_train,
            y_train,
        )

        validation_probability = model.predict_proba(
            X_validation
        )[:, 1]

        auc = roc_auc_score(
            y_validation,
            validation_probability,
        )

        results.append(
            {
                "C": c,
                "roc_auc": auc,
            }
        )

        print(
            f"C={c:<5} "
            f"Validation ROC-AUC={auc:.4f}"
        )

    best = max(
        results,
        key=lambda result: result["roc_auc"],
    )

    print()
    print("Best configuration")
    print("===================")
    print(f"C:        {best['C']}")
    print(f"ROC-AUC:  {best['roc_auc']:.4f}")


if __name__ == "__main__":
    main()