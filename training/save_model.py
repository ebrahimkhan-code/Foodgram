from pathlib import Path
import pickle

from sklearn.linear_model import LogisticRegression

from training.feature_matrix import load_feature_matrices


BASE_DIR = Path(__file__).parent.parent

TRAIN_PATH = BASE_DIR / "data" / "synthetic" / "train.csv"
VALIDATION_PATH = BASE_DIR / "data" / "synthetic" / "validation.csv"
TEST_PATH = BASE_DIR / "data" / "synthetic" / "test.csv"

MODEL_PATH = BASE_DIR / "models" / "logistic_regression.pkl"


def main():

    (
        X_train,
        y_train,
        _,
        _,
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

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(model, file)

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Features: {X_train.shape[1]}")
    print(f"Training samples: {X_train.shape[0]}")


if __name__ == "__main__":
    main()