import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import pyotp
import instaloader
import os
import time
from threading import Thread
from flask import Flask

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

TOKEN = '8725974283:AAFQGak5YDhbVH2VdGzhg-vCEffuTN3H_k0'
bot = telebot.TeleBot(TOKEN)
user_data = {}

def start_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🍪 কুকি বের করুন'))
    return markup

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "👋 **স্বাগতম!**\n\nকুকি বের করতে বাটনে ক্লিক করুন।", reply_markup=start_markup(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🍪 কুকি বের করুন')
def ask_usernames(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('❌ বাতিল করুন'))
    msg = bot.send_message(chat_id, "✍️ **আপনার ইউজারনেম লিস্ট দিন (নিচে নিচে):**", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_password)

def ask_password(message):
    chat_id = message.chat.id
    if message.text == '❌ বাতিল করুন':
        bot.send_message(chat_id, "🚫 বাতিল করা হয়েছে।", reply_markup=start_markup(), parse_mode="Markdown")
        return
    user_data[chat_id]['usernames'] = message.text.strip().split('\n')
    msg = bot.send_message(chat_id, "🔑 **আপনার কমন পাসওয়ার্ডটি দিন:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_2fa)

def ask_2fa(message):
    chat_id = message.chat.id
    if message.text == '❌ বাতিল করুন':
        bot.send_message(chat_id, "🚫 বাতিল করা হয়েছে।", reply_markup=start_markup(), parse_mode="Markdown")
        return
    user_data[chat_id]['password'] = message.text.strip()
    msg = bot.send_message(chat_id, "🔐 **আপনার 2FA সিক্রেট কী গুলো দিন (নিচে নিচে):**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_logins)

def process_logins(message):
    chat_id = message.chat.id
    if message.text == '❌ বাতিল করুন':
        bot.send_message(chat_id, "🚫 বাতিল করা হয়েছে।", reply_markup=start_markup(), parse_mode="Markdown")
        return

    two_fa_keys = message.text.strip().split('\n')
    usernames = user_data[chat_id].get('usernames', [])
    password = user_data[chat_id].get('password', '')
    
    bot.send_message(chat_id, "⏳ **চেকিং শুরু হয়েছে...**", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    
    success_list = []
    report = "📊 **রিপোর্ট আপডেট:**\n\n"
    
    for i in range(len(usernames)):
        try:
            L = instaloader.Instaloader(quiet=True)
            u = usernames[i].strip().replace("@", "")
            
            # TOTP generation
            secret = two_fa_keys[i].replace(" ", "").upper()
            totp = pyotp.TOTP(secret)
            otp_code = totp.now()
            
            # Login process
            L.login(u, password)
            L.two_factor_login(otp_code)
            
            cookies = L.context._session.cookies.get_dict()
            c_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            success_list.append(f"{u}|{password}|{c_str}")
            report += f"✅ **{u}** - সফল\n"
        except Exception as e:
            report += f"❌ **{u}** - ব্যর্থ (Login Blocked/Wrong Credentials)\n"
            
    if success_list:
        file_name = f"cookies_{chat_id}.txt"
        with open(file_name, "w") as f: f.write("\n".join(success_list))
        with open(file_name, "rb") as f: bot.send_document(chat_id, f, caption="✨ **সফল কুকি ফাইল!**", parse_mode="Markdown")
        os.remove(file_name)
    
    bot.send_message(chat_id, report, reply_markup=start_markup(), parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception:
            time.sleep(5)
