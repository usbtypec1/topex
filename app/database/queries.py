import datetime

from sqlalchemy import select

from app.database.models import (
    Adress, async_session, FirstActivation,
    Managers, ParcelData, PickUpPoint, PromocodeData, SupportLinks, UserData,
    Verification,
)


# ПУНКТЫ ВЫДАЧИ

async def get_pickup_points(city: str):
    async with async_session() as session:
        pickup_points = await session.scalars(select(PickUpPoint).where(PickUpPoint.city == city))

        return pickup_points.all()


async def get_pickup_point(id: int):
    async with async_session() as session:
        pickup_point = await session.scalar(select(PickUpPoint).where(PickUpPoint.id == id))

        return pickup_point


async def add_pickup_point(city: str, adress: str):
    async with async_session() as session:
        new_pickup_point = PickUpPoint(
            city=city,
            adress=adress
        )
        session.add(new_pickup_point)
        await session.commit()


async def delete_pickup_point(point_id: int):
    async with async_session() as session:
        point = await session.scalar(select(PickUpPoint).where(PickUpPoint.id == point_id))

        if point:
            await session.delete(point)
            await session.commit()


# ПОЛЬЗОВАТЕЛИ

async def add_user(tg_id, name, ucode, fullname, city, pickup_point, phone, promocode, discount=0, verify=0, balance=0):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

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
            session.add(new_user)
            await session.commit()


async def user_verify(tg_id, verify):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.verify = verify
            await session.commit()
            
            
async def edit_user(tg_id, name, ucode, fullname, city, phone, promocode):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.name = name
            user.uid = ucode
            user.fullname = fullname
            user.city = city
            user.phone = phone
            user.promocode = promocode
            await session.commit()


async def edit_user_status(tg_id, new_status):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.status = new_status
            await session.commit()


async def update_user(tg_id: int, pickup_point: str = None):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            if pickup_point:
                user.pickup_points = pickup_point
            await session.commit()


async def update_balance(user_uid, new_balance):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.uid == user_uid))

        if user:
            user.balance = new_balance
            await session.commit()


async def update_user_promo(tg_id, promo):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.promo = promo
            await session.commit()


async def edit_user_discount(tg_id, discount):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))
        if user:
            user.discount = discount
            await session.commit()


async def edit_user_promo(tg_id, promocode):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.promocode = promocode
            await session.commit()


async def get_users():
    async with async_session() as session:
        result = await session.scalars(select(UserData))
        return result


async def get_user_by_uid(uid):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.uid == uid))
        return user


async def get_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))
        return user


async def get_last_ucode(is_osh: bool):
    async with async_session() as session:
        query = select(UserData.uid)
        if is_osh:
            query = query.where(UserData.uid.like('OK%'))
        else:
            query = query.where(UserData.uid.like('UK%'))
        query = query.order_by(UserData.uid.desc()).limit(1)
        result = await session.scalar(query)
        return result


async def get_users_by_promo(phone):
    async with async_session() as session:
        users = await session.execute(select(UserData).where(UserData.promocode == phone))

        items = users.fetchall()

        item_values = [item[0] for item in items]
        return item_values


async def get_user_by_phone(phone):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.phone == phone))
        return user


async def delete_user(uid):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.uid == uid))
        if user:
            verifys = await session.scalars(select(Verification).where(Verification.tg_id == user.tg_id))
            for verify in verifys:
                await session.delete(verify)
            await session.delete(user)
        await session.commit()


async def set_first_activation(tg_id, promocode):
    async with async_session() as session:
        first_activation = await session.scalar(select(FirstActivation).where(FirstActivation.tg_id == tg_id))
        print(first_activation)
        if first_activation:
            first_activation.promocode = promocode
            
        else:
            new_first_activation = FirstActivation(
                tg_id=tg_id,
                promocode=promocode
            )
            session.add(new_first_activation)
        await session.commit()


async def get_first_activation(tg_id):
    async with async_session() as session:
        first_activation = await session.scalar(select(FirstActivation).where(FirstActivation.tg_id == tg_id))
        if first_activation:
            return first_activation.promocode
        else:
            return None

# ВЕРИФИКАЦИИ

async def add_verification(tg_id, uid, msg_id, file_id, recheck, area):
    async with async_session() as session:
        verification = await session.scalar(select(Verification).where(Verification.tg_id == tg_id, Verification.area == area))

        if not verification:
            new_verification = Verification(tg_id=tg_id, uid=uid, msg_id=msg_id, file_id=file_id, area=area, recheck=recheck)
            session.add(new_verification)
            await session.commit()

        verification = await session.scalar(select(Verification).where(Verification.tg_id == tg_id, Verification.uid == uid, Verification.area == area))
        return verification


async def delete_old_verify(tg_id, area):
    async with async_session() as session:
        verification = await session.scalar(select(Verification).where(Verification.tg_id == tg_id, Verification.area == area))
        if verification:
            await session.delete(verification)
        await session.commit()


async def verify_status_update(verify_id, response):
    async with async_session() as session:
        verification = await session.scalar(select(Verification).where(Verification.id == verify_id))
        verification.response = response
        await session.commit()


async def get_verify(id):
    async with async_session() as session:
        verification = await session.scalar(select(Verification).where(Verification.id == id))
        return verification


async def get_verify_by_tg_id_and_area(tg_id, area):
    async with async_session() as session:
        verification = await session.scalar(select(Verification).where(Verification.tg_id == tg_id, Verification.area == area))
        return verification


