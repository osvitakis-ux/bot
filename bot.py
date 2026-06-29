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

BRANCHES = {
    "branch_1": {
        "name": "Філіал №1 — Центр",
        "address": "вул. Рішельєвська, 15",
        "phone": "+38 (048) 123-45-67",
        "schedule": "Пн–Пт: 9:00–20:00 | Сб: 10:00–18:00",
        "transport": "🚌 Зупинка «Дерибасівська»",
        "map_url": "https://maps.google.com/?q=вул.+Рішельєвська+15+Одеса",
    },
    "branch_2": {
        "name": "Філіал №2 — Північний",
        "address": "вул. Черьомушки, 42",
        "phone": "+38 (048) 234-56-78",
        "schedule": "Пн–Пт: 10:00–20:00 | Сб: 10:00–17:00",
        "transport": "🚌 Зупинка «Черьомушки»",
        "map_url": "https://maps.google.com/?q=вул.+Черьомушки+42+Одеса",
    },
    "branch_3": {
        "name": "Філіал №3 — Таїрова",
        "address": "пр. Глушка, 29",
        "phone": "+38 (048) 345-67-89",
        "schedule": "Пн–Пт: 10:00–20:00 | Нд: 11:00–16:00",
        "transport": "🚌 Зупинка «Таїрова»",
        "map_url": "https://maps.google.com/?q=пр.+Глушка+29+Одеса",
    },
}

