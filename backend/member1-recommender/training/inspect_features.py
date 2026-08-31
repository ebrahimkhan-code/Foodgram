from pathlib import Path

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

    print("Feature matrix inspection")
    print()
    print(f"X_train:       {X_train.shape}")
    print(f"y_train:       {y_train.shape}")
    print(f"X_validation:  {X_validation.shape}")
    print(f"y_validation:  {y_validation.shape}")
    print(f"X_test:        {X_test.shape}")
    print(f"y_test:        {y_test.shape}")
    print()
    print(f"Training feature count: {X_train.shape[1]}")
    print(f"Training samples:       {X_train.shape[0]}")


if __name__ == "__main__":
    main()