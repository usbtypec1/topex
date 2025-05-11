from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import select

from src.config import SQLALCHEMY_URL
from sqlalchemy import ForeignKey

engine = create_async_engine(SQLALCHEMY_URL, echo=False)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class PickUpPoint(Base):
    __tablename__ = 'PickupPoints'

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column()
    adress: Mapped[str] = mapped_column()


class FirstActivation(Base):
    __tablename__ = 'FirstActivations'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    promocode: Mapped[int] = mapped_column()


class UserData(Base):
    __tablename__ = 'Users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column()
    uid: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    fullname: Mapped[str] = mapped_column()
    city: Mapped[str] = mapped_column()
    pickup_points: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column()
    discount: Mapped[int] = mapped_column()
    promocode: Mapped[str] = mapped_column()
    verify: Mapped[int] = mapped_column()
    promo: Mapped[str] = mapped_column(nullable=True)
    balance: Mapped[float] = mapped_column()


class ParcelData(Base):
    __tablename__ = 'Parcels'

    id: Mapped[int] = mapped_column(primary_key=True)
    datetime: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column()
    trackcode: Mapped[str] = mapped_column()
    uid: Mapped[str] = mapped_column(default=None, nullable=True)
    weight: Mapped[float] = mapped_column()
    usdprice: Mapped[float] = mapped_column(nullable=True)


class PromocodeData(Base):
    __tablename__ = 'Promocodes'

    id: Mapped[int] = mapped_column(primary_key=True)
    promocode: Mapped[str] = mapped_column()


class SupportLinks(Base):
    __tablename__ = 'Support'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    link: Mapped[str] = mapped_column()


class Verification(Base):
    __tablename__ = 'Verification'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column()
    uid: Mapped[str] = mapped_column()
    msg_id: Mapped[int] = mapped_column()
    file_id: Mapped[str] = mapped_column()
    area: Mapped[str] = mapped_column()
    recheck: Mapped[str] = mapped_column()
    response: Mapped[str] = mapped_column(nullable=True)


class Managers(Base):
    __tablename__ = 'Managers'

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[int] = mapped_column(BigInteger)


class Adress(Base):
    __tablename__ = 'Adress'

    id: Mapped[int] = mapped_column(primary_key=True)
    main_adress: Mapped[str] = mapped_column(nullable=True)
    pinduoduo_example: Mapped[str] = mapped_column(nullable=True)
    taobao_example: Mapped[str] = mapped_column(nullable=True)
    _1688_example: Mapped[str] = mapped_column(nullable=True)
    poizon_example: Mapped[str] = mapped_column(nullable=True)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
