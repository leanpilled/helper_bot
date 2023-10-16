import logging
import asyncio
import openai
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from pytz import utc

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '6222270154:AAFcFa5W9ecys8MC68ZgKuQ0XRwFaMkRGpg'

API_KEY = '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'
messages = [{"role": "system", "content" : "You’re a kind helpful assistant"}]
openai.api_key = API_KEY

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    task = State()
    deadline = State()

tasks = {}

async def on_startup(dp):
    await bot.send_message(chat_id=1270860013, text='Bot has been started')


async def on_shutdown(dp):
    await bot.send_message(chat_id=1270860013, text='Bot has been stopped')

    await dp.storage.close()
    await dp.storage.wait_closed()


async def send_deadline_reminder():
    while True:
        await asyncio.sleep(60)
        now = utc.localize(datetime.now())
        now = now.replace(tzinfo=None)
        for task, deadline in tasks.items():
            time_left = deadline - now

            if timedelta(minutes=15) >= time_left > timedelta(minutes=14):
                await bot.send_message(chat_id=1270860013, text=f"⏰ 15-minute reminder: {task}")
            elif timedelta(days=1) >= time_left > timedelta(days=1) - timedelta(minutes=1):
                await bot.send_message(chat_id=1270860013, text=f"📆 1-day reminder: {task}")

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hi! I'm a task manager bot. You can add new tasks, delete certain tasks, and specify a deadline for each task. Use /addtask to add a new task, /deletetask to delete a task, and /tasks to list all your tasks.")

@dp.message_handler(Command("q"))
async def q_handler(message: types.Message):
    content = message.text
    messages.append({"role": "user", "content": content})
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=messages)
    await message.reply(f"{completion.choices[0].message.content}")

@dp.message_handler(Command("addtask"))
async def cmd_addtask(message: types.Message):
    await Form.task.set()
    await message.answer("Please enter the task:")

@dp.message_handler(state=Form.task)
async def process_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['task'] = message.text

    await Form.next()
    await message.answer("Please enter the deadline (YYYY-MM-DD HH:MM):")

@dp.message_handler(state=Form.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['deadline'] = message.text

        try:
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M')
            deadline = deadline.replace(tzinfo=None)
            tasks[data['task']] = deadline
            await message.answer(f"Task '{data['task']}' added with deadline {data['deadline']}.")
        except ValueError:
            await message.answer("Invalid deadline format. Please use the format 'YYYY-MM-DD HH:MM'.")

    await state.finish()

@dp.message_handler(Command("deletetask"))
async def cmd_deletetask(message: types.Message):
    if not tasks:
        await message.answer("No tasks found.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        for task, deadline in tasks.items():
            button = types.InlineKeyboardButton(text=task, callback_data=f"deletetask_{task}")
            keyboard.add(button)

        await message.answer("Which task would you like to delete?", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('deletetask'))
async def process_deletetask(callback_query: types.CallbackQuery):
    task = callback_query.data.split('_')[1]
    if task in tasks:
        del tasks[task]
        await callback_query.answer(f"Task '{task}' deleted.")
    else:
        await callback_query.answer("Task not found")

@dp.message_handler(commands=['tasks'])
async def show_tasks(message: types.Message):
    if tasks:
        task_list = ""
        for task, deadline in tasks.items():
            task_list += f"{task} - Deadline: {deadline.strftime('%Y-%m-%d %H:%M UTC')}\n"
        await message.reply(task_list)
    else:
        await message.reply("You have no tasks.")

if __name__ == '__main__':
    from aiogram import executor

    loop = asyncio.get_event_loop()
    loop.create_task(send_deadline_reminder())
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)