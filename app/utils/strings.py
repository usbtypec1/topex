import re


import app.database.requests as db
from aiogram import Bot


async def registration_text(fullname=None, city=None, pickup_point=None, phone=None, promocode=None):
    if pickup_point:
        pp = await db.get_pickup_point(pickup_point)
        pickup_point = pp.adress
    
    if fullname and city and pickup_point and phone and promocode:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город: {city}\n"
            f"Пункт выдачи: {pickup_point}\n\n"
            f"Номер телефона: {phone}\n"
            f"Промокод: {promocode}\n\n"
        )
    elif fullname and city and pickup_point and phone:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город: {city}\n"
            f"Пункт выдачи: {pickup_point}\n"
            f"Номер телефона: {phone}\n\n"
            f"Введите промокод:"
        )
    elif fullname and city and pickup_point:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город: {city}\n"
            f"Пункт выдачи: {pickup_point}\n\n"
            f"Отправьте номер телефона:"
        )
    elif fullname and city:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город: {city}\n\n"
            f"Выберите пункт выдачи:"
        )
    elif fullname:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Ф.И.О.: {fullname}\n\n"
            f"Выберите город:"
        )
    else:
        text = (
            f"Добро пожаловать в TOPEX!\n\n"
            f"Для начала нужно зарегистрироваться!\n\n"
            f"Введите Ф.И.О. одним сообщением:"
        )

    return text


async def edit_user_text(uid=None, fullname=None, city=None, phone=None, promocode=None):
    if fullname and city and phone and promocode:
        text = (
            f"Личный код: {uid}\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город получения: {city}\n"
            f"Номер телефона: {phone}\n"
            f"Промокод: {promocode}\n\n"
        )
    elif fullname and city and phone:
        text = (
            f"Личный код: {uid}\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город получения: {city}\n"
            f"Номер телефона: {phone}\n\n"
            f"Введите промокод:"
        )
    elif fullname and city:
        text = (
            f"Личный код: {uid}\n"
            f"Ф.И.О.: {fullname}\n"
            f"Город получения: {city}\n\n"
            f"Отправьте номер телефона:"
        )
    elif fullname:
        text = (
            f"Личный код: {uid}\n"
            f"Ф.И.О.: {fullname}\n\n"
            f"Выберите город получения:"
        )
    else:
        text = (
            f"Личный код: {uid}\n\n"
            f"Отправьте Ф.И.О. одним сообщением:"
        )

    return text


async def user_personal_area(user_id):
    user = await db.get_user(user_id)

    weight = 0

    msg_txt = await user_info(user_id)

    users = await db.get_users_by_promo(user.phone)
    for userr in users:
        parcels = await db.get_parcels(userr.uid)
        try:
            for parcel in parcels:
                weight += round(parcel.weight, 2)
        except Exception as e:
            print(e)

    text = msg_txt + (
        f"\n\n*Ваш промокод:* `{user.phone}`"
        f"\n*Ваша пригласительная ссылка:*\n`https://t.me/topexpress_bot?start={user_id}`"
        f"\n➖➖➖➖➖➖➖➖"
        f"\nПриглашенных: *{len(users)}*"
        f"\nЗаработано: *{weight / 5:.2f}*"
        f"\n_Приглашенные заказали товаров весом {weight:.2f} кг._"
        f"\n➖➖➖➖➖➖➖➖"
        f"\nБаланс: *{user.balance:.2f}*"
    )

    return text


async def check_format(text):
    pattern = r'^UK\d{4}$'
    if re.match(pattern, text):
        return True
    else:
        return False


def validate_and_format_phone(phone):
    phone = re.sub(r"\D", "", phone)

    phone = re.sub(r"^(?:996|0)", "", phone)

    if len(phone) == 9:
        return phone
    else:
        return None


def clean_number(value):
    value = value.replace(',', '.')
    value = re.sub(r'[^0-9.]', '', value)
    return value


def check_next_step(total_weight):
    if total_weight < 100:
        return 100 - total_weight
    elif total_weight < 200:
        return 200 - total_weight
    elif total_weight < 300:
        return 300 - total_weight
    elif total_weight < 400:
        return 400 - total_weight
    elif total_weight < 500:
        return 500 - total_weight
    elif total_weight >= 500:
        return 0


