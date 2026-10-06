//158.Create src/pages/HighRiskCustomers.js
import { useEffect, useState } from "react";
import axios from "axios";
import { BASE_URL } from "../api";

function HighRiskCustomers() {
  const [customers, setCustomers] = useState([]);
  const [limit, setLimit] = useState(50);
  const [sortDirection, setSortDirection] = useState("ascending");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  //159.On mount, fetch GET /customers/high-risk (default limit 50)
  const fetchHighRiskCustomers = async (requestedLimit) => {
    setLoading(true);
    setError("");

    try {
      const response = await axios.get(`${BASE_URL}/customers/high-risk`, {
        params: { limit: requestedLimit },
      });
      setCustomers(response.data);
    } catch (requestError) {
      console.error(requestError);
      setError("Failed to load high-risk customers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHighRiskCustomers(50);
  }, []);

  //162.Add a "Load More" button that refetches with limit increased by 50
  const handleLoadMore = () => {
    const nextLimit = limit + 50;
    setLimit(nextLimit);
    fetchHighRiskCustomers(nextLimit);
  };

  //163.Add a sort toggle on the tenure column: clicking the header sorts ascending/descending
  const toggleTenureSort = () => {
    setSortDirection((currentDirection) =>
      currentDirection === "ascending" ? "descending" : "ascending"
    );
  };

  const sortedCustomers = [...customers].sort((firstCustomer, secondCustomer) => {
    const difference = firstCustomer.tenure - secondCustomer.tenure;
    return sortDirection === "ascending" ? difference : -difference;
  });

  //160.Render results in an HTML table: customer_id | tenure | monthly_charges | contract_type | risk_reason
  return (
    <section id="high-risk-customers">
      <h1>High-Risk Customers</h1>

      {/* 161.Show a count banner: "X high-risk customers identified" */}
      <p className="count-banner">
        {customers.length} high-risk customers identified
      </p>

      {loading && <p>Loading high-risk customers...</p>}
      {error && <p>{error}</p>}

      {!loading && !error && customers.length === 0 && (
        //165.Handle the case where 0 results are returned: show "No high-risk customers found"
        <p>No high-risk customers found</p>
      )}

      {!loading && !error && customers.length > 0 && (
        <>
          <table className="high-risk-table">
            <thead>
              <tr>
                <th>Customer ID</th>
                <th
                  onClick={toggleTenureSort}
                  role="button"
                  tabIndex="0"
                  aria-sort={sortDirection}
                >
                  Tenure {sortDirection === "ascending" ? "↑" : "↓"}
                </th>
                <th>Monthly Charges</th>
                <th>Contract Type</th>
                <th>Risk Reason</th>
              </tr>
            </thead>
            <tbody>
              {sortedCustomers.map((customer) => (
                <tr key={customer.customer_id}>
                  <td>{customer.customer_id}</td>
                  <td>{customer.tenure}</td>
                  {/* 164.Format monthly_charges as currency: "$" + value.toFixed(2) */}
                  <td>{"$" + customer.monthly_charges.toFixed(2)}</td>
                  <td>{customer.contract_type}</td>
                  <td>{customer.risk_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={handleLoadMore}>Load More</button>
        </>
      )}
    </section>
  );
}

export default HighRiskCustomers;
