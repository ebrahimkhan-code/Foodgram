import pandas as pd

CSV_PATH = "../menu_dataset_enriched_claude_FINAL.csv"

df = pd.read_csv(CSV_PATH)


def is_unknown(column):
    return (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["unknown", ""])
    )


columns = [
    "cuisine",
    "protein",
    "flavor",
    "base",
]


for column in columns:

    unknown = is_unknown(column)

    print()
    print("=" * 90)
    print(f"{column.upper()} — SAMPLE UNKNOWN VALUES")
    print("=" * 90)

    sample = df.loc[
        unknown,
        [
            "name",
            "description",
            "category",
            "dish_type",
            "food_type",
            "semantic_text",
        ],
    ].head(15)

    for index, row in sample.iterrows():

        print()
        print(f"NAME:        {row['name']}")
        print(f"CATEGORY:    {row['category']}")
        print(f"DISH TYPE:   {row['dish_type']}")
        print(f"FOOD TYPE:   {row['food_type']}")
        print(f"DESCRIPTION: {row['description']}")
        print(f"SEMANTIC:    {row['semantic_text']}")