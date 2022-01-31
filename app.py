from typing import Optional

import strawberry
from sqlalchemy import select
from fastapi import FastAPI
from strawberry.asgi import GraphQL

import models.models as models


@strawberry.type
class Brand:
    id: strawberry.ID
    name: str

    @classmethod
    def marshal(cls, model: models.Brand) -> "Brand":
        return cls(id=strawberry.ID(str(model.id)), name=model.name)


@strawberry.type
class Car:
    id: strawberry.ID
    name: str
    brand: Optional[Brand] = None

    @classmethod
    def marshal(cls, model: models.Car) -> "Car":
        return cls(
            id=strawberry.ID(str(model.id)),
            name=model.name,
            brand=Brand.marshal(model.brand) if model.brand else None,
        )


# @strawberry.type
# class Brand:
#     message: str = "Brand with this name does not exist"


AddCarResponse = strawberry.union("AddCarResponse", (Car,))


@strawberry.type
class BrandExists:
    message: str = "Brand with this name already exist"


AddBrandResponse = strawberry.union("AddBrandResponse", (Brand, BrandExists))


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_car(self, name: str, brand_name: Optional[str]) -> AddCarResponse:
        async with models.get_session() as s:
            db_brand = None
            if brand_name:
                sql = select(models.Brand).where(models.Brand.name == brand_name)
                db_brand = (await s.execute(sql)).scalars().first()
                # if db_brand is None:
                #     return BrandNotFound()
            db_car = models.Car(name=name, brand=db_brand)
            s.add(db_car)
            await s.commit()
        return Car.marshal(db_car)

    @strawberry.mutation
    async def add_brand(self, name: str) -> AddBrandResponse:
        async with models.get_session() as s:
            sql = select(models.Brand).where(models.Brand.name == name)
            existing_db_brand = (await s.execute(sql)).first()
            if existing_db_brand is not None:
                return BrandExists()
            db_brand = models.Brand(name=name)
            s.add(db_brand)
            await s.commit()
        return Brand.marshal(db_brand)


@strawberry.type
class Query:
    @strawberry.field
    async def cars(self) -> list[Car]:
        async with models.get_session() as s:
            sql = select(models.Car).order_by(models.Car.name)
            db_cars = (await s.execute(sql)).scalars().unique().all()
        return [Car.marshal(cars) for cars in db_cars]

    @strawberry.field
    async def brands(self) -> list[Brand]:
        async with models.get_session() as s:
            sql = select(models.Brand).order_by(models.Brand.name)
            db_brands = (await s.execute(sql)).scalars().unique().all()
        return [Brand.marshal(loc) for loc in db_brands]


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQL(schema)

app = FastAPI()

@app.get("/")
def read_root():
    return {"GraphQL": "/graphql"}

app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)
