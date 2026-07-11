import os
import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SITE_URL = "https://borisov.store"
PORT = int(os.getenv("PORT", 10000))

# ========== АВТО-СБРОС WEBHOOK ==========
async def delete_webhook():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook") as resp:
            result = await resp.json()
            print(f"Webhook deleted: {result}")

# ========== БАЗА ЗНАНИЙ ==========
KNOWLEDGE = """
Ты — официальный представитель и консультант сервиса borisov.store.
Твоя задача — помогать клиентам, используя только информацию ниже. Запрещено вставлять прямые ссылки в текст ответа. Используй кнопку «Перейти на сайт».

О СЕРВИСЕ:
borisov.store — сервис по созданию сайтов на бесплатном хостинге GitHub Pages.
Исполнитель: Борисов Сергей Юрьевич, самозанятый.
Проверить статус самозанятого можно через кнопку «Перейти на сайт» под этим сообщением.

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
• Бесплатно, без лимитов
• Не требуется покупать отдельную CRM

**Приём платежей через ЮKassa**:
• Автоматическая, безопасная и надёжная оплата для ваших клиентов
• Поддержка банковских карт, электронных кошельков и СБП

ПОРЯДОК РАБОТЫ И ОПЛАТА:
- Клиент выбирает тариф или согласовывает индивидуальный заказ.
- Техническое задание (ТЗ) обсуждается только после полного ознакомления с офертой.
- Для начала работы нужны: материалы, ТЗ, доступ к GitHub (email и пароль).
- Оплата: предоплата 50% после согласования ТЗ, вторые 50% после приёмки.
- Срок разработки: до 3 рабочих дней (в сложных случаях до 7). Подробнее — в пункте 3.7 оферты.
- Бесплатный хостинг: GitHub Pages.
- Гарантийная поддержка: 30 дней.
- Доработки после гарантии: от 2000 руб.
- Отказ от сайта: возврат предоплаты за вычетом комиссии ЮKassa (3,5%). Условия возврата прописаны в оферте в п. 5.3.
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
    "↩️ Гарантии и возврат": "https://borisov.store/offer/",
    "📞 Контакты": "https://borisov.store/#contacts",
    "🛡 Проверка самозанятого": "https://npd.nalog.ru/check-status/",
    "⚙️ Технологии": SITE_URL,
    "⚡ Преимущества": "https://borisov.store/#advantages",
}

# ========== ТРИГГЕРЫ ДЛЯ ОФЕРТЫ ==========
OFFER_KEYWORDS = ["тз", "задание", "оферт", "договор", "ознакомиться"]

def is_offer_request(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in OFFER_KEYWORDS)

# ========== ТРИГГЕРЫ ДЛЯ САМОЗАНЯТОГО (исправлено) ==========
SELFEMPLOYED_KEYWORDS = ["самозанят", "проверк", "статус", "налогов", "инн"]

def is_selfemployed_request(text: str) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SELFEMPLOYED_KEYWORDS)

# ========== КЛИЕНТ OpenRouter ==========
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КНОПКИ МЕНЮ (4×2) ==========
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🛠 Наши услуги"), types.KeyboardButton(text="🚚 Сроки и доставка")],
        [types.KeyboardButton(text="💳 Оплата"), types.KeyboardButton(text="↩️ Гарантии и возврат")],
        [types.KeyboardButton(text="📞 Контакты"), types.KeyboardButton(text="🛡 Проверка самозанятого")],
        [types.KeyboardButton(text="⚙️ Технологии"), types.KeyboardButton(text="⚡ Преимущества")],
    ],
    resize_keyboard=True,
)

# ========== ФЛАГИ ПОКАЗА МЕНЮ ==========
menu_shown = set()

# ========== ОБРАБОТЧИКИ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    menu_shown.add(user_id)
    await message.answer(
        "Здравствуйте! Я виртуальный консультант сервиса borisov.store.\n"
        "Я расскажу об услугах, сроках, оплате и гарантиях.\n"
        "Задайте вопрос или воспользуйтесь кнопками ниже.",
        reply_markup=main_kb,
    )

@dp.message()
async def handle_question(message: types.Message):
    user_text = message.text
    user_id = message.from_user.id
    await bot.send_chat_action(message.chat.id, "typing")

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «ТЕХНОЛОГИИ» ---
    if user_text == "⚙️ Технологии":
        answer = (
            "🛠 <b>Наши технологии</b>\n\n"
            "🔹 <b>HTML5</b> — структура и разметка. Семантическая вёрстка, адаптивность, корректное отображение в любых браузерах.\n\n"
            "🔹 <b>CSS3</b> — дизайн и стили. Современный внешний вид, анимации, идеальная раскладка на всех устройствах.\n\n"
            "🔹 <b>JavaScript</b> — интерактивность и поведение. Умные формы, плавные переходы, динамический контент без перезагрузки.\n\n"
            "📊 <b>Мини-CRM на Google Таблицах</b> — все заявки попадают в таблицу и дублируются вам на почту. Бесплатно и без лимитов.\n\n"
            "💳 <b>Приём платежей через ЮKassa</b> — автоматическая, безопасная и надёжная оплата для ваших клиентов."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=SITE_URL)]]
        )
        await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")
        return

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «ГАРАНТИИ И ВОЗВРАТ» ---
    if user_text == "↩️ Гарантии и возврат":
        answer = (
            "На сервисе borisov.store мы предоставляем гарантийную поддержку в течение 30 дней после завершения разработки.\n\n"
            "Если вы решите отказаться от сайта, предоплата возвращается за вычетом комиссии ЮKassa (3,5%). Подробнее об условиях возврата вы можете узнать в пункте 5.3 оферты.\n\n"
            "Для получения более подробной информации, пожалуйста, нажмите кнопку «Перейти на сайт»."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/offer/")]]
        )
        await message.answer(answer, reply_markup=inline_kb)
        return

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «ОПЛАТА» (комиссия убрана) ---
    if user_text == "💳 Оплата":
        answer = (
            "Мы принимаем оплату через ЮKassa — это безопасный и надёжный способ для ваших клиентов, "
            "поддерживающий банковские карты, электронные кошельки и СБП.\n\n"
            "<b>Порядок оплаты:</b>\n"
            "• Предоплата 50% после согласования технического задания.\n"
            "• Вторые 50% после приёмки готового сайта.\n\n"
            "Если у вас есть вопросы по другим аспектам сервиса, нажмите кнопку «Перейти на сайт»."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#pricing")]]
        )
        await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")
        return

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «СРОКИ И ДОСТАВКА» ---
    if user_text == "🚚 Сроки и доставка":
        answer = (
            "Стандартный срок разработки сайта — до 3 рабочих дней с момента получения предоплаты и всех материалов.\n\n"
            "В сложных случаях срок может быть увеличен до 7 рабочих дней. Подробнее — в пункте 3.7 оферты.\n\n"
            "Если у вас есть вопросы по другим аспектам сервиса, нажмите кнопку «Перейти на сайт»."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/offer/")]]
        )
        await message.answer(answer, reply_markup=inline_kb)
        return

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «ПРОВЕРКА САМОЗАНЯТОГО» ---
    if user_text == "🛡 Проверка самозанятого":
        answer = (
            "Исполнитель — Борисов Сергей Юрьевич, самозанятый.\n"
            "Проверить статус самозанятого можно через официальный сервис Федеральной налоговой службы.\n\n"
            "Для этого нажмите кнопку «Перейти на сайт» — она откроет страницу проверки."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://npd.nalog.ru/check-status/")]]
        )
        await message.answer(answer, reply_markup=inline_kb)
        return

    # --- ФИКСИРОВАННЫЙ ОТВЕТ ДЛЯ «ПРЕИМУЩЕСТВА» (новая кнопка) ---
    if user_text == "⚡ Преимущества":
        answer = (
            "Наши преимущества помогут вам выделиться среди конкурентов и привлечь больше клиентов.\n\n"
            "Подробно о них можно узнать, нажав кнопку «Перейти на сайт» — она откроет раздел «Почему выбирают нас»."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url="https://borisov.store/#advantages")]]
        )
        await message.answer(answer, reply_markup=inline_kb)
        return

    # --- ОСНОВНАЯ ЛОГИКА (нейросеть) ---
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
    except Exception as e:
        answer = "Извините, произошла ошибка. Попробуйте ещё раз через минуту.\n\nЕсли ошибка повторяется, свяжитесь со мной через контакты на сайте."

    # Определяем, куда ведёт кнопка «Перейти на сайт»
    target_url = SITE_URL
    if is_offer_request(user_text):
        target_url = "https://borisov.store/offer/"
    elif is_selfemployed_request(user_text):
        target_url = "https://npd.nalog.ru/check-status/"
    else:
        target_url = BUTTON_LINKS.get(user_text, SITE_URL)

    # Отправляем ответ
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=target_url)]]
    )
    await message.answer(answer, reply_markup=inline_kb)

    # Показываем меню только один раз
    if user_id not in menu_shown:
        menu_shown.add(user_id)
        await message.answer("Воспользуйтесь меню ниже:", reply_markup=main_kb)

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

# ========== ЗАПУСК ==========
async def main():
    await delete_webhook()
    await run_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
