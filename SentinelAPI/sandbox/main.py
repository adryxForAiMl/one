from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="KAVACH Lab - Vulnerable Test API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

users = {
    "token-user-a": {
        "user_id": 1,
        "name": "User A"
    },
    "token-user-b": {
        "user_id": 2,
        "name": "User B"
    }
}

orders = {
    101: {
        "order_id": 101,
        "owner_id": 1,
        "product": "MacBook Air",
        "amount": 999
    },
    102: {
        "order_id": 102,
        "owner_id": 2,
        "product": "iPhone",
        "amount": 799
    }
}


def get_current_user(authorization: str):
    if authorization not in users:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    return users[authorization]


@app.get("/")
def root():
    return {
        "service": "KAVACH Lab - Controlled Security Sandbox",
        "description": "Authorized demonstration API with intentional BOLA vulnerabilities.",
        "warning": "INTENTIONALLY VULNERABLE - CONTROLLED TEST ENVIRONMENT",
        "purpose": "Demonstrating Broken Object Level Authorization (BOLA/IDOR)",
        "status": "online",
        "endpoints": ["/orders", "/orders/{order_id}"],
    }


@app.get("/orders")
def get_my_orders(
    authorization: str = Header(...)
):
    user = get_current_user(authorization)

    return [
        order
        for order in orders.values()
        if order["owner_id"] == user["user_id"]
    ]


@app.get("/orders/{order_id}")
def get_order(
    order_id: int,
    authorization: str = Header(...)
):
    get_current_user(authorization)

    if order_id not in orders:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order = orders[order_id]

    # INTENTIONALLY VULNERABLE:
    # The API does not verify that the order belongs to the user.
    return order