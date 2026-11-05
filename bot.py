import os
import asyncio
import aiohttp
import uuid
import zoneinfo
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI
from datetime import datetime
from dotenv import load_dotenv
from yookassa import Configuration, Payment

load_dotenv()

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SITE_URL = "https://borisov.store"
PORT = int(os.getenv("PORT", 10000))
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# ===== ТВОЙ TELEGRAM ID (для уведомлений) =====
ADMIN_CHAT_ID = 990317436

# ========== НАСТРОЙКА ЮKASSA ==========
if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY
    print("ЮKassa настроена")
else:
    print("ЮKassa не настроена (отсутствуют shopId или secretKey)")

# ========== ССЫЛКА НА APPS SCRIPT (НОВАЯ ТАБЛИЦА) ==========
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzeaN4cYCw7emtUJoobYMRSibWPsVdLjLxD1cXGA2ODq3LJyfpEtCvK7kNesBQuzHUeCA/exec"

# ========== БАЗА ЗНАНИЙ (консультант) ==========
KNOWLEDGE = """
Ты — официальный представитель и консультант сервиса borisov.store.
Твоя задача — помогать клиентам, используя только информацию ниже. Запрещено вставлять прямые ссылки в текст ответа. Используй кнопку «Перейти на сайт».

О СЕРВИСЕ:
borisov.store — сервис по созданию сайтов и ботов на бесплатном хостинге GitHub Pages.
Исполнитель: Борисов Сергей, самозанятый.
Мы создаем качественные и функциональные сайты и Telegram-боты. Чтобы попасть на наш сайт нажмите кнопку «Перейти на сайт» под этим сообщением.

ТЕХНОЛОГИИ ДЛЯ САЙТОВ:
Ваш сайт будет построен на трёх надёжных технологиях:

**HTML5** – «скелет» сайта:
• Семантическая вёрстка для лучшего понимания поисковиками
• Адаптивность: корректное отображение на любых устройствах
• Современные формы: удобный ввод данных
• Отложенная загрузка: высокая скорость работы
• Кроссбраузерность: Chrome, Firefox, Safari, Edge, Яндекс.Браузер
• Чистый код без устаревших тегов

**CSS3** – «одежда» сайта:
• Современный дизайн: тени, градиенты, плавные переходы
• Адаптивная вёрстка под все экраны
• Красивая типографика: шрифты, отступы, читаемость
• Анимация кнопок и элементов без замедления
• Flexbox и Grid для идеального позиционирования
• Лёгкость: стили вместо тяжёлых картинок

**JavaScript** – «поведение» сайта:
• Интерактивность: кнопки, меню, формы реагируют на действия
• Плавная прокрутка и модальные окна
• Проверка форм при вводе (email, телефон)
• Динамический контент без перезагрузки страницы
• Повышение конверсии: анимация важных элементов

**Мини-CRM на Google Таблицах**:
• Все заявки автоматически попадают в Google Таблицу и дублируются вам на почту

**Приём платежей через ЮKassa**:
• Автоматическая, безопасная и надёжная оплата для ваших клиентов
• Поддержка банковских карт, электронных кошельков и СБП

ТЕХНОЛОГИИ ДЛЯ TELEGRAM-БОТОВ:
Ваш Telegram-бот будет построен на современных инструментах:

**Python 3** – основа всего бота:
• Простой и надёжный язык с огромным количеством библиотек
• Асинхронность: бот работает одновременно с тысячами пользователей
• Поддержка всех современных возможностей Telegram

**aiogram 3.x** – фреймворк для управления ботом:
• Обработка команд, кнопок, состояний (FSM)
• Гибкая маршрутизация сообщений
• Встроенная поддержка клавиатур и инлайн-кнопок
• Простое управление диалогами

**OpenAI / OpenRouter API** – подключение нейросетей:
• Интеграция с моделями (например, Gemini, GPT)
• Консультации, ответы на вопросы, генерация текста
• Гибкая настройка температуры и длины ответа

**SQLite** – лёгкая база данных:
• Хранение прогресса пользователей, настроек, заказов
• Быстрая работа без внешних серверов
• Простота резервного копирования

**YooKassa** – приём платежей:
• Автоматическая, безопасная оплата через карты, СБП, кошельки
• Простая интеграция через API
• Поддержка тестового и боевого режимов

**Amvera / Render** – хостинг и деплой:
• Бесплатные тарифы для старта
• Автоматический деплой из GitHub
• Масштабирование при росте пользователей

**GitHub** – хранение кода и контроль версий:
• Удобная работа в команде или в одиночку
• Автоматическая сборка и развёртывание
• История изменений и откат к любой версии

ТЕХНОЛОГИИ ДЛЯ MAX-БОТОВ:
• Python 3 — основной язык.
• maxapi — библиотека для работы с API MAX.
• OpenAI / OpenRouter API — для умного консультирования.
• YooKassa — для приёма платежей.
• Amvera — российский хостинг для работы 24/7.

ТЕХНОЛОГИИ ДЛЯ AI-АГЕНТА НА САЙТ:
• Python 3 — основной язык.
• FastAPI — веб-фреймворк для обработки запросов с сайта.
• OpenAI / OpenRouter API — для общения с клиентами 24/7.
• Amvera / Render — хостинг.

ЦЕНЫ НА БОТОВ И АГЕНТОВ:
- Telegram-бот: 6 400 ₽ (сбор контактов), 9 600 ₽ (с консультантом), 16 000 ₽ (с оплатой).
- MAX-бот: 8 000 ₽ (сбор контактов), 16 000 ₽ (с консультантом), 24 000 ₽ (с оплатой).
- AI-агент на сайт: 16 000 ₽.

ПОРЯДОК РАБОТЫ И ОПЛАТА:
- Клиент выбирает тариф или согласовывает индивидуальный заказ.
- Желательно обсудить техническое задание (ТЗ) перед выполнением работ.
- Для начала работы нужны: материалы, ТЗ, доступ к GitHub (email и пароль).
- Оплата: предоплата 50% в начале работы, вторые 50% после приёмки. Различные способы оплаты:
банковские карты, СБП, ЮМани, Яндекс Сплит (рассрочка), криптовалюта - ETH, USDT, USDC (сети Optimism, Arbitrum).
- Срок разработки: до 3 рабочих дней (в сложных случаях до 7). Подробнее — в пункте 6.1 оферты.
- Бесплатный хостинг: GitHub Pages.
- Гарантийная поддержка: 30 дней.
- Доработки после гарантии: от 2000 руб.
- Условия сдачи и приемки сайта или бота прописаны в оферте в п. 5.3.
- Домен оплачивается клиентом отдельно.

ПРЕИМУЩЕСТВА:
Подробно о преимуществах можно узнать, нажав кнопку «Перейти на сайт» — вы попадёте в раздел «Почему выбирают нас».

НАВИГАЦИЯ:
Если клиент спрашивает о чём-то, чего нет в базе, предложи нажать «Перейти на сайт» для перехода в нужный раздел.
"""

