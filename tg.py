import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Парсинг адреса сайта из файла конфигурации
def parse_site_url(config_file="config.txt"):
    try:
        with open(config_file, "r") as f:
            for line in f:
                if line.startswith("SITE_URL="):
                    return line.strip().split("=")[1]
        raise ValueError("SITE_URL not found in config file")
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {config_file} not found")

# Глобальная переменная для адреса сайта
try:
    FLASK_API_URL = parse_site_url()
    logging.info(f"Адрес сайта: {FLASK_API_URL}")
except Exception as e:
    logging.error(f"Ошибка при парсинге адреса сайта: {e}")
    FLASK_API_URL = "http://127.0.0.1:5000/api"  # Значение по умолчанию

# Инициализация бота и диспетчера
bot = Bot(token="8129948923:AAEBAULMQmeXS41nmWZecxBWL4AH_e2TBlY")  # Замени YOUR_BOT_TOKEN на токен твоего бота
dp = Dispatcher()
router = Router()

# Функция для получения списка направлений через API
async def get_directions():
    try:
        response = requests.get(f"{FLASK_API_URL}/directions")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении направлений: {e}")
        return []

# Функция для получения законов направления через API
async def get_laws(direction_name):
    try:
        response = requests.get(f"{FLASK_API_URL}/laws/{direction_name}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении законов для {direction_name}: {e}")
        return []

# Функция для получения информации о законе через API
async def get_law(law_id):
    try:
        response = requests.get(f"{FLASK_API_URL}/law/{law_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении закона {law_id}: {e}")
        return {}

# Создание клавиатуры с направлениями
async def create_directions_keyboard():
    directions = await get_directions()
    if not directions:
        return None
    # Создаём список кнопок
    buttons = [KeyboardButton(text=direction["name"]) for direction in directions]
    # Разбиваем кнопки на ряды (например, по 2 кнопки в ряду)
    keyboard_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Создание клавиатуры с законами направления
async def create_laws_keyboard(direction_name):
    laws = await get_laws(direction_name)
    if not laws:
        return None
    # Создаём список кнопок для законов
    buttons = [KeyboardButton(text=law["name"]) for law in laws]
    # Разбиваем кнопки на ряды (по 2 кнопки в ряду)
    keyboard_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    # Добавляем кнопку "Направления" в отдельный ряд
    keyboard_rows.append([KeyboardButton(text="Направления")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Создание клавиатуры после выбора закона
def create_law_navigation_keyboard(direction_name):
    keyboard_rows = [
        [
            KeyboardButton(text="Направления"),
            KeyboardButton(text=f"Законы ({direction_name})")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    keyboard = await create_directions_keyboard()
    if not keyboard:
        await message.answer("Извини, не удалось загрузить направления. Попробуй позже.")
        return
    await message.answer(
        f"Привет, {user_name}, я расскажу тебе любой закон — например.",
        reply_markup=keyboard
    )

# Обработчик выбора направления или кнопки "Направления"
@router.message(F.text == "Направления")
async def show_directions(message: Message):
    keyboard = await create_directions_keyboard()
    if not keyboard:
        await message.answer("Извини, не удалось загрузить направления. Попробуй позже.")
        return
    await message.answer(
        "Выбери направление:",
        reply_markup=keyboard
    )

# Обработчик выбора закона или кнопки "Законы (в данном направлении)"
@router.message(lambda message: message.text.startswith("Законы ("))
async def show_laws_in_direction(message: Message):
    direction_name = message.text.replace("Законы (", "").replace(")", "")
    keyboard = await create_laws_keyboard(direction_name)
    if not keyboard:
        await message.answer("Законы не найдены для этого направления.")
        return
    await message.answer(
        f"Законы в направлении {direction_name}:",
        reply_markup=keyboard
    )

# Обработчик выбора направления или закона
@router.message()
async def handle_message(message: Message):
    text = message.text

    # Проверяем, является ли текст названием направления
    directions = await get_directions()
    direction_names = [direction["name"] for direction in directions]
    if text in direction_names:
        keyboard = await create_laws_keyboard(text)
        if not keyboard:
            await message.answer("Законы не найдены для этого направления.")
            return
        await message.answer(
            f"Законы в направлении {text}:",
            reply_markup=keyboard
        )
        return

    # Проверяем, является ли текст названием закона
    for direction in directions:
        laws = await get_laws(direction["name"])
        for law in laws:
            if law["name"] == text:
                law_info = await get_law(law["id"])
                # Оборачиваем текст закона в обратные кавычки для отображения как код
                await message.answer(
                    f"**{law_info['name']}**\n\n`{law_info['text']}`",
                    reply_markup=create_law_navigation_keyboard(direction["name"]),
                    parse_mode="Markdown"
                )
                return

    # Если текст не распознан
    await message.answer("Пожалуйста, выбери направление или закон из клавиатуры.")

# Запуск бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())