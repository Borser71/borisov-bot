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
• Кроссбузерность: Chrome, Firefox, Safari, Edge, Яндекс.Браузер
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

# ========== ОБРАБОТЧИКИ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте! Я виртуальный консультант сервиса borisov.store.\n"
        "Я расскажу об услугах, сроках, оплате и гарантиях.\n"
        "Задайте вопрос или воспользуйтесь кнопками ниже.",
        reply_markup=main_kb,
    )

@dp.message()
async def handle_question(message: types.Message):
    user_text = message.text
    await bot.send_chat_action(message.chat.id, "typing")

    # Блок «Технологии» отдаём без нейросети, чтобы гарантировать точность
    if user_text == "⚙️ Технологии":
        answer = (
            "🛠 <b>Наши технологии</b>\n\n"
            "Ваш сайт будет построен на трёх китах:\n\n"
            "🔹 <b>HTML5</b> — структура и разметка. Семантическая вёрстка, адаптивность, "
            "корректное отображение в любых браузерах.\n\n"
            "🔹 <b>CSS3</b> — дизайн и стили. Современный внешний вид, анимации, "
            "идеальная раскладка на всех устройствах.\n\n"
            "🔹 <b>JavaScript</b> — интерактивность и поведение. Умные формы, "
            "плавные переходы, динамический контент без перезагрузки.\n\n"
            "📊 <b>Мини-CRM на Google Таблицах</b> — все заявки попадают в таблицу "
            "и дублируются вам на почту. Бесплатно и без лимитов."
        )
        inline_kb = types.InlineKeyboardMarkup(
            inline_keyboard=[[types.InlineKeyboardButton(text="Перейти на сайт", url=SITE_URL)]]
        )
        await message.answer(answer, reply_markup=inline_kb, parse_mode="HTML")
        return

    # Основная логика – ответ через нейросеть
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

# ========== ЗАПУСК ==========
async def main():
    await delete_webhook()
    await run_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
