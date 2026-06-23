"""
Lead Scoring ML Model
Uses a simple Random Forest trained on synthetic features.
In production: retrain on your actual CRM data (won leads vs lost).
"""
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler

MODEL_PATH = os.getenv("MODEL_PATH", "ml/model.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "ml/scaler.pkl")

FEATURE_ORDER = [
    "has_company",
    "has_title",
    "skills_count",
    "has_summary",
    "has_news",
    "has_jobs",
]


def train_and_save():
    """Train on synthetic data and save model. Run once on startup if model missing."""
    np.random.seed(42)
    n = 500

    X = np.column_stack([
        np.random.randint(0, 2, n),          # has_company
        np.random.randint(0, 2, n),          # has_title
        np.random.randint(0, 15, n),         # skills_count
        np.random.randint(0, 2, n),          # has_summary
        np.random.randint(0, 2, n),          # has_news
        np.random.randint(0, 2, n),          # has_jobs
    ])

    # Synthetic label: higher score = better lead
    y = (
        X[:, 0] * 0.3 +
        X[:, 1] * 0.2 +
        (X[:, 2] / 15) * 0.2 +
        X[:, 3] * 0.1 +
        X[:, 4] * 0.1 +
        X[:, 5] * 0.1 +
        np.random.normal(0, 0.05, n)
    )
    y_binary = (y > 0.5).astype(int)

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y_binary)

    os.makedirs("ml", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    return model, scaler


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_and_save()
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def score_lead(features: dict) -> float:
    """
    Score a lead 0-100.
    features: dict with keys from FEATURE_ORDER
    """
    try:
        model, scaler = load_model()
        X = np.array([[features.get(f, 0) for f in FEATURE_ORDER]])
        X_scaled = scaler.transform(X)
        proba = model.predict_proba(X_scaled)[0][1]

        # Add bonus for completeness
        bonus = sum([
            features.get("has_news", 0) * 5,
            features.get("has_jobs", 0) * 5,
            min(features.get("skills_count", 0), 10),
        ])

        score = min(100, proba * 80 + bonus)
        return round(score, 1)
    except Exception as e:
        print(f"Scoring error: {e}")
        return 50.0
