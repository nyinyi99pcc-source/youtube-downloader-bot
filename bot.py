import os
import asyncio
import yt_dlp
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Bot Token ---
TOKEN = "8782409050:AAFbBpCml4EP4RD0knObKPySZoibMshCVZA"

last_update_time = {}

def progress_hook(d, status_msg, loop, chat_id):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        speed = d.get('_speed_str', '0KB/s')
        eta = d.get('_eta_str', '00:00')
        text = f"⏳ Downloading... {p}\n🚀 Speed: {speed}\n⏰ ကျန်ရှိချိန်: {eta}"
        
        current_time = time.time()
        if chat_id not in last_update_time or current_time - last_update_time[chat_id] > 3:
            last_update_time[chat_id] = current_time
            # message edit တာကို error မတက်အောင် try-except နဲ့ အုပ်ထားတယ်
            try:
                asyncio.run_coroutine_threadsafe(status_msg.edit_text(text), loop)
            except:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 YouTube Downloader Bot ပါ။\n\n📽 Video: Link ကို တိုက်ရိုက်ပို့ပါ။\n🎵 Audio: `/mp3 [link]` ဟု ရိုက်ပို့ပါ။")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    file_name = f"video_{chat_id}.mp4"
    loop = asyncio.get_running_loop()
    
    status_msg = await update.message.reply_text("🔎 ဗီဒီယိုကို စစ်ဆေးနေပါတယ်...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_name,
        'quiet': True,
        'progress_hooks': [lambda d: progress_hook(d, status_msg, loop, chat_id)],
    }

    try:
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        title = info.get('title', 'Video')

        await status_msg.edit_text("📤 တယ်လီဂရမ်သို့ ပို့ဆောင်နေပါပြီ (ခဏစောင့်ပါ)...")
        
        # Timeout ကို ၁၀၀၀ (စက္ကန့်) အထိ တိုးလိုက်ပါတယ်
        with open(file_name, 'rb') as f:
            await update.message.reply_video(video=f, caption=f"✅ {title}", write_timeout=1000, read_timeout=1000, connect_timeout=1000)
                
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(file_name): os.remove(file_name)
        try: await status_msg.delete()
        except: pass

async def download_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ `/mp3 [link]` ဟု ပို့ပါ။")
        return

    url = context.args[0]
    chat_id = update.message.chat_id
    # file_name ကို .mp3 မပါဘဲ ပေးရမယ်
    base_name = f"audio_{chat_id}"
    full_path = f"{base_name}.mp3"
    loop = asyncio.get_running_loop()
    
    status_msg = await update.message.reply_text("🎵 MP3 ပြောင်းလဲနေပါတယ်...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_name,
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True,
        'progress_hooks': [lambda d: progress_hook(d, status_msg, loop, chat_id)],
    }

    try:
        info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
        
        await status_msg.edit_text("📤 MP3 ပို့ဆောင်နေပါပြီ...")
        
        # ပို့တဲ့နေရာမှာ timeout ထည့်ထားတယ်
        with open(full_path, 'rb') as f:
            await update.message.reply_audio(audio=f, caption=f"✅ {info.get('title')}", write_timeout=1000, read_timeout=1000)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(full_path): os.remove(full_path)
        try: await status_msg.delete()
        except: pass

def main():
    # Application builder မှာလည်း timeout တွေ တိုးထားပါတယ်
    app = Application.builder().token(TOKEN).connect_timeout(100).read_timeout(100).write_timeout(100).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mp3", download_mp3))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🚀 Bot is running with Timeout Fix...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

