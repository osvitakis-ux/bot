"""
Telegram-бот Репетиторського центру "Константа"
Запуск: python bot.py
Потрібен: pip install python-telegram-bot
"""

import json
import os
import logging
import random
from config import BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_PASSWORD
GAMES_URL = os.environ.get("GAMES_URL", "")  # URL вашого Railway сервісу + /games
from admin import start_admin_in_thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# ═══════════════════════════════════════════════════════════
# НАДСИЛАННЯ ПОДІЙ В ГРУПУ АДМІНА
# ═══════════════════════════════════════════════════════════
async def notify(bot, msg: str):
    """Надіслати повідомлення адміну / у групу."""
    try:
        await bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"notify error: {e}")


# ═══════════════════════════════════════════════════════════
# ДИНАМІЧНЕ ЗАВАНТАЖЕННЯ ДАНИХ З data.json
# ═══════════════════════════════════════════════════════════
DATA_FILE = os.environ.get("DATA_PATH", os.path.join(os.path.dirname(__file__), "data.json"))
_REPO_DATA = os.path.join(os.path.dirname(__file__), "data.json")

def load_db():
    """Завантажити актуальні дані з data.json (Volume або репозиторій)."""
    try:
        if DATA_FILE != _REPO_DATA and not os.path.exists(DATA_FILE):
            if os.path.exists(_REPO_DATA):
                import shutil
                os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
                shutil.copy2(_REPO_DATA, DATA_FILE)
                logging.info(f"✅ Перший запуск: дані скопійовано у Volume")
        target = DATA_FILE if os.path.exists(DATA_FILE) else _REPO_DATA
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Помилка читання data.json: {e}")
        return {}

def get_tutors():   return load_db().get("tutors", {})
def get_branches(): return load_db().get("branches", {})
def get_subjects(): return load_db().get("subjects", {})
def get_tests():    return load_db().get("tests", {})
def get_games():    return load_db().get("games", {})
def get_about():    return load_db().get("about", {})

def build_center_info():
    ab = get_about()
    if ab and ab.get("text"):
        return ab["text"]
    return CENTER_INFO

def save_feedback(user, text, rating):
    """Зберегти відгук у data.json."""
    try:
        d = load_db()
        import datetime
        d.setdefault("feedbacks", []).append({
            "user": f"@{user.username or user.first_name}",
            "text": text,
            "rating": rating,
            "date": datetime.date.today().strftime("%d.%m.%Y")
        })
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Помилка збереження відгуку: {e}")


# ═══════════════════════════════════════════════════════════
# ДАНІ ЦЕНТРУ
# ═══════════════════════════════════════════════════════════
CENTER_INFO = """
🎓 *Репетиторський центр "Константа"*

Ми працюємо з 2010 року та допомагаємо учням 1–11 класів
досягати відмінних результатів у навчанні.

📌 *Наша місія:* Якісна індивідуальна та групова підготовка
в комфортній атмосфері з досвідченими педагогами.

🏆 *Наші досягнення:*
• Понад 2 000 випускників
• 94% учнів успішно складають ЗНО/НМТ
• 15+ років досвіду
• Рейтинг 4.9 ⭐ на Google Maps
"""




# ═══════════════════════════════════════════════════════════
# РЕПЕТИТОРИ
# ─────────────────────────────────────────────────────────
# photo_id — Telegram file_id фото.
#   Як отримати: запустіть бот, надішліть йому фото репетитора,
#   він відповість file_id. Вставте його у поле photo_id.
#   Якщо фото ще немає — залиште порожнім рядком "".
#
# schedule — словник {день: [години]}
#   Використовуйте скорочення: "Пн","Вт","Ср","Чт","Пт","Сб","Нд"
#   Якщо викладач не веде заняття в якийсь день — не включайте його.
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
# ТЕСТИ
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
# ІГРИ
# ═══════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════
# ДОПОМІЖНІ КЛАВІАТУРИ
# ═══════════════════════════════════════════════════════════
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏫 Про центр",       callback_data="about"),
         InlineKeyboardButton("📚 Предмети та ціни", callback_data="subjects")],
        [InlineKeyboardButton("👩‍🏫 Репетитори",      callback_data="tutors"),
         InlineKeyboardButton("📍 Філіали",          callback_data="branches")],
        [InlineKeyboardButton("🎮 Ігри на логіку",  callback_data="games"),
         InlineKeyboardButton("📝 Пройти тест",      callback_data="tests")],
        [InlineKeyboardButton("💬 Відгук",           callback_data="feedback"),
         InlineKeyboardButton("📞 Записатися",       callback_data="enroll")],
    ])

