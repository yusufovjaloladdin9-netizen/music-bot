import asyncio
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yt_dlp import YoutubeDL

# --- SOZLAMALAR ---
API_TOKEN = '8624918413:AAF4uly6O6Wwv-qKh0CnxnvY2n3HOJEog3o' # Tokeningiz
DB_NAME = 'juratbot2008.db'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                          (user_id INTEGER PRIMARY KEY, username TEXT)''')
        await db.commit()

async def add_user(user_id, username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                         (user_id, username))
        await db.commit()

# --- BUYRUQLAR ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await add_user(message.from_user.id, message.from_user.username)
    await message.answer(f"Salom {message.from_user.full_name}! 👋\n\n"
                         "🎵 Qo'shiq nomini yozsangiz - MP3 qilib beraman.\n"
                         "🔗 YouTube yoki Instagram linkini yuborsangiz - Videoni yuklab beraman!")

@dp.message(Command("statistika"))
async def stats(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT COUNT(*) FROM users') as cursor:
            count = await cursor.fetchone()
            await message.answer(f"📊 Foydalanuvchilar: {count[0]} ta")

# --- ASOSIY YUKLASH FUNKSIYASI ---
@dp.message()
async def handle_message(message: types.Message):
    query = message.text
    is_link = query.startswith(('http://', 'https://'))
    status_msg = await message.answer("Ishlov berilmoqda... ⏳")

    # Video yoki Audio tanlash
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
    }

    if not is_link:
        # Agar shunchaki nom yozilsa -> MP3 yuklash
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        })
        search_query = f"ytsearch1:{query}"
    else:
        # Agar link yuborilsa -> Video yuklash (MP4)
        ydl_opts.update({'format': 'best'})
        search_query = query

    try:
        if not os.path.exists('downloads'): os.makedirs('downloads')
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            video_info = info['entries'][0] if 'entries' in info else info
            file_path = ydl.prepare_filename(video_info)
            
            # Agar MP3 bo'lsa, nomini to'g'irlaymiz
            if not is_link:
                file_path = file_path.rsplit('.', 1)[0] + ".mp3"

        # Telegramga yuborish
        file_to_send = types.FSInputFile(file_path)
        if is_link:
            await bot.send_video(message.chat.id, file_to_send, caption=f"✅ Video yuklandi!")
        else:
            await bot.send_audio(message.chat.id, file_to_send, caption=f"✅ Musiqa topildi!")
        
        os.remove(file_path)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"Xatolik: Link noto'g'ri yoki video juda katta.")

async def main():
    await init_db()
    print("Bot universal rejimda yoqildi! ")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
