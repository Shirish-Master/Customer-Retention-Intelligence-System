#LAB_API1



# 90. Create main.py with a FastAPI app instance

from fastapi import FastAPI, HTTPException

# 91. Create a SQLAlchemy engine and session factory pointing to your database

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
# 267. In main.py: import predict_churn from predict.py; replace the stub with a real call.
from Phase_6.predict import predict_churn as run_churn_prediction

# 92. Define a Pydantic CustomerResponse model with the fields to return: customer_id, tenure, contract_type, internet_service, monthly_charges, churn

from pydantic import BaseModel,Field

# 136. Add FastAPI CORS middleware: allow origins=["http://localhost:3000"] in main.py

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS middleware to allow requests from React frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(
    "mysql+pymysql://root:root@localhost/churn"
)

SessionLocal = sessionmaker(bind=engine)


class CustomerResponse(BaseModel):
    customer_id: str
    tenure: int
    contract_type: str
    internet_service: str
    monthly_charges: float
    churn: int


# 93. Implement GET /customer/{customer_id}: query the customers + fact_customer_account + dim_contract tables, raise HTTPException(404) if not found

# 94. Return the result as the CustomerResponse model

@app.get(
    "/customer/{customer_id}",
    response_model=CustomerResponse
)
def get_customer(customer_id: str):

    session = SessionLocal()

    query = text(
        """
        SELECT
            s.customerID AS customer_id,
            f.tenure,
            dc.contract_type,
            s.InternetService AS internet_service,
            f.monthly_charges,
            f.churn
        FROM fact_customer_account f
        JOIN dim_contract dc
            ON f.contract_id = dc.contract_id
        JOIN stg_customer_raw s
            ON f.customer_id = s.customerID
        WHERE f.customer_id = :customer_id
        """
    )

    result = session.execute(
        query,
        {"customer_id": customer_id}
    ).fetchone()

    session.close()

    # 97. Test a non-existent ID — confirm 404 is returned with a clear message
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return CustomerResponse(
        customer_id=result.customer_id,
        tenure=result.tenure,
        contract_type=result.contract_type,
        internet_service=result.internet_service,
        monthly_charges=float(result.monthly_charges),
        churn=result.churn
    )


# 95. Run the server: uvicorn main:app --reload
# we can see swagger ui in this link http://127.0.0.1:8000/docs


#96.Test at /docs: look up a known customer ID (e.g. "7590-VHVEG") 
#Go to http://127.0.0.1:8000/customer/7590-VHVEG and then execute it.


#97.Test a non-existent ID — confirm 404 is returned with a clear message 
#Now try adding "ABC123" and you should see a 404 error with the message "Customer not found".

# 98. Add GET /churn/summary to main.py

# 99. Create a service layer function get_churn_summary(db) — keep business logic out of the route




#LAB_API2



