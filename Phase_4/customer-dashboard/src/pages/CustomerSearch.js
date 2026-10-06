//141.Create src/pages/CustomerSearch.js
import { useState } from "react";
import axios from "axios";
import { BASE_URL } from "../api";

function CustomerSearch() {
  //142.Add a controlled text input for customer ID (useState for the input value)
  const [customerId, setCustomerId] = useState("");
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  //144.Call GET /customer/{id} with the input value using axios
  const handleSearch = async () => {
    setLoading(true);
    setError("");
    setCustomer(null);

    try {
      const response = await axios.get(
        `${BASE_URL}/customer/${customerId}`
      );
      setCustomer(response.data);
    } catch (requestError) {
      //147.Handle 404 gracefully: show "Customer not found" instead of a crash
      if (requestError.response?.status === 404) {
        setError("Customer not found");
      } else {
        setError("Failed to load customer");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="customer-search">
      <h2>Customer Search</h2>

      <input
        //142.Add a controlled text input for customer ID (useState for the input value)
        type="text"
        value={customerId}
        onChange={(event) => setCustomerId(event.target.value)}
        placeholder="Enter customer ID"
      />

      {/* 143.Add a Search button — onClick triggers the API call */}
      <button onClick={handleSearch}>Search</button>

      {/* 145.Show a loading spinner/message while the request is in flight */}
      {loading && <p>Loading...</p>}
      {error && <p>{error}</p>}

      {/* 146.Display the result in a card layout: customer_id, tenure, contract_type, internet_service, monthly_charges, churn status */}
      {customer && (
        <div className="customer-card">
          <p>Customer ID: {customer.customer_id}</p>
          <p>Tenure: {customer.tenure}</p>
          <p>Contract Type: {customer.contract_type}</p>
          <p>Internet Service: {customer.internet_service}</p>
          <p>Monthly Charges: {customer.monthly_charges}</p>

          {/* 148.Show the churn field with colour coding: red background for churned, green for active */}
          <p className={customer.churn ? "churned" : "active"}>
            Churn Status: {customer.churn ? "Churned" : "Active"}
          </p>
        </div>
      )}
    </section>
  );
}

export default CustomerSearch;
