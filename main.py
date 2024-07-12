import os
import logging
import psycopg2
import pytesseract
import cv2
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

parms_for_postgresql = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT")
}

os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/5/tessdata'

bot = Bot(token=os.getenv("TELEGRAM_BOT_KEY"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Убедитесь, что путь правильный

def process_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    text = pytesseract.image_to_string(binary, lang='rus+eng')
    return text

def parse_text(text):
    import re
    iin_pattern = r'\b\d{12}\b'
    fio_pattern = r'ТЕГІ / ФАМИЛИЯ\s*([А-Я]+)\s*АТЫ / ИМЯ\s*([А-Я]+)\s*ӘКЕСІНІҢ АТЫ / ОТЧЕСТВО\s*([А-Я]+)\b'
    date_pattern = r'\d{2}\.\d{2}\.\d{4}'
    issued_by_pattern = r'БЕРГЕН ОРГАН / ОРГАН ВЫДАЧИ\s*([\s\S]+?)\n'

    iin_match = re.search(iin_pattern, text)
    fio_match = re.search(fio_pattern, text)
    date_matches = re.findall(date_pattern, text)
    issued_by_match = re.search(issued_by_pattern, text)

    iin = iin_match.group(0) if iin_match else 'Не найдено'
    fio = ' '.join(fio_match.groups()) if fio_match else 'Не найдено'
    date_of_birth = date_matches[0] if len(date_matches) > 0 else 'Не найдено'
    date_of_issue = date_matches[1] if len(date_matches) > 1 else 'Не найдено'
    issued_by = issued_by_match.group(1).strip() if issued_by_match else 'Не найдено'

    return iin, fio, date_of_birth, date_of_issue, issued_by

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне фото удостоверения личности, и я извлеку из него информацию.")

@router.message(F.photo)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)

    with open("temp_photo.jpg", "wb") as f:
        f.write(downloaded_file.getvalue())

    text = process_image("temp_photo.jpg")
    iin, fio, date_of_birth, date_of_issue, issued_by = parse_text(text)

    date_of_birth = None if date_of_birth == 'Не найдено' else date_of_birth
    date_of_issue = None if date_of_issue == 'Не найдено' else date_of_issue

    try:
        connection = psycopg2.connect(**parms_for_postgresql)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, telegram_id, iin, fio, date_of_birth, date_of_issue, issued_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (message.from_user.full_name, message.from_user.id, iin, fio, date_of_birth, date_of_issue, issued_by))
        connection.commit()
        cursor.close()
        connection.close()
        await message.reply('Информация успешно извлечена и сохранена в базу данных!')
    except Exception as error:
        logger.error(f"Ошибка при подключении к PostgreSQL: {error}")
        await message.reply('Произошла ошибка при сохранении данных.')

async def main():
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
