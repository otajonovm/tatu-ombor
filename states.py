from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
  waiting_quantity = State()
  waiting_phone = State()


class AdminProductStates(StatesGroup):
  waiting_name = State()
  waiting_description = State()
  waiting_price = State()
  waiting_quantity = State()
  waiting_image = State()


class AdminStockStates(StatesGroup):
  waiting_quantity = State()
  waiting_comment = State()


class AdminEditStates(StatesGroup):
  waiting_price = State()
