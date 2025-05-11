import ast

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.media_group import MediaGroupBuilder

from app.const import const_ru
from app.config import Admin, get_admins, bot_username
from loader import bot

from app.states import AddSupport, Verification, EditBalance
import app.database.requests as db
import app.admin_keyboards as kb

admin_router = Router()


@admin_router.message(Admin(), Command('admin'))
async def mstart(message: Message):
    await message.answer('Админ-панель:', reply_markup=await kb.admin_main_menu())
    await message.delete()
    
    
@admin_router.callback_query(Admin(), F.data.startswith('admin_main_menu'))
async def cstart(call: CallbackQuery):
    await call.message.edit_text('Админ-панель:', reply_markup=await kb.admin_main_menu())


@admin_router.callback_query(Admin(), F.data == 'edit_pickup_points')
async def pickup_points(call: CallbackQuery):
    await call.message.edit_text('Редактирование пунктов самовывоза:', reply_markup=await kb.admin_pickup_points())


@admin_router.callback_query(Admin(), F.data.startswith('admin_pickup_point:'))
async def pickup_point(call: CallbackQuery, state: FSMContext):
    await state.clear()

    city = call.data.split(':')[1]

    await call.message.edit_text(
        f'Редактирование пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.admin_pickup_point(city)
    )


@admin_router.callback_query(Admin(), F.data.startswith('add_point_'))
async def add_point(call: CallbackQuery, state: FSMContext):
    city = call.data.split('_')[2]

    await call.message.edit_text(
        f'Введите адрес пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.cancel(f'admin_pickup_point:{city}')
    )

    await state.update_data(city=city, call_id=call.id, message_id=call.message.message_id)
    await state.set_state('PickUpPoint.Adress')


@admin_router.message(Admin(), StateFilter('PickUpPoint.Adress'), F.text)
async def adress(message: Message, state: FSMContext):
    data = await state.get_data()
    city = data.get('city')
    message_id = data.get('message_id')

    await db.add_pickup_point(city, message.text)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=f'Редактирование пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.admin_pickup_point(city)
    )

    await state.clear()
    await message.delete()


@admin_router.callback_query(Admin(), F.data.startswith('admin_point_'))
async def admin_point(call: CallbackQuery):
    data = call.data.split('_')
    point = await db.get_pickup_point(data[2])

    await call.message.edit_text(
        (
            f'Город: {const_ru[point.city]}\n'
            f'Пункт выдачи: {point.adress}\n\n'
            f'Ссылка для qr кода:\n'
            f'https://t.me/{bot_username}?start=point_{point.id}'
        ),
        reply_markup=await kb.admin_point(point.id)
    )



@admin_router.callback_query(Admin(), F.data.startswith('delete_point_'))
async def delete_point(call: CallbackQuery):
    
    data = call.data.split('_')
    point = await db.get_pickup_point(data[2])

    if len(data) == 3:
        await call.message.edit_text(
            f'Удалить пункт выдачи {point.adress}',
            reply_markup=await kb.confirm(f'delete_point_{point.id}_coonfirm', f'admin_pickup_point:{point.city}')
        )
    else:
        await db.delete_pickup_point(point.id)

        await call.message.edit_text(
            f'Редактирование пункта самовывоза: {const_ru[point.city]}',
            reply_markup=await kb.admin_pickup_point(point.city)
        )


@admin_router.callback_query(Admin(), F.data == 'admin_support')
async def support(call: CallbackQuery):
    await call.message.edit_text('Поддержка:', reply_markup=await kb.admin_supports_kb())


@admin_router.callback_query(Admin(), F.data == 'cncl_add_sprt')
async def cncl_add_sprt(call: CallbackQuery, state: FSMContext):
    await call.answer('Отмена 🔸')
    await support(call)
    await state.clear()