def get_churn_summary(db):

    total_summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_customers,
                SUM(churn) AS total_churned,
                AVG(churn) AS churn_rate
            FROM fact_customer_account
            """
        )
    ).fetchone()

    contract_summary = db.execute(
        text(
            """
            SELECT
                dc.contract_type,
                AVG(f.churn) AS churn_rate
            FROM fact_customer_account f
            JOIN dim_contract dc
                ON f.contract_id = dc.contract_id
            GROUP BY dc.contract_type
            ORDER BY churn_rate DESC
            """
        )
    ).fetchall()

    internet_summary = db.execute(
        text(
            """
            SELECT
                s.InternetService AS internet_service,
                AVG(f.churn) AS churn_rate
            FROM fact_customer_account f
            JOIN stg_customer_raw s
                ON f.customer_id = s.customerID
            GROUP BY s.InternetService
            ORDER BY churn_rate DESC
            """
        )
    ).fetchall()

    return {
        "total_customers": total_summary.total_customers,
        "total_churned": total_summary.total_churned,
        "churn_rate": round(float(total_summary.churn_rate), 4),

        # 101. Query: churn rate by contract type (list of {contract_type, churn_rate})
        "by_contract": [
            {
                "contract_type": row.contract_type,
                "churn_rate": round(float(row.churn_rate), 4)
            }
            for row in contract_summary
        ],

        # 102. Query: churn rate by internet service type
        "by_internet_service": [
            {
                "internet_service": row.internet_service,
                "churn_rate": round(float(row.churn_rate), 4)
            }
            for row in internet_summary
        ]
    }


# 100. Query: total customers, total churned, churn rate (as float 0–1)

# 103. Return all of this in a single structured JSON response

@app.get("/churn/summary")
def churn_summary():

    db = SessionLocal()

    try:
        return get_churn_summary(db)

    finally:
        db.close()


# 104. Test at /docs — verify values match your SQL4 query results

# 105. Discuss: why create a service layer function rather than putting SQL directly in the route?
# Service layer functions separate business logic from API routing.
# This improves reusability, testability and keeps route handlers clean.




#LAB_API3





# 106. Add GET /customers/high-risk to main.py

from typing import Optional


# 107. Query the v_high_risk_customers view

# 109. Return a list of customer objects with: customer_id, tenure, monthly_charges, contract_type, risk_reason

class HighRiskCustomerResponse(BaseModel):
    customer_id: str
    tenure: int
    monthly_charges: float
    contract_type: str
    risk_reason: str


@app.get(
    "/customers/high-risk",
    response_model=list[HighRiskCustomerResponse]
)

# 108. Add optional query parameters: limit (default 50) and min_tenure / max_tenure for filtering

def get_high_risk_customers(
    limit: int = 50,
    min_tenure: Optional[int] = None,
    max_tenure: Optional[int] = None
):

    db = SessionLocal()

    query = """
        SELECT
            customer_id,
            tenure,
            monthly_charges,
            contract_type,
            risk_reason
        FROM v_high_risk_customers
        WHERE 1=1
    """

    params = {}

    if min_tenure is not None:
        query += " AND tenure >= :min_tenure"
        params["min_tenure"] = min_tenure

    if max_tenure is not None:
        query += " AND tenure <= :max_tenure"
        params["max_tenure"] = max_tenure

    query += " LIMIT :limit"
    params["limit"] = limit

    result = db.execute(
        text(query),
        params
    ).fetchall()

    db.close()

    return [
        HighRiskCustomerResponse(
            customer_id=row.customer_id,
            tenure=row.tenure,
            monthly_charges=float(row.monthly_charges),
            contract_type=row.contract_type,
            risk_reason=row.risk_reason
        )
        for row in result
    ]


# 110. Test with default parameters — confirm results match v_high_risk_customers view

# Open:
# http://127.0.0.1:8000/docs

# Execute:
# GET /customers/high-risk

# Compare result count/sample rows with:
# SELECT * FROM v_high_risk_customers;


# 111. Test with limit=10 and max_tenure=6 — verify filtering works

# Swagger Example:
# limit = 10
# max_tenure = 6

# Expected:
# Maximum 10 rows returned
# All returned rows should have tenure <= 6


# 112. Discuss: this is a rule-based list. How will it change when ML predictions are available (ML5)?

# Rule-based scoring uses fixed business rules and is easy to explain.
# ML-based scoring will assign a churn probability to every customer using patterns learned from historical data.
# The high-risk endpoint can later return customers ranked by predicted churn probability instead of simple rule matches.



#LAB_API4


# 117. Define a Pydantic CustomerFeatures response model

class CustomerFeatures(BaseModel):
    service_count: int
    tenure_bucket: str
    high_charge_flag: int
    is_long_term_customer: int
    has_streaming_bundle: int
    auto_pay_flag: int
    monthly_charges: float
    total_charges: float


# 113. Add GET /customer/{customer_id}/features to main.py

# 114. Query the customer_ml_features table for the given customer_id

# 115. Return all engineered features: service_count, tenure_bucket,
# high_charge_flag, is_long_term_customer, has_streaming_bundle,
# auto_pay_flag, monthly_charges, total_charges

@app.get(
    "/customer/{customer_id}/features",
    response_model=CustomerFeatures
)
def get_customer_features(customer_id: str):

    db = SessionLocal()

    query = text(
        """
        SELECT
            service_count,
            tenure_bucket,
            high_charge_flag,
            is_long_term_customer,
            has_streaming_bundle,
            auto_pay_flag,
            monthly_charges,
            total_charges
        FROM customer_ml_features
        WHERE customer_id = :customer_id
        """
    )

    result = db.execute(
        query,
        {"customer_id": customer_id}
    ).fetchone()

    db.close()

    # 116. Raise 404 if customer not found

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Customer features not found"
        )

    return CustomerFeatures(
        service_count=result.service_count,
        tenure_bucket=result.tenure_bucket,
        high_charge_flag=result.high_charge_flag,
        is_long_term_customer=result.is_long_term_customer,
        has_streaming_bundle=result.has_streaming_bundle,
        auto_pay_flag=result.auto_pay_flag,
        monthly_charges=float(result.monthly_charges),
        total_charges=float(result.total_charges)
    )


# 118. Test with a known customer ID — verify values match customer_features.csv for that customer





#LAB_API5





# 119. Define a Pydantic ChurnPredictionRequest model: tenure (int), monthly_charges (float), contract_type (str), service_count (int)

class ChurnPredictionRequest(BaseModel):
    tenure: int
    monthly_charges: float
    contract_type: str
    service_count: int


# 120. Add POST /predict-churn to main.py

@app.post("/predict-churn")

# Old LAB_API5 implementation, retained for reference before LAB_ML4:
# @app.post("/predict-churn")
# def predict_churn(request: ChurnPredictionRequest):
#     return {
#         "customer_id": "N/A",
#         "risk_score": 0.78,
#         "prediction": "Likely to churn",
#         "note": "stub - real model in ML4",
#     }
def predict_churn(request: ChurnPredictionRequest):
    try:
        return run_churn_prediction(
            tenure=request.tenure,
            monthly_charges=request.monthly_charges,
            contract_type=request.contract_type,
            service_count=request.service_count,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


# 123. Test via /docs: submit a month-to-month customer with short tenure -> expect high risk.
# 268. Test via /docs: submit a month-to-month customer with short tenure -> expect high risk.

# 124. Verify that submitting wrong types (e.g. tenure as a string) returns a 422 Validation Error automatically from Pydantic
# 269. Test: submit a two-year contract customer with long tenure -> expect low risk.
# 270. Full end-to-end: test from RE5 React form -> API -> model -> coloured response in UI.






#LAB_API6





# 125. Add field-level Pydantic validators to ChurnPredictionRequest: tenure must be >= 0 and <= 100; monthly_charges must be > 0

from pydantic import BaseModel, Field
from fastapi import HTTPException, Header, Request
from fastapi.responses import JSONResponse
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class ChurnPredictionRequest(BaseModel):
    tenure: int = Field(..., ge=0, le=100)
    monthly_charges: float = Field(..., gt=0)
    contract_type: str
    service_count: int


# 126. Add a consistent error response model: ErrorResponse(detail: str, status_code: int)

class ErrorResponse(BaseModel):
    detail: str
    status_code: int


# 131. Add a basic token check: read an API_KEY from environment variable; any request without matching X-API-Key header gets 401

API_KEY = os.getenv("API_KEY", "my-secret-key")


def verify_api_key(
    x_api_key: str = Header(...)
):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )


# 129. Add a 404 handler for all routes using @app.exception_handler(404)

@app.exception_handler(404)
async def not_found_handler(
    request: Request,
    exc
):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Resource not found",
            "status_code": 404
        }
    )


# 127. Wrap all DB queries in try/except — return 500 with ErrorResponse if DB is unavailable

# Example pattern to be used inside every database route:

"""
try:

    result = db.execute(
        query,
        params
    )

except HTTPException:
    raise

except Exception:

    logger.error(
        "Database unavailable"
    )

    raise HTTPException(
        status_code=500,
        detail="Database unavailable"
    )
"""


# 128. Add Python logging to every route: log the incoming request (method, path, key params) and the response status

# Example pattern to be used inside every route:

"""
logger.info("GET /customer/%s", customer_id)

logger.info("Response Status: 200")
"""


# 130. Test: valid request, invalid tenure (negative), unknown customer ID, simulate DB down

# Valid Request:
# Expected: 200 OK

# Invalid Tenure:
# {
#     "tenure": -1,
#     "monthly_charges": 75.5,
#     "contract_type": "Month-to-month",
#     "service_count": 3
# }
# Expected: 422 Validation Error

# Unknown Customer:
# Expected: 404 Not Found

# Database Down:
# Expected: 500 Internal Server Error


# 132. Discuss: how does this differ from full OAuth2/JWT? What would change in production?

# API key authentication uses a shared secret and verifies only that the client knows the correct key.
# OAuth2/JWT adds user identity, token expiry, permissions and role-based access control.
# In production systems OAuth2/JWT is preferred because it provides secure user authentication and authorization.