import datetime
import time
from collections import defaultdict

from aiogram import Bot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import app.database.requests as db
from app.utils.strings import clean_number


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SAMPLE_SPREADSHEET_ID = "1gp3KJYHLHB4tOR-yJVPwTeUYmfBoLYZHuuSEYlvnyGg"
creds = Credentials.from_service_account_file("/root/bot/credentials.json", scopes=SCOPES)


async def GetNewAdress():
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Адреса")
        .execute()
    )

    values = result.get("values", [])

    if values[7][1] == 'TRUE':
        main_adress = values[1][0]
        pinduoduo_example = values[1][1]
        taobao_example = values[1][2]
        _1688_example = values[1][3]
        poizon_example = values[1][4]

        await db.new_adress(main_adress, pinduoduo_example, taobao_example, _1688_example, poizon_example)
        await db.edit_verify_response()
        
        new_values = [
            [
                'FALSE',
                f'Адрес обновлен {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'
            ]
        ]
        data_to_sheets = [
            {"range": f"Адреса!B8:C8",
            "majorDimension": "ROWS",
            "values": new_values}
        ]

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": data_to_sheets
            }
        ).execute()


async def UpdateUserDataSheets():
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    users = await db.get_users()

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Клиенты")
        .execute()
    )

    values = result.get("values", [])

    data_to_sheets = []

    for index, item in enumerate(values[1:], start=1):
        if len(item) > 8 and item[8] == 'TRUE':
            if all(i != '' for i in item[0:7]):
                user = await db.get_user_by_uid(item[0])
                if user:
                    await db.edit_user(user.tg_id, user.name, user.uid, item[1], item[2], item[4], item[6])
                    await db.update_balance(user.uid, float(item[7].replace(",", ".")))
                    message = f'Обновлено {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'
                else:
                    message = f"Такой пользователь не найден!"
            else:
                message = "Не все данные заполнены!"
            new_values = [
                [
                    'FALSE',
                    f"{message}"
                ]
            ]
            data_to_sheets.append(
                {"range": f"Клиенты!J{index+1}:K{index+1}",
                "majorDimension": "ROWS",
                "values": new_values})
    
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": data_to_sheets
        }
    ).execute()

    new_values = [
        [
            user.uid,
            # user.status,
            user.fullname,
            user.city,
            user.pickup_points,
            user.phone,
            user.discount,  
            user.promocode,
            user.balance,
            'Верифицирован' if user.verify == 1 else 'Не верифицирован',
            'False'
        ]
        for user in users
    ]
    
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Клиенты!A2:J1256000",
                "majorDimension": "ROWS",
                "values": new_values}
            ]
        }
    ).execute()


async def GetParcelsFromStorage(bot: Bot):
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Склад")
        .execute()
    )

    values = result.get("values", [])

    data_to_sheets = []
    data = defaultdict(lambda: {"items": [], "total_price": 0, "total_weight": 0})
    new_status_data = defaultdict(lambda: {"items": []})

    for index, item in enumerate(values[1:], start=1):
        if all(i != '' for i in item[0:3]) and len(item) > 3:
            try:
                weight = round(float(clean_number(item[4])), 3)
            except:
                weight = 0

            status = item[0]
            trackcode = item[2]
            uid = item[3]
            date = item[1]

            parcel = await db.get_parcel_by_track_code(trackcode)
            if parcel:
                await db.update_parcel(trackcode, status, uid)

                if parcel.weight == 0 and weight != 0:
                    await db.update_parcel(status, trackcode, uid, weight, date)
                    
                    user = await db.get_user_by_uid(uid)
                    if user and user.promocode != 'Отсутствует':
                        promo_user = await db.get_user_by_phone(user.promocode)
                        if promo_user:
                            await db.update_balance(promo_user.uid, promo_user.balance + weight / 5)
                
                if parcel.status != status:
                    # Генерация накладных
                    new_status_data[parcel.uid]["items"].append(f"*{status}* - `{trackcode}`")
            # else:
            #     data[item[3]]["items"].append(f"*{item[0]}* - `{item[2]}`")






            #     # Посылка уже существует - обрабатываем изменения
            #     if parcel.uid != item[3]:
            #         # Изменился владелец - корректируем бонусы
            #         # Снимаем бонус со старого пользователя
            #         old_user = await db.get_user_by_uid(parcel.uid)
            #         if old_user and old_user.promocode != 'Отсутствует':
            #             old_promo_user = await db.get_user_by_phone(old_user.promocode)
            #             if old_promo_user:
            #                 await db.update_balance(old_promo_user.uid, old_promo_user.balance - parcel.weight / 5)
                    
            #         # Начисляем новому пользователю
            #         new_user = await db.get_user_by_uid(item[3])
            #         if new_user and new_user.promocode != 'Отсутствует':
            #             new_promo_user = await db.get_user_by_phone(new_user.promocode)
            #             if new_promo_user:
            #                 await db.update_balance(new_promo_user.uid, new_promo_user.balance + weight / 5)
                
            #     elif parcel.weight != weight:
            #         # Изменился только вес - корректируем бонус
            #         user = await db.get_user_by_uid(parcel.uid)
            #         if user and user.promocode != 'Отсутствует':
            #             promo_user = await db.get_user_by_phone(user.promocode)
            #             if promo_user:
            #                 # Корректируем с учетом разницы веса
            #                 weight_diff = weight - parcel.weight
            #                 await db.update_balance(promo_user.uid, promo_user.balance + weight_diff / 5)
                
            #     # Обновляем данные посылки
            #     await db.update_parcel(item[0], item[2], parcel.uid, weight, item[1])
            #     if parcel.status != item[0]:

            # else:
            #     # Новая посылка - добавляем и начисляем бонус один раз
            #     await db.add_parcel(item[0], item[2], item[3], weight, item[1])
                
            #     # Начисляем бонус только при первом создании
            #     user = await db.get_user_by_uid(item[3])
            #     if user and user.promocode != 'Отсутствует':
            #         promo_user = await db.get_user_by_phone(user.promocode)
            #         if promo_user:
            #             await db.update_balance(promo_user.uid, promo_user.balance + weight / 5)

    for uid, info in data.items():
        if uid != '':
            user = await db.get_user_by_uid(uid)
            items_str = "\n".join(info["items"])
            
            message = (
                f"Обнаружены товары:\n{items_str}\n\n"
            )

            await bot.send_message(chat_id=user.tg_id, text=message, parse_mode='Markdown')

    for uid, info in new_status_data.items():
        if uid != '':
            user = await db.get_user_by_uid(uid)
            items_str = "\n".join(info["items"])

            message = (
                f"Изменены статусы следующих трек-кодов:\n{items_str}\n\n"
            )

            await bot.send_message(chat_id=user.tg_id, text=message, parse_mode='Markdown')