# ========== ЦЕНЫ ==========
# Для сайтов
SITE_NAMES = {
    "len": "Лендинг",
    "info": "Информационный сайт",
    "vizit": "Визитка",
    "portfolio": "Портфолио",
    "shop": "Интернет-магазин",
    "universal": "Универсальный сайт"
}
SITE_PRICES = {
    "len": 6400,
    "info": 9600,
    "vizit": 12800,
    "portfolio": 16000,
    "shop": 19200,
    "universal": 32000
}
SITE_ADDONS = {
    1: 0,      # favicon
    2: 1280,   # форма обратной связи
    3: 1280,   # карта проезда
    4: 1920,   # еще 6 товаров (для интернет-магазина)
    5: 1920,   # оферта
    6: 1920,   # политика конфиденциальности
    7: 1920,   # блок отзывов
    8: 1920,   # Яндекс-Метрика
    9: 1920,   # виджет звонка
    10: 3200,  # еще 2 товара (для лендинга)
    11: 3200,  # автоплатеж (ЮKassa)
    12: 3200,  # Google Таблица
    13: 3200,  # календарь
    14: 4000   # автоматическая оплата криптовалютой
}
ADDON_NAMES = {
    1: "favicon", 2: "Форма обратной связи", 3: "Карта проезда",
    4: "Еще 6 товаров (для интернет-магазина)", 5: "Оферта", 6: "Политика конфиденциальности",
    7: "Блок отзывов", 8: "Яндекс-Метрика", 9: "Виджет звонка",
    10: "Еще 2 товара (для лендинга)", 11: "Автоплатеж (ЮKassa)", 12: "Google Таблица", 13: "Календарь",
    14: "Автоматическая оплата криптовалютой"
}

