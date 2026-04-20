import os
import asyncio
import threading
import requests
import time
import json
import re
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime, timedelta
from telegram.error import BadRequest
from fastapi import FastAPI
import uvicorn
import random
from typing import Dict, List, Optional, Tuple
import jwt

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.ERROR,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", ""))
BASE_URL = os.environ.get("BASE_URL", "")

RENDER_PORT = int(os.environ.get("PORT", 10000))

PAYMENT_GROUP_ID = os.environ.get("PAYMENT_GROUP_ID", "-1003768366485")
PAYMENT_GROUP_LINK = os.environ.get("PAYMENT_GROUP_LINK", "https://t.me/livepaymentupdate")

FAKE_PAYMENT_GROUP_ID = os.environ.get("FAKE_PAYMENT_GROUP_ID", PAYMENT_GROUP_ID)
FAKE_PAYMENT_ENABLED = os.environ.get("FAKE_PAYMENT_ENABLED", "True").lower() == "true"

REQUIRED_CHANNEL = "@CashxByte"
REQUIRED_PAYMENT_GROUP = os.environ.get("REQUIRED_PAYMENT_GROUP", "@livepaymentupdate")
CHANNEL_INVITE_LINK = "https://t.me/CashxByte"
PAYMENT_GROUP_INVITE_LINK = os.environ.get("PAYMENT_GROUP_INVITE_LINK", "https://t.me/livepaymentupdate")

FAKE_USERNAMES = [
    "Rakib_Hasan", "Sakib_Khan", "Rafiq_Islam", "Sohel_Rana", "Nayeem_Chy",
    "Fahim_Ahmed", "Ridoy_Hossain", "Tanvir_Haque", "Saif_Uddin", "Shanto_Chy",
    "Mahmud_Hasan", "Habib_Rahman", "Shahin_Ahmed", "Rashed_Khan", "Mamun_Mia",
    "Asif_Iqbal", "Rony_Chy", "Shakil_Hossain", "Imran_Hasan", "Nurul_Islam"
]

FAKE_FIRST_NAMES = [
    "Rakib", "Sakib", "Rafiq", "Sohel", "Nayeem", "Fahim", "Ridoy", 
    "Tanvir", "Saif", "Shanto", "Mahmud", "Habib", "Shahin", "Rashed",
    "Mamun", "Asif", "Rony", "Shakil", "Imran", "Nurul"
]

FAKE_LAST_NAMES = [
    "Hasan", "Khan", "Islam", "Rana", "Chy", "Ahmed", "Hossain", "Haque",
    "Uddin", "Rahman", "Mia", "Iqbal", "Chowdhury", "Begum", "Ali", "Miah"
]

FAKE_COUNTRIES = [
    "Bangladesh", "India", "Pakistan", "USA", "Canada", "UK", "UAE", 
    "Saudi Arabia", "Malaysia", "Singapore", "Thailand", "Indonesia"
]

if 'RENDER' in os.environ:
    ACCOUNTS_FILE = "/tmp/accounts.json"
    STATS_FILE = "/tmp/stats.json"
    OTP_STATS_FILE = "/tmp/otp_stats.json"
    SETTINGS_FILE = "/tmp/settings.json"
else:
    ACCOUNTS_FILE = "accounts.json"
    STATS_FILE = "stats.json"
    OTP_STATS_FILE = "otp_stats.json"
    SETTINGS_FILE = "settings.json"

USD_TO_BDT = 125
MAX_PER_ACCOUNT = 10

status_map = {
    0: "⚠️ Process Failed",
    1: "🟢 Success", 
    2: "🔵 In Progress",
    3: "⚠️ Try Again Later",
    4: "🚫 Not Register",
    7: "🚫 Ban Number",
    5: "⏳️ Recent Request",
    6: "🔴 Wrong OTP",
    8: "🟠 Limited",
    9: "🔶 Restricted", 
    10: "🟣 VIP Number",
    11: "⚠️ Add Again",
    12: "🟤 Temp Blocked",
    13: "⚠️ Bad Number",
    14: "🌀 Processing",
    15: "📞 Call Required",
    -1: "❌ Token Expired",
    -2: "❌ API Error",
    -3: "❌ No Data Found",
    16: "🚫 Already Exists"
}

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "🤖 Python Number Checker Bot is Running!", "status": "active", "timestamp": datetime.now().isoformat()}

@app.get("/ping")
async def ping():
    return {"message": "Bot is alive!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "bot": "online"}

async def keep_alive_enhanced():
    keep_alive_urls = [
        "https://wsotpall-yitn.onrender.com",
        "https://wschecker-rwjf.onrender.com"
    ]
    
    while True:
        try:
            for url in keep_alive_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=10) as response:
                            await asyncio.sleep(2)
                except:
                    pass
            await asyncio.sleep(3 * 60)
        except:
            await asyncio.sleep(3 * 60)

async def random_ping():
    while True:
        try:
            random_time = random.randint(2 * 60, 5 * 60)
            await asyncio.sleep(random_time)
            async with aiohttp.ClientSession() as session:
                async with session.get("https://webck-9utn.onrender.com", timeout=10) as response:
                    pass
        except:
            pass

async def immediate_ping():
    await asyncio.sleep(30)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://webck-9utn.onrender.com", timeout=10) as response:
                pass
    except:
        pass

