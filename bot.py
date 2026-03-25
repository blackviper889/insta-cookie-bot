import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import pyotp
from instagrapi import Client
import os
import time
from threading import Thread
from flask import Flask
import uuid

app = Flask('')
@app.route('/')
def home(): return "Server Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

TOKEN = '8725974283:AAFQGak5YDhbVH2VdGzhg-vCEffuTN3H_k0'
bot = telebot.TeleBot(TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🍪 কুকি বের করুন'))
    bot.send_message(message.chat.id, "🚀 **InstaCookie Pro v3.0**\nইউজারনেম ও পাসওয়ার্ড দিয়ে আনলিমিটেড কুকি বের করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🍪 কুকি বের করুন')
def ask_u(message):
    msg = bot.send_message(message.chat.id, "✍️ **ইউজারনেম দিন (একের অধিক হলে নিচে নিচে):**", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, ask_p)

def ask_p(message):
    user_data[message.chat.id] = {'u': message.text.strip().split('\n')}
    msg = bot.send_message(message.chat.id, "🔑 **কমন পাসওয়ার্ডটি দিন:**")
    bot.register_next_step_handler(msg, ask_2)

def ask_2(message):
    user_data[message.chat.id]['p'] = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔐 **2FA সিক্রেট কী গুলো দিন (নিচে নিচে):**")
    bot.register_next_step_handler(msg, process)

def process(message):
    chat_id = message.chat.id
    two_fa = message.text.strip().split('\n')
    usernames = user_data[chat_id]['u']
    password = user_data[chat_id]['p']
    
    bot.send_message(chat_id, f"⏳ {len(usernames)}টি আইডির কাজ শুরু হয়েছে... একটু সময় দিন।")
    
    results = []
    for i in range(len(usernames)):
        try:
            cl = Client()
            # রিয়েল ডিভাইস সিমুলেশন
            cl.set_device({
                "app_version": "269.0.0.18.75",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "Samsung",
                "device": "SM-G950F",
                "model": "dreamqlte",
            })
            
            u = usernames[i].strip().replace("@", "")
            secret = two_fa[i].replace(" ", "").upper()
            otp = pyotp.TOTP(secret).now()
            
            # লগইন
            cl.login(u, password, verification_code=otp)
            
            # কুকি সংগ্রহ
            ck = cl.get_cookies()
            c_str = f"ds_user_id={ck['ds_user_id']}; sessionid={ck['sessionid']}; csrftoken={ck['csrftoken']}"
            results.append(f"{u}|{password}|{c_str}")
            time.sleep(2) # সেফটি ডিলে
        except Exception:
            continue

    if results:
        with open(f"{chat_id}.txt", "w") as f: f.write("\n".join(results))
        bot.send_document(chat_id, open(f"{chat_id}.txt", "rb"), caption="✅ সফল কুকি ফাইল!")
        os.remove(f"{chat_id}.txt")
    else:
        bot.send_message(chat_id, "❌ সব আইডিতে লগইন ব্লক হয়েছে। আইডিতে ঢুকে 'This Was Me' কনফার্ম করুন।")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
