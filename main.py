# main.py
from fastapi import FastAPI

from gztprocessor.db_connections.db_gov import init_db as init_gov_db
from gztprocessor.db_connections.db_person import init_db as init_person_db
from gztprocessor.db_connections.db_trans import init_db as init_transaction_db
from routes.mindep_router import mindep_router
from routes.person_router import person_router
from routes.transaction_router import transaction_router
from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    init_gov_db()
    init_person_db()
    init_transaction_db()
    print("✅ Databases initialized.")

app = FastAPI()
app.include_router(mindep_router)
app.include_router(person_router)
app.include_router(transaction_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Gazette Processor backend running."}
