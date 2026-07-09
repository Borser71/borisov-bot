import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
SITE_URL = "https://borisov.store"
PORT = int(os.getenv("PORT", 10000))

# База знаний
KNOWLEDGE = """
Ты — официальный представитель и консультант сервиса по созданию сайтов borisov.store.
Твоя задача — помогать клиентам, используя только информацию ниже.

О СЕРВИСЕ:
borisov.store — сервис по созданию сайтов на бесплатном хостинге GitHub Pages.
Исполнитель: Борисов Сергей Юрьевич, самозанятый.
Проверить статус самозанятого: https://npd.nalog.ru/check-status/ (ИНН 665200001260).
Сайты создаются на основе HTML5, CSS и JavaScript.

ТЕХНИЧЕСКИЕ ВОЗМОЖНОСТИ:
- В проекты встроена мини-CRM: вся информация о заказе автоматически приходит исполнителю на почту.
- Можно подключить корпоративную почту и делать рассылку с неё.

ПОРЯДОК РАБОТЫ И ОПЛАТА:
- Клиент выбирает тариф на сайте или согласовывает индивидуальный заказ.
- Для начала работы клиент предоставляет: материалы, ТЗ, доступ к GitHub (email и пароль).
- Оплата: предоплата 50% после согласования ТЗ, вторые 50% после приемки.
- Срок разработки: до 3 рабочих дней (в сложных случаях до 7).
- Бесплатный хостинг: GitHub Pages.
- Гарантийная поддержка: 30 дней.
- Доработки после гарантии: от 2000 руб.
- Отказ от сайта: возврат предоплаты за вычетом комиссии ЮKassa (3,5%).
- Домен оплачивается клиентом отдельно.

НАВИГАЦИЯ ПО САЙТУ:
Если клиент спрашивает о чём-то, чего нет в твоей базе, или хочет узнать подробнее про услуги, преимущества, цены или контакты — направляй его прямо в соответствующий раздел сайта:
- Услуги и тарифы: https://borisov.store/#services
- Преимущества: https://borisov.store/#advantages
- Цены: https://borisov.store/#pricing
- Контакты: https://borisov.store/#contacts
"""

# Подключаем OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КНОПКИ ==========
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🛍 Услуги и тарифы")],
        [types.KeyboardButton(text="🚚 Сроки и доставка сайта")],
        [types.KeyboardButton(text="💳 Оплата")],
        [types.KeyboardButton(text="↩️ Гарантии и возврат")],
        [types.KeyboardButton(text="📞 Контакты")],
        [types.KeyboardButton(text="🛡 Проверка самозанятого")],
    ],
    resize_keyboard=True,
)

# ========== ОБРАБОТЧИКИ ==========
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте! Я виртуальный консультант borisov.store.\n"
        "Я расскажу об услугах, сроках, оплате и гарантиях.\n"
        "Задайте вопрос или воспользуйтесь кнопками ниже.",
        reply_markup=main_kb,
    )

@dp.message()
async def handle_question(message: types.Message):
    user_text = message.text
    await bot.send_chat_action(message.chat.id, "typing")

    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[
                {"role": "system", "content": f"{KNOWLEDGE}\n\nНаправляй клиента на соответствующий раздел сайта {SITE_URL}, если информации недостаточно."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Извините, произошла ошибка. Попробуйте ещё раз через минуту.\n\nЕсли ошибка повторяется, свяжитесь со мной напрямую через контакты на сайте: {SITE_URL}/#contacts"

    # Добавляем кнопку-ссылку на сайт
    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Перейти на сайт", url=SITE_URL)],
        ],
    )
    await message.answer(answer, reply_markup=inline_kb)

# ========== HTTP-сервер для Render ==========
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
    await run_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
