import csv
from pathlib import Path

from training.split_dataset import split_by_user_time


BASE_DIR = Path(__file__).parent.parent

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "synthetic"
    / "training_dataset.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "synthetic"
)


def load_rows():

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        return list(reader), reader.fieldnames


def save_rows(
    path,
    rows,
    fieldnames,
):

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def main():

    rows, fieldnames = load_rows()

    train, validation, test = split_by_user_time(
        rows,
        train_ratio=0.70,
        validation_ratio=0.15,
    )

    save_rows(
        OUTPUT_DIR / "train.csv",
        train,
        fieldnames,
    )

    save_rows(
        OUTPUT_DIR / "validation.csv",
        validation,
        fieldnames,
    )

    save_rows(
        OUTPUT_DIR / "test.csv",
        test,
        fieldnames,
    )

    print("Dataset split successfully.")
    print()
    print(f"Total:      {len(rows)}")
    print(f"Train:      {len(train)}")
    print(f"Validation: {len(validation)}")
    print(f"Test:       {len(test)}")


if __name__ == "__main__":
    main()