def load_tracking():
    try:
        with open("tracking.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "today_added" not in data or not isinstance(data["today_added"], dict):
                data["today_added"] = {}
            if "yesterday_added" not in data or not isinstance(data["yesterday_added"], dict):
                data["yesterday_added"] = {}
            if "today_success" not in data or not isinstance(data["today_success"], dict):
                data["today_success"] = {}
            if "yesterday_success" not in data or not isinstance(data["yesterday_success"], dict):
                data["yesterday_success"] = {}
            if "today_success_counts" not in data or not isinstance(data["today_success_counts"], dict):
                data["today_success_counts"] = {}
            if "daily_stats" not in data or not isinstance(data["daily_stats"], dict):
                data["daily_stats"] = {}
            if "in_progress_timestamp" not in data or not isinstance(data["in_progress_timestamp"], dict):
                data["in_progress_timestamp"] = {}
            if "pending_delete" not in data or not isinstance(data["pending_delete"], dict):
                data["pending_delete"] = {}
            return data
    except:
        return {
            "added_numbers": {},
            "success_numbers": {},
            "today_added": {},
            "yesterday_added": {},
            "today_success": {},
            "yesterday_success": {},
            "today_success_counts": {},
            "daily_stats": {},
            "in_progress_timestamp": {},
            "pending_delete": {},
            "last_reset": datetime.now().isoformat()
        }

def save_tracking(tracking):
    try:
        with open("tracking.json", 'w', encoding='utf-8') as f:
            json.dump(tracking, f, indent=4, ensure_ascii=False)
    except:
        pass

async def reset_daily_stats(context: CallbackContext):
    stats = load_stats()
    otp_stats = load_otp_stats()
    tracking = load_tracking()
    
    today_date = datetime.now().date().isoformat()
    
    tracking["yesterday_added"] = tracking.get("today_added", {}).copy()
    
    if "daily_stats" not in tracking:
        tracking["daily_stats"] = {}
    
    today_success_by_user = tracking.get("today_success_counts", {}).copy()
    tracking["daily_stats"][today_date] = today_success_by_user
    
    tracking["today_added"] = {}
    tracking["yesterday_success"] = tracking.get("today_success_counts", {}).copy()
    tracking["today_success"] = {}
    tracking["today_success_counts"] = {}
    tracking["last_reset"] = datetime.now().isoformat()
    
    stats["yesterday_checked"] = stats["today_checked"]
    stats["today_checked"] = 0
    stats["yesterday_deleted"] = stats["today_deleted"]
    stats["today_deleted"] = 0
    
    otp_stats["yesterday_success"] = otp_stats["today_success"]
    otp_stats["today_success"] = 0
    
    for user_id_str in otp_stats.get("user_stats", {}):
        otp_stats["user_stats"][user_id_str]["yesterday_success"] = otp_stats["user_stats"][user_id_str].get("today_success", 0)
        otp_stats["user_stats"][user_id_str]["today_success"] = 0
    
    save_stats(stats)
    save_otp_stats(otp_stats)
    save_tracking(tracking)
    
    try:
        await context.bot.send_message(ADMIN_ID, "🔄 Daily Statistics Reset Completed", parse_mode='none')
    except:
        pass

def load_accounts():
    try:
        possible_paths = [ACCOUNTS_FILE, "accounts.json", "/tmp/accounts.json", "./accounts.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data
            except:
                continue
        
        initial_data = {
            str(ADMIN_ID): {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        }
        save_accounts(initial_data)
        return initial_data
    except:
        initial_data = {
            str(ADMIN_ID): {
                "accounts": [],
                "selected_account_id": 1,
                "telegram_username": "",
                "last_active": datetime.now().isoformat()
            }
        }
        return initial_data

def save_accounts(accounts):
    try:
        possible_paths = [ACCOUNTS_FILE, "accounts.json", "/tmp/accounts.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(accounts, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except:
        pass

def load_stats():
    try:
        possible_paths = [STATS_FILE, "stats.json", "/tmp/stats.json", "./stats.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            required_keys = ["total_checked", "total_deleted", "today_checked", "today_deleted", "yesterday_checked", "yesterday_deleted", "last_reset"]
                            for key in required_keys:
                                if key not in data:
                                    if key in ["total_checked", "today_checked", "yesterday_checked"]:
                                        data[key] = 0
                                    elif key in ["total_deleted", "today_deleted", "yesterday_deleted"]:
                                        data[key] = 0
                                    elif key == "last_reset":
                                        data[key] = datetime.now().isoformat()
                            return data
            except:
                continue
        return create_default_stats()
    except:
        return create_default_stats()

def create_default_stats():
    return {
        "total_checked": 0, 
        "total_deleted": 0, 
        "today_checked": 0, 
        "today_deleted": 0,
        "yesterday_checked": 0,
        "yesterday_deleted": 0,
        "last_reset": datetime.now().isoformat()
    }

def save_stats(stats):
    try:
        required_keys = ["total_checked", "total_deleted", "today_checked", "today_deleted", "yesterday_checked", "yesterday_deleted", "last_reset"]
        for key in required_keys:
            if key not in stats:
                if key in ["total_checked", "today_checked", "yesterday_checked"]:
                    stats[key] = 0
                elif key in ["total_deleted", "today_deleted", "yesterday_deleted"]:
                    stats[key] = 0
                elif key == "last_reset":
                    stats[key] = datetime.now().isoformat()
        
        possible_paths = [STATS_FILE, "stats.json", "/tmp/stats.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except:
        pass

def load_otp_stats():
    try:
        possible_paths = [OTP_STATS_FILE, "otp_stats.json", "/tmp/otp_stats.json", "./otp_stats.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data
            except:
                continue
        return {
            "total_success": 0,
            "today_success": 0,
            "yesterday_success": 0,
            "user_stats": {},
            "last_reset": datetime.now().isoformat()
        }
    except:
        return {
            "total_success": 0,
            "today_success": 0,
            "yesterday_success": 0,
            "user_stats": {},
            "last_reset": datetime.now().isoformat()
        }

def save_otp_stats(otp_stats):
    try:
        possible_paths = [OTP_STATS_FILE, "otp_stats.json", "/tmp/otp_stats.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(otp_stats, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except:
        pass

def load_settings():
    try:
        possible_paths = [SETTINGS_FILE, "settings.json", "/tmp/settings.json", "./settings.json"]
        for file_path in possible_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data
            except:
                continue
        default_settings = {"settlement_rate": 0.10, "last_updated": datetime.now().isoformat(), "updated_by": ADMIN_ID}
        save_settings(default_settings)
        return default_settings
    except:
        default_settings = {"settlement_rate": 0.10, "last_updated": datetime.now().isoformat(), "updated_by": ADMIN_ID}
        return default_settings

def save_settings(settings):
    try:
        possible_paths = [SETTINGS_FILE, "settings.json", "/tmp/settings.json"]
        for file_path in possible_paths:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                break
            except:
                continue
    except:
        pass

active_otp_requests = {}

async def login_api_async(username, password):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"account": username, "password": password, "identity": "Member"}
            async with session.post(f"{BASE_URL}/user/login", json=payload, timeout=30) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                        if data and isinstance(data, dict):
                            if "data" in data and "token" in data["data"]:
                                token = data["data"]["token"]
                                try:
                                    decoded = jwt.decode(token, options={"verify_signature": False})
                                    api_user_id = decoded.get('id')
                                    nickname = decoded.get('nickname')
                                    return token, api_user_id, nickname
                                except:
                                    return token, None, None
                            else:
                                return None, None, None
                        else:
                            return None, None, None
                    except:
                        return None, None, None
                else:
                    return None, None, None
    except:
        return None, None, None

async def show_user_statistics(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    
    user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
    user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
    
    user_otp_stats = otp_stats.get("user_stats", {}).get(user_id_str, {})
    today_otp_success = user_otp_stats.get("today_success", 0)
    yesterday_otp_success = user_otp_stats.get("yesterday_success", 0)
    
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    user_accounts = user_data.get("accounts", []) if isinstance(user_data, dict) else []
    active_accounts = account_manager.get_user_active_accounts_count(user_id)
    remaining_checks = account_manager.get_user_remaining_checks(user_id)
    
    message = "📊 Your Daily Statistics 📊\n\n"
    message += f"📅 Date: {datetime.now().strftime('%d %B %Y')}\n"
    message += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n"
    message += f"🔄 Next Reset: Today 4:00 PM (BD Time)\n\n"
    message += "👤 Account Information:\n"
    message += f"• 📱 Total Accounts: {len(user_accounts)}\n"
    message += f"• ✅ Active Login: {active_accounts}\n"
    message += f"• 🎯 Remaining Add: {remaining_checks}\n\n"
    message += "📈 Today's Performance:\n"
    message += f"• 📱Added Numbers: {user_in_progress}\n"
    message += f"• 🟢 Success Counts: {user_success}\n"
    message += f"• ✅ OTP Success: {today_otp_success}\n\n"
    message += "🔄 Auto Reset: Daily at 4:00 PM (Bangladesh Time)"
    
    await update.message.reply_text(message, parse_mode='none')

async def statistics_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status not in allowed_status:
                await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
                return
        except:
            await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
            return
    
    if user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("🏆 Top Performers", callback_data="stats_top_performers")],
            [InlineKeyboardButton("📊 All Statistics", callback_data="stats_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📊 Admin Menu\n\nChoose:", reply_markup=reply_markup)
    else:
        await show_user_statistics(update, context)
        keyboard = [[InlineKeyboardButton("💳 My Wallet", callback_data="open_wallet")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("💳 Manage your payment methods:", reply_markup=reply_markup)

async def wallet_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status not in allowed_status:
                await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
                return
        except:
            await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
            return
    
    accounts = load_accounts()
    
    if user_id_str not in accounts:
        accounts[user_id_str] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": update.effective_user.username or "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
        save_accounts(accounts)
    
    user_data = accounts[user_id_str]
    payment_methods = user_data.get("payment_methods", {})
    
    message = f"💳 YOUR WALLET\n\n"
    message += f"👤 {update.effective_user.first_name}\n"
    message += f"🆔 ID: `{user_id}`\n\n"
    
    if payment_methods:
        message += f"📋 Saved Payment Methods ({len(payment_methods)}):\n"
        for method, data in payment_methods.items():
            payment_id = data.get('id', 'N/A')
            if len(payment_id) > 8:
                masked_id = payment_id[:4] + "****" + payment_id[-4:]
            else:
                masked_id = payment_id
            message += f"├─ {method.upper()}: `{payment_id}`\n"
            if data.get('details'):
                message += f"│  └─ {data['details'][:30]}\n"
        message += f"\n"
    else:
        message += f"❌ No payment methods added yet!\n\n"
    
    message += f"➕ Add Payment Method:\n"
    message += f"• BKash - Click below\n"
    message += f"• Nagad - Click below\n"
    message += f"• Binance - Click below\n\n"
    message += f"💡 Your payment info is secure and only visible to admin."
    
    keyboard = [
        [InlineKeyboardButton("➕ BKash", callback_data="add_bkash"), InlineKeyboardButton("➕ Nagad", callback_data="add_nagad")],
        [InlineKeyboardButton("➕ Binance", callback_data="add_binance")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_wallet"), InlineKeyboardButton("❌ Close", callback_data="close_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_wallet_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "close_wallet":
        await query.delete_message()
        return
    
    if data == "refresh_wallet":
        await handle_refresh_wallet(update, context)
        return
    
    if data == "add_bkash":
        context.user_data['pending_payment_method'] = 'bkash'
        await query.edit_message_text(
            f"💳 ADD BKASH NUMBER\n\nPlease send your BKash number.\n\nExample: `017XXXXXXXX`\n\n⚠️ Type /cancel to cancel.",
            parse_mode='Markdown'
        )
    elif data == "add_nagad":
        context.user_data['pending_payment_method'] = 'nagad'
        await query.edit_message_text(
            f"💳 ADD NAGAD NUMBER\n\nPlease send your Nagad number.\n\nExample: `018XXXXXXXX`\n\n⚠️ Type /cancel to cancel.",
            parse_mode='Markdown'
        )
    elif data == "add_binance":
        context.user_data['pending_payment_method'] = 'binance'
        await query.edit_message_text(
            f"💳 ADD BINANCE PAY ID\n\nPlease send your Binance Pay ID.\n\nExample: `8277372966555`\n\n⚠️ Type /cancel to cancel.",
            parse_mode='Markdown'
        )

async def handle_refresh_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer("🔄 Refreshing wallet...")
    
    user_id = query.from_user.id
    user_id_str = str(user_id)
    
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    payment_methods = user_data.get("payment_methods", {})
    
    message = f"💳 YOUR WALLET (Refreshed)\n\n"
    message += f"👤 {query.from_user.first_name}\n"
    message += f"🆔 ID: `{user_id}`\n\n"
    
    if payment_methods:
        message += f"📋 Saved Payment Methods ({len(payment_methods)}):\n"
        for method, data in payment_methods.items():
            payment_id = data.get('id', 'N/A')
            if len(payment_id) > 8:
                masked_id = payment_id[:4] + "****" + payment_id[-4:]
            else:
                masked_id = payment_id
            message += f"├─ {method.upper()}: `{payment_id}`\n"
            if data.get('details'):
                message += f"│  └─ {data['details'][:30]}\n"
        message += f"\n"
    else:
        message += f"❌ No payment methods added yet!\n\n"
    
    message += f"➕ Add Payment Method:\n• BKash / Nagad / Binance - Click below\n\n💡 Your payment info is secure."
    
    keyboard = [
        [InlineKeyboardButton("➕ BKash", callback_data="add_bkash"), InlineKeyboardButton("➕ Nagad", callback_data="add_nagad")],
        [InlineKeyboardButton("➕ Binance", callback_data="add_binance")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_wallet"), InlineKeyboardButton("❌ Close", callback_data="close_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_payment_method_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    text = update.message.text.strip()
    
    if 'pending_payment_method' not in context.user_data:
        return
    
    if text.lower() == '/cancel':
        del context.user_data['pending_payment_method']
        await update.message.reply_text("❌ Payment method addition cancelled.\n\nYou can now send phone numbers normally.", parse_mode='none')
        return
    
    method = context.user_data['pending_payment_method']
    
    if method in ['bkash', 'nagad']:
        if not re.match(r'^01[3-9]\d{8}$', text):
            await update.message.reply_text(f"❌ Invalid {method.upper()} number!\n\nExample: `017XXXXXXXX`\n\nType /cancel to cancel.", parse_mode='Markdown')
            return
    elif method == 'binance':
        if not re.match(r'^\d{5,}$', text):
            await update.message.reply_text(f"❌ Invalid Binance Pay ID!\n\nExample: `8277372966555`\n\nType /cancel to cancel.", parse_mode='Markdown')
            return
    
    accounts = load_accounts()
    
    if user_id_str not in accounts:
        accounts[user_id_str] = {
            "accounts": [],
            "selected_account_id": 1,
            "telegram_username": update.effective_user.username or "",
            "last_active": datetime.now().isoformat(),
            "payment_methods": {}
        }
    
    if "payment_methods" not in accounts[user_id_str]:
        accounts[user_id_str]["payment_methods"] = {}
    
    accounts[user_id_str]["payment_methods"][method] = {
        "id": text,
        "details": "",
        "added_by": user_id,
        "added_at": datetime.now().isoformat()
    }
    
    save_accounts(accounts)
    del context.user_data['pending_payment_method']
    
    masked_id = text
    if len(text) > 8:
        masked_id = text[:4] + "****" + text[-4:]
    
    await update.message.reply_text(
        f"✅ {method.upper()} Added Successfully!\n\n💰 Method: {method.upper()}\n🔢 ID: `{text}`\n🔒 Masked: `{masked_id}`\n\nYou can now send phone numbers normally.\nUse /wallet to view all your payment methods.",
        parse_mode='Markdown'
    )
    
    username = update.effective_user.username or "No username"
    full_name = update.effective_user.full_name or "Unknown"
    
    admin_message = f"💳 NEW PAYMENT METHOD ADDED BY USER\n\n👤 User: {full_name}\n🆔 ID: `{user_id}`\n📛 Username: @{username}\n\n💰 Method: {method.upper()}\n🔢 ID: `{text}`\n🔒 Masked: `{masked_id}`\n\n📅 Added: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n\n💡 Tip: Click 'Refresh' on user card to see updated payment methods."
    await context.bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')

async def cancel_payment_method(update: Update, context: CallbackContext):
    if 'pending_payment_method' in context.user_data:
        del context.user_data['pending_payment_method']
        await update.message.reply_text("❌ Payment method addition cancelled.\n\n✅ Phone number checking is now back ON.", parse_mode='none')
    else:
        await update.message.reply_text("ℹ️ No pending payment method addition.", parse_mode='none')

async def handle_wallet_open(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "open_wallet":
        await wallet_command(update, context)
        await query.delete_message()

async def handle_statistics_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "stats_top_performers":
        await show_top_performers(query, context)
    elif data == "stats_all":
        await show_admin_statistics_from_callback(query, context)

async def show_top_performers(query, context):
    await query.edit_message_text("🔄 Generating top performers report...")
    
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    accounts = load_accounts()
    
    today_display = datetime.now().strftime('%d %B %Y')
    
    total_in_progress = 0
    total_success = 0
    total_users = 0
    user_stats = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        if isinstance(user_data, dict):
            user_accounts = user_data.get("accounts", [])
        else:
            user_accounts = []
        if not user_accounts:
            continue
        total_users += 1
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
        user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
        user_otp_success = otp_stats.get("user_stats", {}).get(user_id_str, {}).get("today_success", 0)
        total_in_progress += user_in_progress
        total_success += user_success
        user_stats.append({'user_id': user_id_str, 'username': username, 'in_progress': user_in_progress, 'success': user_success, 'otp_success': user_otp_success, 'accounts': len(user_accounts)})
    
    user_stats.sort(key=lambda x: x['success'], reverse=True)
    
    header_message = f"🎯 TOP PERFORMERS SUMMARY 🎯\n\n📅 Date: {today_display}\n⏰ Report Time: {datetime.now().strftime('%H:%M:%S')}\n\n📊 TOTAL STATISTICS:\n• 👥 Total Active Users: {total_users}\n• 🔵 Total In Progress Numbers: {total_in_progress}\n• 🟢 Total Success Counts: {total_success}\n• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n\n"
    if total_in_progress > 0:
        overall_success_rate = (total_success / total_in_progress) * 100
        header_message += f"📈 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%\n\n"
    header_message += "🏆 TOP PERFORMERS TODAY:\n"
    
    await query.edit_message_text(header_message, parse_mode='none')
    
    users_per_chunk = 50
    total_chunks = (len(user_stats) + users_per_chunk - 1) // users_per_chunk
    
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * users_per_chunk
        end_idx = min(start_idx + users_per_chunk, len(user_stats))
        chunk = user_stats[start_idx:end_idx]
        chunk_message = ""
        if total_chunks > 1:
            chunk_message += f"📋 Part {chunk_index + 1}/{total_chunks}\n\n"
        for i, user in enumerate(chunk, start=start_idx + 1):
            chunk_message += f"{i}. {user['username']} - {user['success']} success\n"
        chunk_in_progress = sum(u['in_progress'] for u in chunk)
        chunk_success = sum(u['success'] for u in chunk)
        chunk_message += f"\n📊 Chunk Summary:\n• Users: {len(chunk)}\n• Success: {chunk_success}\n"
        if chunk_in_progress > 0:
            chunk_success_rate = (chunk_success / chunk_in_progress) * 100
            chunk_message += f"• Success Rate: {chunk_success_rate:.1f}%\n"
        if chunk_index < total_chunks - 1:
            chunk_message += "\n⬇️ More users in next message..."
        try:
            await context.bot.send_message(ADMIN_ID, chunk_message, parse_mode='none')
            await asyncio.sleep(0.5)
        except:
            pass
    
    footer_message = "\n🔄 Statistics will reset at 4:00 PM (Bangladesh Time)"
    await context.bot.send_message(ADMIN_ID, footer_message, parse_mode='none')

async def show_admin_statistics_from_callback(query, context):
    await query.edit_message_text("🔄 Generating all users statistics report...")
    await show_admin_statistics_from_message(query, context)

async def show_admin_statistics_from_message(message_obj, context):
    tracking = load_tracking()
    stats = load_stats()
    otp_stats = load_otp_stats()
    accounts = load_accounts()
    
    today_display = datetime.now().strftime('%d %B %Y')
    total_in_progress = 0
    total_success = 0
    total_users = 0
    user_stats = []
    
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        if isinstance(user_data, dict):
            user_accounts = user_data.get("accounts", [])
        else:
            user_accounts = []
        if not user_accounts:
            continue
        total_users += 1
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        user_in_progress = tracking.get("today_added", {}).get(user_id_str, 0)
        user_success = tracking.get("today_success_counts", {}).get(user_id_str, 0)
        user_otp_success = otp_stats.get("user_stats", {}).get(user_id_str, {}).get("today_success", 0)
        total_in_progress += user_in_progress
        total_success += user_success
        user_stats.append({'user_id': user_id_str, 'username': username, 'in_progress': user_in_progress, 'success': user_success, 'otp_success': user_otp_success, 'accounts': len(user_accounts)})
    
    user_stats.sort(key=lambda x: x['success'], reverse=True)
    
    summary_message = f"👑 ADMIN STATISTICS SUMMARY 👑\n\n📅 Date: {today_display}\n⏰ Time: {datetime.now().strftime('%H:%M:%S')} (BD Time)\n🔄 Next Reset: Today 4:00 PM (BD Time)\n\n📊 TODAY'S OVERVIEW:\n• 👥 Total Users: {total_users}\n• 🔵 Total In Progress: {total_in_progress}\n• 🟢 Total Success: {total_success}\n• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n• 📊 Total Checked: {stats.get('today_checked', 0)}\n• 🗑️ Total Deleted: {stats.get('today_deleted', 0)}\n\n"
    
    await message_obj.edit_message_text(summary_message, parse_mode='none')
    
    users_per_message = 10
    total_chunks = (len(user_stats) + users_per_message - 1) // users_per_message
    
    for chunk_index in range(total_chunks):
        start_idx = chunk_index * users_per_message
        end_idx = min(start_idx + users_per_message, len(user_stats))
        chunk = user_stats[start_idx:end_idx]
        details_message = f"📋 USER STATISTICS - PART {chunk_index + 1}/{total_chunks} 📋\n\n📅 Date: {today_display}\n\n"
        for i, user in enumerate(chunk, start=start_idx + 1):
            details_message += f"{i}. {user['username']} (ID: {user['user_id']})\n   ├─ 📱 Accounts: {user['accounts']}\n   ├─ 🔵 In Progress: {user['in_progress']}\n   ├─ 🟢 Success: {user['success']}\n   ├─ ✅ OTP Success: {user['otp_success']}\n"
            if user['in_progress'] > 0:
                success_rate = (user['success'] / user['in_progress']) * 100
                details_message += f"   └─ 📈 Success Rate: {success_rate:.1f}%\n"
            else:
                details_message += f"   └─ 📈 Success Rate: 0%\n"
            details_message += "\n"
        chunk_in_progress = sum(u['in_progress'] for u in chunk)
        chunk_success = sum(u['success'] for u in chunk)
        details_message += f"📊 Chunk {chunk_index + 1} Summary:\n• 👥 Users: {len(chunk)}\n• 🔵 In Progress: {chunk_in_progress}\n• 🟢 Success: {chunk_success}\n"
        if chunk_index < total_chunks - 1:
            details_message += "\n⬇️ More users in next message..."
        try:
            await context.bot.send_message(ADMIN_ID, details_message, parse_mode='none')
            await asyncio.sleep(1)
        except:
            pass
    
    final_message = f"🎯 FINAL DAILY SUMMARY 🎯\n\n📅 Date: {today_display}\n⏰ Report Time: {datetime.now().strftime('%H:%M:%S')}\n\n📊 TOTAL STATISTICS:\n• 👥 Total Active Users: {total_users}\n• 🔵 Total In Progress Numbers: {total_in_progress}\n• 🟢 Total Success Counts: {total_success}\n• ✅ Total OTP Success: {otp_stats.get('today_success', 0)}\n\n"
    if total_in_progress > 0:
        overall_success_rate = (total_success / total_in_progress) * 100
        final_message += f"📈 OVERALL SUCCESS RATE: {overall_success_rate:.1f}%\n\n"
    if len(user_stats) >= 3:
        final_message += "🏆 TOP 3 PERFORMERS TODAY:\n"
        for i in range(min(3, len(user_stats))):
            user = user_stats[i]
            final_message += f"{i+1}. {user['username']} - {user['success']} success\n"
        final_message += "\n"
    final_message += "🔄 Statistics will reset at 4:00 PM (Bangladesh Time)\n✅ Report generation complete!"
    await context.bot.send_message(ADMIN_ID, final_message, parse_mode='none')

def extract_phone_numbers(text: str) -> List[Dict[str, str]]:
    all_numbers = []
    country_codes = {'1': '11', '7': 'RU/KZ', '20': 'EG', '27': 'ZA'}
    
    pattern_plus = r'\+\s*(\d{1,4})\s*([\d\s\-\.\(\)]+)'
    matches_plus = re.finditer(pattern_plus, text, re.IGNORECASE)
    
    for match in matches_plus:
        cc = match.group(1).strip()
        phone_part = match.group(2).strip()
        phone_digits = re.sub(r'\D', '', phone_part)
        if cc == '1':
            cc = '11'
        if cc in ['11', '7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', '41', '43', '44', '45', '46', '47', '48', '49', '51', '52', '53', '54', '55', '56', '57', '58', '60', '61', '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91', '92', '93', '94', '95', '98', '212', '213', '216', '218', '220', '221', '222', '223', '224', '225', '226', '227', '228', '229', '230', '231', '232', '233', '234', '235', '236', '237', '238', '239', '240', '241', '242', '243', '244', '245', '246', '247', '248', '249', '250', '251', '252', '253', '254', '255', '256', '257', '258', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '290', '291', '297', '298', '299', '350', '351', '352', '353', '354', '355', '356', '357', '358', '359', '370', '371', '372', '373', '374', '375', '376', '377', '378', '379', '380', '381', '382', '383', '385', '386', '387', '389', '420', '421', '423', '500', '501', '502', '503', '504', '505', '506', '507', '508', '509', '590', '591', '592', '593', '594', '595', '596', '597', '598', '599', '670', '672', '673', '674', '675', '676', '677', '678', '679', '680', '681', '682', '683', '685', '686', '687', '688', '689', '690', '691', '692', '850', '852', '853', '855', '856', '880', '886', '960', '961', '962', '963', '964', '965', '966', '967', '968', '970', '971', '972', '973', '974', '975', '976', '977', '992', '993', '994', '995', '996', '998']:
            if 7 <= len(phone_digits) <= 15:
                all_numbers.append({'cc': cc, 'phone': phone_digits, 'source': 'plus_format'})
    
    if not all_numbers:
        all_digits = re.findall(r'\d+', text)
        for digits in all_digits:
            if len(digits) >= 10:
                found_cc = None
                found_phone = None
                if digits.startswith('1') and len(digits) == 11:
                    found_cc = '11'
                    found_phone = digits[1:]
                if not found_cc:
                    for cc_length in range(4, 0, -1):
                        if len(digits) > cc_length:
                            possible_cc = digits[:cc_length]
                            possible_phone = digits[cc_length:]
                            if possible_cc == '1':
                                found_cc = '11'
                                found_phone = possible_phone
                                break
                            elif possible_cc in ['7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40', '41', '43', '44', '45', '46', '47', '48', '49', '51', '52', '53', '54', '55', '56', '57', '58', '60', '61', '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91', '92', '93', '94', '95', '98', '212', '213', '216', '218', '220', '221', '222', '223', '224', '225', '226', '227', '228', '229', '230', '231', '232', '233', '234', '235', '236', '237', '238', '239', '240', '241', '242', '243', '244', '245', '246', '247', '248', '249', '250', '251', '252', '253', '254', '255', '256', '257', '258', '260', '261', '262', '263', '264', '265', '266', '267', '268', '269', '290', '291', '297', '298', '299', '350', '351', '352', '353', '354', '355', '356', '357', '358', '359', '370', '371', '372', '373', '374', '375', '376', '377', '378', '379', '380', '381', '382', '383', '385', '386', '387', '389', '420', '421', '423', '500', '501', '502', '503', '504', '505', '506', '507', '508', '509', '590', '591', '592', '593', '594', '595', '596', '597', '598', '599', '670', '672', '673', '674', '675', '676', '677', '678', '679', '680', '681', '682', '683', '685', '686', '687', '688', '689', '690', '691', '692', '850', '852', '853', '855', '856', '880', '886', '960', '961', '962', '963', '964', '965', '966', '967', '968', '970', '971', '972', '973', '974', '975', '976', '977', '992', '993', '994', '995', '996', '998'] and 7 <= len(possible_phone) <= 15:
                                found_cc = possible_cc
                                found_phone = possible_phone
                                break
                if not found_cc:
                    if digits.startswith('1'):
                        found_cc = '11'
                        found_phone = digits[1:] if len(digits) > 1 else digits
                    elif len(digits) == 10:
                        found_cc = '11'
                        found_phone = digits
                    elif len(digits) >= 7:
                        found_cc = '11'
                        found_phone = digits
                if found_cc and found_phone:
                    all_numbers.append({'cc': found_cc, 'phone': found_phone, 'source': 'digits_only'})
    
    unique_numbers = []
    seen_phones = set()
    for num in all_numbers:
        phone = num['phone']
        if phone not in seen_phones:
            is_substring = False
            for seen_phone in seen_phones:
                if phone in seen_phone or seen_phone in phone:
                    is_substring = True
                    if len(phone) > len(seen_phone):
                        unique_numbers = [n for n in unique_numbers if n['phone'] != seen_phone]
                        seen_phones.remove(seen_phone)
                        unique_numbers.append(num)
                        seen_phones.add(phone)
                    break
            if not is_substring:
                unique_numbers.append(num)
                seen_phones.add(phone)
    
    return unique_numbers

async def add_number_async(session, token, cc, phone, retry_count=2):
    for attempt in range(retry_count):
        try:
            headers = {"Admin-Token": token}
            add_url = f"{BASE_URL}/z-number-base/addNum?cc={cc}&phoneNum={phone}&smsStatus=2"
            async with session.post(add_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return True
                elif response.status in (400, 409):
                    return False
        except:
            pass
    return False

async def get_status_async(session, token, phone):
    try:
        headers = {"Admin-Token": token}
        status_url = f"{BASE_URL}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
        async with session.get(status_url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            if response.status == 401:
                return -1, "❌ Token Expired", None
            try:
                res = await response.json(content_type=None)
            except:
                try:
                    cleaned_text = response_text.strip()
                    if cleaned_text.startswith('\ufeff'):
                        cleaned_text = cleaned_text[1:]
                    res = json.loads(cleaned_text)
                except:
                    return -2, "❌ API Error", None
            if res.get('code') == 28004:
                return -1, "❌ Token Expired", None
            if res.get('msg') and any(keyword in str(res.get('msg')).lower() for keyword in ["already exists", "cannot register", "number exists"]):
                return 16, "🚫 Already Exists", None
            if res.get('code') in (400, 409):
                return 16, "🚫 Already Exists", None
            if res and "data" in res and "records" in res["data"] and res["data"]["records"] and len(res["data"]["records"]) > 0:
                record = res["data"]["records"][0]
                status_code = record.get("registrationStatus")
                record_id = record.get("id")
                status_name = status_map.get(status_code, f"🔸 Status {status_code}")
                return status_code, status_name, record_id
            return None, "🚫 Already Registered...", None
    except:
        return -2, "🔄 Refresh Server", None

async def delete_single_number_async(session, token, record_id, username):
    try:
        headers = {"Admin-Token": token}
        delete_url = f"{BASE_URL}/z-number-base/deleteNum/{record_id}"
        async with session.delete(delete_url, headers=headers, timeout=10) as response:
            if response.status == 200:
                return True
            else:
                return False
    except:
        return False

async def submit_otp_async(session, token, phone, code, cc='1'):
    try:
        headers = {"Admin-Token": token}
        otp_url = f"{BASE_URL}/z-number-base/allNum/uploadCode?cc={cc}&phoneNum={phone}&code={code}"
        async with session.get(otp_url, headers=headers, timeout=15) as response:
            response_text = await response.text()
            if response.status == 200:
                try:
                    result = await response.json(content_type=None)
                    if result.get('code') == 200:
                        return True, "OTP verified successfully"
                    else:
                        return False, result.get('msg', 'Unknown error')
                except:
                    if "success" in response_text.lower() or "200" in response_text:
                        return True, "OTP verified successfully"
                    else:
                        return False, response_text
            elif response.status == 401:
                return False, "Token expired! Please refresh server."
            else:
                return False, f"HTTP Error: {response.status}"
    except asyncio.TimeoutError:
        return False, "Request timeout! Network issue."
    except:
        return False, "Unknown error"

async def get_user_settlements(session, token, user_id, page=1, page_size=2):
    try:
        headers = {"Admin-Token": token}
        url = f"{BASE_URL}/m-settle-accounts/closingEntries?page={page}&pageSize={page_size}&userid={user_id}"
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                try:
                    result = await response.json(content_type=None)
                    if result.get('code') == 200:
                        data = result.get('data', {})
                        if 'records' in data:
                            records = data.get('records', [])
                            total = data.get('total', len(records))
                            pages = data.get('pages', 1)
                            api_rates = {}
                            for record in records:
                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                country = country.strip(', ')
                                receipt_price = record.get('receiptPrice', 0)
                                if receipt_price > 0:
                                    api_rates[country] = receipt_price
                            return {'records': records, 'total': total, 'pages': pages, 'page': page, 'size': page_size, 'api_rates': api_rates}, None
                        else:
                            return {'records': [], 'total': 0, 'pages': 0, 'page': page, 'size': page_size, 'api_rates': {}}, None
                    else:
                        return None, f"API Error: {result.get('msg', 'Unknown error')}"
                except:
                    return None, "JSON parse error"
            else:
                return None, f"HTTP Error: {response.status}"
    except:
        return None, "Request error"

def generate_fake_payment_details():
    import random
    total_usd = round(random.uniform(2.0, 10.0), 2)
    personal_count = random.randint(int(total_usd * 8), int(total_usd * 12))
    personal_earnings = round(personal_count * 0.10, 2)
    if personal_earnings > total_usd:
        personal_earnings = round(total_usd * 0.7, 2)
        personal_count = int(personal_earnings / 0.10)
    friend_count = random.randint(5, int(total_usd * 5))
    friend_earnings = round(friend_count * 0.10, 2)
    commission = round(friend_count * 0.002, 2)
    calculated_total = personal_earnings + friend_earnings + commission
    if abs(calculated_total - total_usd) > 0.5:
        total_usd = round(calculated_total, 2)
    first_names = ["Rakib", "Sakib", "Rafiq", "Sohel", "Nayeem", "Fahim", "Ridoy", "Tanvir", "Saif", "Shanto"]
    last_names = ["Hasan", "Khan", "Islam", "Rana", "Ahmed", "Hossain", "Haque", "Uddin", "Rahman", "Mia"]
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    username = f"{first_name}_{last_name}"
    user_id = str(random.randint(1000000, 999999999))
    telegram_username = f"{first_name.lower()}{random.randint(100, 999)}"
    countries = ["Bangladesh", "India", "Pakistan", "USA", "Canada", "UK", "UAE", "Saudi Arabia", "Malaysia"]
    country = random.choice(countries)
    num_friends = random.randint(1, 3)
    friends_details = []
    for i in range(num_friends):
        friend_first = random.choice(first_names)
        friend_last = random.choice(last_names)
        friend_name = f"{friend_first} {friend_last}"
        friend_telegram = f"{friend_first.lower()}{random.randint(10, 99)}"
        friend_amount = round(random.uniform(0.5, 3.0), 2)
        friends_details.append({'name': friend_name, 'telegram': friend_telegram, 'amount': friend_amount})
    return {'total_usd': total_usd, 'total_bdt': round(total_usd * 125, 0), 'personal_count': personal_count, 'personal_earnings': personal_earnings, 'friend_count': friend_count, 'friend_earnings': friend_earnings, 'commission': commission, 'username': username, 'user_id': user_id, 'telegram_username': telegram_username, 'country': country, 'friends_details': friends_details}

async def send_fake_payment_confirmation(context: CallbackContext, count: int = 1):
    if not FAKE_PAYMENT_ENABLED:
        return 0
    sent_count = 0
    current_time = datetime.now()
    for i in range(count):
        try:
            payment = generate_fake_payment_details()
            if i > 0:
                await asyncio.sleep(random.uniform(2, 5))
            msg_time = current_time - timedelta(seconds=random.randint(0, 300))
            time_str = msg_time.strftime('%d %B %Y, %H:%M:%S')
            user_id = payment['user_id']
            if len(user_id) >= 6:
                masked_user_id = f"{user_id[:3]}xxxx{user_id[-3:]}"
            elif len(user_id) >= 4:
                masked_user_id = f"{user_id[:2]}xx{user_id[-2:]}"
            else:
                masked_user_id = "xxx"
            username = payment['username']
            if len(username) >= 4:
                masked_username = f"{username[:2]}xxx{username[-2:]}"
            elif len(username) >= 3:
                masked_username = f"{username[:1]}xx{username[-1:]}"
            else:
                masked_username = "xxx"
            message = f"💰 PAYMENT CONFIRMATION 💰\n\n🕐 Time: {time_str}\n\n👤 User: {masked_username}\n🆔 User ID: {masked_user_id}\n\n📊 Payment Details:\n├─ 🔢 Personal Count: {payment['personal_count']}\n├─ 💵 Personal Earnings: ${payment['personal_earnings']:.2f}\n"
            if payment['friend_count'] > 0:
                message += f"├─ 👥 Friend Count: {payment['friend_count']}\n├─ 💰 Friends Earned: ${payment['friend_earnings']:.2f}\n"
            if payment['commission'] > 0:
                message += f"├─ 💸 Commission: ${payment['commission']:.2f}\n"
            message += f"├─ 📈 Total USD: ${payment['total_usd']:.2f}\n└─ 🇧🇩 Total BDT: {payment['total_bdt']:.0f}\n\n"
            if payment['friends_details']:
                message += f"👥 Friends to Collect From ({len(payment['friends_details'])} friends):\n"
                for j, friend in enumerate(payment['friends_details'], 1):
                    friend_name = friend['name']
                    if len(friend_name) >= 4:
                        masked_friend_name = f"{friend_name[:2]}xxx{friend_name[-2:]}"
                    elif len(friend_name) >= 3:
                        masked_friend_name = f"{friend_name[:1]}xx{friend_name[-1:]}"
                    else:
                        masked_friend_name = "xxx"
                    message += f"├─ {j}. {masked_friend_name}\n├─   └─ ${friend['amount']:.2f}\n"
            tx_id = f"PAY-{msg_time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            message += f"\n✅ Status: Payment Completed\n🔒 Privacy: User details masked for security\n📨 Transaction ID: {tx_id}\n\n#PaymentConfirmation #{masked_user_id}"
            await context.bot.send_message(chat_id=FAKE_PAYMENT_GROUP_ID, text=message, parse_mode='none')
            sent_count += 1
        except:
            pass
    return sent_count

async def forward_payment_confirmation_to_group(context: CallbackContext, user_id: str, username: str, 
                                                telegram_username: str, total_usd: float, total_bdt: float,
                                                personal_count: int, personal_earnings: float,
                                                friend_count: int, friend_earnings: float,
                                                commission: float, friends_details: list, 
                                                payment_method: str, payment_id: str, is_fake: bool = False):
    """
    Forward payment confirmation to a separate Telegram group with MASKED payment ID
    """
    try:
        # Mask user ID
        masked_user_id = user_id
        if len(user_id) >= 6:
            masked_user_id = f"{user_id[:3]}xxxx{user_id[-3:]}"
        elif len(user_id) >= 4:
            masked_user_id = f"{user_id[:2]}xx{user_id[-2:]}"
        else:
            masked_user_id = "xxx"
        
        # Mask username
        masked_username = username
        if len(username) >= 4:
            masked_username = f"{username[:2]}xxx{username[-2:]}"
        elif len(username) >= 3:
            masked_username = f"{username[:1]}xx{username[-1:]}"
        else:
            masked_username = "xxx"
        
        # Mask telegram username
        masked_telegram = ""
        if telegram_username:
            if len(telegram_username) >= 4:
                masked_telegram = f"{telegram_username[:2]}xxx{telegram_username[-2:]}"
            elif len(telegram_username) >= 3:
                masked_telegram = f"{telegram_username[:1]}xx{telegram_username[-1:]}"
            else:
                masked_telegram = "xxx"
        
        current_time = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        
        message = f"💰 PAYMENT CONFIRMATION\n\n"
        message += f"🕐 {current_time}\n\n"
        
        message += f"👤 {masked_username}\n"
        message += f"🆔 {masked_user_id}\n"
        if masked_telegram:
            message += f"📱 @{masked_telegram}\n"
        
        message += f"\n📊 DETAILS\n"
        
        # 🔴 PERSONAL COUNTS
        if personal_count > 0:
            message += f"├─ 🔢 Personal Accounts: {personal_count}\n"
        else:
            message += f"├─ 🔢 Personal Accounts: 0\n"
        
        if personal_earnings > 0:
            message += f"├─ 💵 Personal Earnings: ${personal_earnings:.2f}\n"
        
        # 🔴 FRIEND DETAILS
        total_friend_counts = 0
        if friends_details and len(friends_details) > 0:
            total_friend_counts = sum(f.get('counts', 0) for f in friends_details)
            message += f"├─ 👥 Friends: {len(friends_details)} users\n"
            message += f"├─ 🔢 Friend Accounts: {total_friend_counts}\n"
        
        # 🔴 FRIENDS EARNINGS
        if friend_earnings > 0:
            message += f"├─ 💰 Friends Earned: ${friend_earnings:.2f}\n"
        
        # 🔴 COMMISSION
        if commission > 0:
            message += f"├─ 💸 Commission: ${commission:.2f}\n"
        
        # 🔴 GRAND TOTAL ACCOUNTS (Personal + Friend)
        total_all_counts = personal_count + total_friend_counts
        if total_all_counts > 0:
            message += f"├─ 📊 GRAND TOTAL: {total_all_counts} accounts\n"
        
        # 🔴 FRIENDS DETAILS BREAKDOWN
        if friends_details and len(friends_details) > 0:
            message += f"│\n├─ 📋 FRIENDS DETAILS:\n"
            for i, friend in enumerate(friends_details, 1):
                friend_name = friend.get('name', 'Unknown')
                # Mask friend name
                if len(friend_name) >= 4:
                    masked_friend_name = f"{friend_name[:2]}xxx{friend_name[-2:]}"
                elif len(friend_name) >= 3:
                    masked_friend_name = f"{friend_name[:1]}xx{friend_name[-1:]}"
                else:
                    masked_friend_name = "xxx"
                
                friend_counts = friend.get('counts', 0)
                friend_amount = friend.get('amount', 0)
                
                message += f"│  ├─ {i}. {masked_friend_name}\n"
                message += f"│  │  ├─ Total Accounts: {friend_counts}\n"
                message += f"│  │  └─ Earned: ${friend_amount:.2f}\n"
        
        # 🔴 TOTAL AMOUNT
        message += f"│\n└─ 💰 Total Amount: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        message += f"💳 Payment Method: {payment_method.upper()}\n"
        message += f"🔢 Payment ID: `{payment_id}`\n\n"
        
        if is_fake:
            message += f"⚠️ Test Mode\n\n"
        
        message += f"✅ Status: Completed\n"
        message += f"🔒 Privacy: Masked\n\n"
        message += f"#PaymentConfirmation #{masked_user_id}"
        
        try:
            await context.bot.send_message(
                chat_id=PAYMENT_GROUP_ID,
                text=message,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            return False
            
    except Exception as e:
        return False

async def fake_payment_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    count = 1
    if context.args:
        try:
            count = int(context.args[0])
            if count < 1:
                count = 1
            if count > 100:
                count = 100
                await update.message.reply_text("⚠️ Maximum 100 messages per command. Sending 100...")
        except:
            await update.message.reply_text("❌ Invalid count! Please provide a number.\nExample: `/fakepay 10`")
            return
    if not FAKE_PAYMENT_ENABLED:
        await update.message.reply_text("❌ Fake payments are disabled!")
        return
    processing_msg = await update.message.reply_text(f"🔄 Sending {count} fake payment confirmation(s)...")
    try:
        sent_count = await send_fake_payment_confirmation(context, count)
        await processing_msg.edit_text(f"✅ Fake Payment Confirmation(s) Sent!\n\n📊 Summary:\n├─ 📨 Requested: {count}\n├─ ✅ Sent: {sent_count}\n└─ ❌ Failed: {count - sent_count}")
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error sending fake payments: {e}")

async def fake_payment_toggle_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    global FAKE_PAYMENT_ENABLED
    command = context.args[0].lower() if context.args else ""
    if command == "enable" or command == "on":
        FAKE_PAYMENT_ENABLED = True
        status = "ENABLED ✅"
    elif command == "disable" or command == "off":
        FAKE_PAYMENT_ENABLED = False
        status = "DISABLED ❌"
    else:
        await update.message.reply_text(f"❌ Usage:\n`/fakeenable` - Enable fake payments\n`/fakedisable` - Disable fake payments\n\nCurrent status: {'✅ ENABLED' if FAKE_PAYMENT_ENABLED else '❌ DISABLED'}")
        return
    await update.message.reply_text(f"✅ Fake Payments {status}")

async def fake_payment_status_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    sample = generate_fake_payment_details()
    message = f"📊 Fake Payment Settings\n\n✅ Status: {'ENABLED' if FAKE_PAYMENT_ENABLED else 'DISABLED'}\n📨 Target Group: {FAKE_PAYMENT_GROUP_ID}\n\n📝 Commands:\n• `/fakepay [count]` - Send fake confirmations\n• `/fakeenable` - Enable fake payments\n• `/fakedisable` - Disable fake payments\n• `/fakestatus` - Show this status"
    await update.message.reply_text(message, parse_mode='none')

class AccountManager:
    def __init__(self):
        self.accounts = self._load_accounts_compatible()
        self.user_tokens = {}
        self.token_owners = {}
        self.token_info = {}
        self.user_selected_accounts = {}
        self.user_accounts_data = {}
        
    def _load_accounts_compatible(self):
        try:
            accounts_data = load_accounts()
            converted_accounts = {}
            for user_id_str, user_data in accounts_data.items():
                if isinstance(user_data, list):
                    converted_accounts[user_id_str] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
                    for i, acc in enumerate(user_accounts, 1):
                        new_account = {'id': i, 'custom_name': acc.get('custom_name', f"Account {i}"), 'username': acc.get('username', ''), 'password': acc.get('password', ''), 'token': acc.get('token'), 'api_user_id': acc.get('api_user_id'), 'nickname': acc.get('nickname', acc.get('username', '')), 'last_login': acc.get('last_login', datetime.now().isoformat()), 'active': acc.get('active', True), 'default': (i == 1), 'added_by': acc.get('added_by', 'unknown'), 'added_at': acc.get('added_at', datetime.now().isoformat()), 'telegram_username': acc.get('telegram_username', ''), 'friends': acc.get('friends', [])}
                        converted_accounts[user_id_str]["accounts"].append(new_account)
                elif isinstance(user_data, dict):
                    converted_accounts[user_id_str] = user_data
                else:
                    converted_accounts[user_id_str] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
            if converted_accounts != accounts_data:
                save_accounts(converted_accounts)
            return converted_accounts
        except:
            return {}
    
    async def initialize_user(self, user_id):
        user_id_str = str(user_id)
        self.accounts = self._load_accounts_compatible()
        user_data = self.accounts.get(user_id_str, {})
        if not user_data or not user_data.get("accounts"):
            self.user_selected_accounts[user_id_str] = None
            return 0
        user_accounts = user_data["accounts"]
        selected_id = user_data.get("selected_account_id", 1)
        valid_tokens = []
        selected_account = None
        for acc in user_accounts:
            if acc['id'] == selected_id:
                selected_account = acc
                break
        if not selected_account:
            selected_account = user_accounts[0] if user_accounts else None
            selected_id = selected_account['id'] if selected_account else 1
        if selected_account and selected_account.get('active', True):
            username = selected_account['username']
            password = selected_account['password']
            custom_name = selected_account.get('custom_name', username)
            if selected_account.get('token') and selected_account.get('api_user_id'):
                is_valid = await self.validate_token(selected_account['token'])
                if is_valid:
                    valid_tokens.append((username, selected_account['token'], selected_account['api_user_id'], custom_name, selected_id))
                else:
                    new_token, api_user_id, nickname = await login_api_async(username, password)
                    if new_token:
                        selected_account['token'] = new_token
                        selected_account['api_user_id'] = api_user_id
                        selected_account['nickname'] = nickname
                        selected_account['last_login'] = datetime.now().isoformat()
                        valid_tokens.append((username, new_token, api_user_id, custom_name, selected_id))
                    else:
                        selected_account['active'] = False
            else:
                new_token, api_user_id, nickname = await login_api_async(username, password)
                if new_token:
                    selected_account['token'] = new_token
                    selected_account['api_user_id'] = api_user_id
                    selected_account['nickname'] = nickname
                    selected_account['last_login'] = datetime.now().isoformat()
                    valid_tokens.append((username, new_token, api_user_id, custom_name, selected_id))
                else:
                    selected_account['active'] = False
        save_accounts(self.accounts)
        self.user_tokens[user_id_str] = []
        self.user_selected_accounts[user_id_str] = selected_id
        for username, token, api_user_id, custom_name, account_id in valid_tokens:
            self.user_tokens[user_id_str].append(token)
            self.token_owners[token] = (user_id_str, username, custom_name, account_id)
            self.token_info[token] = {'username': username, 'custom_name': custom_name, 'api_user_id': api_user_id, 'usage': 0, 'account_id': account_id, 'user_id': user_id_str}
        return len(valid_tokens)
    
    async def validate_token(self, token):
        try:
            async with aiohttp.ClientSession() as session:
                status_code, _, _ = await get_status_async(session, token, "0000000000")
                if status_code is not None and status_code != -1:
                    return True
            return False
        except:
            return False
    
    def get_user_accounts_count(self, user_id):
        user_id_str = str(user_id)
        if user_id_str in self.accounts:
            user_data = self.accounts[user_id_str]
            if isinstance(user_data, dict):
                accounts = user_data.get("accounts", [])
            else:
                accounts = []
            active_accounts = [acc for acc in accounts if acc.get('active', True)]
            return len(active_accounts)
        return 0
    
    def get_user_active_accounts_count(self, user_id):
        user_id_str = str(user_id)
        if user_id_str in self.user_tokens:
            return len(self.user_tokens[user_id_str])
        return 0
    
    def get_user_remaining_checks(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.user_tokens:
            return 0
        total_slots = 0
        used_slots = 0
        for token in self.user_tokens[user_id_str]:
            if token in self.token_info:
                total_slots += MAX_PER_ACCOUNT
                usage = self.token_info[token].get('usage', 0)
                used_slots += usage
        if user_id_str in self.accounts:
            user_data = self.accounts[user_id_str]
            if isinstance(user_data, dict):
                accounts_list = user_data.get("accounts", [])
                active_accounts = [acc for acc in accounts_list if acc.get('active', True)]
                total_accounts = len(active_accounts)
                logged_accounts = len(self.user_tokens[user_id_str])
                non_logged_accounts = total_accounts - logged_accounts
                total_slots += non_logged_accounts * MAX_PER_ACCOUNT
        return max(0, total_slots - used_slots)
    
    def get_selected_account_name(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.accounts:
            return "Unknown"
        user_data = self.accounts[user_id_str]
        if not isinstance(user_data, dict):
            return "Unknown"
        selected_id = user_data.get("selected_account_id", 1)
        for acc in user_data.get("accounts", []):
            if acc['id'] == selected_id:
                return acc.get('custom_name', acc.get('username', 'Unknown'))
        return "Unknown"
    
    def get_selected_account_id(self, user_id):
        user_id_str = str(user_id)
        return self.user_selected_accounts.get(user_id_str, 1)
    
    def get_next_available_token(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.user_tokens or not self.user_tokens[user_id_str]:
            return None
        available_tokens = []
        for token in self.user_tokens[user_id_str]:
            info = self.token_info.get(token, {})
            usage = info.get('usage', 0)
            if usage < MAX_PER_ACCOUNT:
                custom_name = info.get('custom_name', 'Unknown')
                account_id = info.get('account_id', 0)
                available_tokens.append((token, usage, custom_name, account_id))
        if not available_tokens:
            return None
        best_token, best_usage, custom_name, account_id = min(available_tokens, key=lambda x: x[1])
        if best_usage >= MAX_PER_ACCOUNT:
            return None
        self.token_info[best_token]['usage'] += 1
        return best_token, custom_name
    
    def release_token(self, token):
        if token in self.token_info:
            current_usage = self.token_info[token]['usage']
            if current_usage > 0:
                self.token_info[token]['usage'] = current_usage - 1
    
    def get_api_user_id_for_token(self, token):
        info = self.token_info.get(token, {})
        return info.get('api_user_id')

account_manager = AccountManager()

active_numbers = {}
number_status_history = {}

async def get_status_with_actual_phone(session, token, phone):
    try:
        headers = {"Admin-Token": token}
        status_url = f"{BASE_URL}/z-number-base/getAullNum?page=1&pageSize=15&phoneNum={phone}"
        async with session.get(status_url, headers=headers, timeout=10) as response:
            response_text = await response.text()
            if response.status == 401:
                return -1, "❌ Token Expired", None, phone
            try:
                res = await response.json(content_type=None)
            except:
                try:
                    cleaned_text = response_text.strip()
                    if cleaned_text.startswith('\ufeff'):
                        cleaned_text = cleaned_text[1:]
                    res = json.loads(cleaned_text)
                except:
                    return -2, "❌ API Error", None, phone
            if res.get('code') == 28004:
                return -1, "❌ Token Expired", None, phone
            error_msg = res.get('msg', '').lower()
            if any(keyword in error_msg for keyword in ["already exists", "cannot register", "number exists", "invalid", "wrong format"]):
                return 16, f"🚫 {res.get('msg', 'Already Exists')}", None, phone
            if res.get('code') in (400, 409):
                error_msg = res.get('msg', f'Error {res.get("code")}')
                return 16, f"🚫 {error_msg}", None, phone
            if res and "data" in res and "records" in res["data"] and res["data"]["records"] and len(res["data"]["records"]) > 0:
                record = res["data"]["records"][0]
                status_code = record.get("registrationStatus")
                record_id = record.get("id")
                actual_phone = record.get("phoneNum")
                if not actual_phone:
                    for field in ["phone", "phoneNumber", "mobile", "number"]:
                        if field in record:
                            actual_phone = record[field]
                            break
                status_name = status_map.get(status_code, f"🔸 Status {status_code}")
                return status_code, status_name, record_id, actual_phone or phone
            if res and "data" in res:
                return None, "🚫 Already register or wrong number", None, phone
            return None, "🚫 API Response Error", None, phone
    except:
        return -2, "🔄 Refresh Server", None, phone

async def track_status_optimized(context: CallbackContext):
    data = context.job.data
    phone = data['phone']
    token = data['token']
    username = data['username']
    user_id = data['user_id']
    checks = data['checks']
    last_status = data.get('last_status', '🔵 Processing...')
    serial_number = data.get('serial_number')
    last_status_code = data.get('last_status_code')
    cc = data.get('cc', '1')
    
    try:
        async with aiohttp.ClientSession() as session:
            status_code, status_name, record_id, actual_phone = await get_status_with_actual_phone(session, token, phone)
        
        prefix = f"{serial_number}. " if serial_number else ""
        display_phone = actual_phone if actual_phone and actual_phone != phone else phone
        phone_key = f"{cc}_{phone}_{user_id}"
        
        if status_code == -1:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            account_manager.release_token(token)
            error_text = f"{prefix}+{cc} {display_phone} ❌ Token Error (Auto-Retry)"
            try:
                await context.bot.edit_message_text(chat_id=data['chat_id'], message_id=data['message_id'], text=error_text)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    pass
            return
        
        if last_status_code == 2 and status_code != 2:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
        
        if status_code == 2:
            tracking = load_tracking()
            if "in_progress_timestamp" not in tracking:
                tracking["in_progress_timestamp"] = {}
            if phone_key not in tracking["in_progress_timestamp"]:
                tracking["in_progress_timestamp"][phone_key] = datetime.now().isoformat()
                save_tracking(tracking)
        
        if status_code == 1 and last_status_code != 1:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            user_id_str = str(user_id)
            if phone not in tracking.get("today_success", {}):
                otp_stats = load_otp_stats()
                otp_stats["total_success"] = otp_stats.get("total_success", 0) + 1
                otp_stats["today_success"] = otp_stats.get("today_success", 0) + 1
                if user_id_str not in otp_stats["user_stats"]:
                    otp_stats["user_stats"][user_id_str] = {"total_success": 0, "today_success": 0, "yesterday_success": 0, "username": username, "full_name": ""}
                otp_stats["user_stats"][user_id_str]["total_success"] += 1
                otp_stats["user_stats"][user_id_str]["today_success"] += 1
                tracking["today_success"][phone] = user_id_str
                if "today_success_counts" not in tracking:
                    tracking["today_success_counts"] = {}
                if user_id_str not in tracking["today_success_counts"]:
                    tracking["today_success_counts"][user_id_str] = 0
                tracking["today_success_counts"][user_id_str] += 1
                save_otp_stats(otp_stats)
                save_tracking(tracking)
            else:
                save_tracking(tracking)
        
        if status_code == 2:
            if phone not in active_numbers:
                active_numbers[phone] = {'token': token, 'username': username, 'message_id': data['message_id'], 'user_id': user_id, 'chat_id': data['chat_id'], 'cc': cc, 'phone': phone}
        
        if status_name != last_status:
            new_text = f"{prefix}+{cc} {display_phone} {status_name}"
            try:
                await context.bot.edit_message_text(chat_id=data['chat_id'], message_id=data['message_id'], text=new_text)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    pass
        
        delete_final_states = [0, 4, 7, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, -2]
        
        if status_code in delete_final_states:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
            if status_code not in [1, 2]:
                await delete_number_from_all_accounts_optimized(phone, user_id)
            final_text = f"{prefix}+{cc} {display_phone} {status_name}"
            try:
                await context.bot.edit_message_text(chat_id=data['chat_id'], message_id=data['message_id'], text=final_text)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    pass
            return
        
        if status_code == 1:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
            final_text = f"{prefix}+{cc} {display_phone} {status_name}"
            try:
                await context.bot.edit_message_text(chat_id=data['chat_id'], message_id=data['message_id'], text=final_text)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    pass
            return
        
        if checks >= 100:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            account_manager.release_token(token)
            if phone in active_numbers:
                del active_numbers[phone]
            if status_code not in [1, 2]:
                await delete_number_from_all_accounts_optimized(phone, user_id)
            timeout_text = f"{prefix}+{cc} {display_phone} 🟡 Try Later"
            try:
                await context.bot.edit_message_text(chat_id=data['chat_id'], message_id=data['message_id'], text=timeout_text)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    pass
            return
        
        if context.job_queue:
            context.job_queue.run_once(track_status_optimized, 5, data={**data, 'checks': checks + 1, 'last_status': status_name, 'last_status_code': status_code, 'cc': cc})
            
    except:
        account_manager.release_token(token)

async def check_if_number_in_progress(user_id: int, phone: str, cc: str = "1") -> bool:
    try:
        user_id_str = str(user_id)
        accounts = load_accounts()
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            return False
        user_accounts = user_data.get("accounts", [])
        if not user_accounts:
            return False
        for account in user_accounts:
            token = account.get('token')
            if token:
                async with aiohttp.ClientSession() as session:
                    status_code, status_name, record_id, _ = await get_status_with_actual_phone(session, token, phone)
                    if status_code == 2:
                        return True
                    else:
                        return False
        return False
    except:
        return False

async def check_in_progress_timeout(context: CallbackContext):
    tracking = load_tracking()
    in_progress_timestamp = tracking.get("in_progress_timestamp", {})
    current_time = datetime.now()
    numbers_to_check = []
    
    for phone_key, timestamp_str in list(in_progress_timestamp.items()):
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            time_diff = (current_time - timestamp).total_seconds()
            parts = phone_key.split("_")
            if len(parts) >= 3:
                cc = parts[0]
                phone = parts[1]
                user_id = int(parts[2])
            else:
                continue
            is_still_in_progress = await check_if_number_in_progress(user_id, phone, cc)
            if time_diff > 180 and phone_key not in tracking.get("pending_delete", {}) and is_still_in_progress:
                numbers_to_check.append(phone_key)
                if "pending_delete" not in tracking:
                    tracking["pending_delete"] = {}
                tracking["pending_delete"][phone_key] = current_time.isoformat()
            elif time_diff > 180 and not is_still_in_progress:
                del in_progress_timestamp[phone_key]
        except:
            pass
    
    if numbers_to_check:
        save_tracking(tracking)
        for phone_key in numbers_to_check:
            await notify_user_about_stuck_number(context, phone_key)
    
    if context.job_queue:
        context.job_queue.run_once(check_in_progress_timeout, 30)

async def notify_user_about_stuck_number(context: CallbackContext, phone_key: str):
    try:
        parts = phone_key.split("_")
        if len(parts) >= 3:
            cc = parts[0]
            phone = parts[1]
            user_id = int(parts[2])
        else:
            return
        
        is_still_stuck = await check_if_number_in_progress(user_id, phone, cc)
        if not is_still_stuck:
            tracking = load_tracking()
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if phone_key in tracking.get("pending_delete", {}):
                del tracking["pending_delete"][phone_key]
            save_tracking(tracking)
            return
        
        keyboard = [[InlineKeyboardButton("🗑️ নাম্বারটি ডিলিট করুন", callback_data=f"user_delete_stuck_{cc}_{phone}_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f"⚠️ আপনার নম্বরটি আটকে গেছে (Stuck)!\n\n📞 নম্বর: +{cc} {phone}\n⏰ সময়: {datetime.now().strftime('%H:%M:%S')}\n📊 বর্তমান স্ট্যাটাস: 🔵 In Progress\n\n❌ এই নম্বরটি ৩ মিনিট ধরে 'In Progress' অবস্থায় আছে।\n\n✅ অনুগ্রহ করে নিচের বাটনে ক্লিক করে নম্বরটি ডিলিট করুন।\nডিলিট করার পর আবার নতুন করে নম্বরটি সাবমিট করুন।\n\n💡 টিপ: +{cc}{phone} এই ফরম্যাটে আবার পাঠান"
        await context.bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup, parse_mode='Markdown')
    except:
        pass

async def handle_user_delete_stuck_number(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("user_delete_stuck_"):
        parts = data.split("_")
        if len(parts) >= 6:
            cc = parts[3]
            phone = parts[4]
            user_id = int(parts[5])
        else:
            await query.edit_message_text("❌ ভুল ডিলিট রিকোয়েস্ট!")
            return
        if query.from_user.id != user_id:
            await query.edit_message_text("❌ আপনি এই নম্বরটি ডিলিট করতে পারবেন না!")
            return
        await query.edit_message_text(f"🔄 ডিলিট করা হচ্ছে +{cc} {phone}...")
        deleted_count = await delete_number_from_all_accounts_optimized(phone, user_id)
        if deleted_count > 0:
            tracking = load_tracking()
            phone_key = f"{cc}_{phone}_{user_id}"
            if phone_key in tracking.get("in_progress_timestamp", {}):
                del tracking["in_progress_timestamp"][phone_key]
            if "pending_delete" in tracking and phone_key in tracking["pending_delete"]:
                del tracking["pending_delete"][phone_key]
            user_id_str = str(user_id)
            if user_id_str in tracking.get("today_added", {}):
                if isinstance(tracking["today_added"][user_id_str], dict):
                    if phone in tracking["today_added"][user_id_str]:
                        del tracking["today_added"][user_id_str][phone]
                elif isinstance(tracking["today_added"][user_id_str], (int, float)):
                    tracking["today_added"][user_id_str] = max(0, tracking["today_added"][user_id_str] - 1)
            save_tracking(tracking)
            if phone in active_numbers:
                del active_numbers[phone]
            success_message = f"✅ নম্বরটি সফলভাবে ডিলিট করা হয়েছে!\n\n📞 +{cc} {phone}\n🗑️ {deleted_count} একাউন্ট থেকে ডিলিট হয়েছে\n\n🔄 এখন আপনি আবার নতুন করে নম্বরটি সাবমিট করতে পারেন।\n💡 টিপ: সরাসরি নম্বরটি টাইপ করে পাঠিয়ে দিন: `+{cc}{phone}`"
            await query.edit_message_text(success_message, parse_mode='Markdown')
        else:
            error_message = f"⚠️ নম্বরটি পাওয়া যায়নি বা ইতিমধ্যে ডিলিট হয়ে গেছে!\n\n📞 +{cc} {phone}\n\n💡 আপনি সরাসরি নম্বরটি আবার সাবমিট করতে পারেন: `+{cc}{phone}`"
            await query.edit_message_text(error_message, parse_mode='Markdown')

async def check_and_delete_number_safe(session, token, phone, username):
    try:
        status_code, status_name, record_id, _ = await get_status_with_actual_phone(session, token, phone)
        if status_code == 1:
            return False
        if record_id:
            deleted = await delete_single_number_async(session, token, record_id, username)
            if deleted:
                return True
            else:
                return False
        else:
            return True
    except:
        return False

async def delete_number_from_all_accounts_optimized(phone, user_id):
    accounts = load_accounts()
    user_id_str = str(user_id)
    deleted_count = 0
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict):
        return 0
    async with aiohttp.ClientSession() as check_session:
        for account in user_data.get("accounts", []):
            if account.get("token"):
                status_code, status_name, record_id, _ = await get_status_with_actual_phone(check_session, account["token"], phone)
                if status_code == 1:
                    return 0
                break
    async with aiohttp.ClientSession() as session:
        tasks = []
        for account in user_data.get("accounts", []):
            if account.get("token"):
                task = asyncio.create_task(check_and_delete_number_safe(session, account["token"], phone, account['username']))
                tasks.append(task)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, bool) and result:
                    deleted_count += 1
        stats = load_stats()
        stats["total_deleted"] = stats.get("total_deleted", 0) + deleted_count
        stats["today_deleted"] = stats.get("today_deleted", 0) + deleted_count
        save_stats(stats)
        return deleted_count

async def delete_if_exists(session, token, phone, username):
    try:
        status_code, _, record_id = await get_status_async(session, token, phone)
        if record_id:
            return await delete_single_number_async(session, token, record_id, username)
        return True
    except:
        return False

async def show_user_settlements(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    if user_id_str not in account_manager.user_tokens or not account_manager.user_tokens[user_id_str]:
        await update.message.reply_text("❌ No active accounts found!")
        return
    token = account_manager.user_tokens[user_id_str][0]
    api_user_id = account_manager.get_api_user_id_for_token(token)
    if not api_user_id:
        await update.message.reply_text("❌ Could not find your API user ID.\n\nPlease refresh your accounts by clicking '🚀 Refresh Server' button first.")
        return
    page = 1
    if context.args:
        try:
            page = int(context.args[0])
            if page < 1:
                page = 1
        except:
            pass
    processing_msg = await update.message.reply_text("🔄 Loading your settlement records...")
    async with aiohttp.ClientSession() as session:
        data, error = await get_user_settlements(session, token, str(api_user_id), page=page, page_size=5)
    if error:
        await processing_msg.edit_text(f"❌ Error loading settlements: {error}")
        return
    if not data or not data.get('records'):
        await processing_msg.edit_text("❌ No settlement records found for your account!")
        return
    records = data.get('records', [])
    total_records = data.get('total', 0)
    total_pages = data.get('pages', 1)
    total_count = 0
    total_amount = 0
    for record in records:
        count = record.get('count', 0)
        record_rate = record.get('receiptPrice', 0.10)
        total_count += count
        total_amount += count * record_rate
    message = f"📦 Your Settlement Records\n\n📊 Total Records: {total_records}\n🔢 Total Count: {total_count}\n📄 Page: {page}/{total_pages}\n\n"
    for i, record in enumerate(records, 1):
        record_id = record.get('id', 'N/A')
        if record_id != 'N/A' and len(str(record_id)) > 8:
            record_id = str(record_id)[:8] + '...'
        count = record.get('count', 0)
        record_rate = record.get('receiptPrice', 0.10)
        amount = count * record_rate
        gmt_create = record.get('gmtCreate', 'N/A')
        country = record.get('countryName', 'N/A') or record.get('country', 'N/A')
        try:
            if gmt_create != 'N/A':
                if 'T' in gmt_create:
                    date_obj = datetime.fromisoformat(gmt_create.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S')
                formatted_date = date_obj.strftime('%d %B %Y, %H:%M')
            else:
                formatted_date = 'N/A'
        except:
            formatted_date = gmt_create
        message += f"{i}. Settlement #{record_id}\n📅 Date: {formatted_date}\n🌍 Country: {country}\n🔢 Count: {count}\n\n"
    keyboard = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settlement_{page-1}"))
    if page < total_pages:
        if not row:
            row = []
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"settlement_{page+1}"))
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"settlement_refresh_{page}")])
    if keyboard:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await processing_msg.edit_text(message, reply_markup=reply_markup, parse_mode='none')
    else:
        await processing_msg.edit_text(message, parse_mode='none')

async def set_settlement_rate(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args:
        await update.message.reply_text("💰 SET RATE\n\nUsage: `/setrate [rate] [country] [date]`\nNotice: `/setrate notice [message]`")
        return
    try:
        if context.args[0].lower() == 'notice':
            notice_message = ' '.join(context.args[1:])
            if not notice_message:
                await update.message.reply_text("❌ Please provide a notice message!")
                return
            accounts = load_accounts()
            sent_count = 0
            processing_msg = await update.message.reply_text(f"📢 Sending notice...")
            for user_id_str, user_data in accounts.items():
                if user_id_str == str(ADMIN_ID):
                    continue
                try:
                    await context.bot.send_message(int(user_id_str), f"📢 NOTICE\n\n{notice_message}\n\n📅 {datetime.now().strftime('%d %B %Y')}")
                    sent_count += 1
                    await asyncio.sleep(0.5)
                except:
                    pass
            await processing_msg.edit_text(f"✅ Notice sent to {sent_count} users")
            return
        country_rates = {}
        target_date = datetime.now().date()
        default_rate = None
        args = context.args.copy()
        date_index = -1
        for idx, arg in enumerate(args):
            if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', arg):
                date_index = idx
                break
            elif re.match(r'^\d{1,2}/\d{1,2}$', arg):
                date_index = idx
                break
        if date_index != -1:
            date_str = args.pop(date_index)
            try:
                if '-' in date_str:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                elif '/' in date_str:
                    parts = date_str.split('/')
                    day = parts[0].zfill(2)
                    month = parts[1].zfill(2)
                    current_year = datetime.now().year
                    target_date = datetime.strptime(f"{day}/{month}/{current_year}", "%d/%m/%Y").date()
            except:
                args.insert(date_index, date_str)
        i = 0
        while i < len(args):
            try:
                rate = float(args[i])
                if i + 1 < len(args) and not args[i+1].replace('.', '', 1).isdigit() and not re.match(r'^\d', args[i+1]):
                    country_name = args[i+1].title().rstrip(',')
                    country_rates[country_name] = rate
                    i += 2
                else:
                    default_rate = rate
                    i += 1
            except:
                i += 1
        if not default_rate and not country_rates:
            await update.message.reply_text("❌ Please provide at least one rate!")
            return
        settings = load_settings()
        old_rate = settings.get('settlement_rate', 0.10)
        target_date_str = target_date.strftime('%Y-%m-%d')
        target_date_display = target_date.strftime('%d %B %Y')
        filter_message = ""
        if country_rates:
            if len(country_rates) == 1:
                country = list(country_rates.keys())[0]
                rate = country_rates[country]
                filter_message = f"🌍 {country}: ${rate:.3f}"
            else:
                filter_message = "🌍 Multiple countries"
        else:
            filter_message = f"🌍 All: ${default_rate:.3f}"
        processing_msg = await update.message.reply_text(f"🔄 PROCESSING SETTLEMENT UPDATE\n┌─────────────────────────\n│ 📅 Date: {target_date_display}\n│ {filter_message}\n│ ⏳ Status: Initializing...\n└─────────────────────────")
        accounts = load_accounts()
        all_users_summary = []
        total_users = 0
        total_usd = 0
        total_bdt = 0
        USD_TO_BDT = 125
        users_processed = 0
        users_token_refreshed = 0
        users_with_settlements = 0
        users_with_only_commission = 0
        users_failed = 0
        users_with_earnings = 0
        users_without_earnings = 0
        total_friends_count = 0
        total_eligible_friends = 0
        total_personal_count = 0
        total_friend_counts = 0
        user_under_supervisors = {}
        users_in_friends_lists = set()
        api_rates_by_country = {}
        user_api_rates = {}
        country_wise_totals = {}
        for user_id_str, user_data in accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            if not isinstance(user_data, dict):
                continue
            user_accounts = user_data.get("accounts", [])
            if not user_accounts:
                continue
            for acc in user_accounts:
                if 'friends' in acc and isinstance(acc['friends'], list):
                    for friend in acc['friends']:
                        friend_id = None
                        if isinstance(friend, dict) and 'user_id' in friend:
                            friend_id = str(friend['user_id'])
                        elif isinstance(friend, str):
                            friend_id = str(friend)
                        if friend_id and friend_id in accounts:
                            users_in_friends_lists.add(friend_id)
        total_users_to_process = len([u for u in accounts if u != str(ADMIN_ID)])
        for user_id_str, user_data in accounts.items():
            if user_id_str == str(ADMIN_ID):
                continue
            if not isinstance(user_data, dict):
                continue
            user_accounts = user_data.get("accounts", [])
            if not user_accounts:
                continue
            users_processed += 1
            if users_processed % 3 == 0 or users_processed == total_users_to_process:
                try:
                    progress_percent = int((users_processed / total_users_to_process) * 100)
                    progress_bar = "█" * (progress_percent // 5) + "░" * (20 - (progress_percent // 5))
                    await processing_msg.edit_text(f"🔄 PROCESSING SETTLEMENT UPDATE\n┌─────────────────────────\n│ 📅 Date: {target_date_display}\n│ {filter_message}\n│ ├─ 📊 Progress: {progress_percent}% {progress_bar}\n│ ├─ 👥 Users: {users_processed}/{total_users_to_process}\n│ ├─ ✅ Found: {users_with_earnings}\n│ └─ ⏳ Status: Processing...\n└─────────────────────────")
                except:
                    pass
            username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
            telegram_username = user_data.get('telegram_username', '')
            payment_methods = user_data.get('payment_methods', {})
            user_country_totals = {}
            user_total_count = 0
            user_total_usd = 0
            user_accounts_with_settlements = []
            user_all_filtered_settlements = []
            for acc_idx, account in enumerate(user_accounts):
                account_name = account.get('custom_name', account['username'])
                account_username = account['username']
                account_password = account['password']
                account_token = None
                account_api_user_id = None
                if account.get('token'):
                    async with aiohttp.ClientSession() as session:
                        status_code, _, _ = await get_status_async(session, account['token'], "0000000000")
                    if status_code != -1:
                        account_token = account['token']
                        account_api_user_id = account.get('api_user_id')
                if not account_token:
                    token, api_user_id, nickname = await login_api_async(account_username, account_password)
                    if token:
                        account_token = token
                        account_api_user_id = api_user_id
                        account['token'] = token
                        account['api_user_id'] = api_user_id
                        account['nickname'] = nickname
                        account['last_login'] = datetime.now().isoformat()
                        users_token_refreshed += 1
                    else:
                        continue
                if account_token and account_api_user_id:
                    try:
                        async with aiohttp.ClientSession() as session:
                            settlement_data, error = await get_user_settlements(session, account_token, str(account_api_user_id), page=1, page_size=100)
                        if error:
                            continue
                        if settlement_data and settlement_data.get('records'):
                            for record in settlement_data.get('records', []):
                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                country = country.strip(', ')
                                receipt_price = record.get('receiptPrice', 0)
                                if receipt_price > 0:
                                    if country not in api_rates_by_country:
                                        api_rates_by_country[country] = receipt_price
                                    if user_id_str not in user_api_rates:
                                        user_api_rates[user_id_str] = {}
                                    user_api_rates[user_id_str][country] = receipt_price
                        if settlement_data and settlement_data.get('records'):
                            for record in settlement_data.get('records', []):
                                gmt_create = record.get('gmtCreate')
                                if not gmt_create:
                                    continue
                                try:
                                    if 'T' in gmt_create:
                                        record_date = datetime.fromisoformat(gmt_create.replace('Z', '+00:00')).date()
                                    else:
                                        record_date = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S').date()
                                    if record_date != target_date:
                                        continue
                                    country = record.get('countryName') or record.get('country') or 'Unknown'
                                    country = country.strip(', ')
                                    api_rate_for_country = record.get('receiptPrice', 0)
                                    if country_rates:
                                        matched_rate = default_rate if default_rate else 0.10
                                        for target_country, target_rate in country_rates.items():
                                            if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                matched_rate = target_rate
                                                break
                                        if matched_rate == (default_rate if default_rate else 0.10) and default_rate is None:
                                            continue
                                    else:
                                        if not default_rate:
                                            continue
                                        matched_rate = default_rate
                                    count_value = record.get('count', 0)
                                    country_usd = count_value * matched_rate
                                    if country not in user_country_totals:
                                        user_country_totals[country] = {'count': 0, 'usd': 0, 'rate': matched_rate}
                                    user_country_totals[country]['count'] += count_value
                                    user_country_totals[country]['usd'] += country_usd
                                    if country not in country_wise_totals:
                                        country_wise_totals[country] = {'count': 0, 'usd': 0, 'bdt': 0, 'rate': matched_rate, 'api_rate': api_rate_for_country}
                                    country_wise_totals[country]['count'] += count_value
                                    country_wise_totals[country]['usd'] += country_usd
                                    country_wise_totals[country]['bdt'] = country_wise_totals[country]['usd'] * USD_TO_BDT
                                    if api_rate_for_country > 0 and country_wise_totals[country].get('api_rate', 0) == 0:
                                        country_wise_totals[country]['api_rate'] = api_rate_for_country
                                    user_total_count += count_value
                                    user_total_usd += country_usd
                                    user_accounts_with_settlements.append({'account_name': account_name, 'username': account_username, 'settlement_count': 1, 'total_count': count_value, 'total_usd': country_usd, 'country': country})
                                except:
                                    continue
                    except:
                        continue
            user_personal_usd = user_total_usd
            total_personal_count += user_total_count
            commission_rate = 0.002
            total_commission = 0
            friends_details = []
            friends_list = []
            for acc in user_accounts:
                if isinstance(acc, dict) and 'friends' in acc and isinstance(acc['friends'], list):
                    friends_list = acc['friends']
                    break
            total_friends_count += len(friends_list)
            for friend_data in friends_list:
                friend_user_id = None
                if isinstance(friend_data, dict) and 'user_id' in friend_data:
                    friend_user_id = str(friend_data['user_id'])
                elif isinstance(friend_data, str):
                    friend_user_id = str(friend_data)
                else:
                    continue
                friend_found = False
                actual_friend_id = None
                for acc_key in accounts.keys():
                    if str(acc_key) == str(friend_user_id):
                        actual_friend_id = acc_key
                        friend_found = True
                        break
                if not friend_found or not actual_friend_id:
                    continue
                if actual_friend_id in accounts:
                    friend_accounts_data = accounts[actual_friend_id]
                    if not isinstance(friend_accounts_data, dict):
                        continue
                    friend_accounts = friend_accounts_data.get("accounts", [])
                    if not friend_accounts:
                        continue
                    friend_username = friend_accounts[0].get('username', 'Unknown') if friend_accounts else 'Unknown'
                    friend_telegram_username = friend_accounts_data.get('telegram_username', '')
                    user_under_supervisors[actual_friend_id] = {'name': username, 'telegram_username': telegram_username, 'user_id': user_id_str}
                    friend_country_totals = {}
                    friend_total_count = 0
                    friend_total_usd = 0
                    for friend_acc in friend_accounts:
                        friend_acc_token = None
                        friend_acc_api_id = friend_acc.get('api_user_id')
                        if friend_acc.get('token'):
                            async with aiohttp.ClientSession() as token_session:
                                status_code, _, _ = await get_status_async(token_session, friend_acc['token'], "0000000000")
                            if status_code != -1:
                                friend_acc_token = friend_acc['token']
                        if not friend_acc_token and friend_acc.get('active', True):
                            token, api_id, nickname = await login_api_async(friend_acc['username'], friend_acc['password'])
                            if token:
                                friend_acc_token = token
                                friend_acc['token'] = token
                                if api_id:
                                    friend_acc['api_user_id'] = api_id
                                friend_acc['nickname'] = nickname
                                friend_acc['last_login'] = datetime.now().isoformat()
                        if friend_acc_token and friend_acc_api_id:
                            try:
                                async with aiohttp.ClientSession() as friend_session:
                                    friend_settlement_data, error = await get_user_settlements(friend_session, friend_acc_token, str(friend_acc_api_id), page=1, page_size=100)
                                    if error or not friend_settlement_data:
                                        continue
                                    if friend_settlement_data.get('records'):
                                        for record in friend_settlement_data.get('records', []):
                                            gmt_create = record.get('gmtCreate')
                                            if not gmt_create:
                                                continue
                                            try:
                                                if 'T' in gmt_create:
                                                    record_date = datetime.fromisoformat(gmt_create.replace('Z', '+00:00')).date()
                                                else:
                                                    record_date = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S').date()
                                                if record_date != target_date:
                                                    continue
                                                country = record.get('countryName') or record.get('country') or 'Unknown'
                                                country = country.strip(', ')
                                                if country_rates:
                                                    matched_rate = default_rate if default_rate else 0.10
                                                    for target_country, target_rate in country_rates.items():
                                                        if target_country.lower() in country.lower() or country.lower() in target_country.lower():
                                                            matched_rate = target_rate
                                                            break
                                                    if matched_rate == (default_rate if default_rate else 0.10) and default_rate is None:
                                                        continue
                                                else:
                                                    if not default_rate:
                                                        continue
                                                    matched_rate = default_rate
                                                count = record.get('count', 0)
                                                country_usd = count * matched_rate
                                                if country not in friend_country_totals:
                                                    friend_country_totals[country] = {'count': 0, 'usd': 0, 'rate': matched_rate}
                                                friend_country_totals[country]['count'] += count
                                                friend_country_totals[country]['usd'] += country_usd
                                                friend_total_count += count
                                                friend_total_usd += country_usd
                                            except:
                                                continue
                            except:
                                continue
                    if friend_total_count >= 1:
                        friend_commission = friend_total_count * commission_rate
                        total_commission += friend_commission
                        total_friend_counts += friend_total_count
                        total_eligible_friends += 1
                        friend_name = "Unknown"
                        if isinstance(friend_data, dict) and 'name' in friend_data:
                            friend_name = friend_data['name']
                        elif friend_accounts and friend_accounts[0].get('nickname'):
                            friend_name = friend_accounts[0].get('nickname')
                        elif friend_accounts and friend_accounts[0].get('username'):
                            friend_name = friend_accounts[0].get('username')
                        friends_details.append({'name': friend_name, 'username': friend_username, 'telegram_username': friend_telegram_username, 'accounts': len(friend_accounts), 'counts': friend_total_count, 'commission': friend_commission, 'earnings': friend_total_usd, 'friend_user_id': actual_friend_id, 'country_totals': friend_country_totals})
            total_usd_with_commission = user_personal_usd + total_commission
            total_bdt_user = total_usd_with_commission * USD_TO_BDT
            if user_total_count > 0:
                users_with_settlements += 1
            if total_commission > 0 and user_total_count == 0:
                users_with_only_commission += 1
            has_earnings = user_personal_usd > 0 or total_commission > 0
            if has_earnings:
                users_with_earnings += 1
                user_summary = {'user_id': user_id_str, 'username': username, 'telegram_username': telegram_username, 'settlement_date': target_date_display, 'country_totals': user_country_totals, 'total_count': user_total_count, 'personal_usd': user_personal_usd, 'total_commission': total_commission, 'friends_details': friends_details, 'total_usd': total_usd_with_commission, 'total_bdt': total_bdt_user, 'num_records': len(user_all_filtered_settlements), 'token_refreshed': users_token_refreshed, 'has_personal_settlement': len(user_all_filtered_settlements) > 0, 'friend_counts': sum(f['counts'] for f in friends_details), 'total_counts': user_total_count + sum(f['counts'] for f in friends_details), 'has_earnings': has_earnings, 'in_friends_list': user_id_str in users_in_friends_lists, 'friends_list': friends_details, 'accounts_with_settlements': user_accounts_with_settlements, 'total_accounts': len(user_accounts), 'active_accounts': len([acc for acc in user_accounts if acc.get('active', True)]), 'payment_methods': payment_methods}
                all_users_summary.append(user_summary)
                total_users += 1
                total_usd += total_usd_with_commission
                total_bdt += total_bdt_user
        save_accounts(accounts)
        if default_rate:
            settings['settlement_rate'] = default_rate
        elif country_rates:
            first_country = list(country_rates.keys())[0]
            settings['settlement_rate'] = country_rates[first_country]
        else:
            settings['settlement_rate'] = 0.10
        settings['last_updated'] = datetime.now().isoformat()
        settings['updated_by'] = ADMIN_ID
        save_settings(settings)
        for user_summary in all_users_summary:
            try:
                supervisor_info = user_under_supervisors.get(user_summary['user_id'])
                has_friends = len(user_summary.get('friends_details', [])) > 0
                is_friend = user_summary.get('in_friends_list', False)
                payment_methods = user_summary.get('payment_methods', {})
                has_payment_method = len(payment_methods) > 0
                country_breakdown = ""
                if user_summary.get('country_totals'):
                    country_breakdown = "\n📊 COUNTRY-WISE BREAKDOWN:\n"
                    for country, data in user_summary['country_totals'].items():
                        country_breakdown += f"├─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                if has_friends:
                    message = f"✨ SETTLEMENT UPDATE\n\n📅 {user_summary['settlement_date']}\n\n"
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Personal: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    if user_summary['friends_details']:
                        message += f"\n👥 YOUR NETWORK ({len(user_summary['friends_details'])} friends)\n"
                        for i, friend in enumerate(user_summary['friends_details'], 1):
                            message += f"\n├─ {i}. {friend['name']}\n│  ├─ Total Accounts: {friend['counts']}\n│  ├─ Earned: ${friend['earnings']:.2f}\n"
                            if friend.get('country_totals'):
                                message += f"│  └─ Country Breakdown:\n"
                                for country, data in friend['country_totals'].items():
                                    message += f"│     └─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                            else:
                                message += f"│  └─ Commission: ${friend['commission']:.2f}\n"
                        total_friend_counts = sum(f['counts'] for f in user_summary['friends_details'])
                        message += f"\n💰 COMMISSION SUMMARY\n├─ Total Friend Accounts: {total_friend_counts}\n└─ Total Commission: ${user_summary['total_commission']:.2f}\n"
                    message += f"\n💰 TOTAL EARNINGS\n├─ Personal + Commission: ${user_summary['total_usd']:.2f}\n└─ BDT: {user_summary['total_bdt']:.0f} BDT\n\n"
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                elif is_friend:
                    message = f"✨ SETTLEMENT UPDATE\n\n📅 {user_summary['settlement_date']}\n\n"
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Accounts: {user_summary['total_count']}\n├─ USD: ${user_summary['personal_usd']:.2f}\n└─ BDT: {user_summary['total_bdt']:.0f} BDT\n\n"
                    if supervisor_info:
                        message += f"👤 Added by: {supervisor_info['name']}"
                        if supervisor_info.get('telegram_username'):
                            message += f" (@{supervisor_info['telegram_username']})"
                        message += f"\n\n"
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                    message += f"ℹ️ Note: Your earnings will be collected by your friend.\nThey will pay you directly.\n\n"
                else:
                    message = f"✨ SETTLEMENT UPDATE\n\n📅 {user_summary['settlement_date']}\n\n"
                    if country_rates:
                        message += f"💰 COUNTRY RATES:\n"
                        for country, rate in country_rates.items():
                            message += f"├─ {country}: ${rate:.3f}/account\n"
                        message += f"\n"
                    else:
                        message += f"💰 Rate: ${default_rate:.3f}/account\n\n"
                    message += f"📊 YOUR EARNINGS\n"
                    if user_summary['country_totals']:
                        message += country_breakdown
                        message += f"\n📈 TOTAL: {user_summary['total_count']} accounts (${user_summary['personal_usd']:.2f})\n"
                    else:
                        message += f"├─ Accounts: {user_summary['total_count']}\n├─ USD: ${user_summary['personal_usd']:.2f}\n└─ Total: ${user_summary['total_usd']:.2f} / {user_summary['total_bdt']:.0f} BDT\n\n"
                    if supervisor_info:
                        message += f"👤 Added by: {supervisor_info['name']}\n\n"
                    if not has_payment_method:
                        message += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
                if len(message) > 4000:
                    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
                    for chunk in chunks:
                        await context.bot.send_message(int(user_summary['user_id']), chunk, parse_mode='none')
                        await asyncio.sleep(0.5)
                else:
                    await context.bot.send_message(int(user_summary['user_id']), message, parse_mode='none')
                await asyncio.sleep(0.5)
            except:
                pass
        if all_users_summary:
            total_personal_counts_all = sum(u['total_count'] for u in all_users_summary)
            total_friend_counts_all = sum(u['friend_counts'] for u in all_users_summary)
            grand_total_counts = total_personal_counts_all + total_friend_counts_all
            total_personal_usd_all = sum(u['personal_usd'] for u in all_users_summary)
            total_friend_earnings_all = sum(sum(f['earnings'] for f in u['friends_details']) for u in all_users_summary)
            total_commissions_all = sum(u['total_commission'] for u in all_users_summary)
            total_all_earnings = total_personal_usd_all + total_friend_earnings_all + total_commissions_all
            total_all_bdt = total_all_earnings * USD_TO_BDT
            country_summary = ""
            if country_wise_totals:
                country_summary = "\n🌍 COUNTRY-WISE SUMMARY WITH PROFIT ANALYSIS:\n"
                sorted_countries = sorted(country_wise_totals.items(), key=lambda x: x[1]['count'], reverse=True)
                total_api_all = 0
                total_admin_all = 0
                total_profit_all = 0
                for country, data in sorted_countries:
                    count = data['count']
                    admin_rate = data.get('rate', default_rate or 0.10)
                    api_rate = data.get('api_rate', 0)
                    if api_rate == 0 and country in api_rates_by_country:
                        api_rate = api_rates_by_country[country]
                    if api_rate > 0:
                        api_amount = count * api_rate
                        admin_amount = count * admin_rate
                        profit = admin_amount - api_amount
                        total_api_all += api_amount
                        total_admin_all += admin_amount
                        total_profit_all += profit
                        profit_symbol = "📈" if profit > 0 else "📉" if profit < 0 else "📊"
                        country_summary += f"├─ {country}:\n│  ├─ Accounts: {count}\n│  ├─ API Rate: ${api_rate:.4f}\n│  ├─ Admin Rate: ${admin_rate:.4f}\n│  ├─ API Amount: ${api_amount:.2f}\n│  ├─ Admin Amount: ${admin_amount:.2f}\n│  └─ Profit: {profit_symbol} ${profit:.2f}\n"
                    else:
                        country_summary += f"├─ {country}:\n│  ├─ Accounts: {count}\n│  ├─ API Rate: ⚠️ Not Found\n│  ├─ Admin Rate: ${admin_rate:.4f}\n│  └─ Profit: ⚠️ Unknown\n"
                if total_api_all > 0:
                    country_summary += f"\n📊 GRAND TOTAL PROFIT ANALYSIS:\n├─ Total API Amount: ${total_api_all:.2f}\n├─ Total Admin Amount: ${total_admin_all:.2f}\n└─ Total Profit: ${total_profit_all:.2f}\n"
                country_summary += f"\n📈 GRAND TOTAL ACCOUNTS: {grand_total_counts}\n   (Personal: {total_personal_counts_all} + Friend: {total_friend_counts_all})\n\n"
            detailed_summary = f"📊 SETTLEMENT SUMMARY\n\n📅 {target_date_display}\n"
            if country_rates:
                detailed_summary += "\n💰 RATES USED:\n"
                for country, rate in country_rates.items():
                    detailed_summary += f"├─ {country}: ${rate:.3f}\n"
                if default_rate:
                    detailed_summary += f"└─ Other: ${default_rate:.3f}\n"
                detailed_summary += "\n"
            detailed_summary += f"👥 USERS\n├─ With earnings: {users_with_earnings}\n├─ Without: {users_without_earnings}\n└─ Commission only: {users_with_only_commission}\n\n"
            detailed_summary += country_summary
            detailed_summary += f"💰 FINANCIAL SUMMARY\n├─ Personal Earnings: ${total_personal_usd_all:.2f}\n├─ Friends Earnings: ${total_friend_earnings_all:.2f}\n├─ Commission: ${total_commissions_all:.2f}\n└─ 📈 TOTAL: ${total_all_earnings:.2f} / {total_all_bdt:.0f} BDT\n\n✅ Operation complete!"
            if len(detailed_summary) > 4000:
                summary_chunks = [detailed_summary[i:i+4000] for i in range(0, len(detailed_summary), 4000)]
                for chunk in summary_chunks:
                    await processing_msg.edit_text(chunk, parse_mode='none')
                    await asyncio.sleep(0.5)
            else:
                await processing_msg.edit_text(detailed_summary, parse_mode='none')
            for user_summary in all_users_summary:
                telegram_display = f" (@{user_summary['telegram_username']})" if user_summary['telegram_username'] else ""
                refresh_icon = " 🔄" if user_summary['token_refreshed'] else ""
                settlement_icon = " ✅" if user_summary['has_personal_settlement'] else " 👥"
                user_personal_counts = user_summary['total_count']
                user_friend_counts = user_summary['friend_counts']
                user_grand_total = user_personal_counts + user_friend_counts
                payment_methods = user_summary.get('payment_methods', {})
                has_payment_method = len(payment_methods) > 0
                user_message = f"👤 {user_summary['username']}{telegram_display}{refresh_icon}{settlement_icon}\n├─ 📱 Accounts: {user_summary['active_accounts']}\n"
                if user_summary.get('accounts_with_settlements'):
                    user_message += f"├─ 💰 Active: {len(user_summary['accounts_with_settlements'])}\n"
                if user_summary.get('country_totals'):
                    user_message += f"├─ 📊 PERSONAL (Country-wise):\n"
                    for country, data in user_summary['country_totals'].items():
                        user_message += f"│  ├─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                    user_message += f"├─ 🔢 Total Personal: {user_personal_counts} accounts (${user_summary['personal_usd']:.2f})\n"
                else:
                    user_message += f"├─ 🔢 Personal: {user_personal_counts} accounts (${user_summary['personal_usd']:.2f})\n"
                if user_summary['friends_details']:
                    eligible_friends = len([f for f in user_summary['friends_details'] if f['counts'] >= 1])
                    user_message += f"├─ 👥 Friends: {eligible_friends} users\n├─ 🔢 Friend Accounts: {user_friend_counts}\n├─ 💰 Commission: ${user_summary['total_commission']:.2f}\n├─ 📊 GRAND TOTAL: {user_grand_total} accounts\n\n├─ 📋 FRIENDS DETAILS (Country-wise):\n"
                    for i, friend in enumerate(user_summary['friends_details'], 1):
                        friend_name = friend.get('name', 'Unknown')
                        friend_username = friend.get('username', 'Unknown')
                        friend_counts = friend.get('counts', 0)
                        friend_earnings = friend.get('earnings', 0)
                        friend_commission = friend.get('commission', 0)
                        user_message += f"│  ├─ {i}. {friend_name}"
                        if friend_username and friend_username != 'Unknown':
                            user_message += f" (@{friend_username})"
                        user_message += f"\n│  │  ├─ Total Accounts: {friend_counts}\n│  │  ├─ Earned: ${friend_earnings:.2f}\n"
                        if friend.get('country_totals'):
                            user_message += f"│  │  └─ Country Breakdown:\n"
                            for country, data in friend['country_totals'].items():
                                user_message += f"│  │     └─ {country}: {data['count']} accounts (${data['usd']:.2f})\n"
                        else:
                            user_message += f"│  │  └─ Commission: ${friend_commission:.2f}\n"
                else:
                    user_message += f"├─ 📊 Total: {user_grand_total} accounts\n"
                friend_earnings = sum(f['earnings'] for f in user_summary['friends_details'])
                total_all_earnings_user = user_summary['personal_usd'] + friend_earnings + user_summary['total_commission']
                total_all_bdt_user = total_all_earnings_user * USD_TO_BDT
                user_message += f"├─ 💰 Total: ${total_all_earnings_user:.2f} / {total_all_bdt_user:.0f} BDT\n"
                if payment_methods:
                    user_message += f"├─ 💳 Payment Methods:\n"
                    for method, data in payment_methods.items():
                        payment_id = data.get('id', 'N/A')
                        if len(payment_id) > 8:
                            masked_id = payment_id[:4] + "****" + payment_id[-4:]
                        else:
                            masked_id = payment_id
                        user_message += f"│  ├─ {method.upper()}: `{payment_id}`\n"
                        if data.get('details'):
                            user_message += f"│  │  └─ {data['details'][:30]}\n"
                else:
                    user_message += f"├─ 💳 Payment: ❌ Not Provided\n"
                user_message += f"└─ 📅 {target_date_display}\n\n"
                added_by_list = []
                for other_user in all_users_summary:
                    for friend in other_user.get('friends_details', []):
                        if friend.get('friend_user_id') == user_summary['user_id']:
                            added_by_list.append({'added_by': other_user['username'], 'telegram': other_user['telegram_username']})
                if added_by_list:
                    names = []
                    for adder in added_by_list[:2]:
                        if adder['telegram']:
                            names.append(f"{adder['added_by']} (@{adder['telegram']})")
                        else:
                            names.append(adder['added_by'])
                    added_by_message = f"⚠️ Added by: {', '.join(names)}"
                    if len(added_by_list) > 2:
                        added_by_message += f" +{len(added_by_list) - 2} more"
                    user_message += f"{added_by_message}\n\n"
                keyboard = []
                if user_summary['has_earnings']:
                    if has_payment_method:
                        for method in payment_methods.keys():
                            keyboard.append([InlineKeyboardButton(f"✅ {method.upper()} Payment Complete", callback_data=f"payment_complete_{user_summary['user_id']}_{method}_{target_date_str}")])
                    else:
                        keyboard.append([InlineKeyboardButton("✅ Payment Complete", callback_data=f"force_payment_complete_{user_summary['user_id']}_{target_date_str}")])
                keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_summary['user_id']}_{target_date_str}")])
                keyboard.append([InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_summary['user_id']}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                if len(user_message) > 4000:
                    msg_chunks = [user_message[i:i+4000] for i in range(0, len(user_message), 4000)]
                    for j, chunk in enumerate(msg_chunks):
                        if j == len(msg_chunks) - 1:
                            await context.bot.send_message(ADMIN_ID, chunk, reply_markup=reply_markup, parse_mode='Markdown')
                        else:
                            await context.bot.send_message(ADMIN_ID, chunk, parse_mode='Markdown')
                        await asyncio.sleep(0.5)
                else:
                    await context.bot.send_message(ADMIN_ID, user_message, reply_markup=reply_markup, parse_mode='Markdown')
                await asyncio.sleep(0.5)
            final_stats = f"📊 PAYMENT STATS\n\n📅 {target_date_display}\n👥 Users: {total_users}\n✅ Direct: {len([u for u in all_users_summary if not u['in_friends_list']])}\n👥 Via Friends: {len([u for u in all_users_summary if u['in_friends_list']])}\n💰 Total: ${total_all_earnings:.2f}\n📊 Grand Total Accounts: {grand_total_counts}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if len(final_stats) > 4000:
                final_chunks = [final_stats[i:i+4000] for i in range(0, len(final_stats), 4000)]
                for chunk in final_chunks:
                    await context.bot.send_message(ADMIN_ID, chunk, parse_mode='none')
            else:
                await context.bot.send_message(ADMIN_ID, final_stats, parse_mode='none')
        else:
            summary_message = f"📊 SETTLEMENT UPDATE\n\n📅 {target_date_display}\n\n💰 No settlements found\n\n👥 Users: {users_processed}\n✅ With earnings: {users_with_earnings}\n👥 Without: {users_without_earnings}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            if len(summary_message) > 4000:
                summary_chunks = [summary_message[i:i+4000] for i in range(0, len(summary_message), 4000)]
                for chunk in summary_chunks:
                    await processing_msg.edit_text(chunk, parse_mode='none')
                    await asyncio.sleep(0.5)
            else:
                await processing_msg.edit_text(summary_message, parse_mode='none')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_refresh_user_card(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("refresh_user_card_"):
        parts = data.split("_")
        if len(parts) >= 5:
            user_id = parts[3]
            date_str = parts[4]
        else:
            await query.answer("Invalid request!", show_alert=True)
            return
        await query.edit_message_text(f"🔄 Refreshing card for user {user_id}...")
        accounts = load_accounts()
        user_data = accounts.get(user_id, {})
        if not user_data:
            await query.edit_message_text(f"❌ User {user_id} not found!")
            return
        payment_methods = user_data.get('payment_methods', {})
        has_payment_method = len(payment_methods) > 0
        user_accounts = user_data.get("accounts", [])
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        telegram_username = user_data.get('telegram_username', '')
        original_text = query.message.text
        payment_completed = "✅ Payment Completed" in original_text or "✅ পেমেন্ট সম্পূর্ণ" in original_text or "Completed via" in original_text
        if payment_completed:
            await query.edit_message_text("✅ Payment already completed for this card!")
            return
        has_earnings = "💰 Total:" in original_text or "মোট:" in original_text
        import re
        personal_count = 0
        personal_usd = 0
        total_usd = 0
        total_bdt = 0
        friends_details = []
        personal_match = re.search(r'├─ 🔢 Personal: (\d+) accounts? \(\$([\d\.]+)\)', original_text)
        if not personal_match:
            personal_match = re.search(r'├─ Personal: (\d+) accounts? \(\$([\d\.]+)\)', original_text)
        if personal_match:
            personal_count = int(personal_match.group(1))
            personal_usd = float(personal_match.group(2))
        friend_section = re.search(r'├─ 📋 FRIENDS DETAILS.*?(?=├─ 💰 Total:|└─ 💰 Total:|$)', original_text, re.DOTALL)
        if friend_section:
            friend_text = friend_section.group()
            friend_matches = re.findall(r'│  ├─ \d+\. ([^\n]+).*?Total Accounts: (\d+)', friend_text, re.DOTALL)
            for match in friend_matches:
                friend_name, counts_str = match
                friends_details.append({'name': friend_name.strip(), 'counts': int(counts_str)})
        total_match = re.search(r'├─ 💰 Total: \$([\d\.]+) / ([\d\.]+) BDT', original_text)
        if not total_match:
            total_match = re.search(r'└─ 💰 Total: \$([\d\.]+) / ([\d\.]+) BDT', original_text)
        if total_match:
            total_usd = float(total_match.group(1))
            total_bdt = float(total_match.group(2))
        new_message = f"👤 {username}"
        if telegram_username:
            new_message += f" (@{telegram_username})"
        new_message += f"\n├─ 📱 Accounts: {len(user_accounts)}\n├─ 🔢 Personal: {personal_count} accounts (${personal_usd:.2f})\n"
        if friends_details:
            eligible_friends = len(friends_details)
            friend_counts = sum(f['counts'] for f in friends_details)
            new_message += f"├─ 👥 Friends: {eligible_friends} users\n├─ 🔢 Friend Accounts: {friend_counts}\n├─ 📋 FRIENDS DETAILS (Country-wise):\n"
            for i, friend in enumerate(friends_details, 1):
                new_message += f"│  ├─ {i}. {friend['name']}\n│  │  └─ Total Accounts: {friend['counts']}\n"
        new_message += f"├─ 💰 Total: ${total_usd:.2f} / {total_bdt:.0f} BDT\n"
        if payment_methods:
            new_message += f"├─ 💳 Payment Methods:\n"
            for method, data in payment_methods.items():
                payment_id = data.get('id', 'N/A')
                if len(payment_id) > 8:
                    masked_id = payment_id[:4] + "****" + payment_id[-4:]
                else:
                    masked_id = payment_id
                new_message += f"│  ├─ {method.upper()}: `{payment_id}`\n"
                if data.get('details'):
                    new_message += f"│  │  └─ {data['details'][:30]}\n"
            new_message += f"│  └─ ✅ Payment methods available!\n"
        else:
            new_message += f"├─ 💳 Payment: ❌ Not Provided\n"
        new_message += f"└─ 📅 {date_str}\n\n"
        if "⚠️ Added by:" in original_text:
            added_by_line = re.search(r'⚠️ Added by:.*', original_text)
            if added_by_line:
                new_message += added_by_line.group() + "\n\n"
        new_keyboard = []
        if has_earnings:
            if has_payment_method:
                for method in payment_methods.keys():
                    new_keyboard.append([InlineKeyboardButton(f"✅ {method.upper()} Payment Complete", callback_data=f"payment_complete_{user_id}_{method}_{date_str}")])
            else:
                new_keyboard.append([InlineKeyboardButton("✅ Payment Complete", callback_data=f"force_payment_complete_{user_id}_{date_str}")])
        new_keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_id}_{date_str}")])
        new_keyboard.append([InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")])
        reply_markup = InlineKeyboardMarkup(new_keyboard)
        try:
            await query.edit_message_text(new_message, reply_markup=reply_markup, parse_mode='Markdown')
            if has_payment_method:
                await query.answer(f"✅ Card updated! User has {len(payment_methods)} payment method(s)", show_alert=True)
            else:
                await query.answer("🔄 Card refreshed! User still has no payment method", show_alert=True)
        except:
            await query.edit_message_text(f"❌ Error refreshing card")

async def handle_payment_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('payment_complete_'):
        parts = data.split('_')
        if len(parts) >= 4:
            user_id = parts[2]
            method = parts[3]
            date_str = parts[4] if len(parts) > 4 else datetime.now().strftime('%Y-%m-%d')
            await complete_user_payment_with_method(query, context, user_id, date_str, method)
    elif data.startswith('payment_details_'):
        user_id = data.split('_')[2]
        await show_user_payment_details(query, context, user_id)

async def complete_user_payment_with_method(query, context, user_id, date_str, selected_method):
    await query.edit_message_text(f"🔄 Processing payment via {selected_method.upper()} for user {user_id}...")
    try:
        accounts = load_accounts()
        user_data = accounts.get(user_id, {})
        if not user_data:
            await query.edit_message_text(f"❌ User {user_id} not found!")
            return
        user_accounts = user_data.get("accounts", [])
        username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
        telegram_username = user_data.get('telegram_username', '')
        payment_methods = user_data.get('payment_methods', {})
        selected_payment = payment_methods.get(selected_method, {})
        if not selected_payment:
            await query.edit_message_text(f"❌ Payment method {selected_method.upper()} not found for this user!")
            return
        payment_id = selected_payment.get('id', 'N/A')
        original_text = query.message.text
        import re
        personal_earnings = 0
        friend_earnings = 0
        commission = 0
        total_usd = 0
        total_bdt = 0
        personal_count = 0
        friend_count = 0
        friends_details = []
        
        # 🔴 EXTRACT PERSONAL COUNTS
        personal_match = re.search(r'├─\s*🔢\s*Personal:\s*(\d+)\s+accounts?', original_text)
        if not personal_match:
            personal_match = re.search(r'├─\s*Personal:\s*(\d+)\s+accounts?', original_text)
        if not personal_match:
            personal_match = re.search(r'├─\s*🔢\s*Total\s*Personal:\s*(\d+)\s+accounts?', original_text)
        if not personal_match:
            personal_match = re.search(r'🔢\s*Personal\s*Counts?:\s*(\d+)', original_text)
        if not personal_match:
            country_section = re.search(r'├─\s*📊\s*PERSONAL\s*\(Country-wise\):(.*?)├─\s*🔢\s*Total\s*Personal:', original_text, re.DOTALL)
            if country_section:
                country_counts = re.findall(r'│\s*├─\s*\w+:\s*(\d+)\s+accounts?', country_section.group(1))
                if country_counts:
                    personal_count = sum(int(c) for c in country_counts)
        
        if personal_match and personal_count == 0:
            personal_count = int(personal_match.group(1))
        
        # Extract Personal Earnings
        earnings_match = re.search(r'accounts?\s*\(\$([\d\.]+)\)', original_text)
        if not earnings_match:
            earnings_match = re.search(r'Personal\s*Earnings?:\s*\$([\d\.]+)', original_text)
        if earnings_match:
            personal_earnings = float(earnings_match.group(1))
        
        # 🔴 EXTRACT FRIENDS DETAILS
        friends_section = re.search(r'├─\s*📋\s*FRIENDS DETAILS.*?(?=├─\s*💳|├─\s*💰\s*Total:|└─\s*💰\s*Total:|└─\s*📅|$)', original_text, re.DOTALL)
        if friends_section:
            friend_text = friends_section.group()
            friend_matches = re.findall(r'│\s*├─\s*\d+\.\s*([^\n@]+).*?Total\s*Accounts:\s*(\d+)', friend_text, re.DOTALL)
            for match in friend_matches:
                friend_name = match[0].strip()
                counts = int(match[1])
                earned_match = re.search(rf'{re.escape(friend_name)}.*?Earned:\s*\$([\d\.]+)', friend_text, re.DOTALL)
                friend_amount = float(earned_match.group(1)) if earned_match else counts * 0.09
                friends_details.append({
                    'name': friend_name, 
                    'telegram': '', 
                    'counts': counts, 
                    'amount': friend_amount, 
                    'commission': counts * 0.002
                })
                friend_count += 1
                friend_earnings += friend_amount
                commission += counts * 0.002
        
        # 🔴 EXTRACT GRAND TOTAL
        grand_total_match = re.search(r'├─\s*📊\s*GRAND TOTAL:\s*(\d+)\s+accounts', original_text)
        if grand_total_match:
            grand_total_count = int(grand_total_match.group(1))
        else:
            grand_total_count = personal_count + sum(f['counts'] for f in friends_details)
        
        # Extract totals
        total_match = re.search(r'├─\s*💰\s*Total:\s*\$([\d\.]+)\s*/\s*([\d\.]+)\s*BDT', original_text)
        if not total_match:
            total_match = re.search(r'└─\s*💰\s*Total:\s*\$([\d\.]+)\s*/\s*([\d\.]+)\s*BDT', original_text)
        if total_match:
            total_usd = float(total_match.group(1))
            total_bdt = float(total_match.group(2))
        
        if personal_earnings == 0 and total_usd > 0:
            personal_earnings = total_usd - friend_earnings - commission
        
        current_date = datetime.now().strftime('%d %B %Y')
        current_time = datetime.now().strftime('%H:%M:%S')
        masked_payment_id = payment_id
        if len(payment_id) > 8:
            masked_payment_id = payment_id[:4] + "****" + payment_id[-4:]
        
        # 🔴 USER NOTIFICATION - ALL DETAILS
        user_notification = f"✨ PAYMENT CONFIRMATION\n\n"
        user_notification += f"✅ Your payment has been processed!\n\n"
        user_notification += f"📅 {current_date}\n"
        user_notification += f"👤 {username}"
        if telegram_username:
            user_notification += f" (@{telegram_username})"
        user_notification += f"\n\n"
        
        user_notification += f"📊 DETAILS\n"
        
        # Personal
        user_notification += f"├─ 🔢 Personal Accounts: {personal_count}\n"
        if personal_earnings > 0:
            user_notification += f"├─ 💵 Personal Earnings: ${personal_earnings:.2f}\n"
        
        # Friends
        if friends_details:
            user_notification += f"├─ 👥 Friends: {len(friends_details)} users\n"
            user_notification += f"├─ 🔢 Friend Accounts: {sum(f['counts'] for f in friends_details)}\n"
            if friend_earnings > 0:
                user_notification += f"├─ 💰 Friends Earned: ${friend_earnings:.2f}\n"
        
        # Commission
        if commission > 0:
            user_notification += f"├─ 💸 Commission: ${commission:.2f}\n"
        
        # GRAND TOTAL
        user_notification += f"├─ 📊 GRAND TOTAL: {grand_total_count} accounts\n"
        
        # Friends details breakdown
        if friends_details:
            user_notification += f"│\n├─ 📋 FRIENDS DETAILS:\n"
            for i, friend in enumerate(friends_details, 1):
                friend_name = friend.get('name', 'Unknown')
                friend_counts = friend.get('counts', 0)
                friend_amount = friend.get('amount', 0)
                user_notification += f"│  ├─ {i}. {friend_name}\n"
                user_notification += f"│  │  ├─ Total Accounts: {friend_counts}\n"
                user_notification += f"│  │  └─ Earned: ${friend_amount:.2f}\n"
        
        # Total Amount
        user_notification += f"│\n└─ 💰 Total Amount: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        
        user_notification += f"💳 Payment Method Used:\n"
        user_notification += f"├─ Method: {selected_method.upper()}\n"
        user_notification += f"└─ ID: `{payment_id}`\n\n"
        
        user_notification += f"✅ Status: COMPLETED\n"
        user_notification += f"📨 Transaction ID: PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        user_notified = False
        try:
            await context.bot.send_message(int(user_id), user_notification, parse_mode='Markdown')
            user_notified = True
        except:
            pass
        
        # Friends notification
        friends_notified = 0
        for friend in friends_details:
            friend_user_id = None
            friend_name = friend['name']
            for acc_id, acc_data in accounts.items():
                if acc_id == str(ADMIN_ID):
                    continue
                acc_accounts = acc_data.get("accounts", [])
                if acc_accounts:
                    acc_username = acc_accounts[0].get('username', '')
                    acc_nickname = acc_accounts[0].get('nickname', '')
                    if friend_name.lower() in acc_username.lower() or friend_name.lower() in acc_nickname.lower():
                        friend_user_id = acc_id
                        break
            if friend_user_id and friend['amount'] > 0:
                friend_notification = f"📢 PAYMENT NOTIFICATION\n\n"
                friend_notification += f"👤 Friend: {username}"
                if telegram_username:
                    friend_notification += f" (@{telegram_username})"
                friend_notification += f"\n\n"
                friend_notification += f"💰 Your Share\n"
                friend_notification += f"├─ 🔢 Accounts: {friend.get('counts', 0)}\n"
                friend_notification += f"├─ 💵 USD: ${friend['amount']:.2f}\n"
                friend_notification += f"└─ 🇧🇩 BDT: {friend['amount'] * 125:.0f}\n\n"
                friend_notification += f"✅ Ready for collection!\n"
                friend_notification += f"📨 Contact your friend"
                try:
                    await context.bot.send_message(int(friend_user_id), friend_notification, parse_mode='none')
                    friends_notified += 1
                except:
                    pass
        
        # Update admin message
        lines = original_text.split('\n')
        new_lines = []
        for line in lines:
            if '[🔄 Payment Pending]' in line:
                new_lines.append(f"[✅ Completed via {selected_method.upper()} at {current_time}]")
            else:
                new_lines.append(line)
        updated_text = '\n'.join(new_lines)
        if "✅ Completed" not in updated_text:
            updated_text += f"\n\n✅ Payment Completed via {selected_method.upper()}"
        
        keyboard = [[InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(updated_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Admin confirmation
        confirmation = f"✅ PAYMENT COMPLETED\n\n"
        confirmation += f"👤 {username}"
        if telegram_username:
            confirmation += f" (@{telegram_username})"
        confirmation += f"\n🆔 `{user_id}`\n"
        confirmation += f"💰 ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
        confirmation += f"💳 Payment Method: {selected_method.upper()}\n"
        confirmation += f"🔢 ID: `{payment_id}`\n\n"
        confirmation += f"📊 Breakdown\n"
        confirmation += f"├─ Personal: {personal_count} accounts (${personal_earnings:.2f})\n"
        if friends_details:
            confirmation += f"├─ Friends: {len(friends_details)} users, {sum(f['counts'] for f in friends_details)} accounts (${friend_earnings:.2f})\n"
        if commission > 0:
            confirmation += f"├─ Commission: ${commission:.2f}\n"
        confirmation += f"└─ GRAND TOTAL: {grand_total_count} accounts\n\n"
        confirmation += f"📨 Notifications\n"
        confirmation += f"├─ User: {'✅' if user_notified else '❌'}\n"
        confirmation += f"└─ Friends: {friends_notified}\n\n"
        confirmation += f"⏰ {current_time}"
        await context.bot.send_message(ADMIN_ID, confirmation, parse_mode='Markdown')
        
        # Forward to group
        await forward_payment_confirmation_to_group(
            context=context,
            user_id=user_id,
            username=username,
            telegram_username=telegram_username,
            total_usd=total_usd,
            total_bdt=total_bdt,
            personal_count=personal_count,
            personal_earnings=personal_earnings,
            friend_count=friend_count,
            friend_earnings=friend_earnings,
            commission=commission,
            friends_details=friends_details,
            payment_method=selected_method,
            payment_id=masked_payment_id,
            is_fake=False
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

async def handle_force_payment_complete(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("force_payment_complete_"):
        parts = data.split("_")
        if len(parts) >= 5:
            user_id = parts[3]
            date_str = parts[4]
        else:
            await query.edit_message_text("❌ Invalid request!")
            return
        await query.edit_message_text(f"🔄 Processing payment for user {user_id}...")
        try:
            accounts = load_accounts()
            user_data = accounts.get(user_id, {})
            if not user_data:
                await query.edit_message_text(f"❌ User {user_id} not found!")
                return
            user_accounts = user_data.get("accounts", [])
            username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
            telegram_username = user_data.get('telegram_username', '')
            payment_methods = user_data.get('payment_methods', {})
            original_text = query.message.text
            import re
            personal_earnings = 0
            friend_earnings = 0
            commission = 0
            total_usd = 0
            total_bdt = 0
            personal_count = 0
            friend_count = 0
            friends_details = []
            
            # Extract Personal
            personal_match = re.search(r'├─\s*🔢\s*Personal:\s*(\d+)\s+accounts?', original_text)
            if not personal_match:
                personal_match = re.search(r'├─\s*Personal:\s*(\d+)\s+accounts?', original_text)
            if personal_match:
                personal_count = int(personal_match.group(1))
            
            earnings_match = re.search(r'accounts?\s*\(\$([\d\.]+)\)', original_text)
            if earnings_match:
                personal_earnings = float(earnings_match.group(1))
            
            # Extract Friends
            friends_section = re.search(r'├─\s*📋\s*FRIENDS DETAILS.*?(?=├─\s*💳|├─\s*💰\s*Total:|$)', original_text, re.DOTALL)
            if friends_section:
                friend_text = friends_section.group()
                friend_matches = re.findall(r'│\s*├─\s*\d+\.\s*([^\n@]+).*?Total\s*Accounts:\s*(\d+)', friend_text, re.DOTALL)
                for match in friend_matches:
                    friend_name = match[0].strip()
                    counts = int(match[1])
                    earned_match = re.search(rf'{re.escape(friend_name)}.*?Earned:\s*\$([\d\.]+)', friend_text, re.DOTALL)
                    friend_amount = float(earned_match.group(1)) if earned_match else counts * 0.09
                    friends_details.append({'name': friend_name, 'counts': counts, 'amount': friend_amount})
                    friend_count += 1
                    friend_earnings += friend_amount
                    commission += counts * 0.002
            
            # Extract GRAND TOTAL
            grand_total_match = re.search(r'├─\s*📊\s*GRAND TOTAL:\s*(\d+)\s+accounts', original_text)
            if grand_total_match:
                grand_total_count = int(grand_total_match.group(1))
            else:
                grand_total_count = personal_count + sum(f['counts'] for f in friends_details)
            
            # Extract Total
            total_match = re.search(r'├─\s*💰\s*Total:\s*\$([\d\.]+)\s*/\s*([\d\.]+)\s*BDT', original_text)
            if not total_match:
                total_match = re.search(r'└─\s*💰\s*Total:\s*\$([\d\.]+)\s*/\s*([\d\.]+)\s*BDT', original_text)
            if total_match:
                total_usd = float(total_match.group(1))
                total_bdt = float(total_match.group(2))
            
            selected_method = "bkash"
            payment_id = "No payment method added"
            if payment_methods:
                selected_method = list(payment_methods.keys())[0]
                payment_id = payment_methods[selected_method].get('id', 'N/A')
            
            current_date = datetime.now().strftime('%d %B %Y')
            current_time = datetime.now().strftime('%H:%M:%S')
            masked_payment_id = payment_id
            if len(payment_id) > 8 and payment_id != "No payment method added":
                masked_payment_id = payment_id[:4] + "****" + payment_id[-4:]
            
            # User notification
            user_notification = f"✨ PAYMENT CONFIRMATION\n\n"
            user_notification += f"✅ Your payment has been processed!\n\n"
            user_notification += f"📅 {current_date}\n"
            user_notification += f"👤 {username}"
            if telegram_username:
                user_notification += f" (@{telegram_username})"
            user_notification += f"\n\n"
            
            user_notification += f"📊 DETAILS\n"
            
            user_notification += f"├─ 🔢 Personal Accounts: {personal_count}\n"
            if personal_earnings > 0:
                user_notification += f"├─ 💵 Personal Earnings: ${personal_earnings:.2f}\n"
            
            if friends_details:
                user_notification += f"├─ 👥 Friends: {len(friends_details)} users\n"
                user_notification += f"├─ 🔢 Friend Accounts: {sum(f['counts'] for f in friends_details)}\n"
                if friend_earnings > 0:
                    user_notification += f"├─ 💰 Friends Earned: ${friend_earnings:.2f}\n"
            
            if commission > 0:
                user_notification += f"├─ 💸 Commission: ${commission:.2f}\n"
            
            user_notification += f"├─ 📊 GRAND TOTAL: {grand_total_count} accounts\n"
            
            if friends_details:
                user_notification += f"│\n├─ 📋 FRIENDS DETAILS:\n"
                for i, friend in enumerate(friends_details, 1):
                    friend_name = friend.get('name', 'Unknown')
                    friend_counts = friend.get('counts', 0)
                    friend_amount = friend.get('amount', 0)
                    user_notification += f"│  ├─ {i}. {friend_name}\n"
                    user_notification += f"│  │  ├─ Total Accounts: {friend_counts}\n"
                    user_notification += f"│  │  └─ Earned: ${friend_amount:.2f}\n"
            
            user_notification += f"│\n└─ 💰 Total Amount: ${total_usd:.2f} / {total_bdt:.0f} BDT\n\n"
            
            user_notification += f"💳 Payment Method Used:\n"
            user_notification += f"├─ Method: {selected_method.upper()}\n"
            user_notification += f"└─ ID: `{payment_id}`\n\n"
            
            if not payment_methods:
                user_notification += f"⚠️ আপনার কোনো পেমেন্ট মেথড যোগ করা নেই!\n"
                user_notification += f"✅ অনুগ্রহ করে /wallet কমান্ড ব্যবহার করে পেমেন্ট মেথড যোগ করুন।\n\n"
            
            user_notification += f"✅ Status: COMPLETED\n"
            user_notification += f"📨 Transaction ID: PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            user_notified = False
            try:
                await context.bot.send_message(int(user_id), user_notification, parse_mode='Markdown')
                user_notified = True
            except:
                pass
            
            lines = original_text.split('\n')
            new_lines = []
            for line in lines:
                if '[🔄 Payment Pending]' in line:
                    new_lines.append(f"[✅ Payment Completed at {current_time}]")
                else:
                    new_lines.append(line)
            updated_text = '\n'.join(new_lines)
            if "✅ Payment Completed" not in updated_text:
                updated_text += f"\n\n✅ Payment Completed at {current_time}"
            
            keyboard = [
                [InlineKeyboardButton("📋 Details", callback_data=f"payment_details_{user_id}")],
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_card_{user_id}_{date_str}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(updated_text, reply_markup=reply_markup, parse_mode='Markdown')
            
            await forward_payment_confirmation_to_group(
                context=context,
                user_id=user_id,
                username=username,
                telegram_username=telegram_username,
                total_usd=total_usd,
                total_bdt=total_bdt,
                personal_count=personal_count,
                personal_earnings=personal_earnings,
                friend_count=friend_count,
                friend_earnings=friend_earnings,
                commission=commission,
                friends_details=friends_details,
                payment_method=selected_method,
                payment_id=masked_payment_id,
                is_fake=False
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")

async def show_user_payment_details(query, context, user_id):
    await query.answer("Fetching details...")
    accounts = load_accounts()
    user_data = accounts.get(user_id, {})
    if not user_data:
        await query.edit_message_text(f"❌ User {user_id} not found!")
        return
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    telegram_username = user_accounts[0].get('telegram_username', '') if user_accounts else ''
    details = f"📋 Payment Details for {username}\n\n🆔 User ID: {user_id}\n👤 Telegram: @{telegram_username if telegram_username else 'N/A'}\n📱 Accounts: {len(user_accounts)}\n⏰ Last Active: {user_data.get('last_active', 'N/A')}\n\n🔐 Account Information:\n"
    for i, acc in enumerate(user_accounts, 1):
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        details += f"{i}. {status}{login_status} {acc.get('custom_name', acc['username'])}\n"
    keyboard = [[InlineKeyboardButton("❌ Close", callback_data="close_details")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(details, reply_markup=reply_markup, parse_mode='none')

async def add_payment_method(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("💳 ADD PAYMENT METHOD (Admin)\n\nUsage: `/addpayment [user_id] [method] [id] [details]`\n\nMethods: bkash, nagad, rocket, binance")
        return
    target_user_id = context.args[0]
    method = context.args[1].lower()
    payment_id = context.args[2]
    details = ' '.join(context.args[3:]) if len(context.args) > 3 else ''
    valid_methods = ['bkash', 'nagad', 'rocket', 'binance']
    if method not in valid_methods:
        await update.message.reply_text(f"❌ Invalid method! Use: {', '.join(valid_methods)}")
        return
    accounts = load_accounts()
    if target_user_id not in accounts:
        accounts[target_user_id] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat(), "payment_methods": {}}
    if not isinstance(accounts[target_user_id], dict):
        accounts[target_user_id] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat(), "payment_methods": {}}
    if "payment_methods" not in accounts[target_user_id]:
        accounts[target_user_id]["payment_methods"] = {}
    accounts[target_user_id]["payment_methods"][method] = {"id": payment_id, "details": details, "added_by": ADMIN_ID, "added_at": datetime.now().isoformat()}
    save_accounts(accounts)
    user_accounts = accounts[target_user_id].get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    masked_id = payment_id
    if len(payment_id) > 8:
        masked_id = payment_id[:4] + "****" + payment_id[-4:]
    await update.message.reply_text(f"✅ PAYMENT METHOD ADDED\n\n👤 User: {username}\n🆔 ID: `{target_user_id}`\n\n💰 Method: {method.upper()}\n🔢 Full ID: `{payment_id}`\n🔒 Masked: `{masked_id}`\n{f'📝 Details: {details}' if details else ''}\n\n📅 Added: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", parse_mode='Markdown')
    try:
        user_notification = f"💳 PAYMENT METHOD ADDED BY ADMIN\n\n💰 Method: {method.upper()}\n🔢 ID: `{masked_id}`\n{f'📝 Details: {details}' if details else ''}\n\n✅ Your payment method has been added successfully!"
        await context.bot.send_message(int(target_user_id), user_notification, parse_mode='Markdown')
    except:
        pass

async def remove_payment_method(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ REMOVE PAYMENT METHOD (Admin)\n\nUsage: `/removepayment [user_id] [method]`")
        return
    target_user_id = context.args[0]
    method = context.args[1].lower()
    accounts = load_accounts()
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    if "payment_methods" not in accounts[target_user_id]:
        await update.message.reply_text(f"❌ No payment methods found for this user!")
        return
    if method not in accounts[target_user_id]["payment_methods"]:
        available = ', '.join(accounts[target_user_id]["payment_methods"].keys())
        await update.message.reply_text(f"❌ Method '{method}' not found!\n\nAvailable: {available}")
        return
    removed_data = accounts[target_user_id]["payment_methods"].pop(method)
    save_accounts(accounts)
    user_accounts = accounts[target_user_id].get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    await update.message.reply_text(f"✅ PAYMENT METHOD REMOVED\n\n👤 User: {username}\n🆔 ID: `{target_user_id}`\n\n💰 Removed: {method.upper()}\n🔢 ID: `{removed_data.get('id', 'N/A')}`\n\n📅 Removed: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", parse_mode='Markdown')

async def list_payment_methods(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args:
        await update.message.reply_text("📋 LIST PAYMENT METHODS (Admin)\n\nUsage: `/listpayment [user_id]`")
        return
    target_user_id = context.args[0]
    accounts = load_accounts()
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    user_data = accounts[target_user_id]
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    telegram_username = user_data.get('telegram_username', '')
    payment_methods = user_data.get("payment_methods", {})
    if not payment_methods:
        await update.message.reply_text(f"📋 PAYMENT METHODS\n\n👤 User: {username}\n🆔 ID: `{target_user_id}`\n📱 Telegram: @{telegram_username if telegram_username else 'N/A'}\n\n❌ No payment methods found!", parse_mode='Markdown')
        return
    message = f"📋 PAYMENT METHODS (Full View - Admin Only)\n\n👤 User: {username}\n🆔 ID: `{target_user_id}`\n📱 Telegram: @{telegram_username if telegram_username else 'N/A'}\n\n💰 Available Methods ({len(payment_methods)}):\n"
    for i, (method, data) in enumerate(payment_methods.items(), 1):
        payment_id = data.get('id', 'N/A')
        message += f"\n{i}. {method.upper()}\n   ├─ Full ID: `{payment_id}`\n"
        if data.get('details'):
            message += f"   ├─ Details: {data.get('details')}\n"
        message += f"   ├─ Added by: {'Admin' if data.get('added_by') == ADMIN_ID else 'User'}\n   └─ Added: {data.get('added_at', 'N/A')[:10]}\n"
    await update.message.reply_text(message, parse_mode='Markdown')

async def clear_payment_methods(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args:
        await update.message.reply_text("🗑️ CLEAR PAYMENT METHODS (Admin)\n\nUsage: `/clearpayment [user_id]`")
        return
    target_user_id = context.args[0]
    accounts = load_accounts()
    if target_user_id not in accounts:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
        return
    user_data = accounts[target_user_id]
    user_accounts = user_data.get("accounts", [])
    username = user_accounts[0].get('username', 'Unknown') if user_accounts else 'Unknown'
    old_methods = user_data.get("payment_methods", {})
    count = len(old_methods)
    if count == 0:
        await update.message.reply_text(f"❌ No payment methods to clear for user {username}!")
        return
    method_names = ', '.join(old_methods.keys())
    user_data["payment_methods"] = {}
    accounts[target_user_id] = user_data
    save_accounts(accounts)
    await update.message.reply_text(f"✅ ALL PAYMENT METHODS CLEARED\n\n👤 User: {username}\n🆔 ID: `{target_user_id}`\n\n🗑️ Removed {count} method(s): {method_names.upper()}\n\n📅 Cleared: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", parse_mode='Markdown')

async def admin_add_account(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("❌ Usage: `/addacc user_id username password`\nExample: `/addacc 123456789 user1 pass1`")
        return
    try:
        target_user_id = context.args[0]
        username = context.args[1]
        password = context.args[2]
        processing_msg = await update.message.reply_text(f"🔄 Verifying account `{username}`...")
        token, api_user_id, nickname = await login_api_async(username, password)
        if not token:
            await processing_msg.edit_text(f"❌ Login failed for `{username}`! Please check credentials.")
            return
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        if user_id_str not in accounts:
            accounts[user_id_str] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            user_data = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
        account_exists = False
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                acc['password'] = password
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                acc['active'] = True
                account_exists = True
                break
        if not account_exists:
            new_id = len(user_data.get("accounts", [])) + 1
            user_data["accounts"].append({'id': new_id, 'custom_name': username, 'username': username, 'password': password, 'token': token, 'api_user_id': api_user_id, 'nickname': nickname, 'last_login': datetime.now().isoformat(), 'active': True, 'default': (new_id == 1), 'added_by': update.effective_user.id, 'added_at': datetime.now().isoformat(), 'telegram_username': '', 'friends': []})
        accounts[user_id_str] = user_data
        save_accounts(accounts)
        if user_id_str in account_manager.user_tokens:
            await account_manager.initialize_user(int(target_user_id))
        await processing_msg.edit_text(f"✅ Account added successfully!\n\n👤 User ID: `{target_user_id}`\n📛 Username: `{username}`\n🔑 Password: `{password}`\n🆔 API User ID: `{api_user_id or 'N/A'}`\n✅ Auto-login: Successful")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_start_bot_now(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "start_bot_now":
        try:
            await query.delete_message()
            user_id = query.from_user.id
            active_accounts = await account_manager.initialize_user(user_id)
            if user_id == ADMIN_ID:
                keyboard = [[KeyboardButton("➕ Add Account"), KeyboardButton("📋 List Accounts")], [KeyboardButton("🚀 Refresh Server"), KeyboardButton("💰 Set Rate")], [KeyboardButton("📊 Statistics"), KeyboardButton("📱 Switch Account")]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                remaining = account_manager.get_user_remaining_checks(user_id)
                active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
                selected_account = account_manager.get_selected_account_name(user_id)
                await query.message.reply_text(f"🔥 WA OTP Bot 👑\n\n📱 Active Account: {selected_account}\n✅ Active Login: {active_accounts_count}\n🎯 Remaining Checks: {remaining}\n\n💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n✨ Welcome Admin! ✨", reply_markup=reply_markup, parse_mode='none')
                return
            keyboard = [[KeyboardButton("🚀 Refresh Server"), KeyboardButton("📱 Switch Account")], [KeyboardButton("📦 My Settlements"), KeyboardButton("📊 Statistics")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            remaining = account_manager.get_user_remaining_checks(user_id)
            active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
            selected_account = account_manager.get_selected_account_name(user_id)
            if active_accounts == 0:
                await query.message.reply_text(f"❌ Access Denied!\n\nএক্সেস শুধুমাত্র সিরিয়াস ইউজারদের জন্য।\nআপনার কাজের উদ্দেশ্য সংক্ষেপে উল্লেখ করুন।\n\nআপনার কাছে কোনো দেশের WhatsApp অ্যাকাউন্ট থাকলে বা কাজ করার অভিজ্ঞতা থাকলে এক্সেসের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।\n\n👤 Admin: @Notfound_errorx", reply_markup=reply_markup, parse_mode='none')
                return
            await query.message.reply_text(f"🔥 WA OTP Bot 🔥\n\n📱 Active Account: {selected_account}\n✅ Active Login: {active_accounts_count}\n🎯 Remaining Checks: {remaining}\n\n💡 OTP Tip: Reply to any 'In Progress' number with OTP code\n\n✨ Welcome! Start checking numbers now! ✨", reply_markup=reply_markup, parse_mode='none')
        except:
            await query.message.reply_text("✅ Membership Verified!\n\nPlease use /start command to access the bot.", parse_mode='none')

async def admin_remove_account(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if context.args and len(context.args) >= 2:
        target_user_id = context.args[0]
        username = context.args[1]
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        if user_id_str not in accounts:
            await update.message.reply_text(f"❌ User `{target_user_id}` not found!", parse_mode='Markdown')
            return
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            await update.message.reply_text(f"❌ No accounts found for user `{target_user_id}`", parse_mode='Markdown')
            return
        removed = False
        new_accounts = []
        removed_account_name = None
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                removed = True
                removed_account_name = acc.get('custom_name', acc['username'])
                if acc.get('token') and acc['token'] in account_manager.token_info:
                    del account_manager.token_info[acc['token']]
                if acc.get('token') and acc['token'] in account_manager.token_owners:
                    del account_manager.token_owners[acc['token']]
            else:
                new_accounts.append(acc)
        if removed:
            user_data["accounts"] = new_accounts
            if len(new_accounts) == 0:
                if user_id_str in account_manager.user_tokens:
                    del account_manager.user_tokens[user_id_str]
                if user_id_str in account_manager.user_selected_accounts:
                    del account_manager.user_selected_accounts[user_id_str]
                del accounts[user_id_str]
                save_accounts(accounts)
                await update.message.reply_text(f"✅ User removed successfully!\n\n👤 User ID: `{target_user_id}`\n📛 Username: `{username}`\n🗑️ All accounts removed!")
            else:
                selected_id = user_data.get("selected_account_id", 1)
                if selected_id and removed:
                    user_data["selected_account_id"] = new_accounts[0]['id']
                accounts[user_id_str] = user_data
                save_accounts(accounts)
                if user_id_str in account_manager.user_tokens:
                    await account_manager.initialize_user(int(target_user_id))
                await update.message.reply_text(f"✅ Account removed successfully!\n\n👤 User ID: `{target_user_id}`\n📛 Username: `{username}`\n🗑️ Removed: {removed_account_name}\n📊 Remaining accounts: {len(new_accounts)}")
        else:
            await update.message.reply_text(f"❌ Account `{username}` not found for user `{target_user_id}`", parse_mode='Markdown')
        return
    await show_all_users_with_accounts(update, context)

async def show_all_users_with_accounts(update: Update, context: CallbackContext, page: int = 0):
    accounts = load_accounts()
    users_list = []
    for user_id_str, user_data in accounts.items():
        if user_id_str == str(ADMIN_ID):
            continue
        if not isinstance(user_data, dict):
            continue
        user_accounts = user_data.get("accounts", [])
        if not user_accounts:
            continue
        first_account = user_accounts[0] if user_accounts else {}
        api_username = first_account.get('username', 'Unknown')
        full_name = user_data.get('full_name', '')
        if not full_name:
            full_name = f"User {user_id_str[-6:]}"
        display_name = full_name if full_name else f"User {user_id_str[-6:]}"
        users_list.append({'user_id': user_id_str, 'display_name': display_name, 'api_username': api_username, 'account_count': len(user_accounts), 'accounts': user_accounts})
    if not users_list:
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text("✅ No users with accounts found!")
        else:
            await update.message.reply_text("✅ No users with accounts found!")
        return
    users_list.sort(key=lambda x: x['display_name'])
    items_per_chunk = 90
    total_chunks = (len(users_list) + items_per_chunk - 1) // items_per_chunk
    if total_chunks > 1:
        context.user_data['remove_users_list'] = users_list
        context.user_data['remove_total_chunks'] = total_chunks
        context.user_data['remove_current_chunk'] = page
        start_idx = page * items_per_chunk
        end_idx = min(start_idx + items_per_chunk, len(users_list))
        chunk = users_list[start_idx:end_idx]
        message = f"🗑️ REMOVE USER ACCOUNTS\n\n📊 Total users: {len(users_list)}\n📄 Message {page + 1}/{total_chunks}\n📋 Showing: {start_idx + 1} - {end_idx}\n\n⚠️ Click on a user to see their accounts\n\n"
        keyboard = []
        for user in chunk:
            button_text = f"👤 {user['display_name']}"
            if user['api_username'] != 'Unknown':
                button_text += f" (@{user['api_username']})"
            if user['account_count'] > 1:
                button_text += f" [{user['account_count']}]"
            callback_data = f"view_user_acc_{user['user_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"remove_chunk_{page - 1}"))
        if page < total_chunks - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"remove_chunk_{page + 1}"))
        if nav_buttons:
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')
    else:
        message = f"🗑️ REMOVE USER ACCOUNTS\n\n📊 Total users: {len(users_list)}\n\n⚠️ Click on a user to see their accounts\n\n"
        keyboard = []
        for user in users_list:
            button_text = f"👤 {user['display_name']}"
            if user['api_username'] != 'Unknown':
                button_text += f" (@{user['api_username']})"
            if user['account_count'] > 1:
                button_text += f" [{user['account_count']}]"
            callback_data = f"view_user_acc_{user['user_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        if isinstance(update, Update) and hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')

async def handle_remove_chunk(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("remove_chunk_"):
        page = int(data.split("_")[2])
        await show_all_users_with_accounts(update, context, page)

async def view_user_accounts(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("view_user_acc_"):
        user_id_str = data.replace("view_user_acc_", "")
        accounts = load_accounts()
        if user_id_str not in accounts:
            await query.edit_message_text(f"❌ User not found!")
            return
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            await query.edit_message_text(f"❌ Invalid user data!")
            return
        user_accounts = user_data.get("accounts", [])
        account_count = len(user_accounts)
        first_account = user_accounts[0] if user_accounts else {}
        api_username = first_account.get('username', 'Unknown')
        display_name = user_data.get('full_name', f"User {user_id_str[-6:]}")
        message = f"👤 USER: {display_name}\n🆔 ID: `{user_id_str}`\n📛 API: {api_username}\n📊 Total: {account_count} account(s)\n\n"
        if account_count == 0:
            message += f"❌ No accounts found!\n"
            keyboard = [[InlineKeyboardButton("🔙 Back to Users", callback_data="back_to_users_list")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return
        message += f"📋 ACCOUNTS:\n\n"
        keyboard = []
        for i, acc in enumerate(user_accounts, 1):
            account_id = acc.get('id', i)
            account_name = acc.get('custom_name', f"Account {account_id}")
            account_username = acc.get('username', 'Unknown')
            account_status = "✅" if acc.get('active', True) else "❌"
            token_status = "🔓" if acc.get('token') else "🔒"
            message += f"{i}. {account_status}{token_status} {account_name}\n   └─ @{account_username}\n\n"
            button_text = f"🗑️ Remove {account_name}"
            callback_data = f"remove_single_acc_{user_id_str}_{account_id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        if account_count > 1:
            keyboard.append([InlineKeyboardButton("🗑️ Remove ALL Accounts", callback_data=f"remove_all_accs_{user_id_str}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Users", callback_data="back_to_users_list")])
        keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_remove_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['current_user_id'] = user_id_str
        if len(message) > 3500:
            await query.edit_message_text(message[:3500], reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def remove_single_account_from_list(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("remove_single_acc_"):
        parts = data.split("_")
        user_id_str = parts[3]
        account_id = int(parts[4])
        accounts = load_accounts()
        if user_id_str not in accounts:
            await query.answer("User not found!", show_alert=True)
            return
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            await query.answer("Invalid user data!", show_alert=True)
            return
        user_accounts = user_data.get("accounts", [])
        account_removed = None
        new_accounts = []
        for acc in user_accounts:
            if acc.get('id') == account_id:
                account_removed = acc
                if acc.get('token') and acc['token'] in account_manager.token_info:
                    del account_manager.token_info[acc['token']]
                if acc.get('token') and acc['token'] in account_manager.token_owners:
                    del account_manager.token_owners[acc['token']]
            else:
                new_accounts.append(acc)
        if not account_removed:
            await query.answer("Account not found!", show_alert=True)
            return
        account_name = account_removed.get('custom_name', f"Account {account_id}")
        user_data["accounts"] = new_accounts
        selected_id = user_data.get("selected_account_id", 1)
        if selected_id == account_id and new_accounts:
            user_data["selected_account_id"] = new_accounts[0]['id']
        if len(new_accounts) == 0:
            if user_id_str in account_manager.user_tokens:
                del account_manager.user_tokens[user_id_str]
            if user_id_str in account_manager.user_selected_accounts:
                del account_manager.user_selected_accounts[user_id_str]
            del accounts[user_id_str]
            save_accounts(accounts)
            await query.answer(f"✅ {account_name} removed! User has no more accounts.", show_alert=True)
            await show_all_users_with_accounts(update, context, 0)
            return
        else:
            accounts[user_id_str] = user_data
            save_accounts(accounts)
            if user_id_str in account_manager.user_tokens:
                await account_manager.initialize_user(int(user_id_str))
            await query.answer(f"✅ {account_name} removed successfully!", show_alert=True)
        await view_user_accounts(update, context)

async def remove_all_accounts_from_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("remove_all_accs_"):
        user_id_str = data.replace("remove_all_accs_", "")
        accounts = load_accounts()
        if user_id_str not in accounts:
            await query.answer("User not found!", show_alert=True)
            return
        user_data = accounts[user_id_str]
        user_accounts = user_data.get("accounts", [])
        account_count = len(user_accounts)
        if user_id_str in account_manager.user_tokens:
            for token in account_manager.user_tokens[user_id_str]:
                if token in account_manager.token_info:
                    del account_manager.token_info[token]
                if token in account_manager.token_owners:
                    del account_manager.token_owners[token]
            del account_manager.user_tokens[user_id_str]
        if user_id_str in account_manager.user_selected_accounts:
            del account_manager.user_selected_accounts[user_id_str]
        del accounts[user_id_str]
        save_accounts(accounts)
        await query.answer(f"✅ All {account_count} accounts removed!", show_alert=True)
        await show_all_users_with_accounts(update, context, 0)

async def back_to_users_list(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await show_all_users_with_accounts(update, context, 0)

async def close_remove_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Menu closed!")

async def admin_list_accounts(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    accounts = load_accounts()
    if not accounts:
        await update.message.reply_text("❌ No accounts in database!")
        return
    message = "📋 All User Accounts 👑\n\n"
    for user_id_str, user_data in accounts.items():
        if not isinstance(user_data, dict):
            continue
        user_accounts = user_data.get("accounts", [])
        message += f"👤 User ID: {user_id_str}\n📊 Total Accounts: {len(user_accounts)}\n"
        active_accounts = len([acc for acc in user_accounts if acc.get('active', True)])
        logged_in_accounts = account_manager.get_user_active_accounts_count(int(user_id_str))
        message += f"✅ Active: {active_accounts} | 🔓 Logged In: {logged_in_accounts}\n"
        for i, acc in enumerate(user_accounts, 1):
            status = "✅" if acc.get('active', True) else "❌"
            login_status = "🔓" if acc.get('token') else "🔒"
            nickname = acc.get('nickname', 'N/A')
            api_user_id = acc.get('api_user_id', 'N/A')
            message += f"  {i}. {status}{login_status} {acc['username']} ({nickname}) [ID: {api_user_id[:8] if api_user_id != 'N/A' else 'N/A'}]\n"
        message += "───\n"
    await update.message.reply_text(message)

async def handle_settlement_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('settlement_'):
        if data.startswith('settlement_refresh_'):
            page = int(data.split('_')[2])
        else:
            page = int(data.split('_')[1])
        user_id = query.from_user.id
        user_id_str = str(user_id)
        if user_id_str not in account_manager.user_tokens or not account_manager.user_tokens[user_id_str]:
            await query.edit_message_text("❌ No active accounts found!")
            return
        token = account_manager.user_tokens[user_id_str][0]
        api_user_id = account_manager.get_api_user_id_for_token(token)
        if not api_user_id:
            await query.edit_message_text("❌ Could not find your API user ID.\n\nPlease refresh your accounts by clicking '🚀 Refresh Server' button first.")
            return
        async with aiohttp.ClientSession() as session:
            data_result, error = await get_user_settlements(session, token, str(api_user_id), page=page, page_size=5)
        if error:
            await query.edit_message_text(f"❌ Error loading settlements: {error}")
            return
        if not data_result or not data_result.get('records'):
            await query.edit_message_text("❌ No settlement records found for your account!")
            return
        records = data_result.get('records', [])
        total_records = data_result.get('total', 0)
        total_pages = data_result.get('pages', 1)
        total_count = 0
        total_amount = 0
        for record in records:
            count = record.get('count', 0)
            record_rate = record.get('receiptPrice', 0.10)
            total_count += count
            total_amount += count * record_rate
        message = f"📦 Your Settlement Records\n\n📊 Total Records: {total_records}\n🔢 Total Count: {total_count}\n📄 Page: {page}/{total_pages}\n\n"
        for i, record in enumerate(records, 1):
            record_id = record.get('id', 'N/A')
            if record_id != 'N/A' and len(str(record_id)) > 8:
                record_id = str(record_id)[:8] + '...'
            count = record.get('count', 0)
            record_rate = record.get('receiptPrice', 0.10)
            amount = count * record_rate
            gmt_create = record.get('gmtCreate', 'N/A')
            country = record.get('countryName', 'N/A') or record.get('country', 'N/A')
            try:
                if gmt_create != 'N/A':
                    if 'T' in gmt_create:
                        date_obj = datetime.fromisoformat(gmt_create.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(gmt_create, '%Y-%m-%d %H:%M:%S')
                    formatted_date = date_obj.strftime('%d %B %Y, %H:%M')
                else:
                    formatted_date = 'N/A'
            except:
                formatted_date = gmt_create
            message += f"{i}. Settlement #{record_id}\n📅 Date: {formatted_date}\n🌍 Country: {country}\n🔢 Count: {count}\n\n"
        keyboard = []
        row = []
        if page > 1:
            row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settlement_{page-1}"))
        if page < total_pages:
            if not row:
                row = []
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"settlement_{page+1}"))
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"settlement_refresh_{page}")])
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await query.edit_message_text(message, parse_mode='none')

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    try:
        user = update.effective_user
        current_time = datetime.now().strftime('%d %B %Y, %H:%M:%S')
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        channel_status = "✅ Joined" if channel_joined else "❌ Not Joined"
        group_status = "✅ Joined" if group_joined else "❌ Not Joined"
        user_info = f"🆕 USER STARTED BOT 🆕\n\n👤 Name: {user.full_name or 'N/A'}\n🆔 ID: `{user.id}`\n📛 Username: @{user.username if user.username else 'N/A'}\n📅 Time: {current_time}\n\n🔓 MEMBERSHIP STATUS:\n📢 Channel: {channel_status}\n💰 Group: {group_status}\n\n📍 Status: {'✅ Full Access' if (channel_joined and group_joined) else '⚠️ Restricted Access'}"
        await context.bot.send_message(chat_id="@Wsalluser", text=user_info, parse_mode='Markdown')
    except:
        pass
    channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
    if not (channel_joined and group_joined):
        keyboard = []
        if not channel_joined:
            keyboard.append([InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)])
        if not group_joined:
            keyboard.append([InlineKeyboardButton("💰 Join Payment Group", url=PAYMENT_GROUP_INVITE_LINK)])
        keyboard.append([InlineKeyboardButton("🔄 Check Membership", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
        group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
        missing_text = ", ".join(missing)
        await update.message.reply_text(f"🔒 ACCESS RESTRICTED\n\nTo use this bot, join:\n\n📢 Channel: {REQUIRED_CHANNEL}\n└─ {channel_status}\n\n💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n└─ {group_status}\n\nMissing: {missing_text}\n\n👇 Join then click 'Check Membership'", reply_markup=reply_markup, parse_mode='none')
        return
    active_accounts = await account_manager.initialize_user(user_id)
    if user_id == ADMIN_ID:
        keyboard = [[KeyboardButton("➕ Add Account"), KeyboardButton("📋 List Accounts")], [KeyboardButton("🚀 Refresh Server"), KeyboardButton("💰 Set Rate")], [KeyboardButton("📊 Statistics"), KeyboardButton("📱 Switch Account")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        remaining = account_manager.get_user_remaining_checks(user_id)
        active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
        selected_account = account_manager.get_selected_account_name(user_id)
        await update.message.reply_text(f"🔥 WA OTP BOT\n\n📱 {selected_account}\n✅ {active_accounts_count} active\n🎯 {remaining} remaining\n\n💡 Reply to 'In Progress' with OTP\n\n👑 Admin Mode", reply_markup=reply_markup, parse_mode='none')
        return
    keyboard = [[KeyboardButton("🚀 Refresh Server"), KeyboardButton("📱 Switch Account")], [KeyboardButton("📦 My Settlements"), KeyboardButton("📊 Statistics")], [KeyboardButton("💳 Wallet")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    remaining = account_manager.get_user_remaining_checks(user_id)
    active_accounts_count = account_manager.get_user_active_accounts_count(user_id)
    selected_account = account_manager.get_selected_account_name(user_id)
    if active_accounts == 0:
        await update.message.reply_text(f"❌ Access Denied!\n\nএক্সেস শুধুমাত্র সিরিয়াস ইউজারদের জন্য।\nআপনার কাজের উদ্দেশ্য সংক্ষেপে উল্লেখ করুন।\n\nআপনার কাছে কোনো দেশের WhatsApp অ্যাকাউন্ট থাকলে বা কাজ করার অভিজ্ঞতা থাকলে এক্সেসের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।\n\n👤 Admin: @Notfound_errorx", reply_markup=reply_markup, parse_mode='none')
        return
    await update.message.reply_text(f"🔥 WA OTP BOT\n\n📱 {selected_account}\n✅ {active_accounts_count} active\n🎯 {remaining} remaining\n\n💡 Reply to 'In Progress' with OTP\n\n✨ Welcome!", reply_markup=reply_markup, parse_mode='none')

async def handle_membership_check(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "check_membership":
        user_id = query.from_user.id
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        if channel_joined and group_joined:
            new_text = "✅ Membership Verified!\n\n🎉 Congratulations! You have successfully joined:\n📢 {REQUIRED_CHANNEL}\n💰 {REQUIRED_PAYMENT_GROUP}\n\n✨ Access Granted! ✨\n\nNow please use /start command again to access the bot.\n\n👇 Click below to start:"
            new_reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Start Bot", callback_data="start_bot_now")]])
            current_text = query.message.text
            current_markup = query.message.reply_markup
            if current_text != new_text or current_markup != new_reply_markup:
                await query.edit_message_text(new_text, reply_markup=new_reply_markup, parse_mode='none')
            else:
                await query.answer("Already verified! Click Start Bot to continue.")
        else:
            keyboard = []
            if not channel_joined:
                keyboard.append([InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)])
            if not group_joined:
                keyboard.append([InlineKeyboardButton("💰 Join Payment Group", url=PAYMENT_GROUP_INVITE_LINK)])
            keyboard.append([InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")])
            new_reply_markup = InlineKeyboardMarkup(keyboard)
            channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
            group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
            missing_text = ", ".join(missing)
            new_text = f"🔒 Membership Required 🔒\n\nTo access this bot, please join both:\n\n📢 Channel: {REQUIRED_CHANNEL}\n└─ Status: {channel_status}\n\n💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n└─ Status: {group_status}\n\nMissing: {missing_text}\n\n👇 Click the buttons below to join 👇\nThen click 'Check Again' to verify."
            current_text = query.message.text
            current_markup = query.message.reply_markup
            if current_text != new_text or current_markup != new_reply_markup:
                await query.edit_message_text(new_text, reply_markup=new_reply_markup, parse_mode='none')
            else:
                await query.answer("Please join the required channel/group first!")

async def check_membership_requirements(context: CallbackContext, user_id: int) -> tuple:
    channel_joined = False
    group_joined = False
    missing = []
    try:
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status in allowed_status:
                channel_joined = True
            else:
                missing.append("Channel")
        except:
            missing.append("Channel")
        try:
            group_member = await context.bot.get_chat_member(chat_id=REQUIRED_PAYMENT_GROUP, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if group_member.status in allowed_status:
                group_joined = True
            else:
                missing.append("Payment Group")
        except:
            missing.append("Payment Group")
        return channel_joined, group_joined, missing
    except:
        return False, False, ["Channel", "Payment Group"]

async def show_accounts_menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict) or not user_data.get("accounts"):
        await update.message.reply_text("❌ No accounts found!\n\nPlease contact admin to add accounts for you.\nAdmin: @Notfound_errorx")
        return
    user_accounts = user_data["accounts"]
    selected_id = user_data.get("selected_account_id", 1)
    message = "📱 Your Accounts 📱\n\nSelect an account to use:\n\n"
    keyboard = []
    for acc in user_accounts:
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        selected_mark = " 👑" if acc['id'] == selected_id else ""
        message += f"{status}{login_status} {acc['custom_name']}\n   └─ 👤 Username: {acc['username']}\n   └─ 🆔 ID: {acc.get('api_user_id', 'N/A')[:8]}...{selected_mark}\n\n"
        callback_data = f"select_account_{acc['id']}"
        keyboard.append([InlineKeyboardButton(f"{acc['custom_name']}{selected_mark}", callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_accounts")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='none')

async def handle_account_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_id_str = str(user_id)
    if data == "close_accounts_menu":
        await query.delete_message()
        return
    if data == "refresh_all_accounts":
        await query.edit_message_text("🔄 Refreshing all accounts...")
        await refresh_user_accounts(user_id)
        accounts = load_accounts()
        user_data = accounts.get(user_id_str, {})
        user_accounts = user_data.get("accounts", [])
        selected_id = user_data.get("selected_account_id", 1)
        message = "✅ Accounts Refreshed ✅\n\nUpdated accounts:\n\n"
        for acc in user_accounts:
            status = "✅" if acc.get('active', True) else "❌"
            login_status = "🔓" if acc.get('token') else "🔒"
            selected_mark = " 👑" if acc['id'] == selected_id else ""
            message += f"{status}{login_status} {acc['custom_name']}\n   └─ 👤 Username: {acc['username']}{selected_mark}\n\n"
        keyboard = [[InlineKeyboardButton("📱 Select Account", callback_data="back_to_accounts")], [InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        return
    if data == "back_to_accounts":
        await show_accounts_menu_from_callback(query, context)
        return
    if data.startswith("select_account_"):
        account_id = int(data.split("_")[2])
        accounts = load_accounts()
        user_data = accounts.get(user_id_str, {})
        if not isinstance(user_data, dict):
            await query.edit_message_text("❌ No accounts found!")
            return
        selected_account = None
        for acc in user_data.get("accounts", []):
            if acc["id"] == account_id:
                selected_account = acc
                break
        if not selected_account:
            await query.edit_message_text("❌ Account not found!")
            return
        await query.edit_message_text(f"🔄 Logging into {selected_account['custom_name']}...")
        token, api_user_id, nickname = await login_api_async(selected_account['username'], selected_account['password'])
        if token:
            for acc in user_data["accounts"]:
                if acc["id"] == account_id:
                    acc['token'] = token
                    acc['api_user_id'] = api_user_id
                    acc['nickname'] = nickname
                    acc['last_login'] = datetime.now().isoformat()
                    acc['active'] = True
                    break
            user_data["selected_account_id"] = account_id
            user_data["last_active"] = datetime.now().isoformat()
            accounts[user_id_str] = user_data
            save_accounts(accounts)
            await account_manager.initialize_user(user_id)
            message = f"✅ Account Switched Successfully! ✅\n\n📱 Active Account: {selected_account['custom_name']}\n👤 Username: {selected_account['username']}\n🆔 API ID: {api_user_id or 'N/A'}\n👑 Default: {'Yes' if selected_account.get('default', False) else 'No'}\n\n🔄 Remaining Checks: {account_manager.get_user_remaining_checks(user_id)}\n✅ Active Login: {account_manager.get_user_active_accounts_count(user_id)}\n\nYou can now start checking numbers!"
            keyboard = [[InlineKeyboardButton("📱 Switch Account", callback_data="back_to_accounts")], [InlineKeyboardButton("🚀 Start Checking", callback_data="start_checking")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')
        else:
            await query.edit_message_text(f"❌ Failed to login to {selected_account['custom_name']}!\n\nPlease check credentials or contact admin.")

async def show_accounts_menu_from_callback(query, context):
    user_id = query.from_user.id
    user_id_str = str(user_id)
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict) or not user_data.get("accounts"):
        await query.edit_message_text("❌ No accounts found!\n\nPlease contact admin to add accounts for you.\nAdmin: @Notfound_errorx")
        return
    user_accounts = user_data["accounts"]
    selected_id = user_data.get("selected_account_id", 1)
    message = "📱 Your Accounts 📱\n\nSelect an account to use:\n\n"
    keyboard = []
    for acc in user_accounts:
        status = "✅" if acc.get('active', True) else "❌"
        login_status = "🔓" if acc.get('token') else "🔒"
        selected_mark = " 👑" if acc['id'] == selected_id else ""
        message += f"{status}{login_status} {acc['custom_name']}\n   └─ 👤 Username: {acc['username']}\n   └─ 🆔 ID: {acc.get('api_user_id', 'N/A')[:8]}...{selected_mark}\n\n"
        callback_data = f"select_account_{acc['id']}"
        keyboard.append([InlineKeyboardButton(f"{acc['custom_name']}{selected_mark}", callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton("🔄 Refresh All", callback_data="refresh_all_accounts")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close_accounts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='none')

async def refresh_user_accounts(user_id):
    user_id_str = str(user_id)
    accounts = load_accounts()
    user_data = accounts.get(user_id_str, {})
    if not isinstance(user_data, dict):
        return False
    updated_count = 0
    for acc in user_data.get("accounts", []):
        if acc.get('active', True):
            token, api_user_id, nickname = await login_api_async(acc['username'], acc['password'])
            if token:
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                updated_count += 1
    user_data["last_active"] = datetime.now().isoformat()
    accounts[user_id_str] = user_data
    save_accounts(accounts)
    await account_manager.initialize_user(user_id)
    return updated_count

async def admin_add_account_custom(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command!")
        return
    if not context.args or len(context.args) < 4:
        await update.message.reply_text("❌ Usage: `/addacc user_id custom_name username password`\n\nExample: `/addacc 7319925086 \"Main Account\" RakibulBN pass123`\n\nNote: Use quotes for custom names with spaces")
        return
    try:
        target_user_id = context.args[0]
        custom_name = context.args[1]
        username = context.args[2]
        password = context.args[3]
        processing_msg = await update.message.reply_text(f"🔄 Verifying account `{username}`...")
        token, api_user_id, nickname = await login_api_async(username, password)
        if not token:
            await processing_msg.edit_text(f"❌ Login failed for `{username}`! Please check credentials.")
            return
        accounts = load_accounts()
        user_id_str = str(target_user_id)
        if user_id_str not in accounts:
            accounts[user_id_str] = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
        user_data = accounts[user_id_str]
        if not isinstance(user_data, dict):
            user_data = {"accounts": [], "selected_account_id": 1, "telegram_username": "", "last_active": datetime.now().isoformat()}
        existing_ids = [acc['id'] for acc in user_data.get("accounts", [])]
        new_id = max(existing_ids) + 1 if existing_ids else 1
        account_exists = False
        for acc in user_data.get("accounts", []):
            if acc['username'] == username:
                acc['custom_name'] = custom_name
                acc['password'] = password
                acc['token'] = token
                acc['api_user_id'] = api_user_id
                acc['nickname'] = nickname
                acc['last_login'] = datetime.now().isoformat()
                acc['active'] = True
                account_exists = True
                break
        if not account_exists:
            new_account = {'id': new_id, 'custom_name': custom_name, 'username': username, 'password': password, 'token': token, 'api_user_id': api_user_id, 'nickname': nickname, 'last_login': datetime.now().isoformat(), 'active': True, 'default': (new_id == 1), 'added_by': update.effective_user.id, 'added_at': datetime.now().isoformat(), 'telegram_username': "", 'friends': []}
            user_data["accounts"].append(new_account)
        if new_id == 1:
            user_data["selected_account_id"] = 1
        accounts[user_id_str] = user_data
        save_accounts(accounts)
        if user_id_str in account_manager.user_tokens:
            await account_manager.initialize_user(int(target_user_id))
        await processing_msg.edit_text(f"✅ Account Added Successfully! ✅\n\n👤 User ID: `{target_user_id}`\n📛 Custom Name: `{custom_name}`\n👤 Username: `{username}`\n🔑 Password: `{password}`\n🆔 API User ID: `{api_user_id or 'N/A'}`\n🎯 Account ID: `{new_id}`\n👑 Default: `{'Yes' if new_id == 1 else 'No'}`\n✅ Auto-login: Successful")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def refresh_server(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        try:
            member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if member.status not in allowed_status:
                await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
                return
        except:
            await update.message.reply_text(f"❌ Please join {REQUIRED_CHANNEL} first to use this feature.")
            return
    processing_msg = await update.message.reply_text("🔄 Refreshing your accounts...")
    active_accounts = await account_manager.initialize_user(user_id)
    remaining = account_manager.get_user_remaining_checks(user_id)
    total_accounts = account_manager.get_user_accounts_count(user_id)
    if active_accounts == 0:
        await processing_msg.edit_text(f"❌ No accounts could be logged in!\n\nPlease contact admin to check your account credentials.\nAdmin: @Notfound_errorx")
        return
    await processing_msg.edit_text(f"✅ Accounts Refreshed Successfully!\n\n📊 Result:\n• Successfully Logged In: {active_accounts}\n• Failed: {total_accounts - active_accounts}")

async def async_add_number_optimized(token, phone, msg, username, serial_number=None, user_id=None, cc='1'):
    try:
        async with aiohttp.ClientSession() as session:
            added = await add_number_async(session, token, cc, phone)
            prefix = f"{serial_number}. " if serial_number else ""
            if added:
                tracking = load_tracking()
                user_id_str = str(user_id)
                if user_id_str not in tracking["today_added"]:
                    tracking["today_added"][user_id_str] = 0
                tracking["today_added"][user_id_str] += 1
                save_tracking(tracking)
                stats = load_stats()
                stats["total_checked"] = stats.get("total_checked", 0) + 1
                stats["today_checked"] = stats.get("today_checked", 0) + 1
                save_stats(stats)
                await msg.edit_text(f"{prefix}+{cc} {phone} 🔵 In Progress")
                active_numbers[phone] = {'token': token, 'username': username, 'message_id': msg.message_id, 'user_id': user_id, 'chat_id': msg.chat_id, 'cc': cc, 'phone': phone}
            else:
                status_code, status_name, record_id, actual_phone = await get_status_with_actual_phone(session, token, phone)
                if actual_phone and actual_phone != phone:
                    display_phone = actual_phone
                    status_name = f"{status_name} - Wrong Format"
                else:
                    display_phone = phone
                if status_code == 16:
                    await msg.edit_text(f"{prefix}+{cc} {display_phone} 🚫 Already Exists")
                    account_manager.release_token(token)
                    return
                await msg.edit_text(f"{prefix}+{cc} {display_phone} ❌ Add Failed")
                account_manager.release_token(token)
    except:
        prefix = f"{serial_number}. " if serial_number else ""
        await msg.edit_text(f"{prefix}+{cc} {phone} ❌ Add Failed")
        account_manager.release_token(token)

async def handle_otp_submission(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a number message with OTP code.")
        return
    replied_message = update.message.reply_to_message.text
    phone = None
    cc = None
    match1 = re.search(r'\+\s*(\d+)\s+(\d+)', replied_message)
    if match1:
        cc = match1.group(1)
        phone = match1.group(2)
    if not phone:
        match2 = re.search(r'(\d{9,15})', replied_message)
        if match2:
            phone = match2.group(1)
    if not phone:
        await update.message.reply_text("❌ Could not find phone number in replied message!")
        return
    otp_data = active_numbers.get(phone)
    if not otp_data:
        for num, data in active_numbers.items():
            if data.get('phone') == phone:
                otp_data = data
                break
    if not otp_data:
        await update.message.reply_text("❌ This number is not active or doesn't belong to you.")
        return
    token = otp_data['token']
    username = otp_data['username']
    message_id = otp_data['message_id']
    data_user_id = otp_data['user_id']
    data_cc = otp_data.get('cc', cc if cc else '1')
    if data_user_id != user_id:
        await update.message.reply_text("❌ This number doesn't belong to you!")
        return
    if data_cc == '1' or data_cc == '11':
        if not re.match(r'^\d{6}$', text):
            await update.message.reply_text("❌ USA/Canada requires 6-digit OTP!")
            return
    elif data_cc in ['44', '61', '64']:
        if not re.match(r'^\d{6}$', text):
            await update.message.reply_text("❌ This country requires 6-digit OTP!")
            return
    else:
        if not re.match(r'^\d{4,6}$', text):
            await update.message.reply_text("❌ Invalid OTP format. Please send 4-6 digit OTP code.")
            return
    processing_msg = await update.message.reply_text(f"🔄 Submitting OTP for {phone} (CC: {data_cc})...")
    async with aiohttp.ClientSession() as session:
        success, message = await submit_otp_async(session, token, phone, text, data_cc)
    if success:
        await processing_msg.delete()
        phone_key = f"{data_cc}_{phone}_{user_id}"
        tracking = load_tracking()
        if phone_key in tracking.get("in_progress_timestamp", {}):
            del tracking["in_progress_timestamp"][phone_key]
        if phone_key in tracking.get("pending_delete", {}):
            del tracking["pending_delete"][phone_key]
        save_tracking(tracking)
        async with aiohttp.ClientSession() as session:
            status_code, status_name, record_id = await get_status_async(session, token, phone)
        final_text = f"+{data_cc} {phone} {status_name}"
        try:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=message_id, text=final_text)
        except BadRequest:
            pass
        if phone in active_numbers:
            del active_numbers[phone]
        if status_code == 1:
            otp_stats = load_otp_stats()
            user_id_str = str(user_id)
            if user_id_str not in otp_stats["user_stats"]:
                otp_stats["user_stats"][user_id_str] = {"total_success": 0, "today_success": 0, "yesterday_success": 0, "username": username, "full_name": ""}
            otp_stats["user_stats"][user_id_str]["total_success"] += 1
            otp_stats["user_stats"][user_id_str]["today_success"] += 1
            otp_stats["total_success"] = otp_stats.get("total_success", 0) + 1
            otp_stats["today_success"] = otp_stats.get("today_success", 0) + 1
            save_otp_stats(otp_stats)
    else:
        await processing_msg.edit_text(f"❌ OTP submission failed for {phone}: {message}")

async def handle_message_optimized(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "💳 Wallet":
        await wallet_command(update, context)
        return
    if text == "🚀 Refresh Server":
        await refresh_server(update, context)
        return
    if text == "📦 My Settlements":
        await show_user_settlements(update, context)
        return
    if text == "📊 Statistics":
        await statistics_command(update, context)
        return
    if text == "📱 Switch Account":
        await show_accounts_menu(update, context)
        return
    if user_id == ADMIN_ID:
        if text == "➕ Add Account":
            await update.message.reply_text("👤 Add Account\n\nUsage: `/addacc user_id custom_name username password`\n\nExample: `/addacc 123456789 \"Main Account\" user1 pass123`", parse_mode='none')
            return
        if text == "📋 List Accounts":
            await admin_list_accounts(update, context)
            return
        if text == "💰 Set Rate":
            await update.message.reply_text("💰 Set Settlement Rate\n\nUsage: `/setrate amount [date] [country...]`\n📢 Notice: `/setrate notice Your message`\n\nExample: `/setrate 0.08`\n`/setrate 0.07 canada 0.04 benin`", parse_mode='none')
            return
        if text == "📊 Statistics":
            await statistics_command(update, context)
            return
    if user_id != ADMIN_ID:
        channel_joined, group_joined, missing = await check_membership_requirements(context, user_id)
        if not (channel_joined and group_joined):
            keyboard = []
            if not channel_joined:
                keyboard.append([InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)])
            if not group_joined:
                keyboard.append([InlineKeyboardButton("💰 Join Payment Group", url=PAYMENT_GROUP_INVITE_LINK)])
            keyboard.append([InlineKeyboardButton("🔄 Check Membership", callback_data="check_membership")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            channel_status = "❌ Not Joined" if not channel_joined else "✅ Joined"
            group_status = "❌ Not Joined" if not group_joined else "✅ Joined"
            missing_text = ", ".join(missing)
            await update.message.reply_text(f"🔒 ACCESS RESTRICTED\n\nTo use this bot, join:\n\n📢 Channel: {REQUIRED_CHANNEL}\n└─ {channel_status}\n\n💰 Payment Group: {REQUIRED_PAYMENT_GROUP}\n└─ {group_status}\n\nMissing: {missing_text}\n\n👇 Join then click 'Check Membership'", reply_markup=reply_markup, parse_mode='none')
            return
    if account_manager.get_user_accounts_count(user_id) == 0 and user_id != ADMIN_ID:
        await update.message.reply_text(f"❌ No Accounts Found!\n\nPlease contact admin to add accounts for you.\n👤 Admin: @Notfound_errorx", parse_mode='none')
        return
    if update.message.reply_to_message:
        await handle_otp_submission(update, context)
        return
    if 'pending_payment_method' in context.user_data:
        await handle_payment_method_input(update, context)
        return
    numbers_data = extract_phone_numbers(text)
    if numbers_data:
        if len(numbers_data) > 1:
            valid_numbers = []
            for num_data in numbers_data:
                phone = num_data['phone']
                cc = num_data.get('cc', '1')
                if cc == '229' and len(phone) == 8:
                    valid_numbers.append(num_data)
                elif 7 <= len(phone) <= 15:
                    valid_numbers.append(num_data)
            if valid_numbers:
                num_data = valid_numbers[0]
                await update.message.reply_text(f"ℹ️ Found {len(numbers_data)} possible numbers.\n✅ Processing: +{num_data['cc']} {num_data['phone']}", parse_mode='none')
            else:
                num_data = numbers_data[0]
        else:
            num_data = numbers_data[0]
        phone = num_data['phone']
        cc = num_data.get('cc', '1')
        remaining = account_manager.get_user_remaining_checks(user_id)
        if remaining <= 0:
            active_accounts = account_manager.get_user_active_accounts_count(user_id)
            await update.message.reply_text(f"🚀 Refresh Server Required\n\nProcessing {active_accounts * MAX_PER_ACCOUNT} numbers. Please wait or refresh.", parse_mode='none')
            return
        token_data = account_manager.get_next_available_token(user_id)
        if not token_data:
            await update.message.reply_text("❌ No Available Accounts!\n\nPlease refresh server first using the button.", parse_mode='none')
            return
        token, username = token_data
        stats = load_stats()
        stats["total_checked"] = stats.get("total_checked", 0) + 1
        stats["today_checked"] = stats.get("today_checked", 0) + 1
        save_stats(stats)
        msg = await update.message.reply_text(f"+{cc} {phone} 🔵 Processing...")
        asyncio.create_task(async_add_number_optimized(token, phone, msg, username, user_id=user_id, cc=cc))
        if context.job_queue:
            context.job_queue.run_once(track_status_optimized, 2, data={'chat_id': update.message.chat_id, 'message_id': msg.message_id, 'phone': phone, 'token': token, 'username': username, 'checks': 0, 'last_status': '🔵 Processing...', 'user_id': user_id, 'last_status_code': None, 'cc': cc})
        return
    await update.message.reply_text("❌ No Valid Phone Numbers Found!\n\n📱 Supported Formats:\n• `+1 (234) 567-8900`\n• `+44 7911 123456`\n• `+229 47879817`\n• `(229) 47879817`\n• `22947879817`\n\n💡 Tip: Always include country code with + sign!", parse_mode='none')

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=RENDER_PORT, access_log=False)

def main():
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def initialize_bot():
        await account_manager.initialize_user(ADMIN_ID)
        asyncio.create_task(keep_alive_enhanced())
        asyncio.create_task(random_ping())
        asyncio.create_task(immediate_ping())
    loop.run_until_complete(initialize_bot())
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addacc", admin_add_account_custom))
    application.add_handler(CommandHandler("removeacc", admin_remove_account))
    application.add_handler(CommandHandler("accounts", show_accounts_menu))
    application.add_handler(CommandHandler("refresh", refresh_server))
    application.add_handler(CommandHandler("setrate", set_settlement_rate))
    application.add_handler(CommandHandler("settlements", show_user_settlements))
    application.add_handler(CommandHandler("stats", statistics_command))
    application.add_handler(CommandHandler("statistics", statistics_command))
    application.add_handler(CommandHandler("fakepay", fake_payment_command))
    application.add_handler(CommandHandler("fakeenable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakedisable", fake_payment_toggle_command))
    application.add_handler(CommandHandler("fakestatus", fake_payment_status_command))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("cancel", cancel_payment_method))
    application.add_handler(CommandHandler("addpayment", add_payment_method))
    application.add_handler(CommandHandler("removepayment", remove_payment_method))
    application.add_handler(CommandHandler("listpayment", list_payment_methods))
    application.add_handler(CommandHandler("clearpayment", clear_payment_methods))
    application.add_handler(CallbackQueryHandler(handle_statistics_callback, pattern=r"^stats_"))
    application.add_handler(CallbackQueryHandler(handle_settlement_callback, pattern=r"^settlement_"))
    application.add_handler(CallbackQueryHandler(handle_account_selection, pattern=r"^(select_account_|refresh_all_accounts|close_accounts_menu|back_to_accounts|start_checking)"))
    application.add_handler(CallbackQueryHandler(handle_payment_callback, pattern=r"^(payment_complete_|payment_details_|close_details)"))
    application.add_handler(CallbackQueryHandler(handle_force_payment_complete, pattern=r"^force_payment_complete_"))
    application.add_handler(CallbackQueryHandler(handle_refresh_user_card, pattern=r"^refresh_user_card_"))
    application.add_handler(CallbackQueryHandler(handle_membership_check, pattern=r"^check_membership$"))
    application.add_handler(CallbackQueryHandler(handle_wallet_callback, pattern=r"^(add_bkash|add_nagad|add_binance|close_wallet|refresh_wallet)$"))
    application.add_handler(CallbackQueryHandler(handle_wallet_open, pattern=r"^open_wallet$"))
    application.add_handler(CallbackQueryHandler(handle_remove_chunk, pattern=r"^remove_chunk_"))
    application.add_handler(CallbackQueryHandler(back_to_users_list, pattern=r"^back_to_users_list$"))
    application.add_handler(CallbackQueryHandler(close_remove_menu, pattern=r"^close_remove_menu$"))
    application.add_handler(CallbackQueryHandler(view_user_accounts, pattern=r"^view_user_acc_"))
    application.add_handler(CallbackQueryHandler(remove_single_account_from_list, pattern=r"^remove_single_acc_"))
    application.add_handler(CallbackQueryHandler(remove_all_accounts_from_user, pattern=r"^remove_all_accs_"))
    application.add_handler(CallbackQueryHandler(handle_user_delete_stuck_number, pattern=r"^user_delete_stuck_"))
    application.add_handler(CallbackQueryHandler(handle_start_bot_now, pattern=r"^start_bot_now$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_optimized))
    if application.job_queue:
        application.job_queue.run_daily(reset_daily_stats, time=datetime.strptime("10:00", "%H:%M").time())
        application.job_queue.run_repeating(check_in_progress_timeout, interval=30, first=10)
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