# Три пакета Telegram-ботов (без доп. услуг)
BOT_PACKAGES = {
    "contact": {"name": "Бот для сбора контактов", "price": 6400},
    "contact_consult": {"name": "Сбор контактов и бот-консультант", "price": 9600},
    "full": {"name": "Бот: сбор контактов, консультант, оплата", "price": 16000}
}
BOT_PACKAGE_NAMES = {
    "contact": "Бот для сбора контактов (ТГ)",
    "contact_consult": "Сбор контактов и бот-консультант (ТГ)",
    "full": "Бот: сбор контактов, консультант, оплата (ТГ)"
}
BOT_PACKAGE_PRICES = {
    "contact": 6400,
    "contact_consult": 9600,
    "full": 16000
}
# ========== ПАКЕТЫ ДЛЯ MAX-БОТОВ ==========
MAX_PACKAGES = {
    "contact": {"name": "MAX-бот: сбор контактов", "price": 8000},
    "contact_consult": {"name": "MAX-бот: сбор контактов и консультант", "price": 16000},
    "full": {"name": "MAX-бот: сбор контактов, консультант, оплата", "price": 24000}
}
MAX_PACKAGE_NAMES = {
    "contact": "Бот для сбора контактов (MAX)",
    "contact_consult": "Сбор контактов и бот-консультант (MAX)",
    "full": "Бот: сбор контактов, консультант, оплата (MAX)"
}
MAX_PACKAGE_PRICES = {
    "contact": 8000,
    "contact_consult": 16000,
    "full": 24000
}

# ========== ПАКЕТЫ ДЛЯ AI-АГЕНТА ==========
AI_AGENT_NAMES = "AI-агент на сайт (консультант 24/7)"
AI_AGENT_PRICE = 16000

# ========== ССЫЛКИ ДЛЯ КНОПОК ==========
BUTTON_LINKS = {
    "🛠 Наши услуги": "https://borisov.store/#services",
    "🚚 Сроки и доставка": "https://borisov.store/offer/",
    "💳 Оплата": "https://borisov.store/#pricing",
    "↩️ Гарантии": "https://borisov.store/offer/",
    "📞 Контакты": "https://borisov.store/#contacts",
    "🛡 Проверка самозанятого": "https://npd.nalog.ru/check-status/",
    "⚙️ Технологии": SITE_URL,
}

# ========== ТРИГГЕРЫ ==========
OFFER_KEYWORDS = ["тз", "задание", "оферт", "договор", "ознакомиться"]
def is_offer_request(text: str) -> bool:
    return any(kw in text.lower() for kw in OFFER_KEYWORDS)

SELFEMPLOYED_KEYWORDS = ["самозанят", "проверк", "статус", "налог", "инн"]
def is_selfemployed_request(text: str) -> bool:
    return any(kw in text.lower() for kw in SELFEMPLOYED_KEYWORDS)

# ========== OpenRouter ==========
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# ========== FSM СОСТОЯНИЯ ==========
class ContactForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class OrderForm(StatesGroup):
    waiting_for_type = State()           # выбор: сайт, тг-бот, макс-бот или ии-агент
    waiting_for_site_type = State()      # выбор типа сайта
    waiting_for_addons = State()         # доп. услуги для сайта
    waiting_for_bot_package = State()    # выбор пакета бота
    waiting_for_confirmation = State()   # подтверждение суммы
    waiting_for_offer = State()          # ожидание подтверждения оферты

# ========== БОТ И ДИСПЕТЧЕР ==========
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ========== КЛАВИАТУРЫ ==========
contact_kb = types.ReplyKeyboardMarkup(
    keyboard=[[types.KeyboardButton(text="📝 Оставить контакт")]],
    resize_keyboard=True
)

main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🛠 Наши услуги"), types.KeyboardButton(text="🚚 Сроки и доставка")],
        [types.KeyboardButton(text="💳 Оплата"), types.KeyboardButton(text="↩️ Гарантии")],
        [types.KeyboardButton(text="📞 Контакты"), types.KeyboardButton(text="🛡 Проверка самозанятого")],
        [types.KeyboardButton(text="⚙️ Технологии"), types.KeyboardButton(text="📋 Цены")],
    ],
    resize_keyboard=True
)

# ========== ХРАНИЛИЩА ==========
authorized_users = set()
user_contacts = {}  # user_id -> {"name": ..., "phone": ...}

