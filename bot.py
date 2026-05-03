import os
import time
import random
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "").strip()
LOG_CHAT_ID_RAW = os.getenv("LOG_CHAT_ID", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is empty. Put your token in .env")

OWNER_ADMINS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()] if ADMIN_IDS_RAW else []
LOG_CHAT_ID = int(LOG_CHAT_ID_RAW) if LOG_CHAT_ID_RAW else None

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "bot_admins": [],
    "warnings": {},
    "notes": {},
    "blacklist_words": ["scam", "скам", "лохотрон", "фишинг", "обман"],
    "blocked_links": ["http://", "https://", "t.me/", "telegram.me/", "discord.gg/", "bit.ly/", "tinyurl.com", "vk.com/"],
    "custom_replies": {
        "правила": "Напиши /rules — там полный устав Prizrok чата.",
        "данек": "Данек кодерочек"
    },
    "settings": {
        "max_warnings": 3,
        "mute_minutes": 30,
        "captcha_seconds": 120,
        "link_limit": 3,
        "link_window_seconds": 90
    },
    "stats": {},
    "pending_bans": [],
    "link_strikes": {}
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        for k, v in DEFAULT_DATA.items():
            if k not in old:
                old[k] = v
        for k, v in DEFAULT_DATA["settings"].items():
            if k not in old["settings"]:
                old["settings"][k] = v
        return old
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))

def save_data(obj):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

data = load_data()
# remove annoying old auto-reply if it exists in saved data.json
if "ку" in data.get("custom_replies", {}):
    data["custom_replies"].pop("ку", None)
    save_data(data)

captcha_pending = {}

MEMES = [
    "👻 Призрак смотрит за порядком.",
    "🗿 Админ проснулся — чат напрягся.",
    "💀 Минус вайб, плюс мут.",
    "🐺 Prizrok mode: activated.",
    "🥶 Спокойно, чат под контролем.",
    "⚡ Кто кидает 3 ссылки подряд — тот летит.",
    "🤡 Спам detected. Клоун удалён из цирка.",
    "🧠 Данек кодерочек это закодил, значит работает.",
    "🔥 Чат живёт, бот пашет.",
    "🫡 Уважение админам, свободу нормальным людям."
]

ROASTS = [
    "Не спамь ссылками, брат, интернет не убежит.",
    "Это был не мув, это был путь к муту.",
    "Ты сейчас на тонкой грани между чатом и баном.",
    "Призрак всё видел. Даже это.",
    "Админская дубинка уже прогрелась."
]

BIG_RULES = """
📜 <b>ОГРОМНЫЕ ПРАВИЛА PRIZROK ЧАТА</b> 👻

<b>Главная идея:</b>
Чат сделан для общения, мемов, движения, обсуждений и нормального вайба.

<b>1. Спам ссылками запрещён</b>
Одна ссылка не всегда проблема, но 3 ссылки подряд — это уже спам. Бот считает ссылки и выдаёт наказание.

<b>2. Реклама запрещена</b>
Нельзя рекламировать каналы, группы, магазины, Discord и Telegram-ссылки без разрешения администрации.

<b>3. Скам запрещён полностью</b>
Фейковые розыгрыши, “скинь код”, подозрительные ссылки, обман, фишинг — бан.

<b>4. Уважение участников</b>
Не травить людей, не давить на новичков, не устраивать токсичный цирк.

<b>5. Админы решают спорные моменты</b>
Если админ сказал остановиться — остановись.

<b>6. Не сливай личные данные</b>
Номера, адреса, документы, фотки без разрешения — нельзя.

<b>7. Не обходи мут/бан</b>
Твинк после наказания — причина для нового бана.

<b>8. Мемы можно</b>
Мемы и рофлы можно, но без травли и мусора.

<b>Система наказаний:</b>
3 ссылки подряд → warn.
3 warn → automute.
Скам/рейд/жёсткий спам → ban.

<i>Prizrokoffbot by Данек кодерочек 🧠💻</i>
"""

