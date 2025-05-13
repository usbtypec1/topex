import ast

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.media_group import MediaGroupBuilder

import ui.admin_keyboards as kb
from app.const import const_ru
from app.states import AddSupport, EditBalance, Verification
from config import load_config
from database.queries import DatabaseRepository


admin_router = Router()


def admin_filter(message_or_callback_query: Message | CallbackQuery) -> bool:
    config = load_config()
    return message_or_callback_query.from_user.id in config.admin_user_ids


@admin_router.message(admin_filter, Command('admin'))
async def start(message: Message):
    await message.answer(
        'Админ-панель:', reply_markup=await kb.admin_main_menu()
    )
    await message.delete()


@admin_router.callback_query(
    admin_filter, F.data.startswith('admin_main_menu')
)
async def cstart(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        'Админ-панель:', reply_markup=await kb.admin_main_menu()
    )


@admin_router.callback_query(admin_filter, F.data == 'edit_pickup_points')
async def pickup_points(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        'Редактирование пунктов самовывоза:',
        reply_markup=await kb.admin_pickup_points()
    )


@admin_router.callback_query(
    admin_filter, F.data.startswith('admin_pickup_point:')
)
async def pickup_point(
        callback_query: CallbackQuery,
        state: FSMContext,
        database_repository: DatabaseRepository,
):
    await state.clear()

    city = callback_query.data.split(':')[1]

    await callback_query.message.edit_text(
        f'Редактирование пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.admin_pickup_point(city, database_repository)
    )


@admin_router.callback_query(admin_filter, F.data.startswith('add_point_'))
async def add_point(callback_query: CallbackQuery, state: FSMContext):
    city = callback_query.data.split('_')[2]

    await callback_query.message.edit_text(
        f'Введите адрес пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.cancel(f'admin_pickup_point:{city}')
    )

    await state.update_data(
        city=city, call_id=callback_query.id,
        message_id=callback_query.message.message_id
    )
    await state.set_state('PickUpPoint.Adress')


@admin_router.message(admin_filter, StateFilter('PickUpPoint.Adress'), F.text)
async def address(
        message: Message, state: FSMContext, bot: Bot,
        database_repository: DatabaseRepository,
):
    data = await state.get_data()
    city = data.get('city')
    message_id = data.get('message_id')

    await database_repository.add_pickup_point(city, message.text)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=f'Редактирование пункта самовывоза: {const_ru[city]}',
        reply_markup=await kb.admin_pickup_point(city, database_repository)
    )

    await state.clear()
    await message.delete()


@admin_router.callback_query(admin_filter, F.data.startswith('admin_point_'))
async def admin_point(
        callback_query: CallbackQuery,
        bot: Bot,
        database_repository: DatabaseRepository,
):
    data = callback_query.data.split('_')
    point = await database_repository.get_pickup_point(int(data[2]))

    me = await bot.get_me()

    await callback_query.message.edit_text(
        (
            f'Город: {const_ru[point.city]}\n'
            f'Пункт выдачи: {point.adress}\n\n'
            f'Ссылка для qr кода:\n'
            f'https://t.me/{me.username}?start=point_{point.id}'
        ),
        reply_markup=await kb.admin_point(point.id, database_repository)
    )


@admin_router.callback_query(admin_filter, F.data.startswith('delete_point_'))
async def delete_point(
        callback_query: CallbackQuery,
        database_repository: DatabaseRepository,
):

    data = callback_query.data.split('_')
    point = await database_repository.get_pickup_point(int(data[2]))

    if len(data) == 3:
        await callback_query.message.edit_text(
            f'Удалить пункт выдачи {point.adress}',
            reply_markup=await kb.confirm(
                f'delete_point_{point.id}_coonfirm',
                f'admin_pickup_point:{point.city}'
            )
        )
    else:
        await database_repository.delete_pickup_point(point.id)

        await callback_query.message.edit_text(
            f'Редактирование пункта самовывоза: {const_ru[point.city]}',
            reply_markup=await kb.admin_pickup_point(
                point.city, database_repository
                )
        )


@admin_router.callback_query(admin_filter, F.data == 'admin_support')
async def support(callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        'Поддержка:', reply_markup=await kb.admin_supports_kb()
    )