def progressbar(key, total_weight, percent):
    total_weight = total_weight - key
    if 10 <= total_weight < 20:
        return f"▆▁▁▁▁▁▁▁▁▁ | {percent}% ☑️"
    elif 20 <= total_weight < 30:
        return f"▆▆▁▁▁▁▁▁▁▁ | {percent}% ☑️"
    elif 30 <= total_weight < 40:
        return f"▆▆▆▁▁▁▁▁▁▁ | {percent}% ☑️"
    elif 40 <= total_weight < 50:
        return f"▆▆▆▆▁▁▁▁▁▁ | {percent}% ☑️"
    elif 50 <= total_weight < 60:
        return f"▆▆▆▆▆▁▁▁▁▁ | {percent}% ☑️"
    elif 60 <= total_weight < 70:
        return f"▆▆▆▆▆▆▁▁▁▁ | {percent}% ☑️"
    elif 70 <= total_weight < 80:
        return f"▆▆▆▆▆▆▆▁▁▁ | {percent}% ☑️"
    elif 80 <= total_weight < 90:
        return f"▆▆▆▆▆▆▆▆▆▁▁ | {percent}% ☑️"
    elif 90 <= total_weight < 100:
        return f"▆▆▆▆▆▆▆▆▆▆▁ | {percent}% ☑️"
    elif 99 < total_weight >= 100:
        return f"▆▆▆▆▆▆▆▆▆▆ | {percent}% ✅"
    else:
        return f"▁▁▁▁▁▁▁▁▁▁ | {percent}% ☑️"


async def user_info(user_id):
    user = await db.get_user(user_id)
    msg_txt = (
        f"Личный код:                `{user.uid}`"
        f"\nФ.И.О.:                          {user.fullname}"
        f"\nГород получения:      {user.city}"
        F"\nПункт выдачи:           {user.pickup_points}"
        f"\nНомер телефона:      {user.phone}"
        f"\nПромокод:                   {user.promocode}"
    )
    return msg_txt


async def personal_disc(user_id):
    user = await db.get_user(user_id)
    parcels = await db.get_parcels(user.uid)
    
    total_weight = 0
    for parcel in parcels:
        total_weight += parcel.weight

    msg_txt = (
        f"*Ваша персональная скидка*"
        f"\nВес всех посылок {total_weight:.2f} кг."
        f"\nДо следующей цели {check_next_step(total_weight):.2f} кг."
        f"\n➖➖➖➖➖➖➖➖"
        f"\n{progressbar(0, total_weight, 1)}"
        f"\n{progressbar(100, total_weight, 2)}"
        f"\n{progressbar(200, total_weight, 3)}"
        f"\n{progressbar(300, total_weight, 4)}"
        f"\n{progressbar(400, total_weight, 5)}"
    )
    return msg_txt


async def UpdateUserDiscount():
    users = await db.get_users()
    for user in users:
        parcels = await db.get_parcels(user.uid)
        total_weight = 0
        for parcel in parcels:
            total_weight += parcel.weight
        if round(total_weight, 4) < 100:
            discount = 0
        elif 100 < round(total_weight, 4) < 200:
            discount = 1
        elif 200 < round(total_weight, 4) < 300:
            discount = 2
        elif 300 < round(total_weight, 4) < 400:
            discount = 3
        elif 400 < round(total_weight, 4) < 500:
            discount = 4
        elif 500 < round(total_weight, 4):
            discount = 5
        try:
            await db.edit_user_discount(user.tg_id, discount)
        except:
            pass


async def UpdateUsersType(bot: Bot):
    users = await db.get_users()
    for user in users:
        parcels = await db.get_parcels_by_period(user.uid)
        total_weight = 0
        for parcel in parcels:
            total_weight += parcel.weight

        if total_weight < 500:
            if user.status == 'Оптовый':
                new_status = 'Розничный'
                await db.edit_user_status(user.tg_id, new_status)
                await bot.send_message(chat_id=user.tg_id, text=f"Вы стали розничным клиентом.")
        else:
            if user.status == 'Розничный':
                new_status = 'Оптовый'
                await db.edit_user_status(user.tg_id, new_status)
                await bot.send_message(chat_id=user.tg_id, text=f"Вы стали оптовым клиентом.")


async def instruction_text(uid):
    adress = await db.get_adress()
    
    text = (
        f"*Адрес склада:*"
        f"\n`{adress.main_adress.replace('*КОД*', f'{uid}')}`"
        f"\n\n_Для проверки заполнения адреса, выберите приложение:_"
    )

    return text


async def adress_text(user_id, area):
    adress = await db.get_adress()
    user = await db.get_user(user_id)
    
    msg_text = (
        f"\n\n*Адрес склада:*"
        f"\n`{adress.main_adress.replace('*КОД*', f'{user.uid}')}`"
        f"\n\n*Заполните адрес доставки в приложении по примеру ниже и отправьте нам скриншот*"
    )

    if area == 'pinduoduo':
        msg_text += f"\n{adress.pinduoduo_example.replace('*КОД*', f'{user.uid}')}"
    elif area == 'taobao':
        msg_text += f"\n{adress.taobao_example.replace('*КОД*', f'{user.uid}')}"
    elif area == '1688':
        msg_text += f"\n{adress._1688_example.replace('*КОД*', f'{user.uid}')}"
    elif area == 'poizon':
        msg_text += f"\n{adress.poizon_example.replace('*КОД*', f'{user.uid}')}"

    return msg_text