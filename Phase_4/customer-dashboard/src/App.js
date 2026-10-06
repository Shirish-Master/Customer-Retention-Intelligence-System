//133.Run npx create-react-app customer-dashboard

//134.Install axios: npm install axios

//137.In App.js, add a useEffect that calls GET /churn/summary on load and console.log the result
import { useEffect, useState } from "react";
import axios from "axios";
import { BASE_URL } from "./api";
import "./App.css";
//149.Import and add CustomerSearch to App.js with a simple tab or link
import CustomerSearch from "./pages/CustomerSearch";
import ChurnPrediction from "./pages/ChurnPrediction";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    axios
      .get(`${BASE_URL}/churn/summary`)
      .then((response) => {
        console.log(response.data);
        setData(response.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load data");
        setLoading(false);
      });
  }, []);
  //140.Handle the API call properly: show "Loading..." before data arrives, show error message if call fails
  if (loading) return <h2>Loading...</h2>;

  if (error) return <h2>{error}</h2>;

  // Old pre-LAB_ML4 render retained for reference:
  // <pre>{JSON.stringify(data, null, 2)}</pre>
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">CUSTOMER INTELLIGENCE</p>
          <h1>Churn command center</h1>
          <p className="header-copy">Monitor retention signals and score customers before they leave.</p>
        </div>
        <span className="api-status">API connected</span>
      </header>

      <main className="dashboard-grid">
        <section className="overview-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">PORTFOLIO OVERVIEW</p>
              <h2>At a glance</h2>
            </div>
            <span className="data-note">Live summary</span>
          </div>
          <div className="metric-cards">
            <article className="metric-card">
              <span>Total customers</span>
              <strong>{data.total_customers.toLocaleString()}</strong>
            </article>
            <article className="metric-card metric-card-alert">
              <span>Customers churned</span>
              <strong>{data.total_churned.toLocaleString()}</strong>
            </article>
            <article className="metric-card">
              <span>Churn rate</span>
              <strong>{(data.churn_rate * 100).toFixed(1)}%</strong>
            </article>
          </div>
          <div className="contract-panel">
            <div className="section-heading compact-heading">
              <h3>Churn by contract</h3>
              <span>Rate</span>
            </div>
            <div className="churn-bars">
              {data.by_contract.map((item) => (
                <div className="churn-bar-row" key={item.contract_type}>
                  <span>{item.contract_type}</span>
                  <div className="churn-bar-track">
                    <div className="churn-bar" style={{ width: `${item.churn_rate * 100}%` }} />
                  </div>
                  <strong>{(item.churn_rate * 100).toFixed(1)}%</strong>
                </div>
              ))}
            </div>
          </div>
        </section>

        <CustomerSearch />
        {/* 270. Full end-to-end: test from RE5 React form -> API -> model -> coloured response in UI. */}
        <ChurnPrediction />
      </main>
    </div>
  );
}

export default App;