@admin_router.callback_query(admin_filter, F.data == 'cncl_add_sprt')
async def cncl_add_sprt(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer('Отмена 🔸')
    await support(callback_query)
    await state.clear()


@admin_router.callback_query(admin_filter, F.data == 'add_support')
async def add_support(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        'Введите название:', reply_markup=await kb.cncl_add_sprt()
    )
    await state.update_data(message_id=callback_query.message.message_id)
    await state.set_state(AddSupport.Name)


@admin_router.message(AddSupport.Name)
async def add_support_name(message: Message, bot: Bot, state: FSMContext):
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
async def add_support_link(
        message: Message,
        bot: Bot,
        state: FSMContext,
        database_repository: DatabaseRepository,
):
    data = await state.get_data()
    message_id = data.get("message_id")
    name = data.get("name")

    link = message.text
    if link is None:
        await state.set_state(AddSupport.Link)
        return

    await database_repository.add_support(name, link)

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=f'Название: {name}\nСсылка: {link}',
        reply_markup=None,
        disable_web_page_preview=True
    )

    await bot.send_message(
        message.from_user.id, 'Поддержка:',
        reply_markup=await kb.admin_supports_kb()
    )

    await state.clear()
    await message.delete()


@admin_router.callback_query(admin_filter, F.data.startswith('del_supp_'))
async def delete_support(
        callback_query: CallbackQuery,
        database_repository: DatabaseRepository,
):
    support_id = callback_query.data.split('_')[2]
    if support_id == 'none':
        await callback_query.message.edit_text(
            f'Для удаления нажмите на "✖️":',
            reply_markup=await kb.admin_supports_del_kb(database_repository),
        )
    else:
        await database_repository.delete_support(support_id)
        await callback_query.answer(f'Поддержка удалена...')

        await callback_query.message.edit_text(
            f'Для удаления нажмите на "✖️":',
            reply_markup=await kb.admin_supports_del_kb(database_repository),
        )


async def send_verify_msg(
        verify_id,
        bot: Bot,
        database_repository: DatabaseRepository,
):
    verify = await database_repository.get_verify(verify_id)
    user = await database_repository.get_user(verify.tg_id)

    mess = (
        f"Заявка на проверку от"
        f'\nФ.И.О.: <a href="tg://user?id={user.tg_id}">{user.fullname}</a>'
        f"\nUID: {user.uid}"
        f"\nНомер телефона: {user.phone}"
    )

    mess += f"\n\nПлощадка: {const_ru[f'{verify.area}']}"

    media = MediaGroupBuilder()
    for i in ast.literal_eval(verify.file_id):
        media.add_photo(i)

    for chat_id in load_config().admin_user_ids:
        await bot.send_media_group(chat_id, media=media.build())
        await bot.send_message(
            chat_id=chat_id,
            text=mess,
            reply_markup=await kb.admin_verify_check(verify_id),
            parse_mode='HTML'
        )


@admin_router.callback_query(admin_filter, F.data.startswith('admin_verify_'))
async def verify_check(
        callback_query: CallbackQuery,
        state: FSMContext,
        database_repository: DatabaseRepository,
        bot: Bot,
):
    loyalty = callback_query.data.split('_')[2]
    verify_id = callback_query.data.split('_')[3]

    verify = await database_repository.get_verify(verify_id)
    if verify:
        if loyalty == 'right':
            response = 'Все верно ✓'
            await database_repository.verify_status_update(verify_id, response)
            await callback_query.message.edit_text(
                text=callback_query.message.html_text + f'\n\nОтвет: '
                                                        f'{response}',
                reply_markup=None, parse_mode='HTML'
            )
            from app.user import user_verify_notify
            await user_verify_notify(
                verify_id, state, database_repository, bot
            )
        elif loyalty == 'wrong':
            response = 'Неверно ✗'
            await callback_query.message.edit_text(
                text=callback_query.message.html_text + f'\n\nОтвет: '
                                                        f'{
                                                        response}\nДобавьте '
                                                        f'комментарий:',
                reply_markup=None, parse_mode='HTML'
            )
            await state.update_data(
                message_id=callback_query.message.message_id,
                message_text=callback_query.message.html_text,
                response=response,
                verify_id=verify_id
            )
            await state.set_state(Verification.response)
    else:
        await callback_query.message.edit_text(
            text=callback_query.message.html_text + '\n\nНе актуально.',
            reply_markup=None,
            parse_mode='HTML',
        )


