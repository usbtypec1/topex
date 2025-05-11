import asyncio
import traceback
from datetime import datetime
from aiogram import Bot
from aiogram import Router, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext

from src.middlewares import AlbumMiddleware

from app.database.requests import add_user, get_user
from app.utils.strings import check_format, personal_disc, instruction_text, \
    user_info, validate_and_format_phone, adress_text, registration_text, \
    edit_user_text, user_personal_area
from app.utils.states import Registration, EditData, AddPromo, Verification, Delivery, Search
from src.config import bot_username
from src.const import const_ru
from loader import bot
import app.database.requests as db
import app.user_keyboards as kb


router = Router()
router.message.middleware(AlbumMiddleware())
# router.message.middleware(StateClearMw())


@router.message(CommandStart(deep_link=True))
async def start(message: Message, state: FSMContext, command: CommandObject=None):
    user_id = message.chat.id

    user = await get_user(user_id)
    if user is None:
        promo = None
        pickup_point = None
        city = None
        if command is not None:
            try:
                _id = int(command.args)
                user = await db.get_user(_id)
                promo = user.phone
                await db.set_first_activation(user_id, promo)
                await message.answer(f'Применен промокод {promo}')
            except:
                if command.args.startswith('point_'):
                    pickup_point = command.args.split('_')[1]
                    pp = await db.get_pickup_point(pickup_point)
                    if pp:
                        pickup_point = pp.id
                        city = const_ru[f'{pp.city}']
                else:
                    await message.answer('Ссылка не действительна. Напишите /start, что бы начать регистрацию без промокода.\nПромокод можно добавить в процессе регистрации или после регистрации в личном кабинете!')
                    return

        mess = await message.answer(await registration_text())
        await state.update_data(message_id=mess.message_id, promo=promo, pickup_point=pickup_point, city=city)
        await state.set_state(Registration.FullName)
    else:
        user = await db.get_user(user_id)
        if user.verify == 1:
            msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(user_id)
            await message.answer(msg_txt, reply_markup=await kb.users_main_kb(message.from_user.id), parse_mode='Markdown')
        else:
            verify = await db.get_verify_by_tgid(user_id)

            if len(verify) > 0:
                verifications = 0
                no_verifications = 0
                for i in verify:
                    if i.response == 'Все верно ✓':
                        verifications += 1
                    elif i.response is None:
                        ...
                    elif i.response.startswith('Неверно'):
                        no_verifications += 1
                
                if verifications > 0:
                    msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(user_id)
                    await message.answer(msg_txt, reply_markup=await kb.users_main_kb(message.from_user.id), parse_mode='Markdown')
                if no_verifications > 0:
                    await message.answer(f"Вы не прошли проверку.\nНам нужно проверить правильность заполнения адреса.\n\nВыберите приложение которым пользуетесь:", reply_markup=await kb.select_area(), parse_mode='Markdown')
                else:
                    msg_txt = (
                        f"Ваши данные на проверке. Ожидайте...\n\n_Данные проверяются с 9:00 до 18:00._"
                    )
                    await message.answer(msg_txt, reply_markup=await kb.close_message(), parse_mode='Markdown')
            else:
                await message.answer(f"Вы еще не проходили проверку.\nНам нужно проверить правильность заполнения адреса.\n\nВыберите приложение которым пользуетесь:", reply_markup=await kb.select_area(), parse_mode='Markdown')
                await state.set_state(Registration.Area)

    try:
        await message.delete()
    except:
        pass


@router.callback_query(F.data == 'main_menu')
async def main_menu(call: CallbackQuery):
    await call.answer('Главное меню...')
    
    user_id = call.from_user.id

    msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(user_id) + "\n\n" + await personal_disc(user_id)
    
    await call.message.edit_text(msg_txt, reply_markup=await kb.users_main_kb(user_id), parse_mode='Markdown')


