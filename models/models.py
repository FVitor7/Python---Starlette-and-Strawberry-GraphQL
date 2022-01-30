from decouple import config
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Brand(Base):
    __tablename__ = "brands"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False, unique=True)

    cars: list["Car"] = relationship("Car", lazy="joined", back_populates="brand")


class Car(Base):
    __tablename__ = "cars"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)
    brand_id: Optional[int] = Column(Integer, ForeignKey(Brand.id), nullable=True)

    brand: Optional[Brand] = relationship(Brand, lazy="joined", back_populates="cars")

db_url = config('DB_URL') or "sqlite+aiosqlite:///./database.db"
print(db_url)
engine = create_async_engine(
    db_url, connect_args={"check_same_thread": False}
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            finally:
                await session.close()


async def _async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    print("Dropping and creating tables")
    asyncio.run(_async_main())
    print("Done.")
