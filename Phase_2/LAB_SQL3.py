#Continuation for LAB_SQL3.sql

# 65. Introduce SQLAlchemy: create Python model classes for at least two of these tables (Customer, Contract)

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(20), primary_key=True)
    gender = Column(String(20))
    senior_citizen = Column(Integer)
    partner = Column(Integer)
    dependents = Column(Integer)


class Contract(Base):
    __tablename__ = "dim_contract"

    contract_id = Column(Integer, primary_key=True)
    contract_type = Column(String(50))


engine = create_engine(
    "mysql+pymysql://root:root@localhost/churn"
)

Session = sessionmaker(bind=engine)
session = Session()


# 66. Use a SQLAlchemy session to query one customer by customerID and print the result

customer = session.query(Customer).first()

print("Customer ID:", customer.customer_id)
print("Gender:", customer.gender)
print("Partner:", customer.partner)