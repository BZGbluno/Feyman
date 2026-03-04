from fastapi import FastAPI
from api.helloWorld import router as hello_world_router

app = FastAPI()

app.include_router(hello_world_router)