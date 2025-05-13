import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Adress, FirstActivation,
    Managers, ParcelData, PickUpPoint, PromocodeData, SupportLinks, UserData,
    Verification,
)


class DatabaseRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_pickup_points(self, city: str):

        pickup_points = await self._session.scalars(
            select(PickUpPoint).where(PickUpPoint.city == city)
        )

        return pickup_points.all()

    async def get_pickup_point(self, id: int):
        return await self._session.scalar(
            select(PickUpPoint)
            .where(PickUpPoint.id == id)
        )

    async def add_pickup_point(self, city: str, adress: str):
        new_pickup_point = PickUpPoint(
            city=city,
            adress=adress
        )
        self._session.add(new_pickup_point)
        await self._session.commit()

    async def delete_pickup_point(self, point_id: int):
        point = await self._session.scalar(
            select(PickUpPoint).where(PickUpPoint.id == point_id)
        )

        if point:
            await self._session.delete(point)
            await self._session.commit()

    async def add_user(
            self,
            tg_id,
            name,
            ucode,
            fullname,
            city,
            pickup_point,
            phone,
            promocode,
            discount=0,
            verify=0,
            balance=0,
    ):

        user = await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )

        if not user:
            new_user = UserData(
                tg_id=tg_id,
                name=name,
                uid=ucode,
                status='Розничный',
                fullname=fullname,
                city=city,
                pickup_points=pickup_point,
                phone=phone,
                discount=discount,
                promocode=promocode,
                verify=verify,
                balance=balance
            )
            self._session.add(new_user)
            await self._session.commit()

    async def user_verify(self, tg_id, verify):
        user = await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )
        if user:
            user.verify = verify
            await self._session.commit()

    async def edit_user(
            self,
            tg_id,
            name,
            ucode,
            fullname,
            city,
            phone,
            promocode,
    ):

        user = await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )

        if user:
            user.name = name
            user.uid = ucode
            user.fullname = fullname
            user.city = city
            user.phone = phone
            user.promocode = promocode
            await self._session.commit()

    async def edit_user_status(self, tg_id, new_status):
        statement = (
            update(UserData)
            .where(UserData.tg_id == tg_id)
            .values(status=new_status)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def update_user(self, tg_id: int, pickup_point: str | None = None):
        if pickup_point is None:
            return
        statement = (
            update(UserData)
            .where(UserData.tg_id == tg_id)
            .values(pickup_points=pickup_point)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def update_balance(self, user_uid, new_balance):
        statement = (
            update(UserData)
            .where(UserData.uid == user_uid)
            .values(balance=new_balance)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def update_user_promo(self, tg_id, promo):
        statement = (
            update(UserData)
            .where(UserData.tg_id == tg_id)
            .values(promo=promo)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def edit_user_discount(self, tg_id, discount):
        statement = (
            update(UserData)
            .where(UserData.tg_id == tg_id)
            .values(discount=discount)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def edit_user_promo(self, tg_id, promocode):
        statement = (
            update(UserData)
            .where(UserData.tg_id == tg_id)
            .values(promocode=promocode)
        )
        await self._session.execute(statement)
        await self._session.commit()

    async def get_users(self):
        return await self._session.scalars(select(UserData))

    async def get_user_by_uid(self, uid):
        return await self._session.scalar(
            select(UserData).where(UserData.uid == uid)
        )

    async def get_user(self, tg_id):
        return await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )

    async def get_last_ucode(self, is_osh: bool):
        query = select(UserData.uid)
        if is_osh:
            query = query.where(UserData.uid.like('OK%'))
        else:
            query = query.where(UserData.uid.like('UK%'))
        query = query.order_by(UserData.uid.desc()).limit(1)
        result = await self._session.scalar(query)
        return result

    async def get_users_by_promo(self, phone):
        users = await self._session.execute(
            select(UserData).where(UserData.promocode == phone)
        )

        items = users.fetchall()

        item_values = [item[0] for item in items]
        return item_values

    async def get_user_by_phone(self, phone):
        user = await self._session.scalar(
            select(UserData).where(UserData.phone == phone)
        )
        return user

    async def delete_user(self, uid):

        user = await self._session.scalar(
            select(UserData).where(UserData.uid == uid)
        )
        if user:
            verifys = await self._session.scalars(
                select(Verification).where(Verification.tg_id == user.tg_id)
            )
            for verify in verifys:
                await self._session.delete(verify)
            await self._session.delete(user)
        await self._session.commit()

    async def set_first_activation(self, tg_id, promocode):

        first_activation = await self._session.scalar(
            select(FirstActivation).where(FirstActivation.tg_id == tg_id)
        )
        print(first_activation)
        if first_activation:
            first_activation.promocode = promocode

        else:
            new_first_activation = FirstActivation(
                tg_id=tg_id,
                promocode=promocode
            )
            self._session.add(new_first_activation)
        await self._session.commit()

    async def get_first_activation(self, tg_id):

        first_activation = await self._session.scalar(
            select(FirstActivation).where(FirstActivation.tg_id == tg_id)
        )
        if first_activation:
            return first_activation.promocode
        else:
            return None

    # ВЕРИФИКАЦИИ

    async def add_verification(
            self, tg_id, uid, msg_id, file_id, recheck, area
    ):

        verification = await self._session.scalar(
            select(Verification).where(
                Verification.tg_id == tg_id, Verification.area == area
            )
        )

        if not verification:
            new_verification = Verification(
                tg_id=tg_id, uid=uid, msg_id=msg_id, file_id=file_id,
                area=area, recheck=recheck
            )
            self._session.add(new_verification)
            await self._session.commit()

        verification = await self._session.scalar(
            select(Verification).where(
                Verification.tg_id == tg_id, Verification.uid == uid,
                Verification.area == area
            )
        )
        return verification

    async def delete_old_verify(self, tg_id, area):

        verification = await self._session.scalar(
            select(Verification).where(
                Verification.tg_id == tg_id, Verification.area == area
            )
        )
        if verification:
            await self._session.delete(verification)
        await self._session.commit()

    async def verify_status_update(self, verify_id, response):

        verification = await self._session.scalar(
            select(Verification).where(Verification.id == verify_id)
        )
        verification.response = response
        await self._session.commit()

    async def get_verify(self, id):

        verification = await self._session.scalar(
            select(Verification).where(Verification.id == id)
        )
        return verification

    async def get_verify_by_tg_id_and_area(self, tg_id, area):

        verification = await self._session.scalar(
            select(Verification).where(
                Verification.tg_id == tg_id, Verification.area == area
            )
        )
        return verification

    async def get_verify_by_tgid(self, tg_id):

        verification = await self._session.execute(
            select(Verification).where(Verification.tg_id == tg_id)
        )
        items = verification.fetchall()

        verifications = [item[0] for item in items]
        return verifications

    async def edit_verify_response(self):

        verifications = await self._session.scalars(select(Verification))
        for verify in verifications:
            verify.response = 'Неверно'

        await self._session.commit()

    # ПОСЫЛКИ

    async def add_parcel(self, status, trackcode, uid, weight, date):

        new_parcel = ParcelData(
            datetime=date, status=status, trackcode=trackcode, uid=uid,
            weight=weight
        )
        self._session.add(new_parcel)

        await self._session.commit()

    async def update_parcel(
            self,
            trackcode, status=None, uid=None, weight=None, date=None
    ):

        parcel = await self._session.scalar(
            select(ParcelData).where(ParcelData.trackcode == trackcode)
        )
        if parcel:
            if uid is not None:
                parcel.uid = uid
            if status is not None:
                parcel.status = status
            if date is not None:
                parcel.datetime = date
            if weight is not None:
                parcel.weight = weight

        await self._session.commit()

    async def get_parcel_by_track_code(self, track_code):

        parcel = await self._session.scalar(
            select(ParcelData).where(ParcelData.trackcode == track_code)
        )
        return parcel

    async def get_parcels(self, uid):

        parcel = await self._session.execute(
            select(ParcelData).where(ParcelData.uid == uid)
        )

        items = parcel.fetchall()

        item_values = [item[0] for item in items]
        return item_values

    async def get_parcels_by_period(self, uid):

        start_date = datetime.datetime.now()

        end_date = start_date - datetime.timedelta(days=30)

        result = await self._session.scalars(
            select(ParcelData).where(
                ParcelData.datetime.between(start_date, end_date),
                ParcelData.uid == uid
            )
        )
        return result

    async def get_parcel(self, id):

        parcel = await self._session.scalar(
            select(ParcelData).where(ParcelData.id == id)
        )
        return parcel

    async def get_parcel_by_trackcode(self, trackcode):

        parcel = await self._session.scalar(
            select(ParcelData).where(ParcelData.trackcode == trackcode)
        )
        return parcel

    async def all_parcels(self):

        result = await self._session.scalars(select(ParcelData))
        return result.all()

    async def add_promocode(self, promocode):
        if promocode is None:
            return

        existing_promocode = await self._session.scalar(
            select(PromocodeData).where(
                PromocodeData.promocode == promocode
            )
        )

        if not existing_promocode:
            new_promocode = PromocodeData(promocode=promocode)
            self._session.add(new_promocode)
            await self._session.commit()

    async def get_promocode(self, promo):
        promo = await self._session.scalar(
            select(UserData).where(UserData.promo == promo)
        )
        if promo:
            return promo
        else:
            return None

    async def get_supports(self):
        return await self._session.scalars(select(SupportLinks))

    async def add_support(self, name, link):

        support = await self._session.scalar(
            select(SupportLinks).where(SupportLinks.name == name)
        )

        if not support:
            new_support = SupportLinks(name=name, link=link)
            self._session.add(new_support)
            await self._session.commit()

    async def delete_support(self, id):
        support = await self._session.scalar(
            select(SupportLinks).where(SupportLinks.id == id)
        )

        if support:
            await self._session.delete(support)
            await self._session.commit()

    # Адреса

    async def new_adress(
            self,
            main_adress,
            pinduoduo_example,
            taobao_example,
            _1688_example,
            poizon_example
    ):

        adress = await self._session.scalar(select(Adress))
        if adress is None:
            new_adress = Adress(
                main_adress=main_adress, pinduoduo_example=pinduoduo_example,
                taobao_example=taobao_example, _1688_example=_1688_example,
                poizon_example=poizon_example
            )
            self._session.add(new_adress)
        else:
            adress = await self._session.scalar(
                select(Adress).where(Adress.id == 1)
            )
            adress.main_adress = main_adress
            adress.pinduoduo_example = pinduoduo_example
            adress.taobao_example = taobao_example
            adress._1688_example = _1688_example
            adress.poizon_example = poizon_example
        await self._session.commit()

    async def get_adress(self):
        return await self._session.scalar(select(Adress))

    async def get_managers(self):
        return await self._session.scalars(select(Managers))

    async def add_manager(self, phone):

        manager = await self._session.scalar(
            select(Managers).where(Managers.phone == phone)
        )

        if not manager:
            new_manager = Managers(phone=phone)
            self._session.add(new_manager)
            await self._session.commit()

    async def del_manager(self, phone):

        manager = await self._session.scalar(
            select(Managers).where(Managers.phone == phone)
        )

        if manager:
            await self._session.delete(manager)
            await self._session.commit()

    # ------------------------------------------------

    async def edit_user_phone(self, tg_id, phone):

        user = await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )

        if user:
            user.phone = phone
            await self._session.commit()

    async def get_user_by_promo(self, promocode):

        user = await self._session.scalar(
            select(UserData).where(UserData.promo == promocode)
        )
        return user

    async def edit_user_promocode(self, tg_id, promocode):

        user = await self._session.scalar(
            select(UserData).where(UserData.tg_id == tg_id)
        )

        if user:
            user.promocode = promocode
            await self._session.commit()

    async def get_parcel_by_ucode(self, ucode):

        parcel = await self._session.scalars(
            select(ParcelData).where(ParcelData.uid == ucode)
        )
        return parcel
