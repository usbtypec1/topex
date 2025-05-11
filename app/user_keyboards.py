from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, SwitchInlineQueryChosenChat
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import app.database.requests as db
from src.const import const_ru
from src.config import reg_web, channel_link

contact_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отправить номер ☎️', request_contact=True)]
], resize_keyboard=True, one_time_keyboard=False)


async def cancel_kb(callback_data):
    keyboard = InlineKeyboardBuilder()

    cancel_btn = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'{callback_data}')
    keyboard.add(cancel_btn)

    return keyboard.as_markup()


async def return_kb(callback_data):
    keyboard = InlineKeyboardBuilder()

    return_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'{callback_data}')
    keyboard.add(return_btn)

    return keyboard.as_markup()


async def select_pickup_point(city):
    keyboard = InlineKeyboardBuilder()

    points = await db.get_pickup_points(city)

    for i in points:
        keyboard.row(InlineKeyboardButton(text=f'{i.adress}', callback_data=f'user_point:{i.id}'))

    return keyboard.as_markup()


async def select_city_kb():
    keyboard = InlineKeyboardBuilder()

    bish = InlineKeyboardButton(text=const_ru['bishkek'], callback_data=f'bishkek')
    osh = InlineKeyboardButton(text=const_ru['osh'], callback_data=f'osh')
    chuy = InlineKeyboardButton(text=const_ru['chuy'], callback_data=f'chuy')
    batken = InlineKeyboardButton(text=const_ru['batken'], callback_data=f'batken')
    jalal = InlineKeyboardButton(text=const_ru['jalal-abad'], callback_data=f'jalal-abad')
    naryn = InlineKeyboardButton(text=const_ru['naryn'], callback_data=f'naryn')
    talas = InlineKeyboardButton(text=const_ru['talas'], callback_data=f'talas')
    ik = InlineKeyboardButton(text=const_ru['ik'], callback_data=f'ik')
    keyboard.row(bish, osh)
    keyboard.row(chuy, ik)
    keyboard.row(jalal, talas)
    keyboard.row(naryn, batken)

    return keyboard.as_markup()


async def skip_promocode_kb():
    keyboard = InlineKeyboardBuilder()

    bish = InlineKeyboardButton(text=const_ru['skip'], callback_data=f'skippromo')
    keyboard.row(bish)

    return keyboard.as_markup()


async def select_area():
    keyboard = InlineKeyboardBuilder()

    pinduoduo = InlineKeyboardButton(text=const_ru['pinduoduo'], callback_data=f'area_pinduoduo')
    taobao = InlineKeyboardButton(text=const_ru['taobao'], callback_data=f'area_taobao')
    _1688 = InlineKeyboardButton(text=const_ru['1688'], callback_data=f'area_1688')
    poizon = InlineKeyboardButton(text=const_ru['poizon'], callback_data=f'area_poizon')
    keyboard.row(pinduoduo, taobao)
    keyboard.row(_1688, poizon)

    return keyboard.as_markup()


async def close_kb():
    keyboard = InlineKeyboardBuilder()
    
    close_btn = InlineKeyboardButton(text=const_ru['close'], callback_data=f'close_start_message')
    keyboard.row(close_btn)
    
    return keyboard.as_markup()


async def share_link_kb(user_id):
    keybaord = InlineKeyboardBuilder()
    
    link = InlineKeyboardButton(text=const_ru['topexpress'], url=f'https://t.me/topexpress_bot?start={user_id}')
    keybaord.row(link)
    
    return keybaord.as_markup()


async def users_main_kb(user_id):
    keyboard = InlineKeyboardBuilder()

    user = await db.get_user(user_id)

    reverse_data = {v: k for k, v in const_ru.items()}  
    key = reverse_data.get(user.city)  

    #add_promo = InlineKeyboardButton(text=const_ru['add_promo'], callback_data=f'add_promo')
    #if user.promocode == 'Отсутствует':
    #    keyboard.row(add_promo)

    invite = InlineKeyboardButton(
        text=const_ru['share_link'],
        switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
            allow_bot_chats=True,
            allow_group_chats=True,
            allow_channel_chats=True
        )
    )

    pickup_point = InlineKeyboardButton(text='🆕 ' + const_ru['select_pickup_point'] + f': {user.pickup_points}', callback_data=f'user_pickup_points:{key}')
    personal = InlineKeyboardButton(text=const_ru['personal'], callback_data=f'personal_area')
    parcels = InlineKeyboardButton(text=const_ru['parcels'], callback_data=f'parcels_')
    instruction = InlineKeyboardButton(text=const_ru['instruction'], callback_data=f'instruction')
    support = InlineKeyboardButton(text=const_ru['support'], callback_data=f'support')
    reg_webb = InlineKeyboardButton(text=const_ru['reg_on_website'], url=reg_web)
    product_channel = InlineKeyboardButton(text=const_ru['product_channel'], url=channel_link)
    keyboard.row(invite)
    keyboard.row(pickup_point)
    keyboard.row(personal)
    keyboard.row(parcels)
    keyboard.row(instruction, support)
    keyboard.row(reg_webb)
    keyboard.row(product_channel)

    return keyboard.as_markup()


