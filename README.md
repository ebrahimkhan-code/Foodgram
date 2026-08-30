# Member 1 Recommender System

A personalized food recommendation system built from scratch using **Taste DNA**, historical user behavior, contextual features, candidate generation, and a trained **Logistic Regression** model.

The system learns a user's food preferences and uses them to rank food items by predicted interaction probability.

---

## Overview

The recommender follows this pipeline:

```text
User Taste DNA
       ↓
Candidate Generation
       ↓
Taste + History + Context Features
       ↓
Logistic Regression
       ↓
Recommendation Score
       ↓
Ranked Recommendations
       ↓
User Interaction
       ↓
Taste DNA Update
       ↓
Updated Recommendations
```

The system is designed as a standalone recommender implementation and currently uses synthetic food, user, and interaction data for development and testing.

---

## Main Components

### 1. Taste DNA

Taste DNA represents a user's food preferences across six attributes:

* Cuisine
* Protein
* Flavor
* Spice level
* Base
* Meal type

Preference strengths are represented numerically between:

```text
-1.0 → dislike
 0.0 → neutral
+1.0 → strong preference
```

Taste DNA can be:

* generated from initial preference answers
* loaded from stored data
* updated after user interactions
* persisted for later use

---

### 2. Candidate Generation

The candidate-generation layer identifies foods that are similar to the user's Taste DNA.

Location:

```text
candidate_generation/
├── generator.py
└── similarity.py
```

Candidate similarity is calculated using the six Taste DNA attributes and cosine similarity.

The generator returns candidates sorted by similarity score.

---

### 3. Recommendation Features

Each food is converted into the numerical features expected by the trained ML model.

The model currently uses 15 features:

```text
cuisine_match
protein_match
flavor_match
spice_level_match
base_match
meal_type_match
taste_match_score

previous_likes
previous_dislikes
previous_saves
previous_skips
previous_interactions
days_since_previous_interaction

hour
day_of_week
```

These combine:

* Taste DNA preferences
* historical behavior
* recommendation-time context

---

### 4. User History

Historical interactions are converted into behavioral features.

Supported interaction types:

```text
like
dislike
save
skip
```

The system tracks:

```text
previous_likes
previous_dislikes
previous_saves
previous_skips
previous_interactions
days_since_previous_interaction
```

Historical features are built using interactions that occurred before the relevant recommendation timestamp.

---

### 5. Machine Learning Model

The recommendation model is a trained **Logistic Regression classifier**.

Model artifact:

```text
models/logistic_regression.pkl
```

The model receives the 15 numerical features and produces a probability-like recommendation score.

Foods are sorted by this score to produce the final recommendation ranking.

---

### 6. Adaptive Taste DNA

Taste DNA can change based on user interactions.

Current update strengths:

| Interaction | Update |
| ----------- | -----: |
| Like        |  +0.10 |
| Save        |  +0.15 |
| Dislike     |  -0.15 |
| Skip        |  -0.05 |

Updates are applied to the food's:

```text
cuisine
protein
flavor
spice_level
base
meal_type
```

Preference values are clamped to:

```text
[-1.0, 1.0]
```

This allows the recommender to adapt as the user interacts with more foods.

---

## Project Structure