def back_to_menu():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")
    ]])

def nav(back_target="main_menu", back_label="◀️ Назад"):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(back_label, callback_data=back_target),
        InlineKeyboardButton("🏠 Меню",    callback_data="main_menu"),
    ]])


async def safe_edit(q, text, parse_mode="Markdown", reply_markup=None):
    """
    Редагує повідомлення незалежно від того, чи це текстове повідомлення,
    чи фото з підписом. Telegram вимагає різні методи для цих випадків:
    edit_message_text для тексту, edit_message_caption для фото.
    Якщо саме редагування неможливе (наприклад, повідомлення занадто старе),
    надсилає нове повідомлення замість зламаної кнопки.
    """
    try:
        if q.message and q.message.photo:
            await q.edit_message_caption(
                caption=text, parse_mode=parse_mode, reply_markup=reply_markup
            )
        else:
            await safe_edit(q, 
                text, parse_mode=parse_mode, reply_markup=reply_markup
            )
    except Exception as e:
        logging.warning(f"safe_edit fallback (sending new message): {e}")
        await q.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)


# ═══════════════════════════════════════════════════════════
# ДОПОМІЖНІ ФУНКЦІЇ
# ═══════════════════════════════════════════════════════════
def subject_name(key: str) -> str:
    s = get_subjects().get(key, {})
    return f"{s.get('emoji','')} {s.get('name', key)}"

def branch_name(key: str) -> str:
    return get_branches().get(key, {}).get("name", key)

def format_schedule(schedule: dict) -> str:
    lines = []
    day_order = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    for day in day_order:
        if day in schedule:
            hours = "  ".join(schedule[day])
            lines.append(f"  {day}: {hours}")
    return "\n".join(lines) if lines else "  Уточнюйте розклад"


# ═══════════════════════════════════════════════════════════
# ХЕНДЛЕРИ
# ═══════════════════════════════════════════════════════════
async def datacheck(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    import os
    data_file = os.environ.get("DATA_PATH", "not set")
    exists = os.path.exists(data_file) if data_file != "not set" else False
    db = load_db()
    branches = list(db.get("branches", {}).keys())
    await update.message.reply_text(
        f"DATA_PATH: {data_file}\n"
        f"File exists: {exists}\n"
        f"Branch keys: {branches}"
    )

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"Привіт, {user.first_name}! 👋\n\n"
        "Я — бот Репетиторського центру *\"Константа\"* 🎓\n\n"
        "Тут ви можете:\n"
        "• Дізнатися про наш центр та філіали\n"
        "• Переглянути предмети, ціни та репетиторів\n"
        "• Пройти міні-тест з будь-якого предмету\n"
        "• Зіграти в логічні ігри 🎮\n"
        "• Записатися або залишити відгук\n\n"
        "Оберіть розділ 👇"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )

