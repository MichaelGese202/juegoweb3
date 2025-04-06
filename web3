import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from web3 import Web3
import sqlite3
import json

# Configuración inicial
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración Web3
w3 = Web3(Web3.HTTPProvider("TU_PROVEEDOR_WEB3"))
contract = w3.eth.contract(address="CONTRATO_ADDRESS", abi=json.load(open('contract_abi.json')))

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('noxebot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        speed INTEGER DEFAULT 1,
        boost_active BOOLEAN DEFAULT FALSE,
        tasks_completed INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (referrer_id, referred_id)
    )''')
    
    conn.commit()
    conn.close()

init_db()

# Funciones de base de datos
def get_user_data(user_id):
    conn = sqlite3.connect('noxebot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect('noxebot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Handler principal
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    args = context.args
    
    # Procesar referido si existe
    referred_by = None
    if args and args[0].startswith('ref_'):
        try:
            referred_by = int(args[0][4:])
            if referred_by != user.id:  # Evitar auto-referidos
                conn = sqlite3.connect('noxebot.db')
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO referrals VALUES (?, ?, datetime("now"))', (referred_by, user.id))
                cursor.execute('UPDATE users SET balance = balance + 100 WHERE user_id = ?', (referred_by,))
                conn.commit()
                conn.close()
        except ValueError:
            pass
    
    # Registrar usuario si no existe
    conn = sqlite3.connect('noxebot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, referral_code) VALUES (?, ?, ?)', 
                  (user.id, user.username, f"ref_{user.id}"))
    conn.commit()
    conn.close()
    
    # Mostrar menú principal
    show_main_menu(update, user.id)

def show_main_menu(update: Update, user_id: int):
    user_data = get_user_data(user_id)
    
    # Formatear balance con separadores de miles
    formatted_balance = "{:,}".format(user_data[2]).replace(",", " ")
    
    keyboard = [
        [InlineKeyboardButton("🚀 Boost", callback_data='boost')],
        [InlineKeyboardButton("✅ Complete tasks", callback_data='tasks')],
        [
            InlineKeyboardButton("🏠 Home", callback_data='main_menu'),
            InlineKeyboardButton("👥 Invite", callback_data='invite'),
            InlineKeyboardButton("🏆 TOPs", callback_data='tops')
        ],
        [
            InlineKeyboardButton("💰 Earn", callback_data='earn'),
            InlineKeyboardButton("🎁 Airdrop", callback_data='airdrop')
        ]
    ]
    
    # Estadísticas para el encabezado
    speed = user_data[5]
    rank = "#586"  # Esto debería calcularse basado en la base de datos
    
    message = (
        f"⚡️ *Speed*: {speed} | {rank}\n"
        f"👤 *User*: {user_data[1] or 'Anonymous'}\n"
        f"────────────────\n"
        f"💰 *Balance*: {formatted_balance} NOXE\n"
        f"────────────────\n"
        "🚀 *Boost your earnings* with our booster!\n"
        "✅ *Complete tasks* to earn more NOXE\n"
    )
    
    if hasattr(update, 'callback_query'):
        update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        update.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

# Handlers para cada sección
def boost_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("🔼 Activate Boost (50 NOXE)", callback_data='activate_boost')],
        [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]
    ]
    
    query.edit_message_text(
        text="🚀 *Boost Your Earnings*\n\n"
             "Activate boost to double your mining speed for 24 hours!\n"
             "Cost: 50 NOXE",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def tasks_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    
    tasks = [
        {"name": "Join Telegram Channel", "reward": 50},
        {"name": "Follow Twitter", "reward": 30},
        {"name": "Daily Login", "reward": 10}
    ]
    
    task_buttons = [
        [InlineKeyboardButton(f"✅ {task['name']} (+{task['reward']} NOXE)", callback_data=f"complete_task_{i}")]
        for i, task in enumerate(tasks)
    ]
    task_buttons.append([InlineKeyboardButton("🔙 Back", callback_data='main_menu')])
    
    query.edit_message_text(
        text="✅ *Available Tasks*\n\n"
             "Complete tasks to earn NOXE coins:\n",
        reply_markup=InlineKeyboardMarkup(task_buttons),
        parse_mode='Markdown'
    )

def invite_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Obtener estadísticas de referidos
    conn = sqlite3.connect('noxebot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()
    
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    
    keyboard = [
        [InlineKeyboardButton("📤 Share Link", switch_inline_query=f"Join Noxecoin and earn crypto! {referral_link}")],
        [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]
    ]
    
    query.edit_message_text(
        text="👥 *Invite Friends*\n\n"
             f"🔗 Your referral link:\n`{referral_link}`\n\n"
             f"👥 Total invited: {ref_count}\n"
             "💰 Earn 100 NOXE for each friend who joins!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Implementa handlers similares para TOPs, Earn y Airdrop...

def main():
    updater = Updater("TU_TOKEN_DE_TELEGRAM")
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    updater.start_polling()
    updater.idle()

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'main_menu':
        show_main_menu(update, query.from_user.id)
    elif data == 'boost':
        boost_handler(update, context)
    elif data == 'tasks':
        tasks_handler(update, context)
    elif data == 'invite':
        invite_handler(update, context)
    # Implementa los demás handlers...

if __name__ == '__main__':
    main()