@admin_router.callback_query(Admin(), F.data == 'add_support')
async def add_support(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите название:', reply_markup=await kb.cncl_add_sprt())
    await state.update_data(message_id=call.message.message_id)
    await state.set_state(AddSupport.Name)


@admin_router.message(AddSupport.Name)
async def add_support_name(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    
    name = message.text
    if name is None:
        await state.set_state(AddSupport.Name)
        return

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=f'Название: {name}\nВведите ссылку:',
        reply_markup=await kb.cncl_add_sprt()
    )

    await state.update_data(name=name)
    await state.set_state(AddSupport.Link)
    
    await message.delete()
    

@admin_router.message(AddSupport.Link)
async def add_support_link(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    name = data.get("name")

    link = message.text
    if link is None:
        await state.set_state(AddSupport.Link)
        return

    await db.add_support(name, link)

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=f'Название: {name}\nСсылка: {link}',
        reply_markup=None,
        disable_web_page_preview=True
    )

    await bot.send_message(message.from_user.id, 'Поддержка:', reply_markup=await kb.admin_supports_kb())

    await state.clear()
    await message.delete()


@admin_router.callback_query(Admin(), F.data.startswith('del_supp_'))
async def delete_support(call: CallbackQuery):
    support_id = call.data.split('_')[2]
    if support_id == 'none':
        await call.message.edit_text(f'Для удаления нажмите на "✖️":', reply_markup=await kb.admin_supports_del_kb())
    else:
        await db.delete_support(support_id)
        await call.answer(f'Поддержка удалена...')
    
        await call.message.edit_text(f'Для удаления нажмите на "✖️":', reply_markup=await kb.admin_supports_del_kb())


async def send_verify_msg(verify_id):
    verify = await db.get_verify(verify_id)
    user = await db.get_user(verify.tg_id)

    mess = (
        f"Заявка на проверку от"
        f'\nФ.И.О.: <a href="tg://user?id={user.tg_id}">{user.fullname}</a>'
        f"\nUID: {user.uid}"
        f"\nНомер телефона: {user.phone}"
    )

    mess += f"\n\nПлощадка: {const_ru[f'{verify.area}']}"

    admins = get_admins()

    media = MediaGroupBuilder()
    for i in ast.literal_eval(verify.file_id):
        media.add_photo(i)

    for admin in admins:
        await bot.send_media_group(admin, media=media.build())
        await bot.send_message(admin, text=mess, reply_markup=await kb.admin_verify_check(verify_id), parse_mode='HTML')


@admin_router.callback_query(Admin(), F.data.startswith('admin_verify_'))
async def verify_check(call: CallbackQuery, state: FSMContext):
    loyalty = call.data.split('_')[2]
    verify_id = call.data.split('_')[3]

    verify = await db.get_verify(verify_id)
    if verify:
        if loyalty == 'right':
            response = 'Все верно ✓'
            await db.verify_status_update(verify_id, response)
            await call.message.edit_text(text=call.message.html_text + f'\n\nОтвет: {response}', reply_markup=None, parse_mode='HTML')
            from app.user import user_verify_notify
            await user_verify_notify(verify_id, state)
        elif loyalty == 'wrong':
            response = 'Неверно ✗'
            await call.message.edit_text(text=call.message.html_text + f'\n\nОтвет: {response}\nДобавьте комментарий:', reply_markup=None, parse_mode='HTML')
            await state.update_data(message_id=call.message.message_id, message_text=call.message.html_text, response=response, verify_id=verify_id)
            await state.set_state(Verification.response)
    else:
        await call.message.edit_text(text=call.message.html_text + '\n\nНе актуально.', reply_markup=None, parse_mode='HTML')


@admin_router.message(Verification.response)
async def verify_response(message: Message, state: FSMContext):
    await message.delete()
    
    data = await state.get_data()
    message_id = data.get("message_id")
    message_text = data.get("message_text")
    response = data.get("response")
    verify_id = data.get("verify_id")

    if message.text:
        text = message.text
    else:
        await state.set_state(Verification.response)
        return

    await db.verify_status_update(verify_id, response + f'\nКомментарий: {text}')
    
    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=message_text + f'\n\nОтвет: {response}\nКомментарий: {text}',
        reply_markup=None,
        parse_mode='HTML'
    )

    from app.user import user_verify_notify
    await user_verify_notify(verify_id, state)
    await state.clear()