# ========== ФУНКЦИИ ==========

# Функция записи в таблицу
async def append_to_sheet(name: str, phone: str, username: str, order: str = ""):
    # Устанавливаем часовой пояс Екатеринбурга (UTC+5)
    ekb_tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
    now = datetime.now(ekb_tz).strftime("%d.%m.%Y %H:%M:%S")
    
    payload = {
        "timestamp": now,
        "name": name,
        "phone": phone,
        "order": order
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GOOGLE_SCRIPT_URL, json=payload) as resp:
                result = await resp.text()
                print(f"Google Sheets ответил: {result}")
    except Exception as e:
        print(f"Ошибка записи в таблицу: {e}")

# Функция создания платежа через ЮKassa
def create_payment(amount: float, description: str, return_url: str) -> str | None:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        print("ЮKassa не настроена")
        return None

    idempotence_key = str(uuid.uuid4())
    try:
        payment = Payment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": description,
            "capture": True,
        }, idempotence_key)
        return payment.confirmation.confirmation_url
    except Exception as e:
        print(f"Ошибка создания платежа: {e}")
        return None

# Функция расчёта суммы для сайта (с доп. услугами)
def calculate_site_total(site_type: str, addons: list = None) -> tuple:
    total = SITE_PRICES.get(site_type, 0)
    services_text = SITE_NAMES.get(site_type, "Сайт")
    if addons:
        addon_list = []
        for a in addons:
            total += SITE_ADDONS.get(a, 0)
            addon_list.append(ADDON_NAMES.get(a, str(a)))
        if addon_list:
            services_text += " + " + ", ".join(addon_list)
    return int(total), services_text

# ========== ОБРАБОТЧИКИ ==========

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in authorized_users:
        await message.answer(
            "Здравствуйте! Я виртуальный консультант сервиса borisov.store.\n"
            "Задайте вопрос или воспользуйтесь кнопками ниже.",
            reply_markup=main_kb
        )
    else:
        await state.clear()
        await message.answer(
            "Здравствуйте! Чтобы начать консультацию, пожалуйста, оставьте свои контактные данные.",
            reply_markup=contact_kb
        )

@dp.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    authorized_users.discard(user_id)
    if user_id in user_contacts:
        del user_contacts[user_id]
    await message.answer(
        "Действие отменено. Чтобы начать заново, нажмите «Оставить контакт».",
        reply_markup=contact_kb
    )

# ===== СБОР КОНТАКТА =====
@dp.message(F.text == "📝 Оставить контакт")
async def start_contact(message: types.Message, state: FSMContext):
    await state.set_state(ContactForm.waiting_for_name)
    await message.answer("Как вас зовут?")

@dp.message(ContactForm.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ContactForm.waiting_for_phone)
    await message.answer("Ваш номер телефона (в формате +7XXXXXXXXXX):")

@dp.message(ContactForm.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not (phone.startswith("+") and phone[1:].isdigit() and len(phone) >= 12) and not (phone.isdigit() and len(phone) >= 11):
        await message.answer("Пожалуйста, введите корректный номер (11 цифр или +7XXXXXXXXXX).")
        return

    data = await state.get_data()
    name = data["name"]
    user_id = message.from_user.id
    username = message.from_user.username or "без username"

    # Сохраняем контакт в словарь
    user_contacts[user_id] = {"name": name, "phone": phone}

    # Запись контакта в таблицу (order = "")
    await append_to_sheet(name, phone, username, "")

    # ===== УВЕДОМЛЕНИЕ В TELEGRAM =====
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"🆕 Новый контакт!\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"🆔 Ник: @{username}"
    )

    # Авторизуем пользователя
    authorized_users.add(user_id)
    await state.clear()

    await message.answer(
        f"Спасибо, {name}! Теперь я ваш консультант.\n"
        "Задайте вопрос или воспользуйтесь кнопками ниже.",
        reply_markup=main_kb
    )

