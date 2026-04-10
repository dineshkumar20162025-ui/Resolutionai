import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import whisper
from deep_translator import GoogleTranslator
import edge_tts

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_videos = {}
model = whisper.load_model("base")

# Step 1: Receive video
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.video.get_file()
    video_path = f"{update.message.chat_id}.mp4"
    await file.download_to_drive(video_path)

    user_videos[update.message.chat_id] = video_path

    keyboard = [
        [InlineKeyboardButton("🇮🇳 Tamil", callback_data="ta")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="en")],
    ]

    await update.message.reply_text(
        "Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# Step 2: Process
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data
    chat_id = query.message.chat_id

    if chat_id not in user_videos:
        await query.message.reply_text("❌ Send video again")
        return

    video_path = user_videos[chat_id]
    audio_path = "audio.wav"

    await query.message.reply_text("⏳ AI Processing...")

    # Extract audio
    os.system(f"ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path}")

    # Whisper transcription
    result = model.transcribe(audio_path)
    text = result["text"]

    # Translate
    translated = GoogleTranslator(source='auto', target=lang).translate(text)

    # Edge TTS (natural voice)
    voice_file = "voice.mp3"
    communicate = edge_tts.Communicate(translated, "ta-IN-PallaviNeural")
    await communicate.save(voice_file)

    # Merge audio + video
    output = "output.mp4"
    os.system(
        f"ffmpeg -i {video_path} -i {voice_file} -c:v copy -map 0:v:0 -map 1:a:0 -shortest {output}"
    )

    await query.message.reply_video(video=open(output, "rb"))

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(button))

    print("Pro AI Dub Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