async def send_delivery_message(user_id, adress):
    admins = get_admins()

    user = await db.get_user(user_id)

    msg_text = (
        f"Заявка на доставку от [{user.fullname}](tg://user?id={user.tg_id})"
        f"\n\nЛичный код: `{user.uid}`"
        f"\nНомер телефона: `{user.phone}`"
        f"\nАдрес: `{adress}`"
    )

    for admin in admins:
        await bot.send_message(admin, msg_text, parse_mode='Markdown')


@admin_router.callback_query(Admin(), F.data.startswith('balance_'))
async def edit_balance(call: CallbackQuery, state: FSMContext):
    action = call.data.split('_')[1]
    user_uid = call.data.split('_')[2]

    if action == 'add':
        msg_text = 'Введите сумму которую нужно добавить к балансу:'
    elif action == 'del':
        msg_text = 'Введите сумму которую нужно снять с баланса:'

    await call.message.edit_text(msg_text, reply_markup=await kb.cncl_edit_blnc(user_uid))
    await state.update_data(message_id=call.message.message_id, user_uid=user_uid, action=action)
    await state.set_state(EditBalance.Amount)


@admin_router.callback_query(Admin(), F.data.startswith('cancel_edit_balance_'))
async def cncl_edit_balance(call: CallbackQuery, state: FSMContext):
    user_uid = call.data.split('_')[3]
    await search_user(call.message, user_uid, call.from_user.id)
    await state.clear()


@admin_router.message(EditBalance.Amount)
async def edit_balance_amount(mess: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    user_uid = data.get("user_uid")
    action = data.get("action")
    
    user = await db.get_user_by_uid(user_uid)
    
    if mess.text:
        try:
            amount = float(mess.text)
        except:
            try:
                await bot.edit_message_text(
                    chat_id=mess.from_user.id,
                    message_id=message_id,
                    text='Неверный формат суммы. Попробуйте снова.'
                )
            except:
                pass
            await state.set_state(EditBalance.Amount)
            return

        if action == 'add':
            new_balance = user.balance + amount
        elif action == 'del':
            new_balance = user.balance - amount

        await db.update_balance(user_uid, new_balance)
        await search_user(message_id, user_uid. mess.from_user.id)
        await state.clear()
    else:
        try:
            await bot.edit_message_text(
                chat_id=mess.from_user.id,
                message_id=message_id,
                text='Сумма не найдена. Попробуйте снова.'
            )
        except:
            pass
        await state.set_state(EditBalance.Amount)
            

@admin_router.message(Admin(), F.text.startswith('UK'))
async def search_user(message: Message, user_uid=None, admin_id=None):
    if user_uid is None:
        try:
            user_uid = message.text
        except:
            await message.answer('Личный код не найден!\nПовторите попытку.')
    else:
        user_uid = user_uid
        
    user = await db.get_user_by_uid(user_uid)

    if user:
        msg_txt = (
            f'\nФ.И.О.: <a href="tg://user?id={user.tg_id}">{user.fullname}</a>'
            f"\nUID: {user.uid}"
            f"\nНомер телефона: {user.phone}"
            f"\n\nБаланс: {user.balance}"
        )

        try:await message.answer(msg_txt, reply_markup=await kb.admin_user_profile(user_uid), parse_mode='HTML')
        except:await bot.send_message(admin_id, msg_txt, reply_markup=await kb.admin_user_profile(user_uid), parse_mode='HTML')
    else:
        try:await message.answer('Пользователь не найден. Проверьте правильность введенного кода.\nФормат UK****\n\nДля перехода в админку введите /admin')
        except:await bot.send_message(admin_id, 'Пользователь не найден. Проверьте правильность введенного кода.\nФормат UK****\n\nДля перехода в админку введите /admin')

    try:await message.delete()
    except:await bot.delete_message(admin_id, message)


@admin_router.message(Admin(), Command('delete_user'))
async def delete_user(message: Message):
    await message.delete()
    
    uid = message.text.split(' ')[1]
    user = await db.get_user_by_uid(uid)
    
    if user:
        await db.delete_user(uid)