SUBJECTS = {
    "math": {
        "emoji": "📐", "name": "Математика",
        "desc": "Алгебра, геометрія, підготовка до НМТ",
        "prices": {
            "1–4 клас":  {"індив": 350, "група": 200},
            "5–8 клас":  {"індив": 400, "група": 230},
            "9–11 клас": {"індив": 500, "група": 280},
        },
    },
    "ukr": {
        "emoji": "🇺🇦", "name": "Українська мова",
        "desc": "Граматика, правопис, диктанти, НМТ",
        "prices": {
            "1–4 клас":  {"індив": 320, "група": 190},
            "5–8 клас":  {"індив": 380, "група": 220},
            "9–11 клас": {"індив": 480, "група": 260},
        },
    },
    "eng": {
        "emoji": "🌍", "name": "Англійська мова",
        "desc": "Граматика, розмовна практика, підготовка до ЄВІ",
        "prices": {
            "1–4 клас":  {"індив": 380, "група": 220},
            "5–8 клас":  {"індив": 430, "група": 250},
            "9–11 клас": {"індив": 520, "група": 290},
        },
    },
    "phys": {
        "emoji": "⚛️", "name": "Фізика",
        "desc": "Механіка, електрика, оптика, НМТ",
        "prices": {
            "5–8 клас":  {"індив": 420, "група": 240},
            "9–11 клас": {"індив": 520, "група": 280},
        },
    },
    "chem": {
        "emoji": "🧪", "name": "Хімія",
        "desc": "Органічна, неорганічна хімія, задачі",
        "prices": {
            "7–8 клас":  {"індив": 400, "група": 230},
            "9–11 клас": {"індив": 500, "група": 270},
        },
    },
    "bio": {
        "emoji": "🧬", "name": "Біологія",
        "desc": "Загальна, анатомія, підготовка до НМТ",
        "prices": {
            "7–8 клас":  {"індив": 380, "група": 210},
            "9–11 клас": {"індив": 480, "група": 260},
        },
    },
    "hist": {
        "emoji": "📜", "name": "Історія України",
        "desc": "Шкільна програма, підготовка до НМТ/ДПА",
        "prices": {
            "5–8 клас":  {"індив": 370, "група": 210},
            "9–11 клас": {"індив": 460, "група": 250},
        },
    },
}


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
TUTORS = {
    "t1": {
        "name": "Олена Василівна Коваль",
        "photo_id": "",   # ← вставте Telegram file_id фото
        "subjects": ["math", "phys"],
        "branch": "branch_1",
        "experience": "12 років",
        "education": "НУ «Одеська Політехніка», мат.-фіз. факультет",
        "bio": (
            "Спеціалізується на підготовці до НМТ з математики та фізики. "
            "Авторська методика вирішення задач підвищеної складності. "
            "Серед її учнів — переможці обласних олімпіад."
        ),
        "schedule": {
            "Пн": ["10:00", "12:00", "16:00", "18:00"],
            "Ср": ["10:00", "14:00", "18:00"],
            "Пт": ["12:00", "16:00", "18:00"],
            "Сб": ["10:00", "12:00"],
        },
        "price_note": "Індивідуально — від 500 грн/год",
    },
    "t2": {
        "name": "Марина Іванівна Петренко",
        "photo_id": "",
        "subjects": ["ukr", "hist"],
        "branch": "branch_1",
        "experience": "8 років",
        "education": "ОНУ ім. Мечникова, філологічний факультет",
        "bio": (
            "Закохана в українську мову та літературу. "
            "Готує учнів до ДПА та НМТ, допомагає з написанням творів. "
            "Використовує ігрові методи для молодших класів."
        ),
        "schedule": {
            "Вт": ["10:00", "14:00", "16:00"],
            "Чт": ["10:00", "14:00", "18:00"],
            "Сб": ["10:00", "12:00", "14:00"],
        },
        "price_note": "Індивідуально — від 480 грн/год",
    },
    "t3": {
        "name": "Джон Сміт (John Smith)",
        "photo_id": "",
        "subjects": ["eng"],
        "branch": "branch_2",
        "experience": "6 років",
        "education": "Native speaker, США. CELTA certificate.",
        "bio": (
            "Носій мови з Нью-Йорка. Практика розмовної англійської, "
            "підготовка до ЄВІ та міжнародних іспитів IELTS/TOEFL. "
            "Захоплюється культурою та кіно."
        ),
        "schedule": {
            "Пн": ["14:00", "16:00", "18:00"],
            "Ср": ["14:00", "16:00"],
            "Пт": ["14:00", "16:00", "18:00"],
            "Нд": ["12:00", "14:00"],
        },
        "price_note": "Індивідуально — від 520 грн/год",
    },
    "t4": {
        "name": "Андрій Олексійович Бондар",
        "photo_id": "",
        "subjects": ["chem", "bio"],
        "branch": "branch_3",
        "experience": "10 років",
        "education": "ОНУ ім. Мечникова, хімічний факультет, к.х.н.",
        "bio": (
            "Кандидат хімічних наук. Веде заняття з хімії та біології "
            "для учнів 7–11 класів. Підготував 50+ вступників до медичних "
            "університетів. Автор власних навчальних посібників."
        ),
        "schedule": {
            "Вт": ["16:00", "18:00"],
            "Чт": ["16:00", "18:00"],
            "Пт": ["10:00", "12:00", "16:00"],
            "Сб": ["10:00", "12:00", "14:00"],
        },
        "price_note": "Індивідуально — від 500 грн/год",
    },
    "t5": {
        "name": "Тетяна Сергіївна Мороз",
        "photo_id": "",
        "subjects": ["math", "eng"],
        "branch": "branch_2",
        "experience": "5 років",
        "education": "ОДУВС, математичний факультет",
        "bio": (
            "Молодий та енергійний педагог. Веде математику для учнів 1–8 класів "
            "та розмовну англійську для початківців. "
            "Учні відзначають її доступне пояснення складних тем."
        ),
        "schedule": {
            "Пн": ["14:00", "16:00", "18:00"],
            "Ср": ["10:00", "12:00", "18:00"],
            "Пт": ["10:00", "16:00"],
            "Нд": ["12:00", "14:00", "16:00"],
        },
        "price_note": "Індивідуально — від 400 грн/год",
    },
}


