import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# 🔄 Словник для збереження інформації про замовлення
order_messages = {}

# 🔑 Токен бота
API_TOKEN = "8090513582:AAGlQgFCGTDScwwDaAQsLh9iUi0dWXH2zWE"

# 📌 ID групи для замовлень
GROUP_CHAT_ID = -4720936270

# 🔄 Створюємо бота та диспетчер
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 📌 FSM для збору даних
class OrderForm(StatesGroup):
    service = State()
    name = State()
    phone = State()
    address = State()
    district = State()

# 📌 Перевірка номера телефону
def is_valid_phone(phone):
    pattern = r"^\+?3?8?(0\d{9})$"
    return re.fullmatch(pattern, phone) is not None

# 📌 Ціни на послуги
price_list = {
    "Внутрішньом'язовий укол": "100 грн",
    "Внутрішньовенний укол": "150 грн",
    "Крапельниця до 30 хв": "350 грн",
    "Крапельниця до 1 год": "600 грн",
    "Крапельниця до 2 год": "1200 грн"
}

# 📌 Головне меню
async def send_main_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Старт")]],
        resize_keyboard=True
    )
    text = """
Привіт! Раді вітати вас у Medigo – сервісі професійної медичної допомоги вдома! 😊

✨ <b>Наші послуги:</b>
💉 Внутрішньом'язовий укол – 100 грн  
💉 Внутрішньовенний укол – 150 грн  
💧 Крапельниця до 30 хв – 350 грн  
💧 Крапельниця до 1 год – 600 грн  
💧 Крапельниця до 2 год – 1200 грн  

⚠️ <b>Зверніть увагу!</b>  
Наш сервіс не надає медикаменти та витратні матеріали, тому перед викликом медсестри вам необхідно самостійно придбати всі 
необхідні лікарські препарати та вироби медичного призначення, які є необхідними для надання Послуг, згідно з призначенням лікаря.

<b>Як оплатити?</b>
💳 Оплата тільки за реквізитами після прибуття медсестри.

🏥 Усі наші медсестри – сертифіковані спеціалісти з медичною освітою.

📜 Натискаючи кнопку "Старт", ви погоджуєтеся з <a href="https://docs.google.com/document/d/1HHiGjuGHyGgZiDyKsLbOeNvqcp58Uv7L/edit?usp=sharing">Умовами надання послуг</a> Medigo.

"""
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)

# 📌 Старт
@dp.message(Command("start"))
async def welcome_message(message: types.Message):
    await send_main_menu(message)

# 📌 Вибір послуги
@dp.message(F.text == "Старт")
async def choose_service(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Внутрішньом'язовий укол")],
            [KeyboardButton(text="Внутрішньовенний укол")],
            [KeyboardButton(text="Крапельниця")]
        ],
        resize_keyboard=True
    )
    await message.answer("Виберіть послугу:", reply_markup=keyboard)

# 📌 Обробка вибору крапельниці
@dp.message(F.text == "Крапельниця")
async def choose_drip_type(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Крапельниця до 30 хв")],
            [KeyboardButton(text="Крапельниця до 1 год")],
            [KeyboardButton(text="Крапельниця до 2 год")]
        ],
        resize_keyboard=True
    )
    await message.answer("Оберіть тип крапельниці:", reply_markup=keyboard)

# 📌 Обробка вибору послуги
@dp.message(F.text.in_(price_list.keys()))
async def service_selected(message: types.Message, state: FSMContext):
    await state.update_data(service=message.text, price=price_list[message.text])
    await state.set_state(OrderForm.name)
    await message.answer("📌 Введіть ваше ім'я:", reply_markup=types.ReplyKeyboardRemove())

# 📌 Отримання імені
@dp.message(OrderForm.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.phone)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Надіслати номер телефону", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("📞 Введіть номер або натисніть кнопку:", reply_markup=keyboard)

# 📌 Отримання номера телефону
@dp.message(OrderForm.phone)
async def get_phone(message: types.Message, state: FSMContext):
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = message.text.strip()
        if not is_valid_phone(phone_number):
            await message.answer("❌ Введено неправильний номер. Спробуйте ще раз.")
            return

    await state.update_data(phone=phone_number)
    await state.set_state(OrderForm.address)
    await message.answer("🏠 Введіть вашу адресу (місто, вулиця, будинок, квартира):", reply_markup=types.ReplyKeyboardRemove())
# 📌 Отримання адреси
@dp.message(OrderForm.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(OrderForm.district)
    await message.answer("📍 Введіть район вашого міста:")

# 📌 Завершення збору даних
@dp.message(OrderForm.district)
async def get_district(message: types.Message, state: FSMContext):
    await state.update_data(district=message.text)
    user_data = await state.get_data()

    text = f"""
✅ Дякуємо, {user_data['name']}! Ваше замовлення прийнято.

🏠 Адреса: {user_data['address']}
📍 Район: {user_data['district']}
📞 Телефон: {user_data['phone']}

💡 Оплата після прибуття медсестри.
💰 Сума до оплати: {user_data['price']}

🏥 Дякуємо, що обираєте Medigo!
"""

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="До головного меню")]],
        resize_keyboard=True
    )

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    await message.answer("💳 Реквізити для оплати: UA433220010000026004330072431
    У призначенні платежу обов’язково вкажіть: Прізвище та ім'я замовника")

    # 📌 Виправлене повідомлення в групі
    group_text = f"""
📌 <b>Нове замовлення!</b>

👤 <b>Ім'я:</b> {user_data['name']}
🏠 <b>Адреса:</b> {user_data['address']}
📍 <b>Район:</b> {user_data['district']}
📞 <b>Телефон:</b> {user_data['phone']}
🩺 <b>Послуга:</b> {user_data['service']}
💰 <b>Сума до оплати:</b> {user_data['price']}
"""

    await bot.send_message(GROUP_CHAT_ID, group_text, parse_mode="HTML")

    await state.clear()

# 📌 Обробка кнопки "До головного меню"
@dp.message(F.text == "До головного меню")
async def back_to_main(message: types.Message):
    await send_main_menu(message)

# 📌 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
