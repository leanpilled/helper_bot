import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from PIL import Image
import cv2

TOKEN = ""

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

task = []

def resize_image(image_path, width, height):
    image = cv2.imread(image_path)
    if width and height:
        image_resized = cv2.resize(image, (width, height))
    elif width is not None:
        aspect_ratio = width / image.shape[1]
        new_height = int(image.shape[0] * aspect_ratio)
        image_resized = cv2.resize(image, (width, new_height))
    else:
        aspect_ratio = height / image.shape[0]
        new_width = int(image.shape[1] * aspect_ratio)
        image_resized = cv2.resize(image, (new_width, height))
    
    cv2.imwrite("resized_image.jpg", image_resized)

def rotate_image(image_path, angle):
    image = cv2.imread(image_path)
    height, width = image.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
    
    cv2.imwrite("rotated_image.jpg", rotated_image)
    
    
def adjust_brightness(image_path, brightness):
    image = cv2.imread(image_path)
    adjusted_image = cv2.convertScaleAbs(image, beta=brightness)
    cv2.imwrite("adjusted_image.jpg", adjusted_image)

@dp.message_handler(content_types=['photo'])
async def process_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    file_path = await bot.get_file(file_id)

    downloaded_file = await bot.download_file(file_path.file_path)
    with open("user_image.jpg", "wb") as f:
        f.write(downloaded_file.read())

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton("Resize", callback_data="resize"),
        types.InlineKeyboardButton("Rotate", callback_data="rotate"),
        types.InlineKeyboardButton("Adjust Brightness", callback_data="brightness"),
    ]
    keyboard.add(*buttons)

    await bot.send_message(chat_id=message.chat.id, text="Choose an action:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in ["resize", "rotate", "brightness"])
async def process_callback(callback_query: types.CallbackQuery):
    action = callback_query.data
    await bot.answer_callback_query(callback_query.id)

    if action == "resize":
        await bot.send_message(chat_id=callback_query.from_user.id, text="Please send the new width and height as 'width,height'")
        task.append(1)
    elif action == "rotate":
        await bot.send_message(chat_id=callback_query.from_user.id, text="Please send the angle to rotate the image in degrees")
        task.append(2)
    else:
        await bot.send_message(chat_id=callback_query.from_user.id, text="Please send the brightness adjustment value")
        task.append(3)

@dp.message_handler(lambda message: message.text)
async def process_action_input(message: types.Message):
    if task[0] == 1:
        if re.search(r'\d+,\d+', message.text):
            numbers = re.findall(r'\d+', message.text)
            if len(numbers) == 2:
                num1 = int(numbers[0])
                num2 = int(numbers[1])
                resize_image("user_image.jpg", num1, num2)
                with open("resized_image.jpg", 'rb') as photo:
                    await bot.send_photo(chat_id=message.chat.id, photo=photo)

    elif task[0] == 2:
        num = int(message.text)
        rotate_image("user_image.jpg", num)
        with open("rotated_image.jpg", 'rb') as photo:
            await bot.send_photo(chat_id=message.chat.id, photo=photo)

    
    elif task[0] == 3:
        num = int(message.text)
        adjust_brightness("user_image.jpg", num)
        with open("adjusted_image.jpg", 'rb') as photo:
            await bot.send_photo(chat_id=message.chat.id, photo=photo)

    task.clear()

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)