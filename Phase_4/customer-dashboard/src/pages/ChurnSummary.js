//150.Create src/pages/ChurnSummary.js
import { useEffect, useState } from "react";
import axios from "axios";
import { BASE_URL } from "../api";

function ChurnSummary() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  //151.On mount (useEffect with []), fetch GET /churn/summary
  useEffect(() => {
    axios
      .get(`${BASE_URL}/churn/summary`)
      .then((response) => {
        setSummary(response.data);
        setLoading(false);
      })
      .catch((requestError) => {
        console.error(requestError);
        setError("Failed to load churn summary");
        setLoading(false);
      });
  }, []);

  //156.Handle loading and error states
  if (loading) {
    return <p>Loading churn summary...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  //157.Add a page title and a one-sentence description of what the page shows
  return (
    <section id="churn-summary">
      <h1>Customer Churn Summary</h1>
      <p>
        This page shows overall customer churn metrics and churn rates by
        contract type.
      </p>

      {/* 152.Display three metric cards: total customers, total churned, churn rate (as a percentage) */}
      <div className="metric-cards">
        <div className="metric-card">
          <h2>Total Customers</h2>
          <p>{summary.total_customers}</p>
        </div>
        <div className="metric-card">
          <h2>Total Churned</h2>
          <p>{summary.total_churned}</p>
        </div>
        <div className="metric-card">
          <h2>Churn Rate</h2>
          <p>{(summary.churn_rate * 100).toFixed(1) + "%"}</p>
        </div>
      </div>

      {/* 153.Display a contract-type churn table: contract_type | churn_rate columns */}
      <table className="churn-table">
        <thead>
          <tr>
            <th>Contract Type</th>
            <th>Churn Rate</th>
          </tr>
        </thead>
        <tbody>
          {summary.by_contract.map((contract) => (
            <tr key={contract.contract_type}>
              <td>{contract.contract_type}</td>
              {/* 154.Format churn_rate as a percentage: (rate * 100).toFixed(1) + "%" */}
              <td>{(contract.churn_rate * 100).toFixed(1) + "%"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 155.Add a simple visual: for each contract type, show a coloured bar whose width is proportional to its churn rate */}
      <div className="churn-bars">
        {summary.by_contract.map((contract) => (
          <div className="churn-bar-row" key={contract.contract_type}>
            <span>{contract.contract_type}</span>
            <div className="churn-bar-track">
              <div
                className="churn-bar"
                style={{ width: `${contract.churn_rate * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default ChurnSummary;