HELP_TEXT = """
👻 <b>Prizrokoffbot Ultra FIX4</b>
<i>Данек кодерочек edition 🧠💻</i>

<b>Для всех:</b>
/rules — правила
/help — помощь
/meme — мем
/roast — рофл
/ping — проверка
/mywarns — твои варны
/profile — профиль

<b>Модерация reply или ID:</b>
/warn [id]
/mute [id]
/unmute [id]
/ban [id]
/unban [id]
/kick [id]
/clearwarns [id]

<b>Полное управление ботом:</b>
/botpanel — главная панель
/buttons — кнопки mute/ban/warn ответом или /buttons ID
/settings — настройки
/set max_warnings 3
/set mute_minutes 30
/set link_limit 3
/set link_window_seconds 90
/addbotadmin ID — добавить админа бота
/delbotadmin ID — убрать админа бота
/botadmins — список админов бота

<b>Фильтры и база:</b>
/addbad слово
/delbad слово
/badlist
/addlink домен
/dellink домен
/linklist
/addreply слово | ответ
/delreply слово
/replies
/note ключ | текст
/getnote ключ
/delnote ключ
/notes
/stats
/status
/buttons [id] — кнопки управления юзером

<b>Важно:</b>
Флуда по обычным сообщениям больше нет.
Наказание только если пользователь кидает 3 ссылки подряд.
"""

def setting(name):
    return data.get("settings", {}).get(name, DEFAULT_DATA["settings"][name])

def is_owner(user_id):
    return user_id in OWNER_ADMINS

def is_bot_admin_id(user_id):
    return user_id in OWNER_ADMINS or user_id in data.get("bot_admins", [])

def is_admin(chat_id, user_id):
    if is_bot_admin_id(user_id):
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False

def log_action(text):
    if LOG_CHAT_ID:
        try:
            bot.send_message(LOG_CHAT_ID, text)
        except Exception:
            pass

def inc_stat(user_id, key):
    uid = str(user_id)
    if uid not in data["stats"]:
        data["stats"][uid] = {"messages": 0, "warns": 0, "deleted": 0, "links": 0}
    data["stats"][uid][key] = data["stats"][uid].get(key, 0) + 1
    save_data(data)

def has_link(text):
    low = (text or "").lower()
    return any(x.lower() in low for x in data.get("blocked_links", []))

def has_bad_word(text):
    low = (text or "").lower()
    return any(x.lower() in low for x in data.get("blacklist_words", []))

