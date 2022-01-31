
from fastapi import FastAPI
from schema.schema import graphql_app


app = FastAPI()

@app.get("/")
def read_root():
    return {"GraphQL": "/graphql"}


app.include_router(graphql_app, prefix='/graphql')

