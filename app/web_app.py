import datetime
from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    async_sessionmaker, AsyncEngine,
    AsyncSession, create_async_engine,
)

from config import ROOT_PATH
from database.repository import DatabaseRepository


async def get_engine() -> AsyncGenerator[AsyncEngine, None]:
    database_path = ROOT_PATH / 'DataBase.sqlite3'
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{str(database_path)}", echo=False
    )
    yield engine
    await engine.dispose()


async def get_session(
        engine: AsyncEngine = Depends(get_engine),
) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine)
    async with session_factory() as session:
        yield session


def get_repository(
        session: AsyncSession = Depends(get_session),
) -> DatabaseRepository:
    return DatabaseRepository(session)


app = FastAPI()


class Parcel(BaseModel):
    date: datetime.date
    trackcode: str
    uid: str
    weight: float
    status: str


@app.get("/parcels")
async def get_parcels(
        status: str,
        database_repository: DatabaseRepository = Depends(get_repository),
):
    parcels = await database_repository.get_parcels_by_status(status)
    return {
        'parcels': [
            {
                'date': parcel.datetime,
                'trackcode': parcel.trackcode,
                'uid': parcel.uid,
                'weight': parcel.weight,
                'status': parcel.status,
            }
            for parcel in parcels
        ]
    }



class ParcelsGivenIn(BaseModel):
    track_codes: set[str]


@app.post('/parcels/given')
async def add_parcel(
        parcels_given_in: ParcelsGivenIn,
        database_repository: DatabaseRepository = Depends(get_repository),
):
    print(parcels_given_in)
    return 200
