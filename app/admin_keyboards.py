from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import app.database.requests as db
from src.const import const_ru


async def cancel(data: str):
    keyboard = InlineKeyboardBuilder()

    cancel = InlineKeyboardButton(text=const_ru['cancel'], callback_data=data)
    keyboard.row(cancel)

    return keyboard.as_markup()


async def confirm(confirm_data: str, cancel_data: str):
    keyboard = InlineKeyboardBuilder()

    confirm = InlineKeyboardButton(text=const_ru['confirm'], callback_data=confirm_data)
    cancel = InlineKeyboardButton(text=const_ru['cancel'], callback_data=cancel_data)
    keyboard.row(confirm, cancel)

    return keyboard.as_markup()


async def admin_main_menu():
    keyboard = InlineKeyboardBuilder()

    support = InlineKeyboardButton(text=const_ru['support'], callback_data=f'admin_support')
    pickup_points = InlineKeyboardButton(text=const_ru['pickup_points'], callback_data=f'edit_pickup_points')
    keyboard.row(support)
    keyboard.row(pickup_points)

    return keyboard.as_markup()


async def admin_pickup_points():
    keyboard = InlineKeyboardBuilder()

    bish = InlineKeyboardButton(text=const_ru['bishkek'], callback_data=f'admin_pickup_point:bishkek')
    osh = InlineKeyboardButton(text=const_ru['osh'], callback_data=f'admin_pickup_point:osh')
    chuy = InlineKeyboardButton(text=const_ru['chuy'], callback_data=f'admin_pickup_point:chuy')
    batken = InlineKeyboardButton(text=const_ru['batken'], callback_data=f'admin_pickup_point:batken')
    jalal = InlineKeyboardButton(text=const_ru['jalal-abad'], callback_data=f'admin_pickup_point:jalal-abad')
    naryn = InlineKeyboardButton(text=const_ru['naryn'], callback_data=f'admin_pickup_point:naryn')
    talas = InlineKeyboardButton(text=const_ru['talas'], callback_data=f'admin_pickup_point:talas')
    ik = InlineKeyboardButton(text=const_ru['ik'], callback_data=f'admin_pickup_point:ik')
    keyboard.row(bish, osh)
    keyboard.row(chuy, ik)
    keyboard.row(jalal, talas)
    keyboard.row(naryn, batken)
    back = InlineKeyboardButton(text=const_ru['back'], callback_data=f'admin_main_menu')
    keyboard.row(back)

    return keyboard.as_markup()


async def admin_pickup_point(city: str):
    keyboard = InlineKeyboardBuilder()

    points = await db.get_pickup_points(city)

    for point in points:
        point_btn = InlineKeyboardButton(text=point.adress, callback_data=f'admin_point_{point.id}')
        keyboard.row(point_btn)

    add_btn = InlineKeyboardButton(text=const_ru['add'], callback_data=f'add_point_{city}')
    back = InlineKeyboardButton(text=const_ru['back'], callback_data=f'edit_pickup_points')
    keyboard.row(add_btn)
    keyboard.row(back)

    return keyboard.as_markup()


async def admin_point(id: int):
    keyboard = InlineKeyboardBuilder()

    point = await db.get_pickup_point(id)

    delete = InlineKeyboardButton(text=const_ru['delete'], callback_data=f'delete_point_{id}')
    back = InlineKeyboardButton(text=const_ru['back'], callback_data=f'admin_pickup_point:{point.city}')
    keyboard.row(delete)
    keyboard.row(back)

    return keyboard.as_markup()


async def cncl_add_sprt():
    keyboard = InlineKeyboardBuilder()

    support = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cncl_add_sprt')
    keyboard.row(support)

    return keyboard.as_markup()


async def admin_supports_kb():
    supports = await db.get_supports()

    keyboard = InlineKeyboardBuilder()
    for support in supports:
        support = InlineKeyboardButton(text=support.name, url=support.link)
        keyboard.row(support)

    add_btns = InlineKeyboardButton(text=const_ru['add'], callback_data=f'add_support')
    edit_btns = InlineKeyboardButton(text=const_ru['delete'], callback_data=f'del_supp_none')
    back_btns = InlineKeyboardButton(text=const_ru['back'], callback_data=f'admin_main_menu')
    keyboard.row(add_btns)
    keyboard.row(edit_btns)
    keyboard.row(back_btns)

    return keyboard.as_markup()


async def admin_supports_del_kb():
    supports = await db.get_supports()

    keyboard = InlineKeyboardBuilder()
    for support in supports:
        support_btn = InlineKeyboardButton(text=support.name, url=support.link)
        del_sup = InlineKeyboardButton(text=const_ru['del_btn'], callback_data=f'del_supp_{support.id}')
        keyboard.row(support_btn, del_sup)

    cancel = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cncl_add_sprt')
    back_btns = InlineKeyboardButton(text=const_ru['back'], callback_data=f'admin_main_menu')
    keyboard.row(cancel)
    keyboard.row(back_btns)

    return keyboard.as_markup()


async def admin_verify_check(verify_id):
    keyboard = InlineKeyboardBuilder()

    right = InlineKeyboardButton(text=const_ru['right'], callback_data=f'admin_verify_right_{verify_id}')
    wrong = InlineKeyboardButton(text=const_ru['wrong'], callback_data=f'admin_verify_wrong_{verify_id}')
    keyboard.row(right, wrong)

    return keyboard.as_markup()


async def admin_user_profile(user_uid):
    keyboard = InlineKeyboardBuilder()

    add_blnc = InlineKeyboardButton(text=const_ru['add_blnc'], callback_data=f'balance_add_{user_uid}')
    decr_blnc = InlineKeyboardButton(text=const_ru['del_blnc'], callback_data=f'balance_del_{user_uid}')
    close = InlineKeyboardButton(text=const_ru['close'], callback_data=f'close_message')
    keyboard.row(add_blnc, decr_blnc)
    keyboard.row(close)

    return keyboard.as_markup()


async def cncl_edit_blnc(user_uid):
    keyboard = InlineKeyboardBuilder()

    close = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cancel_edit_balance_{user_uid}')
    keyboard.row(close)

    return keyboard.as_markup()





