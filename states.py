from aiogram.fsm.state import State, StatesGroup


class StockStates(StatesGroup):
  waiting_quantity = State()
  waiting_recipient = State()


class AdminStates(StatesGroup):
  waiting_product_name = State()
  waiting_product_quantity = State()
  waiting_product_image = State()