async def get_verify_by_tgid(tg_id):
    async with async_session() as session:
        verification = await session.execute(select(Verification).where(Verification.tg_id == tg_id))
        items = verification.fetchall()

        verifications = [item[0] for item in items]
        return verifications


async def edit_verify_response():
    async with async_session() as session:
        verifications = await session.scalars(select(Verification))
        for verify in verifications:
            verify.response = 'Неверно'
        
        await session.commit()


# ПОСЫЛКИ

async def add_parcel(status, trackcode, uid, weight, date):
    async with async_session() as session:
        new_parcel = ParcelData(datetime=date, status=status, trackcode=trackcode, uid=uid, weight=weight)
        session.add(new_parcel)

        await session.commit()


async def update_parcel(trackcode, status=None, uid=None, weight=None, date=None):
    async with async_session() as session:
        parcel = await session.scalar(select(ParcelData).where(ParcelData.trackcode == trackcode))
        if parcel:
            if uid is not None:
                parcel.uid = uid
            if status is not None:
                parcel.status = status
            if date is not None:
                parcel.datetime = date
            if weight is not None:
                parcel.weight = weight

        await session.commit()


async def get_parcel_by_track_code(track_code):
    async with async_session() as session:
        parcel = await session.scalar(select(ParcelData).where(ParcelData.trackcode == track_code))
        return parcel


async def get_parcels(uid):
    async with async_session() as session:
        parcel = await session.execute(select(ParcelData).where(ParcelData.uid == uid))

        items = parcel.fetchall()

        item_values = [item[0] for item in items]
        return item_values


async def get_parcels_by_period(uid):
    async with async_session() as session:
        start_date = datetime.datetime.now()

        end_date = start_date - datetime.timedelta(days=30)

        result = await session.scalars(
            select(ParcelData).where(
                ParcelData.datetime.between(start_date, end_date),
                ParcelData.uid == uid
            )
        )
        return result


async def get_parcel(id):
    async with async_session() as session:
        parcel = await session.scalar(select(ParcelData).where(ParcelData.id == id))
        return parcel


async def get_parcel_by_trackcode(trackcode):
    async with async_session() as session:
        parcel = await session.scalar(select(ParcelData).where(ParcelData.trackcode == trackcode))
        return parcel


async def all_parcels():
    async with async_session() as session:
        result = await session.scalars(select(ParcelData))
        return result.all()


# ПРОМОКОДЫ

async def add_promocode(promocode):
    if promocode is None:
        return

    async with async_session() as session:
        existing_promocode = await session.scalar(select(PromocodeData).where(PromocodeData.promocode == promocode))

        if not existing_promocode:
            new_promocode = PromocodeData(promocode=promocode)
            session.add(new_promocode)
            await session.commit()


async def get_promocode(promo):
    async with async_session() as session:
        promo = await session.scalar(select(UserData).where(UserData.promo == promo))
        if promo:
            return promo
        else:
            return None


# ПОДДЕРЖКА

async def get_supports():
    async with async_session() as session:
        result = await session.scalars(select(SupportLinks))
        return result
    
    
async def add_support(name, link):
    async with async_session() as session:
        support = await session.scalar(select(SupportLinks).where(SupportLinks.name == name))

        if not support:
            new_support = SupportLinks(name=name, link=link)
            session.add(new_support)
            await session.commit()


async def delete_support(id):
    async with async_session() as session:
        support = await session.scalar(select(SupportLinks).where(SupportLinks.id == id))

        if support:
            await session.delete(support)
            await session.commit()


# Адреса

async def new_adress(main_adress, pinduoduo_example, taobao_example, _1688_example, poizon_example):
    async with async_session() as session:
        adress = await session.scalar(select(Adress))
        if adress is None:
            new_adress = Adress(main_adress=main_adress, pinduoduo_example=pinduoduo_example, taobao_example=taobao_example, _1688_example=_1688_example, poizon_example=poizon_example)
            session.add(new_adress)
        else:
            adress = await session.scalar(select(Adress).where(Adress.id == 1))
            adress.main_adress = main_adress
            adress.pinduoduo_example = pinduoduo_example
            adress.taobao_example = taobao_example
            adress._1688_example = _1688_example
            adress.poizon_example = poizon_example
        await session.commit()


async def get_adress():
    async with async_session() as session:
        adress = await session.scalar(select(Adress))
        return adress


# Менеджеры

async def get_managers():
    async with async_session() as session:
        result = await session.scalars(select(Managers))
        return result


async def add_manager(phone):
    async with async_session() as session:
        manager = await session.scalar(select(Managers).where(Managers.phone == phone))

        if not manager:
            new_manager = Managers(phone=phone)
            session.add(new_manager)
            await session.commit()


async def del_manager(phone):
    async with async_session() as session:
        manager = await session.scalar(select(Managers).where(Managers.phone == phone))

        if manager:
            await session.delete(manager)
            await session.commit()


# ------------------------------------------------


async def edit_user_phone(tg_id, phone):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.phone = phone
            await session.commit()


async def get_user_by_promo(promocode):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.promo == promocode))
        return user


async def edit_user_promocode(tg_id, promocode):
    async with async_session() as session:
        user = await session.scalar(select(UserData).where(UserData.tg_id == tg_id))

        if user:
            user.promocode = promocode
            await session.commit()


async def get_parcel_by_ucode(ucode):
    async with async_session() as session:
        parcel = await session.scalars(select(ParcelData).where(ParcelData.uid == ucode))
        return parcel


