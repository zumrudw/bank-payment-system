from fastapi import FastAPI
from app.routers import auth, customers, cards, payments

app = FastAPI(
    title="Bank Card Payment System v2",
    description="OOP-based payment system with FastAPI, PostgreSQL, and JWT auth",
    version="2.0.0"
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(cards.router)
app.include_router(payments.router)


@app.get("/")
def root():
    return {"message": "Bank Payment API v2 is running!"}