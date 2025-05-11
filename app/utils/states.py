from aiogram.filters.state import StatesGroup, State


class Registration(StatesGroup):
    Ucode = State()
    FullName = State()
    City = State()
    PickUpPoint = State()
    Phone = State()
    Promo = State()
    Area = State()


class EditData(StatesGroup):
    FullName = State()
    City = State()
    Phone = State()
    Promo = State()


class AddPromo(StatesGroup):
    Promo = State()


class Verification(StatesGroup):
    photo = State()
    response = State()


class Delivery(StatesGroup):
    adress = State()


class Promo(StatesGroup):
    promocode = State()


class AddSupport(StatesGroup):
    Name = State()
    Link = State()


class EditBalance(StatesGroup):
    Amount = State()


class Search(StatesGroup):
    TrackCode = State()

