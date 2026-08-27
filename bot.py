import os
import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SITE_URL = "https://borisov.store"
PORT = int(os.getenv("PORT", 10000))

# ========== ССЫЛКА НА APPS SCRIPT (НОВАЯ ТАБЛИЦА) ==========
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx1wT8Zo36a-hgk4T1ZgjF2H2IxGehutYrlLsk87THIl98x0apfSA_LtpkN_nFLapOSiw/exec"

# ========== БАЗА ЗНАНИЙ ==========
KNOWLEDGE = """
Ты — официальный представитель и консультант сервиса borisov.store.
Твоя задача — помогать клиентам, используя только информацию ниже. Запрещено вставлять прямые ссылки в текст ответа. Используй кнопку «Перейти на сайт».

О СЕРВИСЕ:
borisov.store — сервис по созданию сайтов на бесплатном хостинге GitHub Pages.
Исполнитель: Борисов Сергей, самозанятый.
Мы создаем качественные и функциональные сайты. Чтобы попасть на наш сайт нажмите кнопку «Перейти на сайт» под этим сообщением.

НАШИ ТЕХНОЛОГИИ:
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

# ========== ССЫЛКИ ДЛЯ КНОПОК ==========
BUTTON_LINKS = {
    "🛠 Наши услуги": "https://borisov.store/#services",
    "🚚 Сроки и доставка": "https://borisov.store/offer/",
    "💳 Оплата": "https://borisov.store/#pricing",
    "↩️ Гарантии": "https://borisov.store/offer/",
    "📞 Контакты": "https://borisov.store/#contacts",
    "🛡 Проверка самозанятого": "https://npd.nalog.ru/check-status/",
    "⚙️ Технологии": SITE_URL,
    "⚡ Преимущества": "https://borisov.store/#advantages",
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

# ========== БОТ И ДИСПЕТЧЕР ==========
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# ========== КЛАВИАТУРЫ ==========
# Кнопка для сбора контакта
contact_kb = types.ReplyKeyboardMarkup(
    keyboard=[[types.KeyboardButton(text="📝 Оставить контакт")]],
    resize_keyboard=True
)

# Главное меню консультанта (8 кнопок)
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🛠 Наши услуги"), types.KeyboardButton(text="🚚 Сроки и доставка")],
        [types.KeyboardButton(text="💳 Оплата"), types.KeyboardButton(text="↩️ Гарантии")],
        [types.KeyboardButton(text="📞 Контакты"), types.KeyboardButton(text="🛡 Проверка самозанятого")],
        [types.KeyboardButton(text="⚙️ Технологии"), types.KeyboardButton(text="⚡ Преимущества")],
    ],
    resize_keyboard=True
)

# ========== ХРАНИЛИЩЕ АВТОРИЗОВАННЫХ ==========
authorized_users = set()

# ========== ФУНКЦИЯ ЗАПИСИ В ТАБЛИЦУ ==========
async def append_to_sheet(name: str, phone: str, username: str, order: str = ""):
    """Отправляет данные в Google Apps Script"""
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
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=contact_kb)

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
    # Проверка формата
    if not (phone.startswith("+") and phone[1:].isdigit() and len(phone) >= 12) and not (phone.isdigit() and len(phone) >= 11):
        await message.answer("Пожалуйста, введите корректный номер (11 цифр или +7XXXXXXXXXX).")
        return

    data = await state.get_data()
    name = data["name"]
    user_id = message.from_user.id
    username = message.from_user.username or "без username"

    # Запись контакта в таблицу (order = "")
    await append_to_sheet(name, phone, username, "")

    # Переводим в режим консультанта
    authorized_users.add(user_id)
    await state.clear()

    await message.answer(
        f"Спасибо, {name}! Теперь я ваш консультант.\n"
        "Задайте вопрос или воспользуйтесь кнопками ниже.",
        reply_markup=main_kb
    )

# ===== РЕЖИМ КОНСУЛЬТАНТА (обработка кнопок) =====

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

@dp.message(F.text == "⚡ Преимущества")
async def handle_advantages(message: types.Message):
    answer = (
        "Наши преимущества помогут вам выделиться среди конкурентов и привлечь больше клиентов.\n\n"
        "Подробно о них можно узнать, нажав кнопку «Перейти на сайт» — она откроет раздел «Почему выбирают нас»."
    )
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#advantages")]]
    )
    await message.answer(answer, reply_markup=inline_kb)

@dp.message(F.text == "📞 Контакты")
async def handle_contacts(message: types.Message):
    answer = (
        "Свяжитесь с нами любым удобным способом:\n\n"
        "📧 Email: wisebor@gmail.com\n"
        "📱 Telegram: @borisovsergey71\n"
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

    # Проверка, не находится ли пользователь в процессе ввода контакта
    current_state = await state.get_state()
    if current_state in [ContactForm.waiting_for_name.state, ContactForm.waiting_for_phone.state]:
        await message.answer("Пожалуйста, завершите ввод контакта или отправьте /cancel для отмены.")
        return

    await bot.send_chat_action(message.chat.id, "typing")

    # Запросы о самозанятости
    if is_selfemployed_request(user_text):
        await message.answer("Выберите в меню: 🛡 Проверка самозанятого")
        return

    # Основная логика через нейросеть
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
        answer = "Извините, произошла ошибка. Попробуйте ещё раз через минуту.\n\nЕсли ошибка повторяется, свяжитесь со мной через контакты на сайте."

    # Определяем ссылку для кнопки
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