@admin_router.message(Verification.response)
async def verify_response(
        message: Message,
        bot: Bot,
        state: FSMContext,
        database_repository: DatabaseRepository,
):
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

    await database_repository.verify_status_update(
        verify_id, response + f'\nКомментарий: {text}'
    )

    await bot.edit_message_text(
        chat_id=message.from_user.id,
        message_id=message_id,
        text=message_text + f'\n\nОтвет: {response}\nКомментарий: {text}',
        reply_markup=None,
        parse_mode='HTML'
    )

    from app.user import user_verify_notify
    await user_verify_notify(verify_id, state, database_repository, bot)
    await state.clear()


async def send_delivery_message(
        user_id,
        address: str,
        bot: Bot,
        database_repository: DatabaseRepository,
):
    user = await database_repository.get_user(user_id)
    msg_text = (
        f"Заявка на доставку от [{user.fullname}](tg://user?id={user.tg_id})"
        f"\n\nЛичный код: `{user.uid}`"
        f"\nНомер телефона: `{user.phone}`"
        f"\nАдрес: `{address}`"
    )
    for admin in load_config().admin_user_ids:
        await bot.send_message(admin, msg_text, parse_mode='Markdown')


@admin_router.callback_query(admin_filter, F.data.startswith('balance_'))
async def edit_balance(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.split('_')[1]
    user_uid = callback_query.data.split('_')[2]

    if action == 'add':
        msg_text = 'Введите сумму которую нужно добавить к балансу:'
    elif action == 'del':
        msg_text = 'Введите сумму которую нужно снять с баланса:'
    else:
        raise

    await callback_query.message.edit_text(
        msg_text, reply_markup=await kb.cncl_edit_blnc(user_uid)
    )
    await state.update_data(
        message_id=callback_query.message.message_id, user_uid=user_uid,
        action=action
    )
    await state.set_state(EditBalance.Amount)


@admin_router.callback_query(
    admin_filter, F.data.startswith('cancel_edit_balance_')
)
async def cncl_edit_balance(
        callback_query: CallbackQuery,
        state: FSMContext,
        bot: Bot,
        database_repository: DatabaseRepository,
):
    user_uid = callback_query.data.split('_')[3]
    await search_user(
        callback_query.message, bot, database_repository, user_uid,
        callback_query.from_user.id
    )
    await state.clear()


@admin_router.message(EditBalance.Amount)
async def edit_balance_amount(
        mess: Message,
        state: FSMContext,
        bot: Bot,
        database_repository: DatabaseRepository,
):
    data = await state.get_data()
    message_id = data.get("message_id")
    user_uid = data.get("user_uid")
    action = data.get("action")

    user = await database_repository.get_user_by_uid(user_uid)

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
        else:
            raise

        await database_repository.update_balance(user_uid, new_balance)
        await search_user(message_id, user_uid.mess.from_user.id)
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


@admin_router.message(admin_filter, F.text.startswith('UK'))
async def search_user(
        message: Message, bot: Bot,
        database_repository: DatabaseRepository,
        user_uid=None,
        admin_id=None,
):
    if user_uid is None:
        user_uid = message.text

    user = await database_repository.get_user_by_uid(user_uid)

    if user:
        msg_txt = (
            f'\nФ.И.О.: <a href="tg://user?id={user.tg_id}">'
            f'{user.fullname}</a>'
            f"\nUID: {user.uid}"
            f"\nНомер телефона: {user.phone}"
            f"\n\nБаланс: {user.balance}"
        )

        try:
            await message.answer(
                msg_txt, reply_markup=await kb.admin_user_profile(
                    user_uid
                ), parse_mode='HTML'
            )
        except Exception:
            await bot.send_message(
                admin_id, msg_txt, reply_markup=await kb.admin_user_profile(
                    user_uid
                ), parse_mode='HTML'
            )
    else:
        try:
            await message.answer(
                'Пользователь не найден. Проверьте правильность введенного '
                'кода.\nФормат UK****\n\nДля перехода в админку введите /admin'
            )
        except:
            await bot.send_message(
                admin_id,
                'Пользователь не найден. Проверьте правильность введенного '
                'кода.\nФормат UK****\n\nДля перехода в админку введите /admin'
            )

    try:
        await message.delete()
    except Exception:
        await bot.delete_message(admin_id, message.message_id)


@admin_router.message(admin_filter, Command('delete_user'))
async def delete_user(
        message: Message,
        database_repository: DatabaseRepository,
):
    await message.delete()

    uid = message.text.split(' ')[1]
    user = await database_repository.get_user_by_uid(uid)

    if user:
        await database_repository.delete_user(uid)
