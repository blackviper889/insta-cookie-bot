import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import pyotp
from instagrapi import Client
import os
import time
from threading import Thread
from flask import Flask

# ১. সার্ভারকে জাগিয়ে রাখা
app = Flask('')
@app.route('/')
def home(): return "Bot is Running 24/7"
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
    bot.send_message(message.chat.id, "🚀 **InstaCookie Pro v2.0**\n২৪ ঘণ্টা সচল এবং দ্রুত সার্ভার।", reply_markup=start_markup(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🍪 কুকি বের করুন')
def ask_usernames(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('❌ বাতিল করুন'))
    msg = bot.send_message(chat_id, "✍️ **ইউজারনেম লিস্ট দিন:**", reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, ask_password)

def ask_password(message):
    chat_id = message.chat.id
    if message.text == '❌ বাতিল করুন':
        bot.send_message(chat_id, "🚫 বাতিল।", reply_markup=start_markup())
        return
    user_data[chat_id]['usernames'] = message.text.strip().split('\n')
    msg = bot.send_message(chat_id, "🔑 **পাসওয়ার্ড দিন:**")
    bot.register_next_step_handler(msg, ask_2fa)

def ask_2fa(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text.strip()
    msg = bot.send_message(chat_id, "🔐 **2FA সিক্রেট কী দিন:**")
    bot.register_next_step_handler(msg, process_logins)

def process_logins(message):
    chat_id = message.chat.id
    two_fa_keys = message.text.strip().split('\n')
    usernames = user_data[chat_id]['usernames']
    password = user_data[chat_id]['password']
    
    bot.send_message(chat_id, "⏳ **সার্ভারে প্রসেসিং হচ্ছে...**", reply_markup=ReplyKeyboardRemove())
    
    success_list = []
    
    for i in range(len(usernames)):
        try:
            cl = Client()
            cl.delay_range = [1, 3] # রোবট ধরা থেকে বাঁচতে ডিলে
            
            u = usernames[i].strip().replace("@", "")
            secret = two_fa_keys[i].replace(" ", "").upper()
            totp = pyotp.TOTP(secret)
            otp_code = totp.now()
            
            # লগইন ট্রাই
            cl.login(u, password, verification_code=otp_code)
            
            # কুকি ফরম্যাট
            cookies = cl.get_cookies()
            c_str = f"sessionid={cookies['sessionid']}; ds_user_id={cookies['ds_user_id']}; csrftoken={cookies['csrftoken']}"
            
            success_list.append(f"{u}|{password}|{c_str}")
        except Exception as e:
            continue
            
    if success_list:
        with open(f"cookies_{chat_id}.txt", "w") as f:
            f.write("\n".join(success_list))
        with open(f"cookies_{chat_id}.txt", "rb") as f:
            bot.send_document(chat_id, f, caption="✅ **কুকি রেডি!**")
        os.remove(f"cookies_{chat_id}.txt")
    else:
        bot.send_message(chat_id, "❌ সব আইডিতে লগইন ব্লক হয়েছে। আইডিতে ঢুকে 'This Was Me' করুন।", reply_markup=start_markup())

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