# ── команда для отримання file_id фото ──────────────────
async def get_photo_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Надішліть боту фото — отримаєте file_id для вставки у TUTORS."""
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(
            f"📸 *file_id фото:*\n`{file_id}`\n\n"
            "Скопіюйте це значення і вставте у поле `photo_id` потрібного репетитора у `bot.py`.",
            parse_mode="Markdown"
        )


# ── головний диспетчер кнопок ────────────────────────────
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    try:
        await _route_button(update, ctx, q, data)
    except Exception as e:
        logging.error(f"button_handler error on data='{data}': {e}", exc_info=True)
        try:
            await safe_edit(q, 
                "⚠️ Сталася помилка. Спробуйте ще раз або поверніться в меню.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Головне меню", callback_data="main_menu")
                ]])
            )
        except Exception:
            pass


async def _route_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE, q, data):

    # ── ГОЛОВНЕ МЕНЮ ────────────────────────────────────
    if data == "main_menu":
        await safe_edit(q, 
            "🏠 *Головне меню*\nОберіть розділ:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    # ── ПРО ЦЕНТР ───────────────────────────────────────
    elif data == "about":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📍 Наші філіали", callback_data="branches")],
            [InlineKeyboardButton("🏠 Меню",         callback_data="main_menu")],
        ])
        await safe_edit(q, build_center_info(), parse_mode="Markdown", reply_markup=kb)

    # ── ФІЛІАЛИ ─────────────────────────────────────────
    elif data == "branches":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📍 " + b["name"], callback_data=f"branch_{k}")]
            for k, b in get_branches().items()
        ] + [[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
        await safe_edit(q, 
            "📍 *Наші три філіали*\nОберіть для детальної інформації:",
            parse_mode="Markdown", reply_markup=kb,
        )

    elif data.startswith("branch_") and not data.startswith("branch_filter"):
        bid = data[len("branch_"):]
        b = get_branches().get(bid)
        if b:
            text = (
                f"📍 *{b['name']}*\n\n"
                f"🏠 Адреса: {b['address']}\n"
                f"📞 Телефон: {b['phone']}\n"
                f"🕐 Режим роботи: {b['schedule']}\n"
                f"{b['transport']}"
            )
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗺 Відкрити на Google Maps", url=b["map_url"])],
                [InlineKeyboardButton("👩‍🏫 Репетитори цього філіалу",
                                      callback_data=f"branch_filter_{bid}")],
                [InlineKeyboardButton("📞 Записатися",  callback_data="enroll")],
                [InlineKeyboardButton("◀️ Всі філіали", callback_data="branches"),
                 InlineKeyboardButton("🏠 Меню",        callback_data="main_menu")],
            ])
            await safe_edit(q, text, parse_mode="Markdown", reply_markup=kb)

    # ── ПРЕДМЕТИ ─────────────────────────────────────────
    elif data == "subjects":
        buttons = [
            [InlineKeyboardButton(f"{s['emoji']} {s['name']}", callback_data=f"subj_{k}")]
            for k, s in get_subjects().items()
        ] + [[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        await safe_edit(q, 
            "📚 *Наші предмети*\nОберіть для перегляду програми та цін:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("subj_"):
        key = data[len("subj_"):]
        s = get_subjects().get(key, {})
        if s:
            price_lines = [
                f"  *{grade}:* індив. — {p['індив']} грн | група — {p['група']} грн"
                for grade, p in s["prices"].items()
            ]
            text = (
                f"{s['emoji']} *{s['name']}*\n"
                f"_{s['desc']}_\n\n"
                "💰 *Вартість (1 заняття 60 хв):*\n"
                + "\n".join(price_lines)
                + "\n\n📌 Перше пробне заняття — _безкоштовно!_"
            )
            # знаходимо репетиторів з цього предмету
            subject_tutors = [k for k, t in get_tutors().items() if key in t["subjects"]]
            tutor_btns = []
            if subject_tutors:
                tutor_btns = [[InlineKeyboardButton(
                    f"👩‍🏫 Репетитори: {s['name']}", callback_data=f"tutors_subj_{key}"
                )]]
            test_btn = []
            if key in get_tests():
                test_btn = [[InlineKeyboardButton(
                    f"📝 Пройти тест: {s['name']}", callback_data=f"test_{key}"
                )]]
            kb = InlineKeyboardMarkup(
                tutor_btns + test_btn
                + [[InlineKeyboardButton("📞 Записатися",    callback_data="enroll")]]
                + [[InlineKeyboardButton("◀️ Предмети",      callback_data="subjects"),
                    InlineKeyboardButton("🏠 Меню",          callback_data="main_menu")]]
            )
            await safe_edit(q, text, parse_mode="Markdown", reply_markup=kb)

    # ── РЕПЕТИТОРИ (список) ──────────────────────────────
    elif data == "tutors":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 За предметом",  callback_data="tutors_by_subj"),
             InlineKeyboardButton("🏫 За філіалом",   callback_data="tutors_by_branch")],
            [InlineKeyboardButton("👥 Усі репетитори", callback_data="tutors_all")],
            [InlineKeyboardButton("🏠 Меню",           callback_data="main_menu")],
        ])
        await safe_edit(q, 
            "👩‍🏫 *Наші репетитори*\nЯк шукаємо?",
            parse_mode="Markdown", reply_markup=kb,
        )

    elif data == "tutors_all":
        await show_tutor_list(q, list(get_tutors().keys()), "tutors")

    elif data == "tutors_by_subj":
        subs = get_subjects()
        tutors = get_tutors()
        buttons = [
            [InlineKeyboardButton(f"{subs[k]['emoji']} {subs[k]['name']}",
                                  callback_data=f"tutors_subj_{k}")]
            for k in subs if any(k in t["subjects"] for t in tutors.values())
        ] + [[InlineKeyboardButton("◀️ Назад", callback_data="tutors"),
              InlineKeyboardButton("🏠 Меню",   callback_data="main_menu")]]
        await safe_edit(q, 
            "📚 Оберіть предмет:", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("tutors_subj_"):
        key = data[len("tutors_subj_"):]
        ids = [k for k, t in get_tutors().items() if key in t["subjects"]]
        if ids:
            await show_tutor_list(q, ids, f"tutors_subj_{key}",
                                  title=f"{subject_name(key)} — репетитори")
        else:
            await safe_edit(q, 
                "На жаль, за цим предметом поки немає доступних репетиторів.",
                reply_markup=nav("tutors"),
            )

    elif data == "tutors_by_branch":
        buttons = [
            [InlineKeyboardButton(f"📍 {b['name']}", callback_data=f"branch_filter_{k}")]
            for k, b in get_branches().items()
        ] + [[InlineKeyboardButton("◀️ Назад", callback_data="tutors"),
              InlineKeyboardButton("🏠 Меню",   callback_data="main_menu")]]
        await safe_edit(q, 
            "📍 Оберіть філіал:", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("branch_filter_"):
        bid = data[len("branch_filter_"):]
        def in_branch(t, bid):
            bl = t.get("branches", [t["branch"]] if t.get("branch") else [])
            return bid in bl
        ids = [k for k, t in get_tutors().items() if in_branch(t, bid)]
        bname = branch_name(bid)
        if ids:
            await show_tutor_list(q, ids, f"tutors_by_branch",
                                  title=f"{bname} — репетитори")
        else:
            await safe_edit(q, 
                f"У філіалі «{bname}» поки немає репетиторів у базі.",
                reply_markup=nav("tutors_by_branch"),
            )

    # ── ПРОФІЛЬ РЕПЕТИТОРА ───────────────────────────────
    elif data.startswith("tutor_"):
        tid = data[len("tutor_"):]
        t = get_tutors().get(tid)
        if not t:
            await safe_edit(q, "Репетитора не знайдено.", reply_markup=nav())
            return

        subj_list  = "  ".join(subject_name(s) for s in t["subjects"])
        branches_list = t.get("branches", [t["branch"]] if t.get("branch") else [])
        branch_txt = ", ".join(branch_name(b) for b in branches_list) if branches_list else "—"
        schedule   = format_schedule(t["schedule"])

        caption = (
            f"👩‍🏫 *{t['name']}*\n"
            f"🎓 Досвід: {t['experience']}\n"
            f"🏛 Освіта: {t['education']}\n\n"
            f"📖 *Предмети:*\n  {subj_list}\n\n"
            f"📍 *Філіал:* {branch_txt}\n\n"
            f"🗓 *Вільні години:*\n{schedule}\n\n"
            f"💰 {t['price_note']}\n\n"
            f"💬 _{t['bio']}_"
        )

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Записатися до цього репетитора",
                                  callback_data=f"enroll_tutor_{tid}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="tutors"),
             InlineKeyboardButton("🏠 Меню",  callback_data="main_menu")],
        ])

        user = update.effective_user
        await notify(ctx.bot,
            f"👀 *Переглянуто профіль репетитора*\n"
            f"👤 {user.first_name} (@{user.username or 'без ніку'})\n"
            f"👩‍🏫 {t['name']}\n"
            f"📚 {', '.join(subject_name(s) for s in t['subjects'])}"
        )
        photo_id = t.get("photo_id", "")
        if photo_id and photo_id.startswith("photo_"):
            # Фото завантажено через адмін-панель — беремо з data.json
            d = load_db()
            photo_b64 = d.get("photos", {}).get(photo_id, "")
            if photo_b64:
                import base64, io
                # Decode base64 data URL
                if "," in photo_b64:
                    photo_b64 = photo_b64.split(",", 1)[1]
                photo_bytes = base64.b64decode(photo_b64)
                await q.message.reply_photo(
                    photo=io.BytesIO(photo_bytes),
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=kb,
                )
                await q.message.delete()
            else:
                await safe_edit(q, caption, parse_mode="Markdown", reply_markup=kb)
        elif photo_id:
            # Telegram file_id — надсилаємо напряму
            await q.message.reply_photo(
                photo=photo_id,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=kb,
            )
            await q.message.delete()
        else:
            # фото ще немає — просто текст
            await safe_edit(q, caption, parse_mode="Markdown", reply_markup=kb)

    # ── ЗАПИС ДО КОНКРЕТНОГО РЕПЕТИТОРА ─────────────────
    elif data.startswith("enroll_tutor_"):
        tid = data[len("enroll_tutor_"):]
        t = get_tutors().get(tid, {})
        b = get_branches().get(t.get("branch", ""), {})
        text = (
            f"📞 *Запис до {t.get('name','')}*\n\n"
            f"Телефон філіалу: {b.get('phone','')}\n"
            f"Адреса: {b.get('address','')}\n\n"
            "Або напишіть своє ім'я та зручний час — ми зателефонуємо самі!"
        )
        ctx.user_data["awaiting"] = f"enroll_{tid}"
        await safe_edit(q, text, parse_mode="Markdown", reply_markup=back_to_menu())

    # ── ЗАГАЛЬНИЙ ЗАПИС ──────────────────────────────────
    elif data == "enroll":
        text = (
            "📞 *Записатися на заняття*\n\n"
            "📱 *Телефони:*\n"
            + "\n".join(
                f"• {b['name']}: {b['phone']}"
                for b in get_branches().values()
            )
            + "\n\n💬 Або напишіть ім'я, клас та предмет — ми зателефонуємо!"
        )
        ctx.user_data["awaiting"] = "enroll_general"
        await safe_edit(q, text, parse_mode="Markdown", reply_markup=back_to_menu())

    # ── ІГРИ ─────────────────────────────────────────────
    elif data == "games":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔢 Числові послідовності", callback_data="game_number")],
            [InlineKeyboardButton("🧩 Логічні загадки",       callback_data="game_riddle")],
            [InlineKeyboardButton("🔤 Анаграми",               callback_data="game_anagram")],
            [InlineKeyboardButton("🧠 Задача-головоломка",    callback_data="game_word")],
            [InlineKeyboardButton("🏠 Меню",                   callback_data="main_menu")],
        ])
        await safe_edit(q, 
            "🎮 *Ігри на логіку та кмітливість*\nОберіть тип:",
            parse_mode="Markdown", reply_markup=kb,
        )

    elif data.startswith("game_"):
        gtype = data[len("game_"):]
        if gtype == "word":
            p = random.choice(get_games().get("word", {}).get("problems", [{}]))
        elif gtype in get_games():
            p = random.choice(get_games()[gtype]["problems"])
        else:
            p = None

        if p:
            ctx.user_data["current_game"] = {"type": gtype, **p}
            ctx.user_data["awaiting"] = "game_answer"
            title = get_games().get(gtype, {}).get("name", "🧠 Задача")
            await safe_edit(q, 
                f"{title}\n\n❓ *{p['q']}*\n\n💡 Надішліть відповідь текстом",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔍 Підказка", callback_data="game_hint")],
                    [InlineKeyboardButton("▶️ Ще завдання", callback_data=data)],
                    [InlineKeyboardButton("🎮 Ігри", callback_data="games"),
                     InlineKeyboardButton("🏠 Меню", callback_data="main_menu")],
                ]),
            )

    elif data == "game_hint":
        game = ctx.user_data.get("current_game", {})
        await q.answer(f"💡 {game.get('hint', 'Підказок немає 😅')}", show_alert=True)

    # ── ТЕСТИ ────────────────────────────────────────────
    elif data == "tests":
        buttons = [
            [InlineKeyboardButton(
                f"{get_subjects().get(k, {}).get('emoji','📝')} {t['name']}",
                callback_data=f"test_{k}"
            )]
            for k, t in get_tests().items()
        ] + [[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        await safe_edit(q, 
            "📝 *Міні-тести*\nПо 5 питань — оберіть предмет:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("test_"):
        key = data[len("test_"):]
        if key in get_tests():
            ctx.user_data["test"] = {
                "key": key,
                "name": get_tests()[key]["name"],
                "questions": get_tests()[key]["questions"].copy(),
                "current": 0,
                "score": 0,
            }
            await send_test_question(q, ctx)
        else:
            await safe_edit(q, "🚧 Тест в розробці!", reply_markup=nav("tests"))

    elif data.startswith("ans_"):
        ans_idx = int(data.split("_")[1])
        t = ctx.user_data.get("test", {})
        if t:
            q_data = t["questions"][t["current"]]
            correct = q_data["ans"]
            is_ok = ans_idx == correct
            if is_ok:
                t["score"] += 1
                res = "✅ Правильно!"
            else:
                res = f"❌ Ні. Правильно: *{q_data['opts'][correct]}*"
            t["current"] += 1
            ctx.user_data["test"] = t
            total = len(t["questions"])

            if t["current"] >= total:
                sc = t["score"]
                pct = sc / total * 100
                grade = ("🥇 Чудово!" if pct >= 80 else "👍 Добре!" if pct >= 60
                         else "📚 Варто повторити матеріал")
                user = update.effective_user
                await notify(ctx.bot,
                    f"📝 *Результат тесту*\n"
                    f"👤 {user.first_name} (@{user.username or 'без ніку'})\n"
                    f"📚 Предмет: {t['name']}\n"
                    f"🏆 Результат: *{sc}/{total}* ({pct:.0f}%)\n"
                    f"{grade}"
                )
                await safe_edit(q, 
                    f"{res}\n\n🏁 *Тест завершено!*\n"
                    f"Результат: *{sc}/{total}* ({pct:.0f}%)\n{grade}",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Ще раз",    callback_data=f"test_{t['key']}")],
                        [InlineKeyboardButton("📝 Інший тест", callback_data="tests")],
                        [InlineKeyboardButton("📞 Записатися", callback_data="enroll")],
                        [InlineKeyboardButton("🏠 Меню",       callback_data="main_menu")],
                    ]),
                )
            else:
                await safe_edit(q, 
                    f"{res}\n\n_Питання {t['current']}/{total}..._",
                    parse_mode="Markdown",
                )
                await send_test_question(q, ctx)

    # ── ФІДБЕК ───────────────────────────────────────────
    elif data == "feedback":
        ctx.user_data["awaiting"] = "feedback"
        await safe_edit(q, 
            "💬 *Ваш відгук*\n\nНапишіть, що вам сподобалось або що покращити.\n"
            "_(надішліть текстом)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Скасувати", callback_data="main_menu")
            ]]),
        )

    elif data.startswith("rate_"):
        stars = int(data.split("_")[1])
        feedback_text = ctx.user_data.pop("feedback_text", "")
        user = update.effective_user
        star_str = "⭐" * stars
        admin_msg = (
            f"📬 *Новий відгук!*\n\n"
            f"👤 {user.first_name} {user.last_name or ''} "
            f"(@{user.username or 'без ніку'})\n"
            f"📝 {feedback_text}\n"
            f"Оцінка: {star_str} ({stars}/5)"
        )
        await notify(ctx.bot, admin_msg)
        save_feedback(user, feedback_text, stars)
        ctx.user_data.pop("awaiting", None)
        await safe_edit(q, 
            f"🙏 *Дякуємо за відгук!*\n\n{star_str}\n\nВаша думка дуже важлива для нас!",
            parse_mode="Markdown",
            reply_markup=back_to_menu(),
        )


# ── СПИСОК РЕПЕТИТОРІВ (загальна функція) ────────────────
async def show_tutor_list(q, ids: list, back_target: str, title: str = "Репетитори"):
    buttons = [
        [InlineKeyboardButton(f"👤 {get_tutors()[tid]['name']}", callback_data=f"tutor_{tid}")]
        for tid in ids if tid in get_tutors()
    ] + [[InlineKeyboardButton("◀️ Назад", callback_data=back_target),
          InlineKeyboardButton("🏠 Меню",  callback_data="main_menu")]]
    await safe_edit(q, 
        f"👩‍🏫 *{title}*\nОберіть репетитора для детального профілю:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ── ПИТАННЯ ТЕСТУ ────────────────────────────────────────
async def send_test_question(q, ctx: ContextTypes.DEFAULT_TYPE):
    t = ctx.user_data.get("test", {})
    if not t:
        return
    idx   = t["current"]
    total = len(t["questions"])
    qdata = t["questions"][idx]
    emojis = ["🅰️", "🅱️", "🇨", "🇩"]
    buttons = [
        [InlineKeyboardButton(f"{emojis[i]} {opt}", callback_data=f"ans_{i}")]
        for i, opt in enumerate(qdata["opts"])
    ]
    await safe_edit(q, 
        f"📝 *{t['name']}* | Питання {idx+1}/{total}\n\n❓ {qdata['q']}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ── ТЕКСТОВІ ПОВІДОМЛЕННЯ ────────────────────────────────
async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    awaiting  = ctx.user_data.get("awaiting", "")

    if awaiting == "feedback":
        ctx.user_data["awaiting"] = "rating"
        ctx.user_data["feedback_text"] = user_text
        await update.message.reply_text(
            "Дякуємо! 🙏 Тепер оцініть нас від 1 до 5 ⭐",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⭐",     callback_data="rate_1"),
                InlineKeyboardButton("⭐⭐",   callback_data="rate_2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
                InlineKeyboardButton("⭐⭐⭐⭐",   callback_data="rate_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5"),
            ]]),
        )

    elif awaiting == "game_answer":
        game = ctx.user_data.get("current_game", {})
        correct = game.get("ans", "").lower()
        is_correct = user_text.lower() in correct or correct in user_text.lower()
        if is_correct:
            reply = "✅ *Правильно! Молодець!* 🎉"
            result_emoji = "✅"
        else:
            reply = (f"❌ Не зовсім. Правильна відповідь: *{game.get('ans','?')}*\n"
                     f"💡 {game.get('hint','')}")
            result_emoji = "❌"
        user = update.effective_user
        game_names = {"number": "Числові послідовності", "riddle": "Логічні загадки",
                      "anagram": "Анаграми", "word": "Задача-головоломка"}
        gname = game_names.get(game.get("type",""), "Гра")
        await notify(ctx.bot,
            f"🎮 *Результат гри*\n"
            f"👤 {user.first_name} (@{user.username or 'без ніку'})\n"
            f"🎯 {gname}\n"
            f"❓ {game.get('q','?')}\n"
            f"💬 Відповідь: {user_text}\n"
            f"{result_emoji} {'Правильно!' if is_correct else f'Неправильно. Вірно: {game.get(chr(97)+chr(110)+chr(115),chr(63))}'}"
        )
        ctx.user_data.pop("awaiting", None)
        await update.message.reply_text(
            reply, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🎮 Ще ігри", callback_data="games"),
                InlineKeyboardButton("🏠 Меню",    callback_data="main_menu"),
            ]]),
        )

    elif awaiting and awaiting.startswith("enroll"):
        # заявка на запис (загальна або до репетитора)
        user = update.effective_user
        tid  = awaiting.replace("enroll_", "") if "_" in awaiting else None
        tutor_info = ""
        if tid and tid in get_tutors():
            tutor_info = f"\nРепетитор: {get_tutors()[tid]['name']}"
        admin_msg = (
            f"📋 *Нова заявка на запис!*\n\n"
            f"👤 {user.first_name} {user.last_name or ''} "
            f"(@{user.username or 'без ніку'})\n"
            f"{tutor_info}\n"
            f"📝 {user_text}"
        )
        await notify(ctx.bot, admin_msg)
        ctx.user_data.pop("awaiting", None)
        await update.message.reply_text(
            "📨 Заявку отримано! Ми зателефонуємо вам найближчим часом. 🙏",
            reply_markup=main_menu_keyboard(),
        )

    else:
        if len(user_text) > 3:
            await update.message.reply_text(
                "📨 Повідомлення отримано! Оберіть розділ 👇",
                reply_markup=main_menu_keyboard(),
            )


# ═══════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("datacheck", datacheck))
    app.add_handler(MessageHandler(filters.PHOTO, get_photo_id))   # ← отримання file_id
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    start_admin_in_thread()  # ← запуск веб-панелі адміна
    print("🤖 Бот «Константа» запущено! Натисніть Ctrl+C для зупинки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
