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

# ========== БАЗА ЗНАНИЙ (без прямых ссылок, «сайт» вместо «сервис») ==========
KNOWLEDGE = """
Ты — официальный представитель и консультант сайта borisov.store.
Твоя задача — помогать клиентам, используя только информацию ниже. Не показывай ссылки в тексте ответа.

О САЙТЕ:
borisov.store — сайт по созданию сайтов на бесплатном хостинге GitHub Pages.
Исполнитель: Борисов Сергей Юрьевич, самозанятый.
Проверить статус самозанятого можно через кнопку «Перейти на сайт» под этим сообщением.
Сайты создаются на основе HTML5, CSS и JavaScript.

ТЕХНИЧЕСКИЕ ВОЗМОЖНОСТИ:
- В проекты встроена мини-CRM: вся информация о заказе автоматически приходит исполнителю на почту.
- Можно подключить корпоративную почту и делать рассылку с неё.

ПОРЯДОК РАБОТЫ И ОПЛАТА:
- Клиент выбирает тариф на сайте или согласовывает индивидуальный заказ.
- Для начала работы клиент предоставляет: материалы, ТЗ, доступ к GitHub (email и пароль).
- Оплата: предоплата 50% после согласования ТЗ, вторые 50% после приемки.
- Срок разработки: до 3 рабочих дней (в сложных случаях до 7). Подробнее — в пункте 3.7 оферты, доступной по кнопке «Перейти на сайт».
- Бесплатный хостинг: GitHub Pages.
- Гарантийная поддержка: 30 дней.
- Доработки после гарантии: от 2000 руб.
- Отказ от сайта: возврат предоплаты за вычетом комиссии ЮKassa (3,5%). Подробнее — в пункте 5.3 оферты.
- Домен оплачивается клиентом отдельно.

НАВИГАЦИЯ ПО САЙТУ:
Если клиент спрашивает о чём-то, чего нет в твоей базе, или хочет узнать подробнее про услуги, преимущества, цены или контакты — предложи нажать кнопку «Перейти на сайт» для перехода в нужный раздел.
"""

# ========== ССЫЛКИ ДЛЯ КНОПОК (обновлены названия и URL) ==========
BUTTON_LINKS = {
    "Наши услуги": "https://borisov.store/#services",
    "🚚 Сроки и доставка сайта": "https://borisov.store/offer/#3.7",
    "💳 Оплата": "https://borisov.store/#pricing",
    "↩️ Гарантии и возврат": "https://borisov.store/offer/#5.3",
    "📞 Контакты": "https://borisov.store/#contacts",
    "🛡 Проверка самозанятого": "https://npd.nalog.ru/check-status/",
}

# ========== КЛИЕНТ OpenRouter ==========
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== КНОПКИ МЕНЮ (3×2, с новой кнопкой «Наши услуги») ==========
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Наши услуги"), types.KeyboardButton(text="🚚 Сроки и доставка сайта")],
        [types.KeyboardButton(text="💳 Оплата"), types.KeyboardButton(text="↩️ Гарантии и возврат")],
        [types.KeyboardButton(text="📞 Контакты"), types.KeyboardButton(text="🛡 Проверка самозанятого")],
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

    # Получаем ответ от нейросети
    try:
        response = await client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[
                {"role": "system", "content": f"{KNOWLEDGE}\n\nНаправляй клиента на соответствующий раздел сайта через кнопку «Перейти на сайт», если информации недостаточно."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.3,
            max_tokens=400,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = "Извините, произошла ошибка. Попробуйте ещё раз через минуту.\n\nЕсли ошибка повторяется, свяжитесь со мной через контакты на сайте."

    # Определяем URL для кнопки «Перейти на сайт»
    target_url = BUTTON_LINKS.get(user_text, SITE_URL)

    inline_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Перейти на сайт", url=target_url)],
        ],
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
