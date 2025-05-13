import asyncio

import gspread
from gspread.utils import InsertDataOption, ValueInputOption
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.repository import DatabaseRepository
from utils.sheets import CREDENTIALS_FILE_PATH

PICKUP_POINT_NAME_TO_SPREADSHEET_ID = {
    'Токтогула 116А': '1eVBXyfBYvvpueAXsyVF0eMkEQhbAfchifh_DwMkCuI0'
}


async def start_distribute_parcels_task(
        session_factory: async_sessionmaker[AsyncSession],
):
    client = gspread.service_account(CREDENTIALS_FILE_PATH)


    async with session_factory() as session:
        database_repository = DatabaseRepository(session)

        for pickup_point_name, spreadsheet_id in PICKUP_POINT_NAME_TO_SPREADSHEET_ID.items():
            spreadsheet = client.open_by_key(spreadsheet_id)
            sheet = spreadsheet.worksheet('Заказы')

            parcels = await database_repository.get_parcels_by_status(
                pickup_point_name
            )

            print(parcels)

            rows = [
                [
                    parcel.datetime,
                    parcel.trackcode,
                    parcel.uid,
                    parcel.weight,
                    False,
                ]
                for parcel in parcels
            ]
            sheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)
            sheet.format("E2:E", {
                "boolValue": True,
            })