# ===== КНОПКА "ЦЕНЫ" =====
@dp.message(F.text == "📋 Цены")
async def show_prices(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in authorized_users:
        await message.answer(
            "Пожалуйста, сначала оставьте контактные данные, нажав кнопку «Оставить контакт».",
            reply_markup=contact_kb
        )
        return

    current_state = await state.get_state()
    if current_state in [OrderForm.waiting_for_type.state, OrderForm.waiting_for_site_type.state,
                         OrderForm.waiting_for_addons.state, OrderForm.waiting_for_bot_package.state,
                         OrderForm.waiting_for_confirmation.state, OrderForm.waiting_for_offer.state]:
        await message.answer("Вы уже в процессе оформления заказа. Чтобы отменить, отправьте /cancel.")
        return

    # Спрашиваем: что хотим заказать?
    await state.set_state(OrderForm.waiting_for_type)
    type_kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🌐 Сайт")],
            [types.KeyboardButton(text="🤖 Telegram-бот")],
            [types.KeyboardButton(text="🟣 MAX-бот")],
            [types.KeyboardButton(text="🧠 AI-агент")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Что вы хотите заказать?",
        reply_markup=type_kb
    )

# ===== ВЫБОР: САЙТ ИЛИ БОТ =====
@dp.message(OrderForm.waiting_for_type)
async def process_type(message: types.Message, state: FSMContext):
    if message.text == "🌐 Сайт":
        text = (
            "Выберите тип сайта:\n\n"
            "1) Лендинг — 6 400 ₽\n"
            "2) Информационный сайт — 9 600 ₽\n"
            "3) Визитка — 12 800 ₽\n"
            "4) Портфолио — 16 000 ₽\n"
            "5) Интернет-магазин — 19 200 ₽\n"
            "6) Универсальный сайт — 32 000 ₽\n\n"
            "Напишите номер (1-6) или название услуги."
        )
        await state.set_state(OrderForm.waiting_for_site_type)
        await message.answer(text, reply_markup=main_kb)
        
    elif message.text == "🤖 Telegram-бот":
        text = (
            "Выберите пакет Telegram-бота:\n\n"
            "1) Бот для сбора контактов — 6 400 ₽ (ТГ). Работает без ИИ.\n"
            "2) Сбор контактов и бот-консультант — 9 600 ₽ (ТГ). Работает с ИИ.\n"
            "3) Бот: сбор контактов, консультант, оплата — 16 000 ₽ (ТГ). Работает с ИИ.\n\n"
            "Напишите номер (1-3)."
        )
        await state.set_state(OrderForm.waiting_for_bot_package)
        await state.update_data(bot_platform="telegram") # Запоминаем, что это ТГ
        await message.answer(text, reply_markup=main_kb)
        
    elif message.text == "🟣 MAX-бот":
        text = (
            "Выберите пакет MAX-бота:\n\n"
            "1) Бот для сбора контактов — 8 000 ₽ (MAX). Работает без ИИ.\n"
            "2) Сбор контактов и бот-консультант — 16 000 ₽ (MAX). Работает с ИИ.\n"
            "3) Бот: сбор контактов, консультант, оплата — 24 000 ₽ (MAX). Работает с ИИ.\n\n"
            "Напишите номер (1-3)."
        )
        await state.set_state(OrderForm.waiting_for_bot_package)
        await state.update_data(bot_platform="max") # Запоминаем, что это MAX
        await message.answer(text, reply_markup=main_kb)
        
    elif message.text == "🧠 AI-агент":
        text = (
            "AI-агент — это умный консультант 24/7 на вашем сайте.\n\n"
            "Один пакет. Стоимость: 16 000 ₽. Работает с ИИ.\n\n"
            "Вы согласны с этим выбором? (да/нет)"
        )
        # Сразу переводим на подтверждение суммы
        await state.update_data(
            total=16000, 
            services_text="AI-агент на сайт (консультант 24/7)"
        )
        await state.set_state(OrderForm.waiting_for_confirmation)
        await message.answer(text, reply_markup=main_kb)
        
    else:
        await message.answer("Пожалуйста, выберите вариант с помощью кнопок.")
        
# ===== ВЫБОР ТИПА САЙТА =====
@dp.message(OrderForm.waiting_for_site_type)
async def process_site_type(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    mapping = {
        "1": "len", "2": "info", "3": "vizit", "4": "portfolio", "5": "shop", "6": "universal",
        "лендинг": "len", "информационный": "info", "визитка": "vizit", "портфолио": "portfolio",
        "интернет-магазин": "shop", "универсальный": "universal"
    }
    site_type = mapping.get(text)
    if not site_type:
        await message.answer("Не понял. Пожалуйста, выберите номер от 1 до 6 или название услуги.")
        return

    await state.update_data(service="site", site_type=site_type)

    # Показываем доп. услуги
    addon_text = "Теперь выберите дополнительные услуги (если нужны).\nВот список:\n"
    for k, v in ADDON_NAMES.items():
        price = SITE_ADDONS.get(k, 0)
        addon_text += f"{k}) {v} — {price} ₽\n"
    addon_text += "Напишите номера через запятую (например: 1,3,5) или отправьте 'нет'."

    await state.set_state(OrderForm.waiting_for_addons)
    await message.answer(addon_text)

# ===== ВЫБОР ДОП. УСЛУГ ДЛЯ САЙТА =====
@dp.message(OrderForm.waiting_for_addons)
async def process_addons(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == "нет":
        addons = []
    else:
        parts = text.replace(",", " ").split()
        addons = []
        for p in parts:
            try:
                num = int(p)
                if num in SITE_ADDONS:
                    addons.append(num)
            except ValueError:
                pass
        if not addons and text.lower() != "нет":
            await message.answer("Я не нашёл подходящих номеров. Попробуйте снова или напишите 'нет'.")
            return

    data = await state.get_data()
    site_type = data.get("site_type")
    total, services_text = calculate_site_total(site_type, addons)

    await state.update_data(total=total, services_text=services_text)
    await state.set_state(OrderForm.waiting_for_confirmation)
    await message.answer(
        f"Ваш заказ:\n📦 {services_text}\n💰 Итоговая сумма: {total} ₽\n\nВы согласны с заказом? (да/нет)"
    )

# ===== ВЫБОР ПАКЕТА БОТА =====
@dp.message(OrderForm.waiting_for_bot_package)
async def process_bot_package(message: types.Message, state: FSMContext):
    text = message.text.strip()
    mapping = {"1": "contact", "2": "contact_consult", "3": "full"}
    package_key = mapping.get(text)
    if not package_key:
        await message.answer("Пожалуйста, выберите номер от 1 до 3.")
        return

    data = await state.get_data()
    platform = data.get("bot_platform", "telegram")

    if platform == "max":
        total = MAX_PACKAGE_PRICES.get(package_key, 0)
        services_text = MAX_PACKAGE_NAMES.get(package_key, "MAX-бот")
    else:
        total = BOT_PACKAGE_PRICES.get(package_key, 0)
        services_text = BOT_PACKAGE_NAMES.get(package_key, "Telegram-бот")

    await state.update_data(total=total, services_text=services_text)
    await state.set_state(OrderForm.waiting_for_confirmation)
    await message.answer(
        f"Ваш заказ:\n📦 {services_text}\n💰 Итоговая сумма: {total} ₽\n\nВы согласны с заказом? (да/нет)"
    )

# ===== ПОДТВЕРЖДЕНИЕ ЗАКАЗА =====
@dp.message(OrderForm.waiting_for_confirmation)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    offer_confirmed = data.get("offer_confirmed", False)

    # Если клиент еще НЕ подтвердил оферту
    if not offer_confirmed:
        if message.text.lower() == "да":
            # Запоминаем, что сумму он подтвердил, но оферту еще нет
            await state.update_data(offer_confirmed=True)
            # Показываем оферту, НО НЕ СОЗДАЕМ ПЛАТЕЖ
            await message.answer(
                "Отлично! Перед оформлением заказа прошу вас ознакомиться с договором публичной оферты:\n"
                "https://borisov.store/offer/\n\n"
                "В ней прописаны все условия заказа, оплаты, а также пункт 5.3 (сдача и приемка).\n"
                "Подтвердите, пожалуйста, что вы ознакомились с офертой (напишите «да»)."
            )
            return
        elif message.text.lower() == "нет":
            await state.clear()
            await message.answer(
                "Хорошо, возвращаемся к выбору. Нажмите «Цены», чтобы начать заново.",
                reply_markup=main_kb
            )
            return
        else:
            await message.answer("Пожалуйста, ответьте «да» или «нет».")
            return

    # Если клиент уже подтвердил оферту (пишет "да" второй раз)
    if message.text.lower() in ["да", "согласен", "ок", "подтверждаю"]:
        user_id = message.from_user.id
        username = message.from_user.username or "без username"
        contact = user_contacts.get(user_id, {})
        name = contact.get("name", "Неизвестно")
        phone = contact.get("phone", "неизвестно")
        services_text = data.get("services_text", "Без описания")
        total = data.get("total", 0)

        short_description = services_text[:100] + "..." if len(services_text) > 100 else services_text
        prepayment = int(total * 0.5)
        payment_url = create_payment(prepayment, f"Заказ: {short_description}", "https://borisov.store/thank-you")

        if payment_url:
            order_text = f"{services_text}, сумма {total} ₽"
            await append_to_sheet(name, phone, username, order_text)

            # Уведомление тебе в ТГ
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Новый заказ!\n"
                f"👤 Имя: {name}\n"
                f"📞 Телефон: {phone}\n"
                f"📋 Заказ: {services_text}\n"
                f"💰 Полная сумма: {total} ₽\n"
                f"💳 Предоплата 50%: {prepayment} ₽"
            )

            # Сообщение клиенту с ссылкой
            await message.answer(
                f"✅ Ваш заказ принят!\n\n"
                f"👤 Имя: {name}\n"
                f"📋 Состав заказа: {services_text}\n"
                f"💰 Полная сумма: {total} ₽\n"
                f"💳 Предоплата (50%): {prepayment} ₽\n\n"
                f"🔗 Оплатите предоплату по ссылке:\n{payment_url}\n\n"
                "Оставшиеся 50% вы оплатите после завершения работы.\n"
                "После оплаты мы начнём работу над вашим заказом."
            )
        else:
            await message.answer("Извините, не удалось создать платёж. Попробуйте позже или свяжитесь с нами через контакты на сайте.")
        
        await state.clear()
    else:
        await message.answer("Пожалуйста, подтвердите, что вы ознакомились с офертой, написав «да».")

# ===== ОБРАБОТЧИКИ КНОПОК (консультант) =====
@dp.message(F.text == "⚙️ Технологии")
async def handle_tech(message: types.Message):
    answer = (
        "🛠 <b>Технологии, которые мы используем:</b>\n\n"
        "🌐 <b>Для сайтов:</b> HTML5, CSS3, JavaScript, Мини-CRM (Google Таблицы), ЮKassa.\n\n"
        "🤖 <b>Для Telegram-ботов:</b> Python 3, aiogram 3.x, OpenRouter, Amvera/Render.\n\n"
        "🟣 <b>Для MAX-ботов:</b> Python 3, maxapi, OpenRouter, YooKassa, Amvera.\n\n"
        "🧠 <b>Для AI-агентов:</b> Python 3, FastAPI, OpenRouter, Amvera/Render.\n\n"
        "Подробнее о технологиях — на нашем сайте."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=SITE_URL)]]
    )
    await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")