async def pickup_points(city: str, user_id: int):
    keyboard = InlineKeyboardBuilder()

    user = await db.get_user(user_id)

    points = await db.get_pickup_points(city)

    for point in points:
        if point.adress == user.pickup_points:
            keyboard.row(InlineKeyboardButton(text=f'✅ {point.adress}', callback_data=f'user_point:{point.id}'))
        else:
            keyboard.row(InlineKeyboardButton(text=f'{point.adress}', callback_data=f'user_point:{point.id}'))

    keyboard.row(InlineKeyboardButton(text=const_ru['back'], callback_data=f'main_menu'))

    return keyboard.as_markup()


async def user_instruction_kb(user_id):
    keyboard = InlineKeyboardBuilder() 

    pinduoduo = await db.get_verify_by_tg_id_and_area(user_id, 'pinduoduo')
    if pinduoduo:
        if pinduoduo.response == 'Все верно ✓':
            pinduoduo_text = const_ru['pinduoduo'] + " ✅"
        elif pinduoduo.response is None:
            pinduoduo_text = const_ru['pinduoduo'] + " ♻️"
        elif pinduoduo.response.startswith('Неверно'):
            pinduoduo_text = const_ru['pinduoduo'] + " ❌"
    else:
        pinduoduo_text = const_ru['pinduoduo']

    taobao = await db.get_verify_by_tg_id_and_area(user_id, 'taobao')
    if taobao:
        if taobao.response == 'Все верно ✓':
            taobao_text = const_ru['taobao'] + " ✅"
        elif taobao.response is None:
            taobao_text = const_ru['taobao'] + " ♻️"
        elif taobao.response.startswith('Неверно'):
            taobao_text = const_ru['taobao'] + " ❌"
    else:
        taobao_text = const_ru['taobao']

    _1688 = await db.get_verify_by_tg_id_and_area(user_id, '1688')
    if _1688:
        if _1688.response == 'Все верно ✓':
            _1688_text = const_ru['1688'] + " ✅"
        elif _1688.response is None:
            _1688_text = const_ru['1688'] + " ♻️"
        elif _1688.response.startswith('Неверно'):
            _1688_text = const_ru['1688'] + " ❌"
    else:
        _1688_text = const_ru['1688']

    poizon = await db.get_verify_by_tg_id_and_area(user_id, 'poizon')
    if poizon:
        if poizon.response == 'Все верно ✓':
            poizon_text = const_ru['poizon'] + " ✅"
        elif poizon.response is None:
            poizon_text = const_ru['poizon'] + " ♻️"
        elif poizon.response.startswith('Неверно'):
            poizon_text = const_ru['poizon'] + " ❌"
    else:
        poizon_text = const_ru['poizon']

    pinduoduo = InlineKeyboardButton(text=pinduoduo_text, callback_data=f'area_recheck_pinduoduo')
    taobao = InlineKeyboardButton(text=taobao_text, callback_data=f'area_recheck_taobao')
    _1688 = InlineKeyboardButton(text=_1688_text, callback_data=f'area_recheck_1688')
    poizon = InlineKeyboardButton(text=poizon_text, callback_data=f'area_recheck_poizon')
    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'main_menu')

    keyboard.row(pinduoduo, taobao)
    keyboard.row(_1688, poizon)
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def user_verify_kb():
    keyboard = InlineKeyboardBuilder()
    
    verify = InlineKeyboardButton(text=const_ru['repeat'], callback_data=f'verify')
    keyboard.row(verify)

    return keyboard.as_markup()


