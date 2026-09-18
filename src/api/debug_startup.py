import sys
import os
sys.path.insert(0, os.getcwd())

print("1. importing fastapi...")
from fastapi import FastAPI
print("2. creating app...")
app = FastAPI()
print("3. importing companies router...")
from src.api.routers.companies import router
print("4. including router...")
app.include_router(router, prefix="/api/v1")
print("5. all imports done")

import uvicorn
print("6. calling uvicorn.run...")
uvicorn.run(app, host="0.0.0.0", port=8000)
print("7. uvicorn.run returned (this means it exited)")