@dp.message(F.text == "↩️ Гарантии")
async def handle_guarantee(message: types.Message):
    answer = (
        "На сервисе borisov.store мы предоставляем гарантийную поддержку в течение 30 дней после завершения разработки.\n\n"
        "Для получения более подробной информации, пожалуйста, нажмите кнопку «Перейти на сайт»."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/offer/")]]
    )
    await message.answer(answer, reply_markup=inline_kb)

@dp.message(F.text == "💳 Оплата")
async def handle_payment(message: types.Message):
    answer = (
        "Мы принимаем оплату через ЮKassa — это безопасный и надёжный способ оплаты, "
        "поддерживающий банковские карты, электронные кошельки и СБП. Также мы можем предложить Яндекс Сплит (рассрочку) и криптовалюту - USDT и USDC (сети Optimism, Arbitrum).\n\n"
        "<b>Порядок оплаты:</b>\n"
        "• Предоплата 50% перед началом работы.\n"
        "• Вторые 50% после приёмки готового сайта или бота.\n\n"
        "Для получения более подробной информации, пожалуйста, нажмите кнопку «Перейти на сайт»."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#pricing")]]
    )
    await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")

@dp.message(F.text == "🚚 Сроки и доставка")
async def handle_delivery(message: types.Message):
    answer = (
        "Стандартный срок разработки сайта или бота — до 3 рабочих дней с момента получения предоплаты и всех материалов.\n\n"
        "В сложных случаях срок может быть увеличен до 7 рабочих дней. Подробнее — в пункте 6.1 оферты.\n\n"
        "Для получения более подробной информации, пожалуйста, нажмите кнопку «Перейти на сайт»."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/offer/")]]
    )
    await message.answer(answer, reply_markup=inline_kb)

