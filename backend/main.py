from fastapi import FastAPI
from api.helloWorld import router as hello_world_router
from api.voice import router as trans
app = FastAPI()


app.include_router(hello_world_router)
app.include_router(trans)