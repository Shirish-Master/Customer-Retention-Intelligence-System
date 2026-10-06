//166.Create src/pages/ChurnPrediction.js
import { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../api";

const initialForm = {
  tenure: "",
  monthly_charges: "",
  contract_type: "Month-to-month",
  service_count: "0",
};

function ChurnPrediction() {
  //167.Build a form with 4 controlled inputs: tenure (number), monthly_charges (number), contract_type (select: Month-to-month / One year / Two year), service_count (number 0–6)
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((currentForm) => ({ ...currentForm, [name]: value }));
  };

  //168.On submit, POST to /predict-churn with the form values as a JSON body
  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await axios.post(`${BASE_URL}/predict-churn`, {
        tenure: Number(form.tenure),
        monthly_charges: Number(form.monthly_charges),
        contract_type: form.contract_type,
        service_count: Number(form.service_count),
      });
      setResult(response.data);
    } catch (requestError) {
      //172.Handle validation errors (422): display the Pydantic error message to the user
      if (requestError.response?.status === 422) {
        const detail = requestError.response.data?.detail;
        const validationMessage = Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : detail || "Validation error";
        setError(validationMessage);
      } else {
        setError("Failed to predict churn");
      }
    } finally {
      setLoading(false);
    }
  };

  //170.Add visual risk indicator: green for low risk (<0.3), amber for medium (0.3–0.6), red for high (>0.6)
  const getRiskClass = (riskScore) => {
    if (riskScore < 0.3) {
      return "risk-low";
    }
    if (riskScore <= 0.6) {
      return "risk-medium";
    }
    return "risk-high";
  };

  //173.Test with stub response first; retest after ML4 wires up the real model
  const confidenceLevel =
    result?.confidence_level || result?.confidence || "Not provided by stub";

  //174.Full end-to-end test: enter values → POST → model response → coloured risk display
  return (
    <section id="churn-prediction">
      <h1>Churn Prediction</h1>

      <form onSubmit={handleSubmit}>
        <label>
          Tenure
          <input
            type="number"
            name="tenure"
            value={form.tenure}
            onChange={handleChange}
            min="0"
            max="100"
            required
          />
        </label>

        <label>
          Monthly Charges
          <input
            type="number"
            name="monthly_charges"
            value={form.monthly_charges}
            onChange={handleChange}
            min="0.01"
            step="0.01"
            required
          />
        </label>

        <label>
          Contract Type
          <select
            name="contract_type"
            value={form.contract_type}
            onChange={handleChange}
          >
            <option value="Month-to-month">Month-to-month</option>
            <option value="One year">One year</option>
            <option value="Two year">Two year</option>
          </select>
        </label>

        <label>
          Service Count
          <input
            type="number"
            name="service_count"
            value={form.service_count}
            onChange={handleChange}
            min="0"
            max="6"
            required
          />
        </label>

        {/* 171.Show a loading state on the submit button while the request is in flight */}
        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Predict Churn"}
        </button>
      </form>

      {error && <p className="prediction-error">{error}</p>}

      {result && (
        <div className={`prediction-result ${getRiskClass(result.risk_score)}`}>
          {/* 169.Display the result: risk_score as a percentage, prediction text, confidence level */}
          <p>Risk Score: {(result.risk_score * 100).toFixed(1)}%</p>
          <p>Prediction: {result.prediction}</p>
          <p>Confidence Level: {confidenceLevel}</p>
          {result.note && <p>{result.note}</p>}
        </div>
      )}
    </section>
  );
}

export default ChurnPrediction;
