import logging, os

from aiogram import Bot, Dispatcher, executor, types
from utils import keyboards, messages
from dotenv import load_dotenv
from utils.parser import GroupUserParser
from telethon.errors.rpcerrorlist import ChatAdminRequiredError, InviteHashExpiredError
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import re

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

messages_limit=5000
messages_per_participant_limit=10

parser = GroupUserParser(os.getenv('PHONE_NUMBER'), os.getenv('API_KEY'),
                            os.getenv('API_HASH'), messages_limit=messages_limit,
                            messages_per_participant_limit=messages_per_participant_limit)


@dp.message_handler(lambda message: re.match("http[s]*:\/\/t.me\/.+", message.text.strip()) or \
                                    re.match("t.me\/.+", message.text.strip()))
async def get_url(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['urls'].append(message.text)
        await bot.send_message(message.from_id, messages.ENTER_NEXT_URL, reply_markup=keyboards.main_kb_markup)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        data['keywords'] = []
        data['urls'] = []

    await bot.send_message(message.from_id, messages.GREETING_MESSAGE
                            .format(messages_limit, messages_per_participant_limit))
    await bot.send_message(message.from_id, messages.ENTER_KEYWORDS)

@dp.message_handler(lambda message: message.text == keyboards.PARSE_СOMMAND)
async def parse_command(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        if data['keywords']:
            if not data['urls']:
                await bot.send_message(message.from_id, messages.EMPTY_URLS_ERROR)
            
            for url in data['urls']:
                await bot.send_message(message.from_id, messages.PARSING_CHANNEL_MESSAGE.format(url))
                try:
                    df = await parser(url, data['keywords'])
                    df.to_csv(f"outputs/{url.split('/')[-1]}.csv")
                    await bot.send_document(message.from_id, open(f"outputs/{url.split('/')[-1]}.csv", "rb"))
                    os.remove(f"outputs/{url.split('/')[-1]}.csv")

                except ChatAdminRequiredError:
                    await bot.send_message(message.from_id, messages.GROUP_ADMIN_REQUIRED_ERROR.format(url))
                    await bot.send_message(message.from_id, messages.TRY_OTHER_URLS)

                except InviteHashExpiredError:
                    await bot.send_message(message.from_id, messages.INVITE_HASH_EXPIRED_ERROR.format(url))
                    await bot.send_message(message.from_id, messages.TRY_OTHER_URLS)

                except ValueError:
                    await bot.send_message(message.from_id, messages.VALUE_ERROR.format(url))
                    await bot.send_message(message.from_id, messages.TRY_OTHER_URLS)

        else:
            await bot.send_message(message.from_id, messages.EMPTY_KEYWORDS_ERROR)


@dp.message_handler(lambda message: message.text == keyboards.CHANGE_KEYWORDS)
async def change_keywords(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['keywords'] = []
        await bot.send_message(message.from_id, messages.ENTER_KEYWORDS)

@dp.message_handler(lambda message: message.text == keyboards.CHECK_URLS)
async def check_urls(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            await bot.send_message(message.from_id, data['urls'])
        except KeyError:
            await bot.send_message(message.from_id, '[]')

@dp.message_handler(lambda message: message.text == keyboards.CHECK_KEYWORDS)
async def check_keywords(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            await bot.send_message(message.from_id, data['keywords'])
        except KeyError:
            await bot.send_message(message.from_id, '[]')

@dp.message_handler(lambda message: re.match("[а-яА-Я0-9]*", message.text.strip()))
async def set_keywords(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['keywords'] = [keyword.strip() for keyword in message.text.split(',')]
        if data['urls']:
            await bot.send_message(message.from_id, messages.ENTER_NEXT_URL)
        else:
            await bot.send_message(message.from_id, messages.ENTER_URL)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)