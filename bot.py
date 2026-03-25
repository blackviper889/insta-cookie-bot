import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import pyotp
import instaloader
import os
import time
from threading import Thread
from flask import Flask

# ১. সার্ভারকে ২৪ ঘণ্টা জাগিয়ে রাখার জন্য ওয়েব পোর্ট
app = Flask('')
@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# ২. তোমার বটের টোকেন ও কনফিগারেশন
TOKEN = '8725974283:AAFQGak5YDhbVH2VdGzhg-vCEffuTN3H_k0'
bot = telebot.TeleBot(TOKEN)
L = instaloader.Instaloader()
user_data = {}

# ৩. স্টার্ট কমান্ড
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🍪 কুকি বের করুন'))
    bot.send_message(message.chat.id, "👋 **স্বাগতম!**\n\n**ইন্সটাগ্রাম কুকি বের করতে নিচের বাটনে ক্লিক করুন।**", reply_markup=markup, parse_mode="Markdown")

# ৪. মেইন লজিক (বোল্ড টেক্সট সহ)
@bot.message_handler(func=lambda m: m.text == '🍪 কুকি বের করুন')
def ask_usernames(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('❌ বাতিল করুন'))
    msg = bot.send_message(chat_id, "✍️ **আপনার ইউজারনেম লিস্ট দিন (নিচে নিচে):**", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_password)

def ask_password(message):
    if message.text == '❌ বাতিল করুন': return
    user_data[message.chat.id]['usernames'] = message.text.strip().split('\n')
    msg = bot.send_message(message.chat.id, "🔑 **আপনার কমন পাসওয়ার্ডটি দিন:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_2fa)

def ask_2fa(message):
    user_data[message.chat.id]['password'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔐 **আপনার 2FA সিক্রেট কী গুলো দিন (নিচে নিচে):**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_logins)

def process_logins(message):
    chat_id = message.chat.id
    two_fa_keys = message.text.strip().split('\n')
    usernames = user_data[chat_id]['usernames']
    password = user_data[chat_id]['password']
    
    bot.send_message(chat_id, "⏳ **চেকিং শুরু হয়েছে, দয়া করে অপেক্ষা করুন...**", parse_mode="Markdown")
    
    success_list = []
    report = "📊 **রিপোর্ট আপডেট:**\n\n"
    
    for i in range(len(usernames)):
        try:
            # TOTP জেনারেট করা
            totp = pyotp.TOTP(two_fa_keys[i].replace(" ", ""))
            otp_code = totp.now()
            
            # ইন্সটাগ্রাম লগইন
            L.login(usernames[i], password)
            L.two_factor_login(otp_code)
            
            # কুকি সংগ্রহ
            cookies = L.context._session.cookies.get_dict()
            c_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            success_list.append(f"{usernames[i]}|{password}|{c_str}")
            report += f"✅ **{usernames[i]}** - সফল\n"
        except Exception as e:
            report += f"❌ **{usernames[i]}** - ব্যর্থ\n"
            
    if success_list:
        file_name = f"cookies_{chat_id}.txt"
        with open(file_name, "w") as f:
            f.write("\n".join(success_list))
        with open(file_name, "rb") as f:
            bot.send_document(chat_id, f, caption="✨ **আপনার সব কুকি ফাইল এখানে!**", parse_mode="Markdown")
        os.remove(file_name)
    
    bot.send_message(chat_id, report, parse_mode="Markdown")

# ৫. অটো-রিস্টার্ট লুপ (বট অফ হবে না)
if __name__ == "__main__":
    keep_alive()
    print("Bot is starting on Render...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=25)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