@router.message(Registration.FullName, F.text)
async def registration_step_3(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    promo = data.get("promo")
    pickup_point = data.get("pickup_point")
    city = data.get("city")

    fullname = message.text
    if fullname == '/start':
        mess = await message.answer(await registration_text())
        await state.update_data(message_id=mess.message_id, promo=promo)
        await state.set_state(Registration.FullName)
        return

    if pickup_point:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
        new_message = await bot.send_message(
            chat_id=message.from_user.id,
            text=await registration_text(fullname, city, pickup_point),
            reply_markup=kb.contact_kb,
        )
        await state.update_data(message_id=new_message.message_id, fullname=fullname, promo=promo, pickup_point=pickup_point)
        await state.set_state(Registration.Phone)
        return

    try:
        await bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=message_id,
            text=await registration_text(fullname),
            reply_markup=await kb.select_city_kb(),
        )
    except:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=await registration_text(fullname),
            reply_markup=await kb.select_city_kb(),
        )

    await state.update_data(fullname=fullname, promo=promo)
    await state.set_state(Registration.City)
    await message.delete()


@router.callback_query(Registration.City)
async def registration_step_4(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    
    city = const_ru[f'{call.data}']

    await call.message.edit_text(
        text=await registration_text(fullname, city),
        reply_markup=await kb.select_pickup_point(call.data),
    )
    
    await state.update_data(message_id=message_id, city=city)
    await state.set_state(Registration.PickUpPoint)


@router.callback_query(Registration.PickUpPoint)
async def select_pickup_point(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    city = data.get("city")
    promo = data.get("promo")

    pickup_point = call.data.split(':')[1]

    await bot.delete_message(chat_id=call.from_user.id, message_id=message_id)
    new_message = await bot.send_message(
        chat_id=call.from_user.id,
        text=await registration_text(fullname, city, pickup_point),
        reply_markup=kb.contact_kb,
    )

    await state.update_data(message_id=new_message.message_id, city=city, promo=promo, pickup_point=pickup_point)
    await state.set_state(Registration.Phone)


@router.message(Registration.Phone)
async def registration_step_5(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    city = data.get("city")
    pickup_point = data.get("pickup_point")
    promo = data.get("promo")
    if promo is None:
        promo = await db.get_first_activation(message.from_user.id)

    try:
        phone = validate_and_format_phone(message.contact.phone_number)
    except:
        phone = None

    if message.text and message.text == '/start':
        mess = await message.answer(await registration_text())
        await state.update_data(message_id=mess.message_id, promo=promo)
        await state.set_state(Registration.FullName)        
        return

    if phone is None:
        phone = validate_and_format_phone(message.text)
        if phone is None:
            await state.set_state(Registration.Phone)
            return
        else:
            user = await db.get_user_by_phone(phone)
            if user:
                await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
                new_message = await bot.send_message(
                    chat_id=message.from_user.id,
                    text=(await registration_text(fullname, city, pickup_point)).rsplit('\n', 1)[0] + "\nТакой номер уже зарегистрирован! Введите другой номер!",
                    reply_markup=kb.contact_kb,
                )

                await state.update_data(message_id=new_message.message_id)
                await state.set_state(Registration.Phone)
                return
    
    if promo:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
        await finish_registration(message, message.from_user.id, message.from_user.first_name, fullname, city, pickup_point, phone, promo, state)
    else:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
        new_message = await bot.send_message(
            chat_id=message.from_user.id,
            text=await registration_text(fullname, city, pickup_point, phone),
            reply_markup=await kb.skip_promocode_kb(),
        )

        await state.update_data(message_id=new_message.message_id, fullname=fullname, city=city, phone=phone)
        await state.set_state(Registration.Promo)

    await message.delete()


@router.message(Registration.Promo, F.text)
async def registration_step_6(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    city = data.get("city")
    pickup_point = data.get("pickup_point")
    phone = data.get("phone")

    if message.text and message.text == '/start':
        mess = await message.answer(await registration_text())
        await state.update_data(message_id=mess.message_id)
        await state.set_state(Registration.FullName)        
        return

    inviter_phone = message.text
    if inviter_phone is None:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=message_id,
                text=(await registration_text(fullname, city, pickup_point, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                reply_markup=await kb.skip_promocode_kb(),            
            )
        except:
            pass
        await state.set_state(Registration.Promo)
        return
    else:
        inviter = await db.get_user_by_phone(inviter_phone)
        if inviter:
            if inviter_phone == inviter.phone:
                await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
                await finish_registration(message, message.from_user.id, message.from_user.full_name, fullname, city, phone, inviter_phone, state)

        else:
            try:
                await bot.edit_message_text(
                    chat_id=message.from_user.id,
                    message_id=message_id,
                    text=(await registration_text(fullname, city, pickup_point, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                    reply_markup=await kb.skip_promocode_kb(),            
                )
            except:
                pass
            await state.set_state(Registration.Promo)
            return

    await message.delete()


@router.callback_query(Registration.Promo)
async def registration_step_6(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fullname = data.get("fullname")
    city = data.get("city")
    pickup_point = data.get("pickup_point")
    phone = data.get("phone")
    
    promocode = '0'
    await finish_registration(call, call.from_user.id, call.from_user.full_name, fullname, city, pickup_point, phone, promocode, state)


async def finish_registration(data, tg_id, name, fullname, city, pickup_point, phone, promocode, state: FSMContext):
    ucode1 = await db.get_last_ucode(city == 'Ош')
    if city == 'Ош':
        if ucode1 is None:
            ucode1 = 'OK0001'
        else:
            number_str = ucode1[2:]
            number = int(number_str) + 1
            ucode1 = ucode1[:2] + str(number).zfill(len(number_str))
    else:
        if ucode1 is None:
            ucode1 = 'UK5001'
        else:
            number_str = ucode1[2:]
            number = int(number_str) + 1
            ucode1 = ucode1[:2] + str(number).zfill(len(number_str))

    if promocode == '0':
        promocode = 'Отсутствует'

    pp = await db.get_pickup_point(pickup_point)

    await add_user(
        tg_id=tg_id,
        name=name,
        ucode=ucode1,
        fullname=fullname,
        city=city,
        pickup_point=pp.adress,
        phone=phone,
        promocode=promocode,
    )

    msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(tg_id) + f"\n\n_Данные можно изменить в личном кабинете_"

    if isinstance(data, Message):
        await data.answer(msg_txt, parse_mode='Markdown')
        await data.answer(f"Нам нужно проверить правильность заполнения адреса.\n\nВыберите приложение которым пользуетесь:", reply_markup=await kb.select_area())
        # await state.update_data(dataa=mess, dataa2=mess2)
    elif isinstance(data, CallbackQuery):
        await data.message.edit_text(msg_txt, parse_mode='Markdown')
        await data.message.answer(f"Нам нужно проверить правильность заполнения адреса.\n\nВыберите приложение которым пользуетесь:", reply_markup=await kb.select_area())
        # await state.update_data(dataa=cdata, dataa2=cdata2)

    await state.set_state(Registration.Area)


@router.callback_query(F.data.startswith('area_'))
@router.callback_query(Registration.Area)
async def select_area(call: CallbackQuery, state: FSMContext):
    if call.data.split('_')[1] == 'recheck':
        area = call.data.split('_')[2]
        recheck = True
    else:
        area = call.data.split('_')[1]
        recheck = False
    
    await call.answer(f"Вы выбрали {const_ru[f'{area}']}")

    msg_text = await adress_text(call.from_user.id, area)

    if recheck is True:
        keyboard = await kb.return_kb('instruction')
    else:
        keyboard = None
    
    await call.message.edit_text(msg_text, reply_markup=keyboard, parse_mode='Markdown')

    await state.update_data(message_id=call.message.message_id, area=area, recheck=recheck)
    await state.set_state(Verification.photo)


@router.message(Verification.photo, F.photo)
async def verify_photo(message: Message, state: FSMContext, album: list = None):
    data = await state.get_data()
    message_id = data.get("message_id")
    area = data.get("area")
    new_message_id = data.get("new_message_id")
    
    file_ids = []
    if album:
        for msg in album:
            if isinstance(msg, Message):
                file_ids.append(msg.photo[-1].file_id)
                await msg.delete()

    elif message.photo:
        file_ids.append(message.photo[0].file_id)
    else:
        new_message = await message.answer('\nСкриншот не найден, повторите попытку:', parse_mode='MarkdownV2')
        msg_text = await adress_text(message.from_user.id, area)

        await state.update_data(new_message_id=msg_text.message_id)
        await state.set_state(Verification.photo)
        return

    recheck = data.get("recheck")
    if recheck is None:
        keyboard = None
    else:
        keyboard = await kb.return_kb('instruction')

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text='\nСкриншот отправлен на проверку. Ожидайте...\n\n_Данные проверяются с 9:00 до 18:00._',
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

    await db.delete_old_verify(message.from_user.id, area)

    user = await db.get_user(message.from_user.id)
    verify = await db.add_verification(user.tg_id, user.uid, message_id, str(file_ids), recheck, area)

    await state.clear()
    from app.admin import send_verify_msg
    await send_verify_msg(verify.id)
    if new_message_id:
        await bot.delete_message(chat_id=message.from_user.id, message_id=new_message_id)
    await message.delete()


async def user_verify_notify(verify_id, state: FSMContext):
    verify = await db.get_verify(verify_id)
    user = await db.get_user(verify.tg_id)
    try:
        await bot.delete_message(user.tg_id, verify.msg_id)
    except:
        pass
    
    if verify.response == 'Все верно ✓':
        await db.user_verify(user.tg_id, 1)
        msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(verify.tg_id)
        
        await bot.send_message(user.tg_id, 'Проверка пройдена!', parse_mode='Markdown')
        await bot.send_message(user.tg_id, msg_txt, reply_markup=await kb.users_main_kb(verify.tg_id), parse_mode='Markdown')
    else:
        if verify.recheck == 1:
            msg_txt = f"Вы не прошли проверку!\n\n{verify.response}"
            keyboard = await kb.return_kb('instruction')
        else:
            msg_txt = (
                f"Вы не прошли проверку!"
                f"\n\n{verify.response}"
                f"\n\nНам нужно проверить правильность заполнения адреса.\n\nВыберите приложение которым пользуетесь:"
            )
            keyboard = await kb.select_area()

        await bot.send_message(user.tg_id, msg_txt, reply_markup=keyboard, parse_mode='Markdown')


@router.callback_query(F.data == 'personal_area')
async def personal_area(call: CallbackQuery):
    user_id = call.from_user.id

    msg_txt = await user_personal_area(user_id)
    try:
        await call.message.edit_text(msg_txt, reply_markup=await kb.user_pers_kb(call.from_user.id), parse_mode='Markdown')
    except:
        await call.answer(msg_txt, reply_markup=await kb.user_pers_kb(call.from_user.id), parse_mode='Markdown')


@router.callback_query(F.data.startswith('user_pickup_points:'))
async def pickup_points(call: CallbackQuery):
    city = call.data.split(':')[1]

    user = await db.get_user(call.from_user.id)
    if user.pickup_points:
        text = f"Пункт выдачи: {user.pickup_points}"
    else:
        text = f"Выберите пункт выдачи:"

    await call.message.edit_text(text, reply_markup=await kb.pickup_points(city, call.from_user.id), parse_mode='Markdown')


@router.callback_query(F.data.startswith('user_point:'))
async def pickup_point(call: CallbackQuery):
    point_id = call.data.split(':')[1]

    point = await db.get_pickup_point(point_id)

    await db.update_user(call.from_user.id, point.adress)

    await call.message.edit_text(f"Пункт выдачи: {point.adress}", reply_markup=await kb.pickup_points(point.city, call.from_user.id), parse_mode='Markdown')


@router.callback_query(F.data == 'edit_data')
async def edit_data(call: CallbackQuery, state: FSMContext):
    await call.answer('Изменение данных...')
    
    user = await db.get_user(call.from_user.id)
    
    await call.message.edit_text(await edit_user_text(user.uid), reply_markup=await kb.cancel_edit_data())

    await state.update_data(call_id=call.id, message_id=call.message.message_id)
    await state.set_state(EditData.FullName)


@router.callback_query(F.data == 'cancel_edit_data')
async def edit_data(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('Отмена 🔸')

    await personal_area(call)


@router.message(EditData.FullName, F.text)
async def edit_data_name(message: Message, state: FSMContext):

    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = message.text

    user = await db.get_user(message.from_user.id)
    
    if fullname == '/start':
        mess = await message.answer(await edit_user_text(user.uid))
        await state.update_data(message_id=mess.message_id)
        await state.set_state(EditData.FullName)
        return

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=await edit_user_text(user.uid, fullname),
        reply_markup=await kb.select_city_kb2(),
    )

    await state.update_data(fullname=fullname)
    await state.set_state(EditData.City)
    
    await message.delete()


@router.callback_query(EditData.City)
async def edit_data_city(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fullname = data.get("fullname")
    message_id = data.get("message_id")

    city = const_ru[f'{call.data}']

    user = await db.get_user(call.from_user.id)

    message = await bot.send_message(
        chat_id=call.from_user.id,
        text=await edit_user_text(user.uid, fullname, city),
        reply_markup=kb.contact_kb
    ) 

    await bot.delete_message(chat_id=call.from_user.id, message_id=message_id)

    await state.update_data(message_id=message.message_id, city=city)
    await state.set_state(EditData.Phone)


@router.message(EditData.Phone)
async def edit_data_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    city = data.get("city")

    if message.text and message.text == '/start':
        user = await db.get_user(message.from_user.id)

        mess = await message.answer(await edit_user_text(user.uid))
        await state.update_data(message_id=mess.message_id)
        await state.set_state(EditData.FullName)
        return

    try:
        phone = validate_and_format_phone(message.contact.phone_number)
    except:
        phone = None

    if phone is None:
        phone = validate_and_format_phone(message.text)
        if phone is None:
            await state.set_state(EditData.Phone)
            return
        else:
            user = await db.get_user_by_phone(phone)
            if user:
                mess = await bot.send_message(
                    chat_id=message.from_user.id,
                    text=(await edit_user_text(user.uid, fullname, city)).rsplit('\n', 1)[0] + "\nТакой номер уже зарегистрирован! Введите другой номер!",
                    reply_markup=kb.contact_kb
                )

                await state.update_data(message_id=mess.message_id)
                await state.set_state(EditData.Phone)
                return
        
    await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
    await message.delete()
    user = await db.get_user(message.from_user.id)

    if user.promocode == 'Отсутствует':
        mess = await message.answer(
            await edit_user_text(user.uid, fullname, city, phone),
            reply_markup=await kb.skip_promocode_kb()
        )
        await state.update_data(message_id=mess.message_id, phone=phone)
        await state.set_state(EditData.Promo)
    else:
        await finish_edit_data(message, message.from_user.id, message.from_user.first_name, fullname, city, phone, user.promocode)
        await state.clear()


@router.message(EditData.Promo)
async def edit_data_promo(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    fullname = data.get("fullname")
    city = data.get("city")
    phone = data.get("phone")

    tg_id = message.from_user.id
    name = message.from_user.first_name

    user = await db.get_user(tg_id)
    
    if message.text and message.text == '/start':
        mess = await message.answer(await edit_user_text(user.uid))
        await state.update_data(message_id=mess.message_id)
        await state.set_state(EditData.FullName)
        return

    inviter_phone = message.text
    if inviter_phone is None:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=message_id,
                text=(await edit_user_text(user.uid, fullname, city, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                reply_markup=await kb.skip_promocode_kb()
            )
        except:
            await bot.send_message(
                chat_id=message.from_user.id,
                text=(await edit_user_text(user.uid, fullname, city, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                reply_markup=await kb.skip_promocode_kb()
            )
            pass
        await state.set_state(EditData.Promo)
        await message.delete()
        return
    else:
        inviter = await db.get_user_by_phone(inviter_phone)
        if inviter:
            if inviter_phone == inviter.phone:
                await bot.delete_message(chat_id=message.from_user.id, message_id=message_id)
                await finish_edit_data(message, tg_id, name, fullname, city, phone, inviter_phone)
                await state.clear()
        else:
            try:
                await bot.edit_message_text(
                    chat_id=message.from_user.id,
                    message_id=message_id,
                    text=(await edit_user_text(user.uid, fullname, city, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                    reply_markup=await kb.skip_promocode_kb()
                )
            except:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=(await edit_user_text(user.uid, fullname, city, phone)).rsplit('\n', 1)[0] + "\nПромокод не действителен, повторите попытку:",
                    reply_markup=await kb.skip_promocode_kb()
                )
            await message.delete()
            await state.set_state(EditData.Promo)
            return


@router.callback_query(EditData.Promo)
async def edit_data_promo(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fullname = data.get("fullname")
    city = data.get("city")
    phone = data.get("phone")

    promocode = '0'

    tg_id = call.from_user.id
    name = call.from_user.first_name

    await finish_edit_data(call, tg_id, name, fullname, city, phone, promocode)
    await state.clear()


async def finish_edit_data(data, tg_id, name, fullname, city, phone, promocode):
    if promocode == '0':
        promocode = 'Отсутствует'
    user = await db.get_user(tg_id)
    
    await db.edit_user(
        tg_id=tg_id,
        name=name,
        ucode=user.uid,
        fullname=fullname,
        city=city,
        phone=phone,
        promocode=promocode,
    )

    if isinstance(data, Message):
        try:
            await data.delete()
        except:
            pass
    if isinstance(data, CallbackQuery):
        try:
            await data.message.delete()
        except:
            pass

    msg_txt = await user_personal_area(tg_id)
    await bot.send_message(tg_id, msg_txt, reply_markup=await kb.user_pers_kb(tg_id), parse_mode='Markdown')


@router.callback_query(F.data == 'add_promo')
async def add_promo(call: CallbackQuery, state: FSMContext):
    await call.answer('Активация промокода...')

    msg_txt = (
        f"\n\nВведите промокод:"
    )
    await call.message.edit_text(msg_txt, reply_markup=await kb.cancel_kb('main_menu'), parse_mode='Markdown')

    await state.update_data(message_id=call.message.message_id)
    await state.set_state(AddPromo.Promo)


@router.message(AddPromo.Promo)
async def edit_data_promo(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    
    user = await db.get_user(message.from_user.id)

    phone = message.text
    if phone is None:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=message_id,
                text=f"Промокод не действителен, повторите попытку:",
                reply_markup=await kb.cancel_kb('main_menu'),
                parse_mode='Markdown'
            )
        except:
            await bot.send_message(
                chat_id=message.from_user.id,
                text=f"Промокод не действителен, повторите попытку:",
                reply_markup=await kb.cancel_kb('main_menu'),
                parse_mode='Markdown'
            )
            
        await state.set_state(AddPromo.Promo)
        return
    else:
        phone_owner = await db.get_user_by_phone(phone)
        user = await db.get_user(message.from_user.id)
        if phone_owner:
            if phone != user.phone:
                await db.edit_user_promo(message.from_user.id, phone)
                await bot.edit_message_text(
                    chat_id=message.from_user.id,
                    message_id=message_id,
                    text=f"Промокод {phone} успешно активирован!",
                    reply_markup=await kb.cancel_kb('main_menu'),
                    parse_mode='Markdown'
                )
                await state.clear()
            else:
                try:
                    await bot.edit_message_text(
                        chat_id=message.from_user.id,
                        message_id=message_id,
                        text=f"Вы не можете использовать собственный промокод!\n\nПовторите попытку:",
                        reply_markup=await kb.cancel_kb('main_menu'),
                        parse_mode='Markdown'
                    )
                except:
                    await bot.send_message(
                        chat_id=message.from_user.id,
                        text=f"Вы не можете использовать собственный промокод!\n\nПовторите попытку:",
                        reply_markup=await kb.cancel_kb('main_menu'),
                        parse_mode='Markdown'
                    )
                    
                await state.set_state(AddPromo.Promo)
                return
        else:
            try:
                await bot.edit_message_text(
                    chat_id=message.from_user.id,
                    message_id=message_id,
                    text=f"\n\nПромокод не действителен, повторите попытку:",
                    reply_markup=await kb.cancel_kb('main_menu'),
                    parse_mode='Markdown'
                )
            except:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=f"\n\nПромокод не действителен, повторите попытку:",
                    reply_markup=await kb.cancel_kb('main_menu'),
                    parse_mode='Markdown'
                )
                
            await state.set_state(AddPromo.Promo)
            return

    await message.delete()


@router.callback_query(F.data == 'support')
async def support(call: CallbackQuery):
    await call.message.edit_text('Поддержка 🔹', reply_markup=await kb.user_supports_kb())


@router.callback_query(F.data == 'instruction')
async def instruction(call: CallbackQuery):
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    
    text = await instruction_text(user.uid)

    await call.message.edit_text(text, reply_markup=await kb.user_instruction_kb(user_id), parse_mode='Markdown')
    

@router.callback_query(F.data == 'close_message')
async def close_message(call: CallbackQuery):
    await call.message.delete()


@router.callback_query(F.data.startswith('parcels_'))
async def parcels(call: CallbackQuery, state: FSMContext):
    await state.clear()

    if len(call.data) > 8:
        page = call.data.split('_')[1]
    else:
        page = 1

    user_id = call.from_user.id
    user = await db.get_user(user_id)
    parcels = await db.get_parcels(user.uid)

    parcel_len = len(parcels)
    total_weight = 0

    for parcel in parcels:
        total_weight += round(parcel.weight, 1)

    msg_txt = (
        f"Посылки 📦"
        f"\n\nВсего посылок: {parcel_len}"
        f"\nОбщий вес посылок: {total_weight:.2f} кг."
        f"\n\nВаши посылки:"
    )

    if parcels:
        try:
            await call.message.edit_text(msg_txt, reply_markup=await kb.user_parcels(user.uid, int(page)), parse_mode='Markdown')
        except:
            print(traceback.format_exc())
    else:
        try:
            await call.message.edit_text('У вас еще нет посылок 📦', reply_markup=await kb.user_parcels(user.uid, int(page)), parse_mode='Markdown')
        except:
            print(traceback.format_exc())


@router.callback_query(F.data.startswith('arrange_deivery_'))
async def arrange_deivery(call: CallbackQuery, state: FSMContext):
    page = call.data.split('_')[2]
    
    await call.message.edit_text('Введите полный адрес одним сообщением:', reply_markup=await kb.cncl_arrange_deivery(page))
    await state.update_data(call_id=call.id, message_id=call.message.message_id, page=page) 
    await state.set_state(Delivery.adress) 


@router.message(Delivery.adress)
async def delivery_adress(message: Message, state: FSMContext):
    data = await state.get_data()
    call_id = data.get("call_id")
    message_id = data.get("message_id")
    page = data.get("page")

    user_id = message.from_user.id

    if message.text:
        adress = message.text
    else:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=message_id,
                text='Введите полный адрес одним сообщением:',
                reply_markup=await kb.cncl_arrange_deivery(page)
            )
        except:
            pass
        return

    try:
        await bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=message_id,
            text=f"Заявка на доставку оформлена. С вами свяжется менеджер",
            reply_markup=None
        )
    except:
        print(traceback.format_exc())

    from app.admin import send_delivery_message
    await send_delivery_message(user_id, adress)

    await state.clear()
    await start(message, state)

    await message.delete()


@router.callback_query(F.data.startswith('parcel_'))
async def parcel(call: CallbackQuery):
    data = call.data.split('_')
    parcel_id = data[1]
    page = data[2]

    parcel = await db.get_parcel(parcel_id)

    try:
        date_obj = datetime.strptime(parcel.datetime, "%Y-%m-%d %H:%M:%S.%f")
        data =  date_obj.strftime("%d.%m.%Y")
    except:
        data = parcel.datetime

    msg_txt = (
        f"Трек код: `{parcel.trackcode}`"
        f"\nСтатус: *{parcel.status}*"
        f"\n\nВес: *{parcel.weight} кг.*"
        f"\nДата прибытия на склад: *{data if data is not None else 'Неизвестно'}*"
    )
    await call.answer(f'Посылка {parcel.trackcode}')
    await call.message.edit_text(msg_txt, reply_markup=await kb.user_parcel(int(page)), parse_mode='Markdown')


@router.callback_query(F.data == 'search_parcel')
async def search_parcel(call: CallbackQuery, state: FSMContext):
    await call.answer('Поиск...')
    await call.message.edit_text('Введите трек код:', reply_markup=await kb.cancel_kb('parcels_'))
    
    await state.update_data(call_id=call.id, message_id=call.message.message_id)
    await state.set_state(Search.TrackCode)


@router.message(Search.TrackCode, F.text)
async def search_parcel_trackcode(message: Message, state: FSMContext):
    data = await state.get_data()
    call_id = data.get("call_id")
    message_id = data.get("message_id")
    
    trackcode = message.text
    parcel = await db.get_parcel_by_trackcode(trackcode)

    if message.text == '/start':
        msg_txt = f"Добро пожаловать в TOPEX!\n" + await user_info(message.from_user.id)
        await message.answer(msg_txt, reply_markup=await kb.users_main_kb(message.from_user.id), parse_mode='Markdown')
        await state.clear()
        return

    if parcel:
        user = await db.get_user(message.from_user.id)
        await db.update_parcel(parcel.trackcode, parcel.status, user.uid, parcel.weight, parcel.datetime)
        msg_txt = (
            f"Трек код: `{parcel.trackcode}`"
            f"\nСтатус: *{parcel.status}*"
            # f"\n\nВес: *{parcel.weight} кг.*"
            # f"\nСтоимость: *{parcel.usdprice:.2f} $*"
        )
        await bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=message_id,
            text=msg_txt,
            reply_markup=await kb.return_kb('parcels_'),
            parse_mode='Markdown'
        )
        await state.clear()
    else:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=message_id,
                text='Посылка не найдена!\n\nВведите трек код:',
                reply_markup=await kb.cancel_kb('parcels_')
            )
        except:
            pass
    
    await message.delete()


@router.callback_query(Search.TrackCode)
async def cncl_search_parcel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await parcels(call)


@router.message()
async def message(message: Message, state: FSMContext):
    await message.delete()
    await start(message, state)


@router.inline_query()
async def share(inline_query: InlineQuery):
    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id="share",
                title="Поделиться своей ссылкой",
                description="Нажмите, что бы поделиться своей ссылкой",
                input_message_content=InputTextMessageContent(
                    message_text=f'Отличный сервис для дешевой и надежной доставки!\nПодробнее по кнопке ниже!',
                    parse_mode='Markdown'
                ),
                reply_markup=await kb.share_link_kb(inline_query.from_user.id) 
            )
        ],
        cache_time=1,
    )