async def GetAllParcelData(bot: Bot):
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Заказы")
        .execute()
    )

    values = result.get("values", [])
    data_to_sheets = []
    data = defaultdict(lambda: {"items": [], "total_price": 0, "total_weight": 0})
    new_status_data = defaultdict(lambda: {"items": []})

    for index, item in enumerate(values[1:], start=1):
        # await bot.send_message(chat_id=910846455, text=f"{index}\n{item[5]}\n{len(item)}", parse_mode='Markdown')

        trackcode = item[1]
        status = item[0]
        from_sheet_uid = item[2]
        date = item[3]
        parcel = await db.get_parcel_by_track_code(trackcode)
        if parcel and parcel.uid:
            data_to_sheets.append(
                {"range": f"Заказы!C{index+1}",
                "majorDimension": "ROWS",
                "values": [
                        [
                            f"{parcel.uid}"
                        ]    
                    ]
                }
            )

        if len(item) > 3 and item[4] == 'TRUE':
            if all(i != '' for i in item[0:1]) and item[2] is not None and all(i != '' for i in item[3:]):
                new_values = [
                    [
                        'FALSE',
                        f'Обновлено {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'
                    ]
                ]
                data_to_sheets.append(
                    {"range": f"Заказы!E{index+1}:F{index+1}",
                    "majorDimension": "ROWS",
                    "values": new_values})
                
                parcel = await db.get_parcel_by_track_code(trackcode)
                if parcel:
                    await db.update_parcel(trackcode, status, from_sheet_uid, 0, date)
                    if parcel.status != status:
                        new_status_data[parcel.uid]["items"].append(f"*{status}* - `{trackcode}`")
                else:
                    data[from_sheet_uid]["items"].append(f"*{status}* - `{trackcode}`")

                    await db.add_parcel(status, trackcode, from_sheet_uid, 0, date)

            else:
                new_values = [
                    [
                        'FALSE',
                        f"Данные о посылке не заполнены полностью!"
                    ]
                ]
                data_to_sheets.append(
                    {"range": f"Заказы!E{index+1}:F{index+1}",
                    "majorDimension": "ROWS",
                    "values": new_values})

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": data_to_sheets
        }
    ).execute()

    for uid, info in data.items():
        if uid != '':
            user = await db.get_user_by_uid(uid)
            items_str = "\n".join(info["items"])
            
            message = (
                f"Обнаружены товары:\n{items_str}\n\n"
            )

            await bot.send_message(chat_id=user.tg_id, text=message, parse_mode='Markdown')

    for uid, info in new_status_data.items():
        if uid != '':
            user = await db.get_user_by_uid(uid)
            items_str = "\n".join(info["items"])

            message = (
                f"Изменены статусы следующих трек-кодов:\n{items_str}\n\n"
            )

            await bot.send_message(chat_id=user.tg_id, text=message, parse_mode='Markdown')


async def GetMailingMessage(bot: Bot):
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Рассылка")
        .execute()
    )

    values = result.get("values", [])
    if values[1:][0][1] == 'TRUE':
        mailing_text = values[1:][0][0]
        
        users = await db.get_users()
        delivered = 0
        not_delivered = 0
        for user in users:
            time.sleep(0.1)
            try:
                await bot.send_message(chat_id=user.tg_id, text=mailing_text)
                delivered += 1
            except:
                not_delivered += 1
                
        new_values = [
            [
                'FALSE',
                f"Рассылка завершена!\n\nДоставлено {delivered} пользователям.\nНе доставлено {not_delivered} пользователям."
            ]
        ]
        data_to_sheets = [
            {"range": f"Рассылка!B2:C2",
            "majorDimension": "ROWS",
            "values": new_values}
        ]

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": data_to_sheets
            }
        ).execute()

