import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

BOT_TOKEN = "7120066348:AAHgyAD0pcCa9kbecR11fCtIfumzVIqyrQg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def handel_start(m: types.Message):
    await m.answer(text=f"Hello, {m.from_user.full_name}")


@dp.message()
async def echo_mes(m: types.Message):
    await m.answer(text=m.text)


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
