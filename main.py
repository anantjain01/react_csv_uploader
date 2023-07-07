from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import csv
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from databases import Database

app = FastAPI()
origins = ["http://localhost:3000"]  # Replace with your frontend URL

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./mydatabase.db"

database = Database(DATABASE_URL)
metadata = MetaData()
csv_table = Table(
    "csv_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("column1", String),
    Column("column2", String),
    # Add more columns as needed
)
engine = create_engine(DATABASE_URL)
metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8")
        reader = csv.DictReader(decoded.splitlines(), delimiter=',')
        data = list(reader)

        query = csv_table.insert()
        await database.execute_many(query=query, values=data)

        return JSONResponse(status_code=201, content={"message": "Data uploaded successfully."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.get("/data")
async def get_data():
    query = csv_table.select()
    results = await database.fetch_all(query)

    return JSONResponse(status_code=200, content={"data": results})