def get_target_user_id(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    parts = (message.text or "").split()
    if len(parts) >= 2:
        try:
            return int(parts[1]), f"ID {parts[1]}"
        except ValueError:
            return None, None
    return None, None

def mute_member(chat_id, user_id, minutes=None):
    if minutes is None:
        minutes = int(setting("mute_minutes"))
    bot.restrict_chat_member(
        chat_id,
        user_id,
        until_date=int(time.time() + minutes * 60),
        permissions=types.ChatPermissions(can_send_messages=False)
    )

def unmute_member(chat_id, user_id):
    bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=types.ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

def warn_by_id(chat_id, user_id, name, reason):
    uid = str(user_id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    count = data["warnings"][uid]
    inc_stat(user_id, "warns")
    save_data(data)

    max_w = int(setting("max_warnings"))
    bot.send_message(
        chat_id,
        f"⚠️ <b>{name}</b> получил предупреждение.\n"
        f"Причина: <b>{reason}</b>\n"
        f"Варны: <b>{count}/{max_w}</b>\n\n"
        f"{random.choice(ROASTS)}"
    )

    if count >= max_w:
        minutes = int(setting("mute_minutes"))
        try:
            mute_member(chat_id, user_id, minutes)
            data["warnings"][uid] = 0
            save_data(data)
            bot.send_message(chat_id, f"🔇 <b>{name}</b> получил автомут на {minutes} минут.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Automute не сработал: <code>{e}</code>")

def get_arg_or_reply_text(message, command_name):
    text = message.text or ""
    parts = text.split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else ""
    if arg:
        return arg
    if message.reply_to_message and message.reply_to_message.text:
        return message.reply_to_message.text.strip()
    return ""

def parse_set_command(message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        return None, None
    return parts[1], parts[2]

def admin_only(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return False
    return True

def owner_only(message):
    return is_owner(message.from_user.id)

@bot.message_handler(commands=["start", "help"])
def help_cmd(message):
    bot.reply_to(message, HELP_TEXT)

@bot.message_handler(commands=["ping"])
def ping_cmd(message):
    bot.reply_to(message, "🏓 Pong. FIX4 живой. Флуд по обычным сообщениям выключен.")

@bot.message_handler(commands=["rules"])
def rules_cmd(message):
    bot.reply_to(message, BIG_RULES)

@bot.message_handler(commands=["meme"])
def meme_cmd(message):
    bot.reply_to(message, random.choice(MEMES))

@bot.message_handler(commands=["roast"])
def roast_cmd(message):
    bot.reply_to(message, random.choice(ROASTS))

@bot.message_handler(commands=["mywarns"])
def mywarns_cmd(message):
    bot.reply_to(message, f"⚠️ У тебя варнов: <b>{data['warnings'].get(str(message.from_user.id), 0)}</b>")

@bot.message_handler(commands=["profile"])
def profile_cmd(message):
    uid = str(message.from_user.id)
    st = data["stats"].get(uid, {"messages": 0, "warns": 0, "deleted": 0, "links": 0})
    bot.reply_to(
        message,
        f"👤 <b>Профиль</b>\n"
        f"ID: <code>{message.from_user.id}</code>\n"
        f"Сообщений: {st.get('messages',0)}\n"
        f"Ссылок: {st.get('links',0)}\n"
        f"Варнов: {data['warnings'].get(uid,0)}"
    )

@bot.message_handler(commands=["status"])
def status_cmd(message):
    try:
        me = bot.get_me()
        member = bot.get_chat_member(message.chat.id, me.id)
        bot.reply_to(
            message,
            f"🤖 <b>Статус бота</b>\n"
            f"Bot: @{me.username}\n"
            f"Chat type: <b>{message.chat.type}</b>\n"
            f"Role: <b>{member.status}</b>\n"
            f"Can restrict/mute: <b>{getattr(member, 'can_restrict_members', None)}</b>\n"
            f"Can delete messages: <b>{getattr(member, 'can_delete_messages', None)}</b>\n"
            f"Can invite users: <b>{getattr(member, 'can_invite_users', None)}</b>\n"
            f"Bot admins in data: <b>{len(data.get('bot_admins', []))}</b>"
        )
    except Exception as e:
        bot.reply_to(message, f"Ошибка status: <code>{e}</code>")

@bot.message_handler(commands=["botpanel", "panel"])
def botpanel_cmd(message):
    if not admin_only(message):
        return
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📜 Rules", callback_data="panel:rules"),
        types.InlineKeyboardButton("📊 Stats", callback_data="panel:stats"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="panel:settings"),
        types.InlineKeyboardButton("👮 Bot admins", callback_data="panel:admins"),
        types.InlineKeyboardButton("🚫 Bad words", callback_data="panel:bad"),
        types.InlineKeyboardButton("🔗 Link filters", callback_data="panel:links"),
        types.InlineKeyboardButton("😂 Meme", callback_data="panel:meme"),
        types.InlineKeyboardButton("🧹 Help", callback_data="panel:help")
    )
    bot.reply_to(message, "🛠 <b>Главная панель Prizrokoffbot</b>\nУправление ботом от Данек кодерочек:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("panel:"))
def panel_callback(call):
    if not is_admin(call.message.chat.id, call.from_user.id):
        bot.answer_callback_query(call.id, "Ты не админ.", show_alert=True)
        return
    action = call.data.split(":")[1]
    if action == "rules":
        bot.send_message(call.message.chat.id, BIG_RULES)
    elif action == "stats":
        bot.send_message(call.message.chat.id, get_stats_text())
    elif action == "settings":
        bot.send_message(call.message.chat.id, get_settings_text())
    elif action == "admins":
        bot.send_message(call.message.chat.id, get_botadmins_text())
    elif action == "bad":
        bot.send_message(call.message.chat.id, "🚫 <b>Bad words:</b>\n" + "\n".join(data["blacklist_words"]))
    elif action == "links":
        bot.send_message(call.message.chat.id, "🔗 <b>Link filters:</b>\n" + "\n".join(data["blocked_links"]))
    elif action == "meme":
        bot.send_message(call.message.chat.id, random.choice(MEMES))
    elif action == "help":
        bot.send_message(call.message.chat.id, HELP_TEXT)
    bot.answer_callback_query(call.id, "Готово.")

def get_stats_text():
    total_warns = sum(int(v) for v in data.get("warnings", {}).values())
    return (
        f"📊 <b>Стата</b>\n"
        f"Юзеров в базе: {len(data.get('stats', {}))}\n"
        f"Активных варнов: {total_warns}\n"
        f"Bot admins: {len(data.get('bot_admins', []))}\n"
        f"Bad words: {len(data['blacklist_words'])}\n"
        f"Link filters: {len(data['blocked_links'])}\n"
        f"Replies: {len(data['custom_replies'])}\n"
        f"Pending bans: {len(data.get('pending_bans', []))}"
    )

def get_settings_text():
    s = data["settings"]
    return (
        "⚙️ <b>Настройки</b>\n"
        f"max_warnings: <code>{s['max_warnings']}</code>\n"
        f"mute_minutes: <code>{s['mute_minutes']}</code>\n"
        f"captcha_seconds: <code>{s['captcha_seconds']}</code>\n"
        f"link_limit: <code>{s['link_limit']}</code>\n"
        f"link_window_seconds: <code>{s['link_window_seconds']}</code>\n\n"
        "Изменить: <code>/set link_limit 3</code>"
    )

def get_botadmins_text():
    owners = "\n".join([f"• owner <code>{x}</code>" for x in OWNER_ADMINS]) or "нет"
    admins = "\n".join([f"• <code>{x}</code>" for x in data.get("bot_admins", [])]) or "нет"
    return f"👮 <b>Админы бота</b>\n\n<b>Owners из .env:</b>\n{owners}\n\n<b>Добавленные через бота:</b>\n{admins}"

@bot.message_handler(commands=["settings"])
def settings_cmd(message):
    if not admin_only(message): return
    bot.reply_to(message, get_settings_text())

@bot.message_handler(commands=["set"])
def set_cmd(message):
    if not admin_only(message): return
    key, value = parse_set_command(message)
    if not key:
        bot.reply_to(message, "Использование: /set key value\nНапример: /set link_limit 3")
        return
    if key not in data["settings"]:
        bot.reply_to(message, "Такой настройки нет. Напиши /settings")
        return
    try:
        if "." in value:
            value = float(value)
        else:
            value = int(value)
    except Exception:
        bot.reply_to(message, "Значение должно быть числом.")
        return
    data["settings"][key] = value
    save_data(data)
    bot.reply_to(message, f"✅ Настройка изменена: <b>{key}</b> = <code>{value}</code>")

@bot.message_handler(commands=["addbotadmin"])
def addbotadmin_cmd(message):
    if not owner_only(message):
        bot.reply_to(message, "❌ Только owner из .env может добавлять админов бота.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Использование: /addbotadmin USER_ID")
        return
    try:
        uid = int(parts[1])
    except Exception:
        bot.reply_to(message, "ID должен быть числом.")
        return
    if uid not in data["bot_admins"]:
        data["bot_admins"].append(uid)
        save_data(data)
    bot.reply_to(message, f"✅ Добавил админа бота: <code>{uid}</code>")

@bot.message_handler(commands=["delbotadmin"])
def delbotadmin_cmd(message):
    if not owner_only(message):
        bot.reply_to(message, "❌ Только owner из .env может удалять админов бота.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Использование: /delbotadmin USER_ID")
        return
    try:
        uid = int(parts[1])
    except Exception:
        bot.reply_to(message, "ID должен быть числом.")
        return
    if uid in data["bot_admins"]:
        data["bot_admins"].remove(uid)
        save_data(data)
    bot.reply_to(message, f"✅ Удалил админа бота: <code>{uid}</code>")

@bot.message_handler(commands=["botadmins"])
def botadmins_cmd(message):
    if not admin_only(message): return
    bot.reply_to(message, get_botadmins_text())

@bot.message_handler(commands=["warn"])
def warn_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /warn ответом на сообщение ИЛИ /warn USER_ID")
        return
    warn_by_id(message.chat.id, uid, name, "нарушение правил")

@bot.message_handler(commands=["mute"])
def mute_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /mute ответом на сообщение ИЛИ /mute USER_ID")
        return
    try:
        mute_member(message.chat.id, uid)
        bot.reply_to(message, f"🔇 <b>{name}</b> замьючен на {setting('mute_minutes')} минут.")
    except Exception as e:
        bot.reply_to(message, f"❌ Не смог замутить: <code>{e}</code>")

@bot.message_handler(commands=["unmute"])
def unmute_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /unmute ответом на сообщение ИЛИ /unmute USER_ID")
        return
    try:
        unmute_member(message.chat.id, uid)
        bot.reply_to(message, f"🔊 <b>{name}</b> размьючен.")
    except Exception as e:
        bot.reply_to(message, f"❌ Не смог размутить: <code>{e}</code>")

@bot.message_handler(commands=["ban"])
def ban_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /ban ответом на сообщение ИЛИ /ban USER_ID")
        return
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"⛔ <b>{name}</b> забанен.")
    except Exception as e:
        bot.reply_to(message, f"❌ Не смог забанить: <code>{e}</code>")

@bot.message_handler(commands=["kick"])
def kick_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /kick ответом на сообщение ИЛИ /kick USER_ID")
        return
    try:
        bot.ban_chat_member(message.chat.id, uid)
        bot.unban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"👢 <b>{name}</b> кикнут.")
    except Exception as e:
        bot.reply_to(message, f"❌ Не смог кикнуть: <code>{e}</code>")

@bot.message_handler(commands=["unban"])
def unban_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /unban USER_ID")
        return
    try:
        bot.unban_chat_member(message.chat.id, uid)
        bot.reply_to(message, f"✅ <b>{name}</b> разбанен.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка разбана: <code>{e}</code>")

@bot.message_handler(commands=["clearwarns"])
def clearwarns_cmd(message):
    if not admin_only(message): return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: /clearwarns ответом ИЛИ /clearwarns USER_ID")
        return
    data["warnings"][str(uid)] = 0
    save_data(data)
    bot.reply_to(message, f"✅ Варны <b>{name}</b> очищены.")

@bot.message_handler(commands=["addbad"])
def addbad_cmd(message):
    if not admin_only(message): return
    word = get_arg_or_reply_text(message, "addbad").lower()
    if not word:
        bot.reply_to(message, "Использование: /addbad слово\nИли ответь /addbad на сообщение.")
        return
    if word not in data["blacklist_words"]:
        data["blacklist_words"].append(word)
        save_data(data)
        bot.reply_to(message, f"✅ Добавил в bad words: <b>{word}</b>")
    else:
        bot.reply_to(message, f"Уже есть: <b>{word}</b>")

@bot.message_handler(commands=["delbad"])
def delbad_cmd(message):
    if not admin_only(message): return
    word = get_arg_or_reply_text(message, "delbad").lower()
    if not word:
        bot.reply_to(message, "Использование: /delbad слово")
        return
    if word in data["blacklist_words"]:
        data["blacklist_words"].remove(word)
        save_data(data)
    bot.reply_to(message, f"✅ Если было — удалил: <b>{word}</b>")

@bot.message_handler(commands=["badlist"])
def badlist_cmd(message):
    if not admin_only(message): return
    bot.reply_to(message, "🚫 <b>Bad words:</b>\n" + "\n".join(data["blacklist_words"]))

@bot.message_handler(commands=["addlink"])
def addlink_cmd(message):
    if not admin_only(message): return
    item = get_arg_or_reply_text(message, "addlink").lower()
    if not item:
        bot.reply_to(message, "Использование: /addlink домен")
        return
    if item not in data["blocked_links"]:
        data["blocked_links"].append(item)
        save_data(data)
    bot.reply_to(message, f"✅ Добавил link filter: <b>{item}</b>")

@bot.message_handler(commands=["dellink"])
def dellink_cmd(message):
    if not admin_only(message): return
    item = get_arg_or_reply_text(message, "dellink").lower()
    if item in data["blocked_links"]:
        data["blocked_links"].remove(item)
        save_data(data)
    bot.reply_to(message, f"✅ Если было — удалил link filter: <b>{item}</b>")

@bot.message_handler(commands=["linklist"])
def linklist_cmd(message):
    if not admin_only(message): return
    bot.reply_to(message, "🔗 <b>Link filters:</b>\n" + "\n".join(data["blocked_links"]))

@bot.message_handler(commands=["addreply"])
def addreply_cmd(message):
    if not admin_only(message): return
    raw = message.text.replace("/addreply", "", 1).strip()
    if "|" not in raw:
        bot.reply_to(message, "Использование: /addreply слово | ответ")
        return
    key, value = [x.strip() for x in raw.split("|", 1)]
    data["custom_replies"][key.lower()] = value
    save_data(data)
    bot.reply_to(message, f"✅ Автоответ добавлен на: <b>{key}</b>")

@bot.message_handler(commands=["delreply"])
def delreply_cmd(message):
    if not admin_only(message): return
    key = get_arg_or_reply_text(message, "delreply").lower()
    if key in data["custom_replies"]:
        data["custom_replies"].pop(key)
        save_data(data)
    bot.reply_to(message, f"✅ Если был — удалил автоответ: <b>{key}</b>")

@bot.message_handler(commands=["replies"])
def replies_cmd(message):
    if not admin_only(message): return
    lines = [f"• {k} → {v}" for k, v in data["custom_replies"].items()]
    bot.reply_to(message, "💬 <b>Автоответы:</b>\n" + "\n".join(lines[:50]))

@bot.message_handler(commands=["note"])
def note_cmd(message):
    if not admin_only(message): return
    raw = message.text.replace("/note", "", 1).strip()
    if "|" not in raw:
        bot.reply_to(message, "Использование: /note ключ | текст")
        return
    key, value = [x.strip() for x in raw.split("|", 1)]
    data["notes"][key.lower()] = value
    save_data(data)
    bot.reply_to(message, f"✅ Заметка сохранена: <b>{key}</b>")

@bot.message_handler(commands=["getnote"])
def getnote_cmd(message):
    key = get_arg_or_reply_text(message, "getnote").lower()
    if not key:
        bot.reply_to(message, "Использование: /getnote ключ")
        return
    bot.reply_to(message, data["notes"].get(key, "Такой заметки нет."))

@bot.message_handler(commands=["delnote"])
def delnote_cmd(message):
    if not admin_only(message): return
    key = get_arg_or_reply_text(message, "delnote").lower()
    if key in data["notes"]:
        data["notes"].pop(key)
        save_data(data)
    bot.reply_to(message, f"✅ Если была — удалил заметку: <b>{key}</b>")

@bot.message_handler(commands=["notes"])
def notes_cmd(message):
    bot.reply_to(message, "📝 <b>Заметки:</b>\n" + "\n".join([f"• {k}" for k in data["notes"].keys()]) if data["notes"] else "Заметок пока нет.")

@bot.message_handler(commands=["stats"])
def stats_cmd(message):
    if not admin_only(message): return
    bot.reply_to(message, get_stats_text())


@bot.message_handler(commands=["buttons", "modbuttons"])
def buttons_cmd(message):
    if not admin_only(message):
        return
    uid, name = get_target_user_id(message)
    if not uid:
        bot.reply_to(message, "Использование: ответь /buttons на сообщение пользователя ИЛИ /buttons USER_ID")
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("⚠️ Warn", callback_data=f"mod:warn:{uid}"),
        types.InlineKeyboardButton("🔇 Mute", callback_data=f"mod:mute:{uid}"),
        types.InlineKeyboardButton("🔊 Unmute", callback_data=f"mod:unmute:{uid}"),
        types.InlineKeyboardButton("⛔ Ban", callback_data=f"mod:ban:{uid}"),
        types.InlineKeyboardButton("👢 Kick", callback_data=f"mod:kick:{uid}"),
        types.InlineKeyboardButton("🧹 Clear warns", callback_data=f"mod:clear:{uid}")
    )
    bot.reply_to(message, f"🛠 <b>Панель управления:</b> {name}\nID: <code>{uid}</code>", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("mod:"))
def mod_callback(call):
    if not is_admin(call.message.chat.id, call.from_user.id):
        bot.answer_callback_query(call.id, "Ты не админ.", show_alert=True)
        return

    try:
        _, action, uid_raw = call.data.split(":")
        uid = int(uid_raw)
    except Exception:
        bot.answer_callback_query(call.id, "Ошибка кнопки.", show_alert=True)
        return

    name = f"ID {uid}"

    try:
        if action == "warn":
            warn_by_id(call.message.chat.id, uid, name, "кнопка админа")
            bot.answer_callback_query(call.id, "Warn выдан.")
        elif action == "mute":
            mute_member(call.message.chat.id, uid)
            bot.send_message(call.message.chat.id, f"🔇 <b>{name}</b> замьючен на {setting('mute_minutes')} минут.")
            bot.answer_callback_query(call.id, "Mute готов.")
        elif action == "unmute":
            unmute_member(call.message.chat.id, uid)
            bot.send_message(call.message.chat.id, f"🔊 <b>{name}</b> размьючен.")
            bot.answer_callback_query(call.id, "Unmute готов.")
        elif action == "ban":
            bot.ban_chat_member(call.message.chat.id, uid)
            bot.send_message(call.message.chat.id, f"⛔ <b>{name}</b> забанен.")
            bot.answer_callback_query(call.id, "Ban готов.")
        elif action == "kick":
            bot.ban_chat_member(call.message.chat.id, uid)
            bot.unban_chat_member(call.message.chat.id, uid)
            bot.send_message(call.message.chat.id, f"👢 <b>{name}</b> кикнут.")
            bot.answer_callback_query(call.id, "Kick готов.")
        elif action == "clear":
            data["warnings"][str(uid)] = 0
            save_data(data)
            bot.send_message(call.message.chat.id, f"🧹 Варны <b>{name}</b> очищены.")
            bot.answer_callback_query(call.id, "Варны очищены.")
    except Exception as e:
        bot.answer_callback_query(call.id, "Ошибка.", show_alert=True)
        bot.send_message(call.message.chat.id, f"❌ Не сработало: <code>{e}</code>")

@bot.message_handler(content_types=["new_chat_members"])
def new_members(message):
    for user in message.new_chat_members:
        if user.is_bot:
            continue

        if user.id in data.get("pending_bans", []):
            try:
                bot.ban_chat_member(message.chat.id, user.id)
                bot.send_message(message.chat.id, f"⛔ <b>{user.first_name}</b> был в pending bans и сразу забанен.")
                continue
            except Exception:
                pass

        seconds = int(setting("captcha_seconds"))
        captcha_pending[user.id] = message.chat.id

        try:
            bot.restrict_chat_member(
                message.chat.id,
                user.id,
                until_date=int(time.time() + seconds),
                permissions=types.ChatPermissions(can_send_messages=False)
            )
        except Exception:
            pass

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("✅ Я не бот", callback_data=f"captcha:{user.id}"))

        bot.send_message(
            message.chat.id,
            f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n"
            f"Нажми кнопку, чтобы писать.\n\n"
            f"<i>Проверка от Данек кодерочек edition.</i>",
            reply_markup=keyboard
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("captcha:"))
def captcha_callback(call):
    user_id = int(call.data.split(":")[1])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "Это кнопка не для тебя.", show_alert=True)
        return
    captcha_pending.pop(user_id, None)
    try:
        unmute_member(call.message.chat.id, user_id)
    except Exception:
        pass
    try:
        bot.edit_message_text(f"✅ <b>{call.from_user.first_name}</b> прошёл проверку. Добро пожаловать 👻", call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    bot.answer_callback_query(call.id, "Готово!")

@bot.message_handler(content_types=["text"])
def moderation(message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    inc_stat(message.from_user.id, "messages")

    if message.from_user.id in captcha_pending:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            inc_stat(message.from_user.id, "deleted")
        except Exception:
            pass
        bot.send_message(message.chat.id, f"⛔ <b>{message.from_user.first_name}</b>, сначала нажми captcha-кнопку выше.")
        return

    if is_admin(message.chat.id, message.from_user.id):
        return

    # NO flood by normal messages anymore.
    # Only 3 links inside window triggers warn.
    if has_link(message.text):
        inc_stat(message.from_user.id, "links")
        uid = str(message.from_user.id)
        now = time.time()
        window = int(setting("link_window_seconds"))
        limit = int(setting("link_limit"))
        strikes = data.get("link_strikes", {}).get(uid, [])
        strikes = [t for t in strikes if now - t <= window]
        strikes.append(now)
        data["link_strikes"][uid] = strikes
        save_data(data)

        if len(strikes) >= limit:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                inc_stat(message.from_user.id, "deleted")
            except Exception:
                pass
            data["link_strikes"][uid] = []
            save_data(data)
            warn_by_id(message.chat.id, message.from_user.id, message.from_user.first_name, f"{limit} ссылки подряд")
        return

    if has_bad_word(message.text):
        warn_by_id(message.chat.id, message.from_user.id, message.from_user.first_name, "запрещённое/подозрительное слово")
        return

    low = message.text.lower().strip()
    for key, reply in data["custom_replies"].items():
        if key in low:
            bot.reply_to(message, reply)
            return

print("Prizrokoffbot Ultra FIX4 started...")
bot.infinity_polling(skip_pending=True)
