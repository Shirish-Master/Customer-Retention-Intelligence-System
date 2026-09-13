"""Tests for questions 268-270: model and API prediction checks."""

from Phase_3.main import ChurnPredictionRequest, predict_churn as api_predict_churn
from Phase_6.predict import predict_churn


# 268. Test via /docs: submit a month-to-month customer with short tenure -> expect high risk.
def test_short_tenure_month_to_month_is_high_risk():
    result = predict_churn(
        tenure=2,
        monthly_charges=85.00,
        contract_type="Month-to-month",
        service_count=1,
    )

    assert result["risk_score"] > 0.6
    assert result["prediction"] == "Likely to churn"
    assert 0.0 <= result["confidence"] <= 1.0


# 269. Test: submit a two-year contract customer with long tenure -> expect low risk.
def test_long_tenure_two_year_contract_is_low_risk():
    result = predict_churn(
        tenure=60,
        monthly_charges=45.00,
        contract_type="Two year",
        service_count=5,
    )

    assert result["risk_score"] < 0.3
    assert result["prediction"] == "Unlikely to churn"
    assert 0.0 <= result["confidence"] <= 1.0


# 270. Full end-to-end: test from RE5 React form -> API -> model -> coloured response in UI.
def test_prediction_api_returns_react_form_response_shape():
    body = api_predict_churn(
        ChurnPredictionRequest(
            tenure=2,
            monthly_charges=85.00,
            contract_type="Month-to-month",
            service_count=1,
        )
    )

    assert set(body) == {"risk_score", "prediction", "confidence"}
    assert body["prediction"] in {"Likely to churn", "Unlikely to churn"}
    assert 0.0 <= body["risk_score"] <= 1.0
    assert 0.0 <= body["confidence"] <= 1.0


# The React form in Phase_4/customer-dashboard/src/pages/ChurnPrediction.js
# consumes this response and applies risk-high, risk-medium, or risk-low styling
# from risk_score before displaying the coloured result.