async def cancel_verify_kb():
    keyboard = InlineKeyboardBuilder()

    back_btn = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cancel_verify')
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def user_pers_kb(tg_id):
    keyboard = InlineKeyboardBuilder()

    add_promo = InlineKeyboardButton(text=const_ru['add_promo'], callback_data=f'add_promo')
    edit_data = InlineKeyboardButton(text=const_ru['edit_data'], callback_data=f'edit_data')
    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'main_menu')

    user = await db.get_user(tg_id)
    if user.promocode == 'Отсутствует':
        keyboard.row(add_promo)
    keyboard.row(edit_data)
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def cancel_edit_data():
    keyboard = InlineKeyboardBuilder()

    back_btn = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cancel_edit_data')
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def select_city_kb2():
    keyboard = InlineKeyboardBuilder()

    bish = InlineKeyboardButton(text=const_ru['bishkek'], callback_data=f'bishkek')
    osh = InlineKeyboardButton(text=const_ru['osh'], callback_data=f'osh')
    chuy = InlineKeyboardButton(text=const_ru['chuy'], callback_data=f'chuy')
    batken = InlineKeyboardButton(text=const_ru['batken'], callback_data=f'batken')
    jalal = InlineKeyboardButton(text=const_ru['jalal-abad'], callback_data=f'jalal-abad')
    naryn = InlineKeyboardButton(text=const_ru['naryn'], callback_data=f'naryn')
    talas = InlineKeyboardButton(text=const_ru['talas'], callback_data=f'talas')
    ik = InlineKeyboardButton(text=const_ru['ik'], callback_data=f'ik')
    back_btn = InlineKeyboardButton(text=const_ru['cancel'], callback_data=f'cancel_edit_data')
    keyboard.row(bish, osh)
    keyboard.row(chuy, ik)
    keyboard.row(jalal, talas)
    keyboard.row(naryn, batken)
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def user_supports_kb():
    supports = await db.get_supports()

    keyboard = InlineKeyboardBuilder()
    for support in supports:
        support = InlineKeyboardButton(text=support.name, url=support.link)
        keyboard.row(support)

    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'main_menu')
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def close_message():
    keyboard = InlineKeyboardBuilder()

    close = InlineKeyboardButton(text=const_ru['close'], callback_data=f'close_message')
    keyboard.row(close)

    return keyboard.as_markup()


def close_message2():
    keyboard = InlineKeyboardBuilder()

    close = InlineKeyboardButton(text=const_ru['close'], callback_data=f'close_message')
    keyboard.row(close)

    return keyboard.as_markup()


async def user_parcels(uid, page, items_per_page=14):
    keyboard = InlineKeyboardBuilder()

    parcels = await db.get_parcels(uid)
    parcels = [parcel for parcel in parcels if parcel.status not in ["Оплачен", "Отдан"]]
    parcels.reverse()

    total_pages = (len(parcels) + items_per_page - 1) // items_per_page

    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_parcels = parcels[start_index:end_index]

    i = 0
    for parcel in parcels:
        if parcel.status == 'Прибыл':
            i += 1

    for parcel in current_parcels:
        if parcel.status == 'Оформлен':
            emoji = '🏷 '
        elif parcel.status == 'На складе':
            emoji = '📦 '
        elif parcel.status == 'В пути':
            emoji = '🚚 '
        elif parcel.status == 'Прибыл':
            emoji = '📥 '
        else:
            emoji = ''

        parcel = InlineKeyboardButton(text=emoji + parcel.trackcode, callback_data=f'parcel_{parcel.id}_{page}')
        keyboard.row(parcel)

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(InlineKeyboardButton(text=const_ru['yback'], callback_data=f'parcels_{page - 1}'))
    else:
        pagination_buttons.append(InlineKeyboardButton(text=const_ru['nback'], callback_data=f'current_page'))

    pagination_buttons.append(InlineKeyboardButton(text=f'{page} / {total_pages}', callback_data='current_page'))
    if end_index < len(parcels):
        pagination_buttons.append(InlineKeyboardButton(text=const_ru['yforward'], callback_data=f'parcels_{page + 1}'))
    else:
        pagination_buttons.append(InlineKeyboardButton(text=const_ru['nforward'], callback_data=f'current_page'))

    search = InlineKeyboardButton(text=const_ru['search'], callback_data=f'search_parcel')
    keyboard.row(search)
    keyboard.row(*pagination_buttons)

    if i != 0:
        arrange_deivery = InlineKeyboardButton(text=const_ru['arrange_deivery'], callback_data=f'arrange_deivery_{page}')
        keyboard.row(arrange_deivery)

    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'main_menu')
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def cncl_arrange_deivery(page):
    keyboard = InlineKeyboardBuilder()

    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'parcels_{page}')
    keyboard.row(back_btn)

    return keyboard.as_markup()


async def user_parcel(page):
    keyboard = InlineKeyboardBuilder()

    back_btn = InlineKeyboardButton(text=const_ru['back'], callback_data=f'parcels_{page}')
    keyboard.row(back_btn)

    return keyboard.as_markup()
