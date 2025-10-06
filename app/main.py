from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="FastAPI DynamoDB CRUD")

app.include_router(router)
