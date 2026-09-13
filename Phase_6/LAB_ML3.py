# 255. Load the best model from ML2 (Logistic Regression: inspect coefficients; Decision Tree: inspect feature importances)

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split

from LAB_ML1 import prepare_ml_data


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_DIR / "Phase_6" / "models"
PLOT_FILE = PROJECT_DIR / "Phase_6" / "top_10_churn_features.png"
DATABASE_URL = "mysql+pymysql://root:root@localhost/churn"

X, y, customer_ids = prepare_ml_data()
X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
    X,
    y,
    customer_ids,
    test_size=0.2,
    stratify=y,
    random_state=42,
)

logistic_model = joblib.load(MODELS_DIR / "logistic_churn.pkl")
tree_model = joblib.load(MODELS_DIR / "tree_churn.pkl")


# 256. For Logistic Regression: extract coef_ as a Series with feature names; sort by absolute value; plot top 10
logistic_coefficients = pd.Series(
    logistic_model.coef_[0],
    index=X.columns,
    name="coefficient",
)
logistic_coefficients = logistic_coefficients.loc[
    logistic_coefficients.abs().sort_values(ascending=False).index
]
print("Logistic Regression coefficients:")
print(logistic_coefficients)

top_logistic = logistic_coefficients.head(10).sort_values()
top_logistic.plot(kind="barh", title="Top 10 Logistic Regression Churn Features")
plt.xlabel("Coefficient")
plt.tight_layout()
plt.savefig(PLOT_FILE)
plt.close()
print(f"Top 10 coefficient plot saved to {PLOT_FILE}")


# 257. For Decision Tree: extract feature_importances_ similarly
tree_importances = pd.Series(
    tree_model.feature_importances_,
    index=X.columns,
    name="importance",
).sort_values(ascending=False)
print("Decision Tree feature importances:")
print(tree_importances)


# 258. Identify the top 3 features most associated with higher churn probability
positive_logistic_features = logistic_coefficients[logistic_coefficients > 0]
top_three_features = positive_logistic_features.head(3)
if len(top_three_features) < 3:
    top_three_features = logistic_coefficients.abs().head(3)
print("Top 3 features associated with higher churn probability:")
print(top_three_features)


# 259. Score all customers in the test set: predict_proba() to get churn probability
best_model = tree_model
best_model_name = "Decision Tree"
test_probabilities = best_model.predict_proba(X_test)[:, 1]
risk_scores = pd.DataFrame(
    {
        "customer_id": ids_test.to_numpy(),
        "churn_probability": test_probabilities,
    }
).sort_values("churn_probability", ascending=False)


# 260. Find the top 20 highest-risk customers in the test set — print their customer IDs and risk scores
top_20_risk = risk_scores.head(20)
print(f"Top 20 highest-risk customers ({best_model_name}):")
print(top_20_risk.to_string(index=False))


# 261. Check: do the top-risk customers match the rule-based high-risk list from SQL6? (partial overlap expected)
def compare_with_rule_based_list(top_risk):
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        rule_based = pd.read_sql(
            text("SELECT customer_id FROM v_high_risk_customers"),
            connection,
        )

    rule_based_ids = set(rule_based["customer_id"])
    top_risk_ids = set(top_risk["customer_id"])
    overlap = sorted(top_risk_ids & rule_based_ids)
    print(
        f"Rule-based overlap: {len(overlap)} of 20 top-risk customers "
        f"({len(overlap) / 20:.1%})"
    )
    print(f"Overlapping customer IDs: {overlap}")
    return overlap


# 262. Write a 5-sentence business interpretation: "Customers most likely to churn are those who..." targeted at a retention manager

def business_interpretation(top_features, overlap_count):
    feature_text = ", ".join(top_features.index)
    print(
        "Customers most likely to churn are those who show the strongest risk signals in "
        f"{feature_text}. "
        "The Decision Tree ranks customers by predicted churn probability so the retention team can prioritize outreach. "
        "The top-risk list should be reviewed alongside contract and service context before an offer is made. "
        f"The ML list shares {overlap_count} customers with the SQL6 rule-based list, so the two approaches provide complementary signals. "
        "Retention managers should contact the highest-risk customers first and track whether targeted interventions reduce future churn."
    )


if __name__ == "__main__":
    overlap = compare_with_rule_based_list(top_20_risk)
    business_interpretation(top_three_features, len(overlap))
