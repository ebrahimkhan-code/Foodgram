import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INPUT = BASE_DIR / "menu_dataset_enriched_claude_FINAL.csv"
OUTPUT = INPUT

df = pd.read_csv(INPUT)

def unknown(v):
    return pd.isna(v) or str(v).strip().lower() in ("", "unknown")

def text(row):
    return f"{row['name']} {row['description']} {row['category']}".lower()

for i, row in df.iterrows():
    t = text(row)
    name = str(row["name"]).lower()

    # -------------------------
    # PROTEIN
    # -------------------------
    if unknown(row["protein"]):
        if "chicken" in t:
            df.at[i, "protein"] = "chicken"
        elif "beef" in t:
            df.at[i, "protein"] = "beef"
        elif "mutton" in t:
            df.at[i, "protein"] = "mutton"
        elif "lamb" in t:
            df.at[i, "protein"] = "lamb"
        elif "prawn" in t:
            df.at[i, "protein"] = "prawns"
        elif "fish" in t:
            df.at[i, "protein"] = "fish"
        elif "seafood" in t:
            df.at[i, "protein"] = "seafood"
        elif any(x in t for x in ["vegetarian", "vegan"]):
            df.at[i, "protein"] = "vegetarian"

    # mixed protein
    if "chicken" in t and "beef" in t:
        df.at[i, "protein"] = "mixed"

    # -------------------------
    # CUISINE
    # -------------------------
    if unknown(row["cuisine"]):
        if any(x in t for x in ["karaage", "sushi", "ramen", "teriyaki"]):
            df.at[i, "cuisine"] = "japanese"
        elif any(x in t for x in ["biryani", "nihari", "tikka", "kebab",
                                   "kabob", "paratha", "naan", "pulao"]):
            df.at[i, "cuisine"] = "pakistani"
        elif any(x in t for x in ["pasta", "lasagna", "fettuccine",
                                   "alfredo", "penne", "pesto"]):
            df.at[i, "cuisine"] = "italian"
        elif any(x in t for x in ["shawarma", "gyro", "hummus",
                                   "falafel", "fattoush"]):
            df.at[i, "cuisine"] = "middle eastern"
        elif any(x in t for x in ["noodle", "chow mein", "manchurian"]):
            df.at[i, "cuisine"] = "chinese"
        elif any(x in t for x in ["taco", "burrito", "quesadilla"]):
            df.at[i, "cuisine"] = "mexican"
        elif "thai" in t:
            df.at[i, "cuisine"] = "thai"
        elif "burger" in t:
            df.at[i, "cuisine"] = "american"

    # -------------------------
    # FLAVOR
    # -------------------------
    if unknown(row["flavor"]):
        if any(x in t for x in ["sour", "lemon", "tamarind"]):
            df.at[i, "flavor"] = "sour"
        elif any(x in t for x in ["savory", "seasoned", "garlic"]):
            df.at[i, "flavor"] = "savory"
        elif any(x in t for x in ["smoky", "smoked", "charcoal"]):
            df.at[i, "flavor"] = "smoky"
        elif any(x in t for x in ["creamy", "cream", "alfredo"]):
            df.at[i, "flavor"] = "creamy"
        elif any(x in t for x in ["spicy", "chili", "chilli"]):
            df.at[i, "flavor"] = "spicy"
        elif any(x in t for x in ["sweet", "sugar", "chocolate"]):
            df.at[i, "flavor"] = "sweet"
        elif any(x in t for x in ["fresh", "salad", "herb"]):
            df.at[i, "flavor"] = "fresh"

    # -------------------------
    # BASE
    # -------------------------
    if unknown(row["base"]):
        if any(x in t for x in ["pasta", "lasagna", "fettuccine", "penne"]):
            df.at[i, "base"] = "pasta"
        elif any(x in t for x in ["rice", "biryani", "pulao", "mandi"]):
            df.at[i, "base"] = "rice"
        elif any(x in t for x in ["naan"]):
            df.at[i, "base"] = "naan"
        elif any(x in t for x in ["roti", "chapati"]):
            df.at[i, "base"] = "roti"
        elif any(x in t for x in ["paratha"]):
            df.at[i, "base"] = "paratha"
        elif any(x in t for x in ["bread", "pita", "toast"]):
            df.at[i, "base"] = "bread"
        elif any(x in t for x in ["wrap", "shawarma", "gyro"]):
            df.at[i, "base"] = "wrap"
        elif any(x in t for x in ["noodle", "chow mein"]):
            df.at[i, "base"] = "noodles"
        elif any(x in t for x in ["burger"]):
            df.at[i, "base"] = "burger_bun"
        elif any(x in t for x in ["salad", "greens"]):
            df.at[i, "base"] = "salad"
        elif any(x in t for x in ["potato", "fries"]):
            df.at[i, "base"] = "potato"

df.to_csv(OUTPUT, index=False)

print("Updated:", OUTPUT)
print("Rows:", len(df))

for col in ["cuisine", "protein", "flavor", "base"]:
    unknown_count = df[col].fillna("").astype(str).str.strip().str.lower().isin(
        ["", "unknown"]
    ).sum()
    print(f"{col}: {unknown_count} unknown")