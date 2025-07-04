# Импорт стандартных библиотек
import os  # Для работы с переменными окружения
import requests  # Для HTTP-запросов к внешнему API

# Импортируем необходимые классы из python-telegram-bot
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# URL бесплатного OCR API (ocr.space)
OCR_API_URL = "https://api.ocr.space/parse/image"
# Можно получить бесплатный API-ключ на https://ocr.space/ocrapi (но для теста можно использовать 'helloworld')
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")

# Функция для отправки изображения на ocr.space и получения результата
async def parse_receipt(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            OCR_API_URL,
            files={"file": f},
            data={"apikey": OCR_API_KEY, "language": "rus"}
        )
    return response.json()

# Обработчик фото
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем объект фото (берём самое большое по размеру)
    photo = update.message.photo[-1]
    # Скачиваем фото во временный файл
    file = await context.bot.get_file(photo.file_id)
    file_path = "temp_photo.jpg"
    await file.download_to_drive(file_path)

    # Отправляем фото на парсинг
    await update.message.reply_text("Фото получено! Парсим чек...")
    try:
        ocr_result = await parse_receipt(file_path)
        # Отправляем пользователю результат в виде JSON (сделаем красиво)
        import json
        pretty_json = json.dumps(ocr_result, ensure_ascii=False, indent=2)
        # Если сообщение слишком длинное, отправим как файл
        if len(pretty_json) > 4000:
            with open("result.json", "w", encoding="utf-8") as f:
                f.write(pretty_json)
            await update.message.reply_document(document=open("result.json", "rb"), filename="result.json")
        else:
            await update.message.reply_text(f"Результат OCR:\n<pre>{pretty_json}</pre>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке: {e}")
    finally:
        # Удаляем временные файлы
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists("result.json"):
            os.remove("result.json")

# Точка входа в программу
if __name__ == "__main__":
    # Получаем токен бота из переменной окружения TELEGRAM_TOKEN
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Пожалуйста, укажите токен в переменной окружения TELEGRAM_TOKEN.")
        exit(1)
    app = ApplicationBuilder().token(token).build()
    # Добавляем обработчик только для фото
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    print("Бот для распознавания чеков запущен!")
    app.run_polling() 