from aiogram.fsm.state import State, StatesGroup


class CommunicationSG(StatesGroup):
    girl_analysis = State()
    my_analysis = State()
    pause = State()
    correspondence = State()