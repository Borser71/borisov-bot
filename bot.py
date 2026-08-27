import os
import asyncio
import aiohttp
import uuid
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

# ========== НАСТРОЙКА ЮKASSA ==========
if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
    Configuration.account_id = YOOKASSA_SHOP_ID
    Configuration.secret_key = YOOKASSA_SECRET_KEY
    print("ЮKassa настроена")
else:
    print("ЮKassa не настроена (отсутствуют shopId или secretKey)")

# ========== ССЫЛКА НА APPS SCRIPT (НОВАЯ ТАБЛИЦА) ==========
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwObzBGHaCjBi0J_fOO0tRyo6P50WyINg-P1eVCwKk1uKz5hoZ7XdC5RBmcQ0uSKpazFA/exec"

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
- Условия сдачи и приемки сайта прописаны в оферте в п. 5.3.
- Домен оплачивается клиентом отдельно.

ПРЕИМУЩЕСТВА:
Подробно о преимуществах можно узнать, нажав кнопку «Перейти на сайт» — вы попадёте в раздел «Почему выбирают нас».

НАВИГАЦИЯ:
Если клиент спрашивает о чём-то, чего нет в базе, предложи нажать «Перейти на сайт» для перехода в нужный раздел.
"""
# ========== ЦЕНЫ (из MAX-бота) ==========
SITE_NAMES = {
    "len": "Лендинг",
    "info": "Информационный сайт",
    "vizit": "Визитка",
    "portfolio": "Портфолио",
    "shop": "Интернет-магазин",
    "universal": "Универсальный сайт"
}
SITE_PRICES = {
    "len": 8000,
    "info": 12000,
    "vizit": 16000,
    "portfolio": 20000,
    "shop": 24000,
    "universal": 40000
}
SITE_ADDONS = {
    1: 0,      # favicon
    2: 1600,   # форма обратной связи
    3: 1600,   # карта проезда
    4: 2400,   # еще 6 товаров
    5: 2400,   # оферта
    6: 2400,   # политика конфиденциальности
    7: 2400,   # блок отзывов
    8: 2400,   # Яндекс-Метрика
    9: 2400,   # виджет звонка
    10: 4000,  # еще 2 товара
    11: 4000,  # автоплатеж
    12: 4000,  # Google Таблица
    13: 4000   # календарь
}
BOT_ADDONS = {
    1: 4000,   # Google Таблица
    2: 4000,   # календарь
    3: 4000    # автоплатеж
}
ADDON_NAMES = {
    1: "favicon", 2: "Форма обратной связи", 3: "Карта проезда",
    4: "Еще 6 товаров", 5: "Оферта", 6: "Политика конфиденциальности",
    7: "Блок отзывов", 8: "Яндекс-Метрика", 9: "Виджет звонка",
    10: "Еще 2 товара", 11: "Автоплатеж", 12: "Google Таблица", 13: "Календарь"
}
BOT_ADDON_NAMES = {1: "Google Таблица", 2: "Календарь", 3: "Автоплатеж"}

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
    waiting_for_base_service = State()
    waiting_for_addons = State()
    waiting_for_confirmation = State()

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
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
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

# Функция расчёта суммы
def calculate_total(service: str, site_type: str = None, addons: list = None) -> tuple:
    total = 0.0
    services_text = ""
    if addons:
        addons = list(set(addons))  # убираем дубли
    if service == "site" and site_type:
        total += SITE_PRICES.get(site_type, 0)
        services_text = SITE_NAMES.get(site_type, "Сайт")
        if addons:
            addon_list = []
            for a in addons:
                total += SITE_ADDONS.get(a, 0)
                addon_list.append(ADDON_NAMES.get(a, str(a)))
            if addon_list:
                services_text += " + " + ", ".join(addon_list)
    elif service == "bot":
        total += 12000
        services_text = "Telegram-бот"
        if addons:
            addon_list = []
            for a in addons:
                total += BOT_ADDONS.get(a, 0)
                addon_list.append(BOT_ADDON_NAMES.get(a, str(a)))
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

    # Проверяем, не находится ли пользователь уже в процессе заказа
    current_state = await state.get_state()
    if current_state in [OrderForm.waiting_for_base_service.state, OrderForm.waiting_for_addons.state, OrderForm.waiting_for_confirmation.state]:
        await message.answer("Вы уже в процессе оформления заказа. Чтобы отменить, отправьте /cancel.")
        return

    text = (
        "Выберите тип сайта или бота:\n\n"
        "1) Лендинг — 8 000 ₽\n"
        "2) Информационный сайт — 12 000 ₽\n"
        "3) Визитка — 16 000 ₽\n"
        "4) Портфолио — 20 000 ₽\n"
        "5) Интернет-магазин — 24 000 ₽\n"
        "6) Универсальный сайт — 40 000 ₽\n"
        "7) Telegram-бот — 12 000 ₽\n\n"
        "Напишите номер (1-7) или название услуги (например, 'лендинг')."
    )
    await state.set_state(OrderForm.waiting_for_base_service)
    await message.answer(text)

# ===== ВЫБОР БАЗОВОЙ УСЛУГИ =====
@dp.message(OrderForm.waiting_for_base_service)
async def process_base_service(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    mapping = {
        "1": "len", "2": "info", "3": "vizit", "4": "portfolio", "5": "shop", "6": "universal", "7": "bot",
        "лендинг": "len", "информационный": "info", "визитка": "vizit", "портфолио": "portfolio",
        "интернет-магазин": "shop", "универсальный": "universal", "telegram-бот": "bot"
    }
    site_type = mapping.get(text)
    if not site_type:
        await message.answer("Не понял. Пожалуйста, выберите номер от 1 до 7 или название услуги.")
        return

    service = "bot" if site_type == "bot" else "site"
    await state.update_data(service=service, site_type=site_type)

    # Показываем дополнительные услуги
    if service == "site":
        addon_text = "Теперь выберите дополнительные услуги (если нужны).\nВот список для сайта:\n"
        for k, v in ADDON_NAMES.items():
            price = SITE_ADDONS.get(k, 0)
            addon_text += f"{k}) {v} — {price} ₽\n"
        addon_text += "Напишите номера через запятую (например: 1,3,5) или отправьте 'нет'."
    else:
        addon_text = "Теперь выберите дополнительные услуги (если нужны).\nВот список для бота:\n"
        for k, v in BOT_ADDON_NAMES.items():
            price = BOT_ADDONS.get(k, 0)
            addon_text += f"{k}) {v} — {price} ₽\n"
        addon_text += "Напишите номера через запятую (например: 1,2) или отправьте 'нет'."

    await state.set_state(OrderForm.waiting_for_addons)
    await message.answer(addon_text)

# ===== ВЫБОР ДОПОЛНИТЕЛЬНЫХ УСЛУГ =====
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
                addons.append(num)
            except ValueError:
                pass
        data = await state.get_data()
        service = data.get("service")
        valid = SITE_ADDONS.keys() if service == "site" else BOT_ADDONS.keys()
        addons = [a for a in addons if a in valid]
        if not addons and text.lower() != "нет":
            await message.answer("Я не нашёл подходящих номеров. Попробуйте снова или напишите 'нет'.")
            return

    await state.update_data(addons=addons)

    # Расчёт суммы
    data = await state.get_data()
    service = data.get("service")
    site_type = data.get("site_type")
    total, services_text = calculate_total(service, site_type, addons)

    await state.update_data(total=total, services_text=services_text)

    await state.set_state(OrderForm.waiting_for_confirmation)
    await message.answer(
        f"Ваш заказ:\n"
        f"📦 {services_text}\n"
        f"💰 Итоговая сумма: {total} ₽\n\n"
        f"Вы согласны с заказом? (да/нет)"
    )

# ===== ПОДТВЕРЖДЕНИЕ ЗАКАЗА =====
@dp.message(OrderForm.waiting_for_confirmation)
async def confirm_order(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        data = await state.get_data()
        user_id = message.from_user.id
        username = message.from_user.username or "без username"
        contact = user_contacts.get(user_id, {})
        name = contact.get("name", "Неизвестно")
        phone = contact.get("phone", "неизвестно")
        services_text = data.get("services_text", "Без описания")
        total = data.get("total", 0)

        # Обрезаем описание до 100 символов (чтобы гарантированно уложиться в 128)
        short_description = services_text[:100] + "..." if len(services_text) > 100 else services_text
        payment_url = create_payment(total, f"Заказ: {short_description}", "https://borisov.store/thank-you")

        if payment_url:
            # Запись заказа в таблицу
            order_text = f"{services_text}, сумма {total} ₽"
            await append_to_sheet(name, phone, username, order_text)

            # Отправляем клиенту сообщение с деталями (как в MAX-боте)
            await message.answer(
                f"✅ Ваш заказ принят!\n\n"
                f"👤 Имя: {name}\n"
                f"📋 Состав заказа: {services_text}\n"
                f"💰 Сумма: {total} ₽\n\n"
                f"🔗 Оплатите по ссылке:\n{payment_url}\n\n"
                "После оплаты мы начнём работу над вашим заказом."
            )
        else:
            await message.answer(
                "Извините, не удалось создать платёж. Попробуйте позже или свяжитесь с нами через контакты на сайте."
            )

        await state.clear()

    elif message.text.lower() == "нет":
        await state.clear()
        await message.answer(
            "Хорошо, возвращаемся к выбору. Нажмите «Цены», чтобы начать заново.",
            reply_markup=main_kb
        )
    else:
        await message.answer("Пожалуйста, ответьте «да» или «нет».")

# ===== ОБРАБОТЧИКИ КНОПОК (консультант) =====
@dp.message(F.text == "⚙️ Технологии")
async def handle_tech(message: types.Message):
    answer = (
        "🛠 <b>Наши технологии</b>\n\n"
        "🔹 <b>HTML5</b> — структура и разметка. Семантическая вёрстка, адаптивность, корректное отображение в любых браузерах.\n\n"
        "🔹 <b>CSS3</b> — дизайн и стили. Современный внешний вид, анимации, идеальная раскладка на всех устройствах.\n\n"
        "🔹 <b>JavaScript</b> — интерактивность и поведение. Умные формы, плавные переходы, динамический контент без перезагрузки.\n\n"
        "📊 <b>Мини-CRM на Google Таблицах</b> — все заявки попадают в таблицу и дублируются вам на почту. Без лимитов.\n\n"
        "💳 <b>Приём платежей через ЮKassa</b> — автоматическая, безопасная и надёжная оплата через СБП и карты."
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
        "• Вторые 50% после приёмки готового сайта.\n\n"
        "Для получения более подробной информации, пожалуйста, нажмите кнопку «Перейти на сайт»."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#pricing")]]
    )
    await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")

@dp.message(F.text == "🚚 Сроки и доставка")
async def handle_delivery(message: types.Message):
    answer = (
        "Стандартный срок разработки сайта — до 3 рабочих дней с момента получения предоплаты и всех материалов.\n\n"
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
        "Мы специализируемся на создании качественных и функциональных **сайтов** и **Telegram-ботов**.\n"
        "Сайты размещаются на бесплатном хостинге GitHub Pages, боты работают 24/7.\n\n"
        "Если вас интересуют наши услуги, вы можете узнать больше, нажав на кнопку «Перейти на сайт» под этим сообщением."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=SITE_URL)]]
    )
    await message.answer(answer, reply_markup=inline_kb)

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
    if current_state in [OrderForm.waiting_for_base_service.state, OrderForm.waiting_for_addons.state, OrderForm.waiting_for_confirmation.state]:
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
                {"role": "system", "content": f"{KNOWLEDGE}\n\nОтвечай без прямых ссылок. Ссылки могут быть только на кнопке «Перейти на сайт»."},
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
    await message.answer(answer, reply_markup=inline_kb)

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
