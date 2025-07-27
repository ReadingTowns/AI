from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Book Crawler API")
app.include_router(router)