# ═══════════════════════════════════════════════════════════
# ТЕСТИ
# ═══════════════════════════════════════════════════════════
TESTS = {
    "math": {
        "name": "Математика",
        "questions": [
            {"q": "Скільки буде 15 × 8?", "opts": ["100", "110", "120", "130"], "ans": 2},
            {"q": "Яке число є простим?", "opts": ["9", "15", "17", "21"], "ans": 2},
            {"q": "√169 = ?", "opts": ["11", "12", "13", "14"], "ans": 2},
            {"q": "Площа квадрата зі стороною 7 см?",
             "opts": ["28 см²", "42 см²", "49 см²", "56 см²"], "ans": 2},
            {"q": "0.5² = ?", "opts": ["0.10", "0.25", "0.50", "1.00"], "ans": 1},
        ],
    },
    "ukr": {
        "name": "Українська мова",
        "questions": [
            {"q": "Яке слово пишеться з апострофом?",
             "opts": ["звязок", "зв'язок", "звьязок", "зв'єзок"], "ans": 1},
            {"q": "Вкажіть іменник II відміни:", "opts": ["земля", "ніч", "степ", "мати"], "ans": 2},
            {"q": "Яке речення є складносурядним?",
             "opts": ["Сонце зайшло, і стало темно.", "Хлопець, який сміявся, пішов.",
                      "Ми бачили, як він падав.", "Прийшов би, якби хотів."], "ans": 0},
            {"q": "Скільки літер в українському алфавіті?",
             "opts": ["30", "32", "33", "35"], "ans": 2},
            {"q": "Яке слово належить до архаїзмів?",
             "opts": ["комп'ютер", "рало", "смартфон", "спорт"], "ans": 1},
        ],
    },
    "eng": {
        "name": "Англійська мова",
        "questions": [
            {"q": "She ___ to school every day.",
             "opts": ["go", "goes", "going", "gone"], "ans": 1},
            {"q": "Past tense of 'write'?",
             "opts": ["writed", "wrote", "written", "writ"], "ans": 1},
            {"q": "I have lived here ___ 2010.",
             "opts": ["for", "since", "during", "from"], "ans": 1},
            {"q": "___ Eiffel Tower is in Paris.",
             "opts": ["A", "An", "The", "—"], "ans": 2},
            {"q": "What does 'ambiguous' mean?",
             "opts": ["Certain", "Unclear", "Angry", "Helpful"], "ans": 1},
        ],
    },
    "phys": {
        "name": "Фізика",
        "questions": [
            {"q": "Одиниця вимірювання сили?",
             "opts": ["Джоуль", "Ват", "Ньютон", "Паскаль"], "ans": 2},
            {"q": "Швидкість світла у вакуумі ≈",
             "opts": ["3×10⁶ м/с", "3×10⁸ м/с", "3×10¹⁰ м/с", "3×10¹² м/с"], "ans": 1},
            {"q": "Яке явище описує закон Ома?",
             "opts": ["Тепло", "Струм і напруга", "Тиск", "Магнетизм"], "ans": 1},
            {"q": "При збільшенні температури опір металів:",
             "opts": ["Зменшується", "Не змінюється", "Збільшується", "Стає нулем"], "ans": 2},
            {"q": "Формула кінетичної енергії:",
             "opts": ["mgh", "mv²/2", "ma", "F·d"], "ans": 1},
        ],
    },
    "bio": {
        "name": "Біологія",
        "questions": [
            {"q": "Яка органела відповідає за фотосинтез?",
             "opts": ["Мітохондрія", "Рибосома", "Хлоропласт", "Лізосома"], "ans": 2},
            {"q": "Скільки хромосом у людини (диплоїдний набір)?",
             "opts": ["23", "46", "48", "92"], "ans": 1},
            {"q": "Що таке ДНК?",
             "opts": ["Білок", "Жирна кислота", "Дезоксирибонуклеїнова кислота", "Вуглевод"],
             "ans": 2},
            {"q": "Яку функцію виконує серце?",
             "opts": ["Дихання", "Травлення", "Кровообіг", "Виділення"], "ans": 2},
            {"q": "Хто відкрив клітину?",
             "opts": ["Дарвін", "Гук", "Пастер", "Менделєєв"], "ans": 1},
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# ІГРИ
# ═══════════════════════════════════════════════════════════
LOGIC_GAMES = {
    "number": {
        "name": "🔢 Числові послідовності",
        "problems": [
            {"q": "Продовжіть ряд: 2, 4, 8, 16, __", "ans": "32",
             "hint": "Кожне число множиться на 2"},
            {"q": "Знайдіть наступне: 1, 1, 2, 3, 5, 8, __", "ans": "13",
             "hint": "Послідовність Фібоначчі: сума двох попередніх"},
            {"q": "Продовжіть: 3, 6, 9, 12, __", "ans": "15",
             "hint": "Таблиця множення на 3"},
            {"q": "Наступне число: 100, 90, 81, 73, __", "ans": "66",
             "hint": "Різниця зменшується: 10, 9, 8, 7..."},
            {"q": "Ряд: 2, 6, 12, 20, 30, __", "ans": "42",
             "hint": "n×(n+1): 1×2, 2×3, 3×4..."},
        ],
    },
    "riddle": {
        "name": "🧩 Логічні загадки",
        "problems": [
            {"q": "Чим більше його береш, тим більша яма. Що це?", "ans": "земля",
             "hint": "Подумайте про фізичні предмети"},
            {"q": "Без рук, без ніг, а малює. Що це?", "ans": "мороз",
             "hint": "Взимку на вікнах"},
            {"q": "У мене є міста, але там не живуть люди. Ліси, але немає дерев. "
                   "Вода, але нема риби. Що я?", "ans": "карта",
             "hint": "Географічний інструмент"},
            {"q": "Що стає більшим, якщо його поставити вверх ногами?", "ans": "6 або 9",
             "hint": "Подивіться на цифри"},
            {"q": "Я завжди перед вами, але ніколи не можу бути позаду. Що це?",
             "ans": "майбутнє", "hint": "Час"},
        ],
    },
    "anagram": {
        "name": "🔤 Анаграми",
        "problems": [
            {"q": "Переставте літери слова СОНЦЕ → нове слово:", "ans": "несоc",
             "hint": "5 літер, пов'язано з рослинами"},
            {"q": "ЛІТО → нове слово:", "ans": "тіло",
             "hint": "Синонім тулуба"},
            {"q": "РУКА → нове слово:", "ans": "кура",
             "hint": "Свійський птах"},
            {"q": "МОРЕ → нове слово:", "ans": "ромe",
             "hint": "Невеликий вірш"},
            {"q": "НОРА → нове слово:", "ans": "рано",
             "hint": "Час доби"},
        ],
    },
}

WORD_PROBLEMS = [
    {"q": "Три кури за три дні знесли три яйця. Скільки яєць знесуть 12 курей за 12 днів?",
     "ans": "48", "hint": "1 кура × 1 день = 1/3 яйця → 12 курей × 12 днів = 48"},
    {"q": "Якщо 5 машин виготовляють 5 деталей за 5 хвилин, скільки машин потрібно для "
          "100 деталей за 100 хвилин?",
     "ans": "5", "hint": "1 машина = 1 деталь за 5 хв = 20 за 100 хв → 5 машин"},
    {"q": "У Петра є лише монети по 5 і 2 гривні. Як зібрати рівно 16 грн "
          "найменшою кількістю монет?",
     "ans": "4", "hint": "2×5 + 3×2 = 16 — це 5 монет. Чи є варіант менше?"},
]


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


# ═══════════════════════════════════════════════════════════
# ДОПОМІЖНІ ФУНКЦІЇ
# ═══════════════════════════════════════════════════════════
def subject_name(key: str) -> str:
    s = get_subjects().get(key, {})
    return f"{s.get('emoji','')} {s.get('name', key)}"

def branch_name(key: str) -> str:
    return BRANCHES.get(key, {}).get("name", key)

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

    # ── ГОЛОВНЕ МЕНЮ ────────────────────────────────────
    if data == "main_menu":
        await q.edit_message_text(
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
        await q.edit_message_text(CENTER_INFO, parse_mode="Markdown", reply_markup=kb)

    # ── ФІЛІАЛИ ─────────────────────────────────────────
    elif data == "branches":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📍 " + b["name"], callback_data=f"branch_{k}")]
            for k, b in get_branches().items()
        ] + [[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]])
        await q.edit_message_text(
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
            await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    # ── ПРЕДМЕТИ ─────────────────────────────────────────
    elif data == "subjects":
        buttons = [
            [InlineKeyboardButton(f"{s['emoji']} {s['name']}", callback_data=f"subj_{k}")]
            for k, s in get_subjects().items()
        ] + [[InlineKeyboardButton("🏠 Меню", callback_data="main_menu")]]
        await q.edit_message_text(
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
            await q.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    # ── РЕПЕТИТОРИ (список) ──────────────────────────────
    elif data == "tutors":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 За предметом",  callback_data="tutors_by_subj"),
             InlineKeyboardButton("🏫 За філіалом",   callback_data="tutors_by_branch")],
            [InlineKeyboardButton("👥 Усі репетитори", callback_data="tutors_all")],
            [InlineKeyboardButton("🏠 Меню",           callback_data="main_menu")],
        ])
        await q.edit_message_text(
            "👩‍🏫 *Наші репетитори*\nЯк шукаємо?",
            parse_mode="Markdown", reply_markup=kb,
        )

    elif data == "tutors_all":
        await show_tutor_list(q, list(TUTORS.keys()), "tutors")

    elif data == "tutors_by_subj":
        buttons = [
            [InlineKeyboardButton(f"{SUBJECTS[k]['emoji']} {SUBJECTS[k]['name']}",
                                  callback_data=f"tutors_subj_{k}")]
            for k in get_subjects() if any(k in t["subjects"] for t in TUTORS.values())
        ] + [[InlineKeyboardButton("◀️ Назад", callback_data="tutors"),
              InlineKeyboardButton("🏠 Меню",   callback_data="main_menu")]]
        await q.edit_message_text(
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
            await q.edit_message_text(
                "На жаль, за цим предметом поки немає доступних репетиторів.",
                reply_markup=nav("tutors"),
            )

    elif data == "tutors_by_branch":
        buttons = [
            [InlineKeyboardButton(f"📍 {b['name']}", callback_data=f"branch_filter_{k}")]
            for k, b in get_branches().items()
        ] + [[InlineKeyboardButton("◀️ Назад", callback_data="tutors"),
              InlineKeyboardButton("🏠 Меню",   callback_data="main_menu")]]
        await q.edit_message_text(
            "📍 Оберіть філіал:", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("branch_filter_"):
        bid = data[len("branch_filter_"):]
        ids = [k for k, t in get_tutors().items() if t["branch"] == bid]
        bname = branch_name(bid)
        if ids:
            await show_tutor_list(q, ids, f"tutors_by_branch",
                                  title=f"{bname} — репетитори")
        else:
            await q.edit_message_text(
                f"У філіалі «{bname}» поки немає репетиторів у базі.",
                reply_markup=nav("tutors_by_branch"),
            )

    # ── ПРОФІЛЬ РЕПЕТИТОРА ───────────────────────────────
    elif data.startswith("tutor_"):
        tid = data[len("tutor_"):]
        t = get_tutors().get(tid)
        if not t:
            await q.edit_message_text("Репетитора не знайдено.", reply_markup=nav())
            return

        subj_list  = "  ".join(subject_name(s) for s in t["subjects"])
        branch_txt = branch_name(t["branch"])
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
                await q.edit_message_text(caption, parse_mode="Markdown", reply_markup=kb)
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
            await q.edit_message_text(caption, parse_mode="Markdown", reply_markup=kb)

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
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_menu())

    # ── ЗАГАЛЬНИЙ ЗАПИС ──────────────────────────────────
    elif data == "enroll":
        text = (
            "📞 *Записатися на заняття*\n\n"
            "📱 *Телефони:*\n"
            + "\n".join(
                f"• {b['name']}: {b['phone']}"
                for b in BRANCHES.values()
            )
            + "\n\n💬 Або напишіть ім'я, клас та предмет — ми зателефонуємо!"
        )
        ctx.user_data["awaiting"] = "enroll_general"
        await q.edit_message_text(text, parse_mode="Markdown", reply_markup=back_to_menu())

    # ── ІГРИ ─────────────────────────────────────────────
    elif data == "games":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔢 Числові послідовності", callback_data="game_number")],
            [InlineKeyboardButton("🧩 Логічні загадки",       callback_data="game_riddle")],
            [InlineKeyboardButton("🔤 Анаграми",               callback_data="game_anagram")],
            [InlineKeyboardButton("🧠 Задача-головоломка",    callback_data="game_word")],
            [InlineKeyboardButton("🏠 Меню",                   callback_data="main_menu")],
        ])
        await q.edit_message_text(
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
            title = LOGIC_GAMES.get(gtype, {}).get("name", "🧠 Задача")
            await q.edit_message_text(
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
        await q.edit_message_text(
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
            await q.edit_message_text("🚧 Тест в розробці!", reply_markup=nav("tests"))

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
                await q.edit_message_text(
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
                await q.edit_message_text(
                    f"{res}\n\n_Питання {t['current']}/{total}..._",
                    parse_mode="Markdown",
                )
                await send_test_question(q, ctx)

    # ── ФІДБЕК ───────────────────────────────────────────
    elif data == "feedback":
        ctx.user_data["awaiting"] = "feedback"
        await q.edit_message_text(
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
        await q.edit_message_text(
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
    await q.edit_message_text(
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
    await q.edit_message_text(
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
    app.add_handler(MessageHandler(filters.PHOTO, get_photo_id))   # ← отримання file_id
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    start_admin_in_thread()  # ← запуск веб-панелі адміна
    print("🤖 Бот «Константа» запущено! Натисніть Ctrl+C для зупинки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
