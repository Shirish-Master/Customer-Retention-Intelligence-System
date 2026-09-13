# 246. Split X and y: train_test_split(test_size=0.2, stratify=y, random_state=42)

from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

from LAB_ML1 import prepare_ml_data


PROJECT_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

X, y, _ = prepare_ml_data()
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42,
)


# 247. Train a LogisticRegression(max_iter=1000) and a DecisionTreeClassifier(max_depth=5)
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
}


# 248. Predict on the test set for both models
predictions = {}
for model_name, model in models.items():
    model.fit(X_train, y_train)
    predictions[model_name] = model.predict(X_test)


# 249. For each model: print classification_report with target_names=["Active","Churned"]
for model_name, prediction in predictions.items():
    print(f"\n{model_name} classification report:")
    print(
        classification_report(
            y_test,
            prediction,
            target_names=["Active", "Churned"],
            zero_division=0,
        )
    )


# 250. For each model: print confusion_matrix
for model_name, prediction in predictions.items():
    print(f"{model_name} confusion matrix:")
    print(confusion_matrix(y_test, prediction))


# 251. Compute 5-fold cross-validation F1 score for both: cross_val_score(scoring="f1")
cv_f1_scores = {}
for model_name, model in models.items():
    scores = cross_val_score(model, X, y, cv=5, scoring="f1")
    cv_f1_scores[model_name] = scores.mean()
    print(f"{model_name} 5-fold CV F1 scores: {scores}")
    print(f"{model_name} mean CV F1: {scores.mean():.4f}")


# 252. Create a comparison table: Model | Accuracy | Precision (Churned) | Recall (Churned) | F1 (Churned) | CV F1
comparison_rows = []
for model_name, prediction in predictions.items():
    comparison_rows.append(
        {
            "Model": model_name,
            "Accuracy": accuracy_score(y_test, prediction),
            "Precision (Churned)": precision_score(y_test, prediction, zero_division=0),
            "Recall (Churned)": recall_score(y_test, prediction, zero_division=0),
            "F1 (Churned)": f1_score(y_test, prediction, zero_division=0),
            "CV F1": cv_f1_scores[model_name],
        }
    )

comparison_table = pd.DataFrame(comparison_rows)
print("\nModel comparison:")
print(comparison_table.to_string(index=False))


# 253. Choose the better model based on F1 for the Churned class and justify the choice
best_model_row = comparison_table.loc[comparison_table["F1 (Churned)"].idxmax()]
print(
    f"\nSelected model: {best_model_row['Model']}. "
    f"It has the higher Churned-class F1 score of "
    f"{best_model_row['F1 (Churned)']:.4f}, balancing precision and recall "
    "for identifying customers likely to churn."
)


# 254. Save both models with joblib: models/logistic_churn.pkl and models/tree_churn.pkl
joblib.dump(models["Logistic Regression"], MODELS_DIR / "logistic_churn.pkl")
joblib.dump(models["Decision Tree"], MODELS_DIR / "tree_churn.pkl")
print(f"Saved models to {MODELS_DIR}")