@dp.message(F.text == "🛡 Проверка самозанятого")
async def handle_selfemployed(message: types.Message):
    answer = (
        "Исполнитель — Борисов Сергей, самозанятый, ИНН: 665200001260.\n"
        "Проверить статус самозанятого можно через официальный сервис Федеральной налоговой службы.\n\n"
        "Для этого нажмите кнопку «Перейти на сайт» — она откроет страницу проверки."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://npd.nalog.ru/check-status/")]]
    )
    await message.answer(answer, reply_markup=inline_kb)

@dp.message(F.text == "🛠 Наши услуги")
async def handle_services(message: types.Message):
    answer = (
        "Здравствуйте! Я — официальный представитель сервиса borisov.store.\n\n"
        "Мы специализируемся на создании качественных и функциональных:\n"
        "🌐 <b>Сайтов</b> (от лендинга до интернет-магазина)\n"
        "🤖 <b>Telegram-ботов</b> (от сбора контактов до оплаты)\n"
        "🟣 <b>MAX-ботов</b> (инновационные решения для мессенджера MAX)\n"
        "🧠 <b>AI-агентов</b> (умный консультант прямо на вашем сайте)\n\n"
        "Сайты размещаются на бесплатном хостинге, а боты работают 24/7.\n\n"
        "Если вас интересуют наши услуги, вы можете узнать больше, нажав на кнопку «Перейти на сайт»."
    )
    # Ссылка ведет на раздел услуг (где находится портфолио)
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#services")]]
    )
    await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")