```text
member1_recommender/

├── candidate_generation/          # Candidate generation and similarity
│   ├── generator.py
│   ├── similarity.py
│   └── __init__.py
│
├── data/                          # Synthetic development data
│   └── synthetic/
│       ├── foods.csv
│       ├── interactions.csv
│       ├── users.csv
│       ├── user_preferences.csv
│       ├── generate_data.py
│       ├── train.csv
│       ├── validation.csv
│       ├── test.csv
│       └── training_dataset.csv
│
├── features/                      # Food feature utilities
│   ├── food_features.py
│   └── __init__.py
│
├── models/                        # Trained model
│   └── logistic_regression.pkl
│
├── recommendation/                # Runtime recommendation system
│   ├── demo.py
│   ├── engine.py
│   ├── feature_builder.py
│   ├── history.py
│   ├── pipeline.py
│   ├── scorer.py
│   ├── user_features.py
│   └── __init__.py
│
├── taste_dna/                     # Taste DNA system
│   ├── generator.py
│   ├── loader.py
│   ├── persistence.py
│   ├── schema.py
│   ├── synthetic_loader.py
│   ├── updater.py
│   └── __init__.py
│
├── training/                      # Model training and evaluation
│   ├── baseline_model.py
│   ├── create_splits.py
│   ├── dataset_builder.py
│   ├── feature_matrix.py
│   ├── history_features.py
│   ├── model_loader.py
│   ├── save_model.py
│   ├── split_dataset.py
│   ├── target.py
│   ├── tune_logistic.py
│   ├── validate_dataset.py
│   └── additional inspection/debug utilities
│
├── tests/                         # Automated test suite
│
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd member1_recommender
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Python 3.13 has been used successfully during development.

---

## Running the Recommendation Demo

The demo uses the synthetic food catalog and synthetic user data.

Run:

```bash
python -m recommendation.demo
```

The default user is:

```text
U001
```

To specify another user:

```bash
python -m recommendation.demo U002
```

Example output:

```text
Food Recommendations
====================

User: U001

User History
------------
Likes:        21
Dislikes:     24
Saves:        17
Skips:        26
Interactions: 90

 1. Food 29                   0.9284
 2. Food 1                    0.8601
 3. Food 6                    0.8601
 ...
```

---

## Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

The current implementation passes:

```text
126 tests
```

The Taste DNA integration suite also verifies the complete adaptive recommendation cycle:

```bash
python -m pytest tests/test_taste_dna_integration.py -v
```

Current result:

```text
8 passed
```

---

## Training Pipeline

The `training/` directory contains the utilities used to construct training data, create train/validation/test splits, train the model, evaluate it, and save the trained model.

The training data combines:

```text
User
+ Food
+ Taste DNA
+ Historical Behavior
+ Context
+ Interaction Target
```

The resulting features are used to train the Logistic Regression recommendation model.

---

## Recommendation Pipeline

The runtime recommendation pipeline is implemented in:

```text
recommendation/pipeline.py
```

For each food:

```text
Food
 ↓
Taste DNA matching
 ↓
Historical features
 ↓
Context features
 ↓
15-feature vector
 ↓
Logistic Regression
 ↓
Recommendation score
```

The highest-scoring foods are returned as the final recommendations.

---

## Adaptive Learning

The system supports continuous preference updates.

For example:

```text
User likes Chicken Biryani
        ↓
Chicken Biryani attributes identified
        ↓
Taste DNA updated
        ↓
Chicken / Pakistani / Savory / etc. preferences increase
        ↓
Future matching foods receive stronger preference signals
```

Similarly, dislikes and skips provide negative signals.

This allows recommendations to evolve as user behavior changes.

---

## Current Validation

The current implementation has been validated through:

```text
126/126 automated tests       PASS
8/8 Taste DNA integration     PASS
End-to-end U001 demo          PASS
End-to-end U002 demo          PASS
Taste DNA updates             PASS
History features              PASS
Candidate ranking             PASS
Recommendation ranking        PASS
Model loading                 PASS
```

The model's previously evaluated metrics include:

```text
Validation ROC-AUC: 0.6690
Test ROC-AUC:       0.7415
```

These metrics describe the current synthetic-data baseline and should not be interpreted as production performance on real-world food recommendation data.

---

## Development Notes

The current food catalog is synthetic and contains placeholder food names such as:

```text
Food 1
Food 2
...
Food 100
```

The architecture is intentionally separated into:

```text
Taste DNA
Candidate Generation
Feature Engineering
History
Model Scoring
Ranking
```

This makes individual components independently testable and allows the synthetic data to be replaced later with real food/menu data without rewriting the entire recommendation pipeline.

---

## Status

**Core standalone recommender implementation: Complete**

The system currently provides:

* Personalized Taste DNA
* Candidate generation
* Historical behavior modeling
* Context-aware features
* Logistic Regression scoring
* Recommendation ranking
* Adaptive Taste DNA updates
* Persistent model artifact
* Automated test coverage
* End-to-end recommendation demo
