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

    # Rebalanced weights: news + jobs matter most (what we can always get)
    # company/title/summary are bonuses, not requirements
    y = (
        X[:, 0] * 0.10 +   # has_company (reduced — not always available)
        X[:, 1] * 0.10 +   # has_title
        (X[:, 2] / 15) * 0.15 +  # skills_count
        X[:, 3] * 0.10 +   # has_summary
        X[:, 4] * 0.30 +   # has_news (most important — signals active company)
        X[:, 5] * 0.25 +   # has_jobs (hiring = growing = good lead)
        np.random.normal(0, 0.05, n)
    )
    y_binary = (y > 0.35).astype(int)  # Lower threshold so more leads qualify

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

        # Bonus points for intelligence we gathered
        bonus = sum([
            features.get("has_news", 0) * 8,   # Found company news = active company
            features.get("has_jobs", 0) * 7,   # Hiring = growing = hot lead
            min(features.get("skills_count", 0), 10) * 1,
        ])

        score = min(100, proba * 75 + bonus)
        return round(score, 1)
    except Exception as e:
        print(f"Scoring error: {e}")
        return 50.0