@dp.message(F.text == "📞 Контакты")
async def handle_contacts(message: types.Message):
    answer = (
        "Свяжитесь с нами любым удобным способом:\n\n"
        "📧 Email: wisebor@gmail.com\n"
        "📞 Телефон: +79582319212\n"
        "🌐 Сайт: https://borisov.store"
    )
    await message.answer(answer)

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ (НЕЙРОСЕТЬ) =====
@dp.message()
async def handle_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text

    # Проверка авторизации
    if user_id not in authorized_users:
        await message.answer(
            "Пожалуйста, сначала оставьте контактные данные, нажав кнопку «Оставить контакт».",
            reply_markup=contact_kb
        )
        return

    # Проверка, не находится ли пользователь в процессе заказа
    current_state = await state.get_state()
    if current_state in [OrderForm.waiting_for_type.state, OrderForm.waiting_for_site_type.state,
                         OrderForm.waiting_for_addons.state, OrderForm.waiting_for_bot_package.state,
                         OrderForm.waiting_for_confirmation.state, OrderForm.waiting_for_offer.state]:
        await message.answer("Вы в процессе оформления заказа. Чтобы отменить, отправьте /cancel.")
        return

    # Остальное — нейросеть
    await bot.send_chat_action(message.chat.id, "typing")

    if is_selfemployed_request(user_text):
        await message.answer("Выберите в меню: 🛡 Проверка самозанятого")
        return

    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[
                {"role": "system", "content": f"{KNOWLEDGE}\n\n"
                 "Отвечай без прямых ссылок. Ссылки могут быть только на кнопке «Перейти на сайт». "
                 "Если клиент спрашивает «Ты кто?», «Кто ты?», «Расскажи о себе» или «Что вы делаете?», "
                 "обязательно представься как консультант Borisov Store и перечисли ВСЕ наши услуги: "
                 "сайты, Telegram-боты, MAX-боты и AI-агенты. "
                 "Для выделения важных слов используй HTML-теги <b> и </b> (например: <b>сайты</b>)."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        answer = response.choices[0].message.content.strip()
        answer = answer.replace("<button>", "").replace("</button>", "")
    except Exception as e:
        answer = "Извините, произошла ошибка. Попробуйте ещё раз через минуту."

    target_url = SITE_URL
    if is_offer_request(user_text):
        target_url = "https://borisov.store/offer/"
    else:
        target_url = BUTTON_LINKS.get(user_text, SITE_URL)

    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=target_url)]]
    )
    await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML") # <-- ВОТ ЗДЕСЬ ДОБАВЛЕН parse_mode

# ========== HTTP-СЕРВЕР ДЛЯ RENDER ==========
async def handle(request):
    return web.Response(text="Bot is running")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"HTTP server started on port {PORT}")

async def delete_webhook():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook") as resp:
            result = await resp.json()
            print(f"Webhook deleted: {result}")

async def main():
    await delete_webhook()
    await run_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
