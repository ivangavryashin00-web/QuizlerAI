"""
QuizletBot — handlers.py
Все режимы: SRS, карточки, письменный, тест, смешанный, слабые карточки,
            найди пару, анаграмма, первая буква, пересказ, спринт,
            марафон, чтение, метод Лейтнера
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from study_modes import StudyModes
from spaced_repetition import SM2, AGAIN, HARD, GOOD, EASY
from gamification import Gamification, ACHIEVEMENTS, LEVEL_NAMES
from datetime import datetime
import random

db = Database()

# ── Состояния ────────────────────────────────────────────────────────────────
(
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE,
    STUDY_WRITE, STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU,
    EDIT_CARD, SETTINGS, IMPORT_CARDS, BROWSE_DICTIONARY,
    STUDY_SRS, STUDY_WEAK, STUDY_MATCH,
    STUDY_ANAGRAM, STUDY_FIRST_LETTER, STUDY_RETELLING,
    STUDY_SPRINT, STUDY_MARATHON, STUDY_READING, STUDY_LEITNER,
) = range(22)

# ── Коллекции словаря ────────────────────────────────────────────────────────
COLLECTIONS = {
    "en_basic": ("🇬🇧 Английский — базовый", [
        ("Hello","Привет"),("Goodbye","Пока"),("Thank you","Спасибо"),
        ("Please","Пожалуйста"),("Sorry","Извини"),("Yes","Да"),("No","Нет"),
        ("Good morning","Доброе утро"),("Good night","Спокойной ночи"),
        ("Water","Вода"),("Food","Еда"),("House","Дом"),("Car","Машина"),
        ("Book","Книга"),("Time","Время"),("Day","День"),("Night","Ночь"),
        ("Friend","Друг"),("Family","Семья"),("Work","Работа"),
        ("School","Школа"),("Money","Деньги"),("City","Город"),
        ("Country","Страна"),("Love","Любовь"),("Life","Жизнь"),
        ("Good","Хороший"),("Bad","Плохой"),("Big","Большой"),("Small","Маленький"),
    ]),
    "en_advanced": ("🇬🇧 Английский — продвинутый", [
        ("Ambiguous","Неоднозначный"),("Ephemeral","Мимолётный"),
        ("Eloquent","Красноречивый"),("Pragmatic","Прагматичный"),
        ("Resilient","Устойчивый"),("Nuanced","Нюансированный"),
        ("Obsolete","Устаревший"),("Profound","Глубокий"),
        ("Scrutiny","Тщательная проверка"),("Tenacious","Настойчивый"),
        ("Ubiquitous","Повсеместный"),("Verbose","Многословный"),
        ("Whimsical","Причудливый"),("Zealous","Рьяный"),
        ("Alacrity","Живость"),("Benevolent","Доброжелательный"),
        ("Cynical","Циничный"),("Diligent","Прилежный"),
        ("Eccentric","Эксцентричный"),("Frugal","Бережливый"),
    ]),
    "de_basic": ("🇩🇪 Немецкий — базовый", [
        ("Hallo","Привет"),("Danke","Спасибо"),("Bitte","Пожалуйста"),
        ("Ja","Да"),("Nein","Нет"),("Wasser","Вода"),("Haus","Дом"),
        ("Auto","Машина"),("Buch","Книга"),("Arbeit","Работа"),
        ("Schule","Школа"),("Freund","Друг"),("Tag","День"),
        ("Nacht","Ночь"),("Gut","Хорошо"),("Schlecht","Плохо"),
        ("Essen","Еда"),("Geld","Деньги"),("Stadt","Город"),("Land","Страна"),
    ]),
    "fr_basic": ("🇫🇷 Французский — базовый", [
        ("Bonjour","Здравствуйте"),("Merci","Спасибо"),
        ("S'il vous plaît","Пожалуйста"),("Oui","Да"),("Non","Нет"),
        ("Au revoir","До свидания"),("Eau","Вода"),("Maison","Дом"),
        ("Livre","Книга"),("Ami","Друг"),("Famille","Семья"),
        ("Travail","Работа"),("Ville","Город"),("Pays","Страна"),
        ("Bien","Хорошо"),("Mal","Плохо"),("Voiture","Машина"),
        ("Temps","Время"),("Argent","Деньги"),("Vie","Жизнь"),
    ]),
    "math": ("📐 Математика", [
        ("Периметр прямоугольника","P = 2(a+b)"),
        ("Площадь прямоугольника","S = a·b"),
        ("Площадь круга","S = πr²"),
        ("Теорема Пифагора","a² + b² = c²"),
        ("Дискриминант","D = b² − 4ac"),
        ("Корни квадратного уравнения","x = (−b ± √D) / 2a"),
        ("Сумма углов треугольника","180°"),
        ("π ≈","3.14159"),("e ≈","2.71828"),
        ("sin²α + cos²α","= 1"),
        ("Производная x^n","n·x^(n−1)"),
        ("∫ x dx","x²/2 + C"),
        ("Объём шара","V = 4/3·π·r³"),
        ("Длина окружности","L = 2πr"),
    ]),
    "it_terms": ("💻 IT и программирование", [
        ("Algorithm","Пошаговые инструкции для решения задачи"),
        ("API","Интерфейс программирования приложений"),
        ("Backend","Серверная часть приложения"),
        ("Frontend","Клиентская часть (интерфейс)"),
        ("Database","База данных"),("Git","Система контроля версий"),
        ("HTTP","Протокол передачи гипертекста"),
        ("JSON","Формат обмена данными"),
        ("REST API","Архитектурный стиль веб-сервисов"),
        ("OOP","Объектно-ориентированное программирование"),
        ("CI/CD","Непрерывная интеграция и доставка"),
        ("Cache","Быстрое временное хранилище данных"),
        ("Recursion","Функция, вызывающая саму себя"),
    ]),
    "geography": ("🌍 География мира", [
        ("Столица России","Москва"),("Столица Франции","Париж"),
        ("Столица Германии","Берлин"),("Столица Японии","Токио"),
        ("Столица США","Вашингтон"),("Столица Китая","Пекин"),
        ("Столица Бразилии","Бразилиа"),("Столица Австралии","Канберра"),
        ("Самая длинная река","Нил (~6650 км)"),
        ("Самая высокая гора","Эверест (8849 м)"),
        ("Самый большой океан","Тихий (165 млн км²)"),
        ("Самый большой материк","Евразия"),
        ("Самая большая страна","Россия"),
        ("Самая населённая страна","Индия"),
        ("Самое глубокое место","Марианская впадина (11 км)"),
    ]),
    "biology": ("🧬 Биология", [
        ("ДНК","Носитель генетической информации"),
        ("Митохондрии","Выработка энергии (АТФ) — электростанция клетки"),
        ("Фотосинтез","CO₂+H₂O+свет → глюкоза+O₂"),
        ("Ген","Участок ДНК, кодирующий признак"),
        ("Хромосома","Структура из ДНК и белков, несущая гены"),
        ("Рибосома","Органелла синтеза белка"),
        ("Мейоз","Деление с уменьшением хромосом вдвое"),
        ("Митоз","Деление с сохранением числа хромосом"),
        ("Гемоглобин","Белок крови, переносит кислород"),
        ("Вирус","Неклеточный агент, размножается внутри клеток"),
    ]),
    "history": ("📜 История России", [
        ("Год основания Москвы","1147"),
        ("Куликовская битва","1380 — победа над ордой Мамая"),
        ("Первый царь России","Иван Грозный (1547)"),
        ("Основание Петербурга","1703, Пётр I"),
        ("Война с Наполеоном","Отечественная война 1812 года"),
        ("Отмена крепостного права","1861, Александр II"),
        ("Октябрьская революция","1917"),
        ("Начало ВОВ","22 июня 1941"),
        ("Конец ВОВ","9 мая 1945"),
        ("Полёт Гагарина","12 апреля 1961"),
        ("Распад СССР","26 декабря 1991"),
    ]),
    "business": ("💼 Бизнес и экономика", [
        ("ROI","Return on Investment — возврат на инвестиции"),
        ("KPI","Key Performance Indicator — ключевой показатель"),
        ("B2B","Business to Business"),("B2C","Business to Consumer"),
        ("MVP","Minimum Viable Product"),
        ("SWOT","Strengths, Weaknesses, Opportunities, Threats"),
        ("Маржинальность","Отношение прибыли к выручке"),
        ("Ликвидность","Способность актива быстро стать деньгами"),
        ("Диверсификация","Распределение рисков по разным активам"),
        ("Unit-экономика","Прибыль или убыток на единицу продукта"),
    ]),
}

# ── Вспомогательные функции ──────────────────────────────────────────────────

def kb(buttons): return InlineKeyboardMarkup(buttons)
def btn(text, data): return InlineKeyboardButton(text, callback_data=data)
def pbar(pct, n=8): return '█'*round(pct/100*n)+'░'*(n-round(pct/100*n))
def mode_icon(m): return {'flashcard':'🎴','write':'✍️','quiz':'🎯','srs':'🧠',
    'mixed':'🎮','weak':'💪','match':'🔗','anagram':'🔤','first_letter':'🔡',
    'retelling':'📖','sprint':'⚡','marathon':'🏃','reading':'👁','leitner':'📦'}.get(m,'📖')

def _s(ctx): return ctx.user_data.get('study_session', {})
def _card(ctx):
    s = _s(ctx); cards = s.get('cards', [])
    idx = s.get('current', 0)
    return cards[idx] if idx < len(cards) else {}

def get_main_kb():
    return kb([
        [btn("📚 Мои колоды",       "my_decks"),
         btn("➕ Создать колоду",   "create_deck")],
        [btn("🧠 SRS — повторение", "srs_all"),
         btn("📋 Задания дня",      "daily_tasks")],
        [btn("📖 Словарь",          "browse_dict"),
         btn("📊 Статистика",       "my_stats")],
        [btn("🏆 Рейтинг",          "leaderboard"),
         btn("⚙️ Настройки",       "settings")],
        [btn("❓ Помощь",            "help")],
    ])

# ── Старт ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    db.init_gamification(user.id)
    g = db.get_gamification(user.id)
    lvl = g.get('level', 1)
    em, lname = LEVEL_NAMES.get(lvl, ('🌱', 'Новичок'))
    streak = g.get('current_streak', 0)
    streak_str = f"🔥 {streak} дн." if streak > 0 else "🆕 Начнём!"

    text = (
        f"🎓 *Добро пожаловать, {user.first_name or 'друг'}!*\n\n"
        f"{em} Уровень {lvl} — {lname}   {streak_str}\n\n"
        f"*QuizletBot* — умный тренажёр памяти:\n"
        f"• 🧠 Интервальное повторение (SM-2)\n"
        f"• 🎮 14 режимов изучения\n"
        f"• 🏆 Достижения и таблица лидеров\n"
        f"• 📋 Ежедневные задания\n"
        f"• 📊 Детальная аналитика"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_kb(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=get_main_kb(), parse_mode="Markdown")
    return MAIN_MENU

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = {
        "my_decks": show_decks_menu, "create_deck": start_create_deck,
        "browse_dict": browse_dictionary, "my_stats": show_full_stats,
        "settings": show_settings, "help": show_help,
        "main_menu": start, "daily_tasks": show_daily_tasks,
        "leaderboard": show_leaderboard, "srs_all": show_srs_all,
        "achievements": show_achievements,
    }
    fn = d.get(query.data)
    if fn:
        return await fn(update, context)
    return MAIN_MENU

# ── Мои колоды ───────────────────────────────────────────────────────────────

async def show_decks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    decks = db.get_user_decks(user_id)
    if not decks:
        await update.callback_query.edit_message_text(
            "📚 *У вас пока нет колод*\n\nСоздайте первую или выберите из словаря!",
            reply_markup=kb([[btn("➕ Создать", "create_deck"),
                              btn("📖 Словарь", "browse_dict")],
                             [btn("⬅️ Назад", "main_menu")]]),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    text = "📚 *Ваши колоды:*\n\n"
    buttons = []
    for d in decks:
        st = db.get_deck_srs_stats(user_id, d['deck_id'])
        due = st.get('due', 0)
        bar = pbar(st.get('progress', 0))
        due_tag = f" 🔔{due}" if due > 0 else ""
        text += (f"{d.get('emoji','📖')} *{d['name']}*{due_tag}\n"
                 f"  {bar} {st.get('progress',0)}%  "
                 f"✅{st.get('mastered',0)} 🔄{st.get('learning',0)} 🆕{st.get('new_cards',0)}\n\n")
        label = f"{d.get('emoji','📖')} {d['name']}"
        if due: label += f" 🔔{due}"
        buttons.append([btn(label, f"deck_menu_{d['deck_id']}")])
    buttons.append([btn("➕ Создать", "create_deck"),
                    btn("📖 Словарь", "browse_dict")])
    buttons.append([btn("⬅️ Назад", "main_menu")])
    await update.callback_query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")
    return MAIN_MENU

# ── Меню колоды ──────────────────────────────────────────────────────────────

async def deck_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("deck_menu_"):
        deck_id = int(data.split("_")[2])
        context.user_data['current_deck_id'] = deck_id
        return await show_deck_menu(update, context, deck_id)

    # Роутинг запуска режимов
    mode_dispatch = {
        "study_flash_":        start_flashcard_mode,
        "study_write_":        start_write_mode,
        "study_quiz_":         start_quiz_mode,
        "study_mixed_":        start_mixed_mode,
        "study_srs_":          start_srs_mode,
        "study_weak_":         start_weak_mode,
        "study_match_":        start_match_mode,
        "study_anagram_":      start_anagram_mode,
        "study_first_letter_": start_first_letter_mode,
        "study_retelling_":    start_retelling_mode,
        "study_sprint_":       start_sprint_mode,
        "study_marathon_":     start_marathon_mode,
        "study_reading_":      start_reading_mode,
        "study_leitner_":      start_leitner_mode,
        "study_select_":       select_study_mode,
    }
    for prefix, fn in mode_dispatch.items():
        if data.startswith(prefix):
            return await fn(update, context)

    # Управление колодой
    if data.startswith("add_cards_"):     return await start_add_cards(update, context)
    if data.startswith("list_cards_"):    return await list_cards(update, context)
    if data.startswith("deck_stats_"):    return await show_deck_stats(update, context)
    if data.startswith("delete_deck_"):   return await confirm_delete_deck(update, context)
    if data.startswith("confirm_delete_"):return await do_delete_deck(update, context)

    # Внутри сессии
    if data == "flip_card":               return await handle_flip(update, context)
    if data.startswith("rate_"):          return await handle_rate(update, context)
    if data == "next_card":               return await handle_next(update, context)
    if data == "retry_card":              return await handle_retry(update, context)
    if data.startswith("hint_"):          return await handle_hint(update, context)
    if data == "stop_study":              return await stop_session(update, context)
    if data.startswith("quiz_ans_"):      return await handle_quiz_answer(update, context)
    if data.startswith("match_pick_"):    return await handle_match_pick(update, context)
    if data == "reading_next":            return await handle_reading_next(update, context)
    if data == "reading_prev":            return await handle_reading_prev(update, context)
    if data.startswith("leitner_"):       return await handle_leitner(update, context)
    if data.startswith("marathon_rate_"): return await handle_marathon_rate(update, context)
    if data.startswith("sprint_ans_"):    return await handle_sprint_answer(update, context)

    return DECK_MENU

async def show_deck_menu(update, context, deck_id):
    user_id = update.effective_user.id
    di = db.get_deck_info(deck_id)
    if not di:
        await update.callback_query.edit_message_text("❌ Колода не найдена")
        return MAIN_MENU

    st = db.get_deck_srs_stats(user_id, deck_id)
    due = st.get('due', 0)
    bar = pbar(st.get('progress', 0))
    history = db.get_deck_history(user_id, deck_id, 3)
    hist = ""
    for h in history:
        t = h['correct'] + h['wrong']
        acc = round(h['correct']/t*100) if t else 0
        hist += f"  {mode_icon(h['mode'])} {h['correct']}/{t} ({acc}%) — {h['started_at'][:10]}\n"

    text = (
        f"{di.get('emoji','📖')} *{di['name']}*\n\n"
        f"📊 {bar} {st.get('progress',0)}%\n"
        f"✅ Выучено: {st.get('mastered',0)}  "
        f"🔄 Учится: {st.get('learning',0)}  "
        f"🆕 Новые: {st.get('new_cards',0)}\n"
        f"{'🔔 К повторению: *' + str(due) + '*' if due else '👌 Всё повторено сегодня!'}\n"
        + (f"\n📈 *Последние сессии:*\n{hist}" if hist else "") +
        "\n*Выберите режим:*"
    )

    markup = kb([
        [btn(f"🧠 SRS повторение{' 🔔'+str(due) if due else ''}", f"study_srs_{deck_id}")],
        [btn("🎮 Все режимы", f"study_select_{deck_id}")],
        [btn("➕ Добавить карточки", f"add_cards_{deck_id}")],
        [btn("📋 Список карточек",  f"list_cards_{deck_id}"),
         btn("📊 Аналитика",        f"deck_stats_{deck_id}")],
        [btn("🗑 Удалить",          f"delete_deck_{deck_id}"),
         btn("⬅️ К колодам",        "my_decks")],
    ])
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return DECK_MENU

# ── Выбор режима — главный экран ─────────────────────────────────────────────

async def select_study_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    context.user_data['current_deck_id'] = deck_id
    di = db.get_deck_info(deck_id)
    cards_n = di.get('card_count', 0) if di else 0

    text = (
        f"🎮 *Выберите режим — {di['name'] if di else ''}*\n\n"
        f"📚 Карточек в колоде: {cards_n}\n\n"

        f"*🧠 Умные режимы:*\n"
        f"🧠 SRS — интервальное повторение (рекомендуется)\n"
        f"📦 Лейтнер — 5 ящиков, классический метод\n\n"

        f"*🎯 Режимы проверки:*\n"
        f"🎴 Карточки — переворот и самооценка\n"
        f"✍️ Письменный — вводите ответ\n"
        f"🎯 Тест — 4 варианта ответа\n"
        f"🔡 Первая буква — подсказка по первым буквам\n"
        f"📖 Пересказ — ключевые слова\n\n"

        f"*🎮 Игровые режимы:*\n"
        f"🔗 Найди пару — соедини вопрос и ответ\n"
        f"🔤 Анаграмма — угадай перемешанное слово\n\n"

        f"*⚡ Скоростные:*\n"
        f"⚡ Спринт — 20 карточек на скорость\n"
        f"🏃 Марафон — вся колода без остановки\n"
        f"🎮 Смешанный — чередование режимов\n\n"

        f"*👁 Пассивные:*\n"
        f"👁 Режим чтения — автопросмотр карточек\n"
        f"💪 Работа над ошибками — слабые места"
    )

    markup = kb([
        # Умные
        [btn("🧠 SRS",     f"study_srs_{deck_id}"),
         btn("📦 Лейтнер", f"study_leitner_{deck_id}")],
        # Проверка
        [btn("🎴 Карточки",   f"study_flash_{deck_id}"),
         btn("✍️ Письменный", f"study_write_{deck_id}")],
        [btn("🎯 Тест",        f"study_quiz_{deck_id}"),
         btn("🔡 Первая буква",f"study_first_letter_{deck_id}")],
        [btn("📖 Пересказ",   f"study_retelling_{deck_id}")],
        # Игровые
        [btn("🔗 Найди пару",  f"study_match_{deck_id}"),
         btn("🔤 Анаграмма",   f"study_anagram_{deck_id}")],
        # Скоростные
        [btn("⚡ Спринт",      f"study_sprint_{deck_id}"),
         btn("🏃 Марафон",     f"study_marathon_{deck_id}")],
        [btn("🎮 Смешанный",   f"study_mixed_{deck_id}"),
         btn("💪 Ошибки",      f"study_weak_{deck_id}")],
        # Пассивные
        [btn("👁 Чтение",      f"study_reading_{deck_id}")],
        [btn("⬅️ Назад",       f"deck_menu_{deck_id}")],
    ])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return STUDY_SELECT_MODE

# ── Общие хелперы сессии ─────────────────────────────────────────────────────

def _init_session(ctx, mode, deck_id, cards, user_id=0, **extra):
    ctx.user_data['study_session'] = {
        'mode': mode, 'deck_id': deck_id, 'cards': cards,
        'current': 0, 'correct': 0, 'wrong': 0,
        'flipped': False, 'hint_level': 0, 'streak': 0,
        'started_at': datetime.now().timestamp(),
        'session_id': db.start_session(user_id, deck_id, mode),
        **extra
    }

async def _finish(query, context, user_id):
    s = _s(context)
    correct = int(s.get('correct', 0))
    wrong   = s.get('wrong', 0)
    total   = correct + wrong
    deck_id = s.get('deck_id', 0)
    mode    = s.get('mode', '')
    dur     = int(datetime.now().timestamp() - s.get('started_at', datetime.now().timestamp()))
    sid     = s.get('session_id')
    if sid:
        db.finish_session(sid, correct, wrong, dur)

    events = Gamification.after_session(user_id, correct, wrong, total, mode, dur)
    streak = events.get('streak', 0)
    level  = events.get('level', 1)
    em, ln = LEVEL_NAMES.get(level, ('⭐', ''))
    acc    = round(correct / total * 100) if total else 0
    mins, secs = dur // 60, dur % 60

    lines = [
        f"🏁 *Сессия завершена!*\n",
        f"{mode_icon(mode)} Режим: *{_mode_name(mode)}*",
        f"✅ Правильно: *{correct}/{total}*",
        f"📊 Точность: {pbar(acc, 10)} {acc}%",
        f"⏱ Время: {mins}м {secs}с",
        f"🔥 Серия: {streak} дней",
        f"{em} Уровень: {level} — {ln}",
        f"⭐ Очков за сессию: +{events.get('points', 0)}",
    ]
    if events.get('perfect'):
        lines.append("🏆 *+50 бонус: идеальный результат!*")
    if events.get('speed'):
        lines.append("⚡ *Скоростной бонус!*")
    if events.get('streak_bonus'):
        lines.append(f"🔥 *Бонус серии: +{events['streak_bonus']} очков!*")
    for a in events.get('achievements', []):
        info = ACHIEVEMENTS.get(a, {})
        lines.append(f"🎖 *Новое достижение: {info.get('name', a)}!*")
    if acc >= 90:   lines.append("\n🌟 _Превосходно!_")
    elif acc >= 70: lines.append("\n👍 _Хороший результат!_")
    else:           lines.append("\n💪 _Практика — путь к мастерству!_")

    context.user_data.pop('study_session', None)
    markup = kb([
        [btn("🔄 Ещё раз",  f"study_select_{deck_id}"),
         btn("🧠 SRS",      f"study_srs_{deck_id}")],
        [btn("📊 Аналитика",f"deck_stats_{deck_id}"),
         btn("📚 Колоды",   "my_decks")],
        [btn("🏠 Главная",  "main_menu")],
    ])
    await query.edit_message_text("\n".join(lines), reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

def _mode_name(m):
    return {'flashcard':'Карточки','write':'Письменный','quiz':'Тест','srs':'SRS',
            'mixed':'Смешанный','weak':'Ошибки','match':'Найди пару',
            'anagram':'Анаграмма','first_letter':'Первая буква',
            'retelling':'Пересказ','sprint':'Спринт','marathon':'Марафон',
            'reading':'Чтение','leitner':'Лейтнер'}.get(m, m)

async def stop_session(update, context):
    return await _finish(update.callback_query, context, update.callback_query.from_user.id)

# ── 1. КАРТОЧКИ (Flashcard) ──────────────────────────────────────────────────

async def start_flashcard_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    if not cards:
        await query.answer("❌ В колоде нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'flashcard', deck_id, cards, user_id)
    await _render_flashcard(query, context)
    return STUDY_FLASHCARD

async def _render_flashcard(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    streak_str = f" 🔥{s.get('streak',0)}" if s.get('streak', 0) >= 3 else ""
    if s.get('flipped'):
        text = (f"🎴 *{n}/{total}*{streak_str}\n\n"
                f"❓ {card['question']}\n\n✅ *{card['answer']}*\n\n"
                f"*Насколько хорошо знали?*")
        markup = kb([
            [btn("😰 Снова", "rate_0"), btn("😓 Трудно", "rate_1"),
             btn("🙂 Знаю",  "rate_2"), btn("😄 Легко",  "rate_3")],
            [btn("⏹ Завершить", "stop_study")],
        ])
    else:
        hint = f"\n💡 _{card['hint']}_" if card.get('hint') else ""
        text = (f"🎴 *{n}/{total}*\n\n❓ *{card['question']}*{hint}\n\n"
                f"_Вспомните ответ и переверните_")
        markup = kb([[btn("🔄 Показать ответ", "flip_card")],
                     [btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def handle_flip(update, context):
    s = _s(context)
    if not s: return MAIN_MENU
    s['flipped'] = True
    await _render_flashcard(update.callback_query, context)
    mode_states = {'srs': STUDY_SRS, 'flashcard': STUDY_FLASHCARD,
                   'weak': STUDY_WEAK, 'marathon': STUDY_MARATHON}
    return mode_states.get(s.get('mode'), STUDY_FLASHCARD)

async def handle_rate(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    quality = int(query.data.split("_")[1])
    card = _card(context)
    db.init_card_progress(user_id, card['card_id'])
    SM2.process_answer(user_id, card['card_id'], quality)
    if quality >= GOOD:
        s['correct'] += 1; s['streak'] += 1
        db.update_daily_task(user_id, 'correct_streak', 1)
    else:
        s['wrong'] += 1; s['streak'] = 0
    db.update_daily_task(user_id, 'study_cards', 1)
    s['current'] += 1; s['flipped'] = False; s['hint_level'] = 0
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)
    mode_states = {'srs': STUDY_SRS, 'marathon': STUDY_MARATHON}
    render = {'srs': _render_srs, 'marathon': _render_marathon}
    fn = render.get(s.get('mode'), _render_flashcard)
    await fn(query, context)
    return mode_states.get(s.get('mode'), STUDY_FLASHCARD)

# ── 2. SRS ───────────────────────────────────────────────────────────────────

async def start_srs_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_srs_cards(user_id, deck_id)
    if not cards:
        await query.edit_message_text(
            "🧠 *SRS — всё повторено!*\n\n"
            "✅ Все карточки повторены по расписанию.\n"
            "Возвращайтесь, когда придёт время — бот напомнит!",
            reply_markup=kb([[btn("🎴 Просто повторить", f"study_flash_{deck_id}")],
                             [btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
            parse_mode="Markdown")
        return DECK_MENU
    _init_session(context, 'srs', deck_id, cards, user_id)
    await _render_srs(query, context)
    return STUDY_SRS

async def _render_srs(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    lvl = card.get('level', 0)
    ivl = card.get('interval_days', 1)
    if s.get('flipped'):
        info = f"\n_Уровень SRS: {lvl} | Следующий интервал зависит от оценки_"
        text = (f"🧠 *SRS {n}/{total}*\n\n"
                f"❓ {card['question']}\n\n✅ *{card['answer']}*{info}\n\n"
                f"*Как хорошо знали?*")
        markup = kb([
            [btn("😰 Снова",  "rate_0"), btn("😓 Трудно", "rate_1"),
             btn("🙂 Знаю",   "rate_2"), btn("😄 Легко",  "rate_3")],
            [btn("⏹ Завершить", "stop_study")],
        ])
    else:
        text = (f"🧠 *SRS {n}/{total}*\n\n❓ *{card['question']}*\n\n"
                f"_Уровень: {lvl} | Интервал: {ivl} дн._\n\nВспомните ответ:")
        markup = kb([[btn("🔄 Показать ответ", "flip_card")],
                     [btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

# ── 3. ПИСЬМЕННЫЙ (Write) ────────────────────────────────────────────────────

async def start_write_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    if not cards:
        await query.answer("❌ В колоде нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'write', deck_id, cards, user_id)
    await _render_write(query, context)
    return STUDY_WRITE

async def _render_write(qm, context, is_msg=False):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    streak_str = f" 🔥{s.get('streak',0)}" if s.get('streak',0) >= 3 else ""
    hint = f"\n💡 _{card['hint']}_" if card.get('hint') else ""
    text = (f"✍️ *{n}/{total}*{streak_str}\n\n"
            f"❓ *{card['question']}*{hint}\n\nНапишите ответ:")
    markup = kb([[btn("💡 Подсказка", f"hint_{s['current']}"),
                  btn("⏹ Завершить", "stop_study")]])
    if is_msg:
        await qm.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await qm.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def check_write_answer(update, context):
    user_id = update.effective_user.id
    s = _s(context)
    if not s or s.get('mode') not in ('write', 'mixed', 'weak', 'first_letter',
                                       'retelling', 'anagram', 'sprint'):
        await update.message.reply_text("Используйте меню:", reply_markup=get_main_kb())
        return MAIN_MENU

    mode = s.get('mode')

    # Роутинг по режиму
    if mode == 'first_letter':  return await _check_first_letter(update, context)
    if mode == 'retelling':     return await _check_retelling(update, context)
    if mode == 'anagram':       return await _check_anagram(update, context)
    if mode == 'sprint':        return await _check_sprint_write(update, context)

    # Обычный write / mixed / weak
    user_ans = update.message.text.strip()
    card = _card(context)
    verdict, sim = StudyModes.check_answer(user_ans, card['answer'])
    db.init_card_progress(user_id, card['card_id'])

    if verdict == 'correct':
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        db.update_daily_task(user_id, 'correct_streak', 1)
        text = (f"✅ *Правильно!*{' 🔥'+str(s['streak']) if s['streak']>=3 else ''}\n\n"
                f"Ваш: _{user_ans}_\nПравильный: *{card['answer']}*")
        markup = kb([[btn("➡️ Далее", "next_card")]])
    elif verdict == 'close':
        s['correct'] += 0.5
        SM2.process_answer(user_id, card['card_id'], HARD)
        text = (f"⚠️ *Почти!* ({round(sim*100)}%)\n\n"
                f"Ваш: _{user_ans}_\nПравильный: *{card['answer']}*")
        markup = kb([[btn("🔄 Ещё раз", "retry_card"),
                      btn("➡️ Далее",   "next_card")]])
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
        text = (f"❌ *Неправильно*\n\n"
                f"Ваш: _{user_ans}_\nПравильный: *{card['answer']}*")
        markup = kb([[btn("🔄 Ещё раз", "retry_card"),
                      btn("➡️ Далее",   "next_card")]])

    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    state_map = {'write': STUDY_WRITE, 'mixed': STUDY_FLASHCARD,
                 'weak': STUDY_WEAK}
    return state_map.get(mode, STUDY_WRITE)

# ── 4. ТЕСТ (Quiz) ───────────────────────────────────────────────────────────

async def start_quiz_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    all_cards = db.get_deck_cards(deck_id)
    if len(all_cards) < 2:
        await query.answer("❌ Нужно минимум 2 карточки", show_alert=True); return DECK_MENU
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    _init_session(context, 'quiz', deck_id, cards, user_id, all_cards=all_cards)
    await _render_quiz(query, context)
    return STUDY_QUIZ

async def _render_quiz(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    all_cards = s.get('all_cards', s['cards'])
    streak_str = f" 🔥{s.get('streak',0)}" if s.get('streak',0) >= 3 else ""
    opts = StudyModes.generate_quiz_options(card, all_cards, 4)
    s['_quiz_opts'] = opts
    text = (f"🎯 *Тест {n}/{total}*{streak_str}\n\n"
            f"❓ *{card['question']}*\n\nВыберите ответ:")
    buttons = [[btn((o[:40]+'…' if len(o)>40 else o), f"quiz_ans_{i}")]
               for i, o in enumerate(opts)]
    buttons.append([btn("⏹ Завершить", "stop_study")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")

async def handle_quiz_answer(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    idx = int(query.data.split("_")[2])
    card = _card(context)
    opts = s.get('_quiz_opts', [])
    correct = idx < len(opts) and opts[idx] == card['answer']
    db.init_card_progress(user_id, card['card_id'])
    if correct:
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        db.update_daily_task(user_id, 'correct_streak', 1)
        await query.answer(f"✅ Правильно!{' 🔥'+str(s['streak']) if s['streak']>=3 else ''}")
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer(f"❌ Неверно! Правильный: {card['answer']}", show_alert=True)
    s['current'] += 1
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)
    await _render_quiz(query, context)
    return STUDY_QUIZ

# ── 5. СМЕШАННЫЙ (Mixed) ─────────────────────────────────────────────────────

async def start_mixed_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    if not cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    modes = ['flashcard', 'write', 'quiz'] if len(cards) >= 2 else ['flashcard']
    for c in cards: c['sub_mode'] = random.choice(modes)
    _init_session(context, 'mixed', deck_id, cards, user_id, all_cards=cards)
    db.update_daily_task(user_id, 'use_mode', 1)
    return await _dispatch_mixed(query, context)

async def _dispatch_mixed(query, context):
    s = _s(context); card = _card(context)
    sub = card.get('sub_mode', 'flashcard')
    if sub == 'write':
        await _render_write(query, context); return STUDY_WRITE
    elif sub == 'quiz':
        await _render_quiz(query, context); return STUDY_QUIZ
    else:
        s['flipped'] = False; await _render_flashcard(query, context); return STUDY_FLASHCARD

# ── 6. РАБОТА НАД ОШИБКАМИ (Weak) ───────────────────────────────────────────

async def start_weak_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_weak_cards(user_id, deck_id)
    if not cards: await query.answer("❌ Нет данных об ошибках", show_alert=True); return DECK_MENU
    _init_session(context, 'weak', deck_id, cards, user_id)
    s = _s(context); s['flipped'] = False
    await _render_flashcard(query, context)
    return STUDY_WEAK

# ── 7. НАЙДИ ПАРУ (Match) ────────────────────────────────────────────────────

async def start_match_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    all_cards = db.get_deck_cards(deck_id)
    if len(all_cards) < 3:
        await query.answer("❌ Нужно минимум 3 карточки", show_alert=True); return DECK_MENU
    pair_count = min(5, len(all_cards))
    round_data = StudyModes.prepare_match_round(all_cards, pair_count)
    _init_session(context, 'match', deck_id, all_cards, user_id,
                  match=round_data, all_cards=all_cards, pairs_done=0, total_pairs=pair_count)
    await _render_match(query, context)
    return STUDY_MATCH

async def _render_match(query, context):
    s = _s(context)
    m = s.get('match', {})
    items = m.get('items', [])
    pairs = m.get('pairs', {})
    selected = m.get('selected')
    total = m.get('total', 0)
    matched = m.get('matched', 0)
    mistakes = m.get('mistakes', 0)

    text = (f"🔗 *Найди пару* — {matched}/{total} пар\n"
            f"❌ Ошибок: {mistakes}\n\n"
            f"Нажмите на слово, затем на его пару:")

    buttons = []
    row = []
    for item in items:
        cid = item['card_id']
        is_matched = pairs.get(cid, False)
        is_selected = selected == item['id']
        if is_matched:
            label = f"✅"
        elif is_selected:
            label = f"▶️ {item['text'][:18]}"
        else:
            label = item['text'][:20] + ("…" if len(item['text']) > 20 else "")
        cb = f"match_pick_{item['id']}" if not is_matched else "stop_study"
        row.append(btn(label, cb))
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([btn("⏹ Завершить", "stop_study")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")

async def handle_match_pick(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    m = s.get('match', {})
    picked_id = query.data.replace("match_pick_", "")
    picked_card_id = int(picked_id.split("_")[1])

    if m.get('selected') is None:
        m['selected'] = picked_id
        await query.answer(f"Выбрано: {_match_item_text(m, picked_id)}")
        await _render_match(query, context)
        return STUDY_MATCH

    first_id = m['selected']
    first_card_id = int(first_id.split("_")[1])
    first_type = first_id.split("_")[0]
    second_type = picked_id.split("_")[0]

    m['selected'] = None

    if first_card_id == picked_card_id and first_type != second_type:
        # Правильная пара!
        m['pairs'][first_card_id] = True
        m['matched'] += 1
        s['correct'] += 1; s['streak'] += 1
        db.init_card_progress(user_id, first_card_id)
        SM2.process_answer(user_id, first_card_id, GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer("✅ Верно!")
        if m['matched'] >= m['total']:
            # Раунд завершён — начать новый или финиш
            all_cards = s.get('all_cards', [])
            s['pairs_done'] = s.get('pairs_done', 0) + 1
            if s['pairs_done'] < 3 and len(all_cards) >= 3:
                new_round = StudyModes.prepare_match_round(all_cards, min(5, len(all_cards)))
                s['match'] = new_round
                await query.answer("🎉 Раунд пройден! Следующий...")
                await _render_match(query, context)
            else:
                return await _finish(query, context, user_id)
            return STUDY_MATCH
    else:
        m['mistakes'] += 1
        s['wrong'] += 1; s['streak'] = 0
        first_text = _match_item_text(m, first_id)
        picked_text = _match_item_text(m, picked_id)
        await query.answer(f"❌ Не пара: {first_text} ≠ {picked_text}", show_alert=True)

    await _render_match(query, context)
    return STUDY_MATCH

def _match_item_text(m, item_id):
    for item in m.get('items', []):
        if item['id'] == item_id:
            return item['text'][:20]
    return '?'

# ── 8. АНАГРАММА ────────────────────────────────────────────────────────────

async def start_anagram_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    # Только короткие ответы подходят для анаграммы
    cards = [c for c in cards if 2 < len(c['answer']) <= 20] or cards
    if not cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'anagram', deck_id, cards, user_id)
    await _render_anagram(query, context)
    return STUDY_ANAGRAM

async def _render_anagram(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    anagram = StudyModes.make_anagram(card['answer'])
    s['_anagram'] = anagram
    text = (f"🔤 *Анаграмма {n}/{total}*\n\n"
            f"❓ *{card['question']}*\n\n"
            f"Буквы ответа перемешаны:\n"
            f"🔀 *`{anagram}`*\n\n"
            f"Напишите правильное слово:")
    markup = kb([[btn("💡 Подсказка", f"hint_{s['current']}"),
                  btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def _check_anagram(update, context):
    user_id = update.effective_user.id
    s = _s(context)
    user_ans = update.message.text.strip()
    card = _card(context)
    verdict, sim = StudyModes.check_answer(user_ans, card['answer'])
    db.init_card_progress(user_id, card['card_id'])
    anagram = s.get('_anagram', '?')

    if verdict == 'correct':
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        text = (f"✅ *Правильно!*{' 🔥' + str(s['streak']) if s['streak']>=3 else ''}\n\n"
                f"🔀 `{anagram}` → *{card['answer']}*")
        markup = kb([[btn("➡️ Далее", "next_card")]])
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        text = (f"❌ *Неверно*\n\n"
                f"🔀 `{anagram}`\nПравильно: *{card['answer']}*\nВаш ответ: _{user_ans}_")
        markup = kb([[btn("🔄 Ещё раз", "retry_card"),
                      btn("➡️ Далее",   "next_card")]])
    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return STUDY_ANAGRAM

# ── 9. ПЕРВАЯ БУКВА ───────────────────────────────────────────────────────────

async def start_first_letter_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    if not cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'first_letter', deck_id, cards, user_id)
    await _render_first_letter(query, context)
    return STUDY_FIRST_LETTER

async def _render_first_letter(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    fl = StudyModes.first_letter_hint(card['answer'])
    text = (f"🔡 *Первая буква {n}/{total}*\n\n"
            f"❓ *{card['question']}*\n\n"
            f"Начало ответа: *`{fl}`*\n\n"
            f"Допишите полностью:")
    markup = kb([[btn("💡 Ещё подсказка", f"hint_{s['current']}"),
                  btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def _check_first_letter(update, context):
    user_id = update.effective_user.id
    s = _s(context)
    user_ans = update.message.text.strip()
    card = _card(context)
    verdict, sim = StudyModes.check_answer(user_ans, card['answer'])
    db.init_card_progress(user_id, card['card_id'])
    if verdict in ('correct', 'close'):
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD if verdict=='correct' else HARD)
        db.update_daily_task(user_id, 'study_cards', 1)
        text = f"✅ *Правильно!*\n\nОтвет: *{card['answer']}*"
        markup = kb([[btn("➡️ Далее", "next_card")]])
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        fl = StudyModes.first_letter_hint(card['answer'])
        text = (f"❌ *Неверно*\n\nПодсказка: `{fl}`\nПравильно: *{card['answer']}*\n"
                f"Ваш ответ: _{user_ans}_")
        markup = kb([[btn("🔄 Ещё раз", "retry_card"),
                      btn("➡️ Далее",   "next_card")]])
    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return STUDY_FIRST_LETTER

# ── 10. ПЕРЕСКАЗ (Retelling) ─────────────────────────────────────────────────

async def start_retelling_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_cards(user_id, deck_id, settings=db.get_settings(user_id))
    # Пересказ лучше для длинных ответов
    long_cards = [c for c in cards if len(c['answer']) > 10] or cards
    if not long_cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'retelling', deck_id, long_cards, user_id)
    await _render_retelling(query, context)
    return STUDY_RETELLING

async def _render_retelling(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    # Show answer briefly, then ask to retell
    if s.get('_show_answer'):
        s['_show_answer'] = False
        text = (f"📖 *Пересказ {n}/{total}*\n\n"
                f"❓ *{card['question']}*\n\n"
                f"Изучите ответ:\n_{card['answer']}_\n\n"
                f"Теперь закройте и перескажите своими словами:")
        markup = kb([[btn("✍️ Готов пересказать", f"hint_{s['current']}")],
                     [btn("⏹ Завершить", "stop_study")]])
    else:
        text = (f"📖 *Пересказ {n}/{total}*\n\n"
                f"❓ *{card['question']}*\n\n"
                f"Перескажите ответ своими словами.\n"
                f"_Ключевые слова будут проверены автоматически_")
        markup = kb([[btn("👁 Показать ответ", f"hint_{s['current']}"),
                      btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def _check_retelling(update, context):
    user_id = update.effective_user.id
    s = _s(context)
    user_text = update.message.text.strip()
    card = _card(context)
    ok, found, missing = StudyModes.check_retelling(user_text, card['answer'])
    db.init_card_progress(user_id, card['card_id'])
    if ok:
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        found_str = ', '.join(f'*{w}*' for w in found[:5])
        text = (f"✅ *Отлично!* Ключевые слова найдены:\n{found_str}\n\n"
                f"Полный ответ: _{card['answer']}_")
        markup = kb([[btn("➡️ Далее", "next_card")]])
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], HARD)
        miss_str = ', '.join(f'_{w}_' for w in missing[:5])
        text = (f"⚠️ *Неполно* — пропущены слова:\n{miss_str}\n\n"
                f"Правильный ответ: *{card['answer']}*")
        markup = kb([[btn("🔄 Попробовать снова", "retry_card"),
                      btn("➡️ Далее", "next_card")]])
    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return STUDY_RETELLING

# ── 11. СПРИНТ (Sprint) ──────────────────────────────────────────────────────

async def start_sprint_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    all_cards = db.get_deck_cards(deck_id)
    if len(all_cards) < 2:
        await query.answer("❌ Нужно минимум 2 карточки", show_alert=True); return DECK_MENU
    cards = random.sample(all_cards, min(20, len(all_cards)))
    _init_session(context, 'sprint', deck_id, cards, user_id, all_cards=all_cards)
    await _render_sprint(query, context)
    return STUDY_SPRINT

async def _render_sprint(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    elapsed = int(datetime.now().timestamp() - s.get('started_at', datetime.now().timestamp()))
    time_left = max(0, 60 - elapsed)
    all_cards = s.get('all_cards', s['cards'])
    opts = StudyModes.generate_quiz_options(card, all_cards, 4)
    s['_sprint_opts'] = opts
    text = (f"⚡ *Спринт {n}/{total}*\n"
            f"⏱ Осталось: *{time_left}с*  ✅{s['correct']} ❌{s['wrong']}\n\n"
            f"❓ *{card['question']}*")
    buttons = [[btn((o[:35]+'…' if len(o)>35 else o), f"sprint_ans_{i}")]
               for i, o in enumerate(opts)]
    buttons.append([btn("⏹ Стоп", "stop_study")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")

async def handle_sprint_answer(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    # Проверяем время
    elapsed = int(datetime.now().timestamp() - s.get('started_at', 0))
    if elapsed > 60:
        await query.answer("⏰ Время вышло!")
        return await _finish(query, context, user_id)
    idx = int(query.data.split("_")[2])
    card = _card(context)
    opts = s.get('_sprint_opts', [])
    correct = idx < len(opts) and opts[idx] == card['answer']
    db.init_card_progress(user_id, card['card_id'])
    if correct:
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer("✅")
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        await query.answer(f"❌ {card['answer']}", show_alert=False)
    s['current'] += 1
    if s['current'] >= len(s['cards']) or elapsed > 60:
        return await _finish(query, context, user_id)
    await _render_sprint(query, context)
    return STUDY_SPRINT

async def _check_sprint_write(update, context):
    # Sprint текстом — не используется, но на случай
    return await check_write_answer(update, context)

# ── 12. МАРАФОН (Marathon) ───────────────────────────────────────────────────

async def start_marathon_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = db.get_deck_cards(deck_id)
    if not cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    random.shuffle(cards)
    _init_session(context, 'marathon', deck_id, cards, user_id)
    text = (f"🏃 *Марафон — {len(cards)} карточек*\n\n"
            f"Вся колода без остановки.\n"
            f"Оценивайте себя честно — результат запишется в SRS.\n\n"
            f"Готовы?")
    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("▶️ Начать", "flip_card")],
                         [btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
        parse_mode="Markdown"
    )
    s = _s(context); s['flipped'] = False
    await _render_marathon(query, context)
    return STUDY_MARATHON

async def _render_marathon(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    pct = round(n / total * 100)
    bar = pbar(pct, 10)
    if s.get('flipped'):
        text = (f"🏃 *Марафон {n}/{total}*  {bar} {pct}%\n\n"
                f"❓ {card['question']}\n\n✅ *{card['answer']}*\n\n"
                f"Знали?")
        markup = kb([
            [btn("✅ Да", "marathon_rate_good"),
             btn("❌ Нет", "marathon_rate_again")],
            [btn("⏹ Стоп", "stop_study")],
        ])
    else:
        text = (f"🏃 *Марафон {n}/{total}*  {bar} {pct}%\n\n"
                f"❓ *{card['question']}*")
        markup = kb([[btn("🔄 Показать", "flip_card")],
                     [btn("⏹ Стоп", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def handle_marathon_rate(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    result = query.data.split("_")[2]
    card = _card(context)
    db.init_card_progress(user_id, card['card_id'])
    if result == 'good':
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
    else:
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
    s['current'] += 1; s['flipped'] = False
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)
    await _render_marathon(query, context)
    return STUDY_MARATHON

# ── 13. РЕЖИМ ЧТЕНИЯ (Reading) ───────────────────────────────────────────────

async def start_reading_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = db.get_deck_cards(deck_id)
    if not cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU
    _init_session(context, 'reading', deck_id, cards, user_id)
    await _render_reading(query, context)
    return STUDY_READING

async def _render_reading(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    bar = pbar(round(n/total*100), 10)
    text = (f"👁 *Чтение {n}/{total}*\n{bar}\n\n"
            f"❓ *{card['question']}*\n\n"
            f"✅ {card['answer']}"
            + (f"\n\n💡 _{card['hint']}_" if card.get('hint') else ""))
    markup = kb([
        [btn("⬅️ Назад", "reading_prev"),
         btn("➡️ Вперёд", "reading_next")],
        [btn("⏹ Завершить", "stop_study")],
    ])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def handle_reading_next(update, context):
    s = _s(context)
    if not s: return MAIN_MENU
    s['current'] = min(s['current'] + 1, len(s['cards']) - 1)
    if s['current'] >= len(s['cards']) - 1 and s['current'] == len(s['cards']) - 1:
        s['correct'] = len(s['cards'])  # считаем все просмотренными
    await _render_reading(update.callback_query, context)
    return STUDY_READING

async def handle_reading_prev(update, context):
    s = _s(context)
    if not s: return MAIN_MENU
    s['current'] = max(0, s['current'] - 1)
    await _render_reading(update.callback_query, context)
    return STUDY_READING

# ── 14. МЕТОД ЛЕЙТНЕРА ───────────────────────────────────────────────────────

LEITNER_BOXES = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}  # box -> interval days

async def start_leitner_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    all_cards = db.get_deck_cards(deck_id)
    if not all_cards: await query.answer("❌ Нет карточек", show_alert=True); return DECK_MENU

    # Инициализируем leitner_boxes в user_data если нет
    if 'leitner' not in context.user_data or context.user_data.get('leitner_deck') != deck_id:
        context.user_data['leitner'] = {str(c['card_id']): 1 for c in all_cards}
        context.user_data['leitner_deck'] = deck_id

    boxes = context.user_data['leitner']
    # Выбираем карточки из ящика 1 (новые/провальные) и пропорционально из остальных
    due_cards = []
    for c in all_cards:
        box = boxes.get(str(c['card_id']), 1)
        c['leitner_box'] = box
        if box == 1:
            due_cards.append(c)
        elif box == 2 and random.random() < 0.6:
            due_cards.append(c)
        elif box == 3 and random.random() < 0.3:
            due_cards.append(c)
        elif box >= 4 and random.random() < 0.15:
            due_cards.append(c)

    if not due_cards:
        due_cards = random.sample(all_cards, min(10, len(all_cards)))
        for c in due_cards: c['leitner_box'] = boxes.get(str(c['card_id']), 1)

    random.shuffle(due_cards)
    cards = due_cards[:20]
    _init_session(context, 'leitner', deck_id, cards, user_id)
    s = _s(context); s['flipped'] = False
    await _render_leitner(query, context)
    return STUDY_LEITNER

async def _render_leitner(query, context):
    s = _s(context); card = _card(context)
    n, total = s['current'] + 1, len(s['cards'])
    box = card.get('leitner_box', 1)
    boxes_vis = ' '.join(['📦' if i <= box else '📭' for i in range(1, 6)])
    if s.get('flipped'):
        text = (f"📦 *Лейтнер {n}/{total}*\n"
                f"Ящик: {boxes_vis} ({box}/5)\n\n"
                f"❓ {card['question']}\n\n✅ *{card['answer']}*\n\n"
                f"Знали?")
        markup = kb([
            [btn("✅ Знал → ящик выше",  "leitner_correct"),
             btn("❌ Не знал → ящик 1",  "leitner_wrong")],
            [btn("⏹ Завершить", "stop_study")],
        ])
    else:
        text = (f"📦 *Лейтнер {n}/{total}*\n"
                f"Ящик: {boxes_vis} ({box}/5)\n\n"
                f"❓ *{card['question']}*")
        markup = kb([[btn("🔄 Показать ответ", "flip_card")],
                     [btn("⏹ Завершить", "stop_study")]])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def handle_leitner(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    result = query.data.replace("leitner_", "")
    card = _card(context)
    boxes = context.user_data.get('leitner', {})
    cid_str = str(card['card_id'])
    curr_box = boxes.get(cid_str, 1)
    db.init_card_progress(user_id, card['card_id'])

    if result == 'correct':
        new_box = min(curr_box + 1, 5)
        boxes[cid_str] = new_box
        s['correct'] += 1; s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer(f"✅ Ящик {curr_box} → {new_box}")
        if new_box == 5 and curr_box < 5:
            await query.answer("🏆 Ящик 5 — почти выучено!", show_alert=True)
    else:
        boxes[cid_str] = 1
        s['wrong'] += 1; s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer(f"❌ Возврат в ящик 1")

    context.user_data['leitner'] = boxes
    s['current'] += 1; s['flipped'] = False
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)
    await _render_leitner(query, context)
    return STUDY_LEITNER

# ── Навигация внутри сессий ───────────────────────────────────────────────────

async def handle_next(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _s(context)
    if not s: return MAIN_MENU
    s['current'] += 1; s['hint_level'] = 0
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)
    mode = s.get('mode')
    renders = {
        'write':        (_render_write,        STUDY_WRITE),
        'quiz':         (_render_quiz,          STUDY_QUIZ),
        'srs':          (_render_srs,           STUDY_SRS),
        'anagram':      (_render_anagram,       STUDY_ANAGRAM),
        'first_letter': (_render_first_letter,  STUDY_FIRST_LETTER),
        'retelling':    (_render_retelling,     STUDY_RETELLING),
        'marathon':     (_render_marathon,      STUDY_MARATHON),
        'leitner':      (_render_leitner,       STUDY_LEITNER),
    }
    if mode in renders:
        fn, state = renders[mode]
        await fn(query, context); return state
    elif mode == 'mixed':
        return await _dispatch_mixed(query, context)
    else:
        s['flipped'] = False
        await _render_flashcard(query, context)
        return STUDY_FLASHCARD

async def handle_retry(update, context):
    query = update.callback_query
    s = _s(context)
    if not s: return MAIN_MENU
    mode = s.get('mode', 'write')
    if mode in ('write', 'mixed', 'weak'):
        await _render_write(query, context); return STUDY_WRITE
    elif mode == 'anagram':
        await _render_anagram(query, context); return STUDY_ANAGRAM
    elif mode == 'first_letter':
        await _render_first_letter(query, context); return STUDY_FIRST_LETTER
    elif mode == 'retelling':
        await _render_retelling(query, context); return STUDY_RETELLING
    return STUDY_WRITE

async def handle_hint(update, context):
    query = update.callback_query
    s = _s(context)
    if not s: return STUDY_WRITE
    card = _card(context)
    mode = s.get('mode', 'write')

    if mode == 'retelling':
        # Показать ответ для изучения
        s['_show_answer'] = True
        await _render_retelling(query, context)
        return STUDY_RETELLING

    level = s.get('hint_level', 0) + 1
    s['hint_level'] = level
    hint = StudyModes.get_hint(card['answer'], level)
    await query.answer(f"💡 {hint}", show_alert=True)
    return mode_to_state(mode)

def mode_to_state(mode):
    return {'write': STUDY_WRITE, 'first_letter': STUDY_FIRST_LETTER,
            'anagram': STUDY_ANAGRAM, 'retelling': STUDY_RETELLING,
            'sprint': STUDY_SPRINT}.get(mode, STUDY_WRITE)

# ── Управление карточками ────────────────────────────────────────────────────

async def start_add_cards(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = di['name'] if di else 'Колода'
    text = (f"➕ *Добавление карточек*\n\nКолода: *{di['name']}*\n\n"
            f"Форматы:\n"
            f"`Вопрос | Ответ`\n"
            f"`Вопрос | Ответ | Подсказка`\n\n"
            f"Примеры:\n`Hello | Привет`\n"
            f"`Столица Японии | Токио | Остров Хонсю`\n\n"
            f"Напишите «*готово*» для завершения.")
    await query.edit_message_text(text,
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown")
    return ADD_CARD

async def list_cards(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    cards = db.get_deck_cards(deck_id)
    di = db.get_deck_info(deck_id)
    if not cards:
        await query.answer("В колоде нет карточек", show_alert=True); return DECK_MENU
    text = f"📋 *{di['name']}* — {len(cards)} карточек:\n\n"
    for i, c in enumerate(cards[:25], 1):
        q = c['question'][:35] + "…" if len(c['question'])>35 else c['question']
        a = c['answer'][:35]   + "…" if len(c['answer'])>35   else c['answer']
        text += f"*{i}.* {q}\n   ✅ {a}\n"
    if len(cards) > 25: text += f"\n_...ещё {len(cards)-25} карточек_"
    await query.edit_message_text(text,
        reply_markup=kb([[btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
        parse_mode="Markdown")
    return DECK_MENU

async def confirm_delete_deck(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    await query.edit_message_text(
        f"⚠️ *Удалить «{di['name']}»?*\n\n"
        f"*{di['card_count']}* карточек и весь прогресс будут удалены.\n*Необратимо!*",
        reply_markup=kb([[btn("🗑 Да, удалить", f"confirm_delete_{deck_id}"),
                          btn("❌ Отмена", f"deck_menu_{deck_id}")]]),
        parse_mode="Markdown")
    return DECK_MENU

async def do_delete_deck(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    deck_id = int(query.data.split("_")[2])
    db.delete_deck(deck_id, user_id)
    await query.answer("✅ Колода удалена")
    return await show_decks_menu(update, context)

async def show_deck_stats(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    st = db.get_deck_srs_stats(user_id, deck_id)
    history = db.get_deck_history(user_id, deck_id, 7)
    weak = db.get_weak_cards(user_id, deck_id, 5)
    bar = pbar(st.get('progress', 0))
    hist_str = "".join(f"  {mode_icon(h['mode'])} {h['correct']}/{h['correct']+h['wrong']} "
                       f"({round(h['correct']/(h['correct']+h['wrong'])*100) if h['correct']+h['wrong'] else 0}%) "
                       f"— {h['started_at'][:10]}\n" for h in history)
    weak_str = "".join(f"  ❗ _{w['question']}_ — {round(w.get('accuracy',0)*100)}% верных\n"
                       for w in weak[:3])
    text = (f"📊 *{di['name']}*\n\n"
            f"{bar} {st.get('progress',0)}%\n"
            f"✅ {st.get('mastered',0)}  🔄 {st.get('learning',0)}  "
            f"🆕 {st.get('new_cards',0)}  🔔 {st.get('due',0)}\n\n"
            + (f"📅 *Сессии:*\n{hist_str}\n" if hist_str else "") +
            (f"⚠️ *Сложные:*\n{weak_str}" if weak_str else ""))
    await query.edit_message_text(text,
        reply_markup=kb([[btn("💪 Отработать слабые", f"study_weak_{deck_id}"),
                          btn("🧠 SRS", f"study_srs_{deck_id}")],
                         [btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
        parse_mode="Markdown")
    return DECK_MENU

# ── Создание колоды ───────────────────────────────────────────────────────────

DECK_EMOJIS = ["📖","🌍","🔬","💻","🎵","🏛","📐","💼","🌿","🎨","🏆","🔤","🧬","🗺","⚗️"]

async def start_create_deck(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *Создание новой колоды*\n\nВведите название:\n"
        "_Например: «Английский B2», «Анатомия», «История»_",
        reply_markup=kb([[btn("❌ Отмена", "main_menu")]]),
        parse_mode="Markdown")
    return CREATE_DECK

async def create_deck_name(update, context):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Слишком короткое. Введите снова:"); return CREATE_DECK
    if len(name) > 50:
        await update.message.reply_text("❌ Максимум 50 символов:"); return CREATE_DECK
    emoji = random.choice(DECK_EMOJIS)
    deck_id = db.create_deck(user_id, name, emoji=emoji)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = name
    text = (f"✅ *{emoji} Колода «{name}» создана!*\n\n"
            f"Добавьте карточки:\n"
            f"`Вопрос | Ответ`  или  `Вопрос | Ответ | Подсказка`\n\n"
            f"Напишите «готово» для завершения.")
    await update.message.reply_text(text,
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown")
    return ADD_CARD

async def add_card_to_deck(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text.lower() in ('готово', 'done', 'stop'):
        return await finish_adding_cards(update, context)
    if '|' not in text:
        await update.message.reply_text(
            "❌ Формат: `Вопрос | Ответ` или `Вопрос | Ответ | Подсказка`",
            parse_mode="Markdown"); return ADD_CARD
    parts = [p.strip() for p in text.split('|')]
    question, answer = parts[0], parts[1] if len(parts) > 1 else ''
    hint = parts[2] if len(parts) > 2 else None
    if not question or not answer:
        await update.message.reply_text("❌ Вопрос и ответ не могут быть пустыми!"); return ADD_CARD
    deck_id = context.user_data.get('new_deck_id')
    if not deck_id:
        await update.message.reply_text("❌ Ошибка. Начните заново /start"); return MAIN_MENU
    card_id = db.add_card(deck_id, question, answer, hint)
    db.init_card_progress(user_id, card_id)
    count = len(db.get_deck_cards(deck_id))
    hint_str = f"\n💡 _{hint}_" if hint else ""
    await update.message.reply_text(
        f"✅ *Карточка {count} добавлена*\n\n❓ {question}\n✅ {answer}{hint_str}\n\nСледующую или «готово»:",
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown")
    return ADD_CARD

async def finish_adding_cards(update, context):
    deck_id = context.user_data.get('new_deck_id')
    name    = context.user_data.get('new_deck_name', 'Колода')
    di = db.get_deck_info(deck_id) if deck_id else None
    count = di['card_count'] if di else 0
    text = (f"🎉 *«{name}» готова!*\n\n📝 Карточек: {count}\n\n"
            f"_Совет: начните с SRS — алгоритм сам построит расписание!_")
    markup = kb([
        [btn("🧠 SRS — начать",  f"study_srs_{deck_id}"),
         btn("🎮 Все режимы",    f"study_select_{deck_id}")],
        [btn("📚 Мои колоды", "my_decks")],
    ])
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

# ── Словарь ───────────────────────────────────────────────────────────────────

async def browse_dictionary(update, context):
    query = update.callback_query
    if query.data.startswith("import_collection_"):
        return await import_collection(update, context)
    text = "📖 *Готовые коллекции*\n\nВыберите и добавьте в свои колоды:"
    buttons = [[btn(f"{name} ({len(cards)} карт.)", f"import_collection_{key}")]
               for key, (name, cards) in COLLECTIONS.items()]
    buttons.append([btn("⬅️ Назад", "main_menu")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")
    return BROWSE_DICTIONARY

async def import_collection(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    key = query.data.replace("import_collection_", "")
    col = COLLECTIONS.get(key)
    if not col:
        await query.answer("❌ Не найдено", show_alert=True); return BROWSE_DICTIONARY
    name, cards = col
    deck_id = db.create_deck(user_id, name, emoji="📖")
    for q, a in cards:
        cid = db.add_card(deck_id, q, a)
        db.init_card_progress(user_id, cid)
    text = (f"✅ *Импортировано!*\n\n📖 {name}\n📝 {len(cards)} карточек\n\n"
            f"_Начните с SRS для умного повторения!_")
    await query.edit_message_text(text,
        reply_markup=kb([[btn("🧠 SRS — начать",  f"study_srs_{deck_id}"),
                          btn("🎮 Все режимы",    f"study_select_{deck_id}")],
                         [btn("📖 Ещё",  "browse_dict"),
                          btn("📚 Колоды","my_decks")]]),
        parse_mode="Markdown")
    return MAIN_MENU

# ── Статистика ────────────────────────────────────────────────────────────────

async def show_full_stats(update, context):
    user_id = update.callback_query.from_user.id if update.callback_query else update.effective_user.id
    stats = db.get_user_stats(user_id)
    g = db.get_gamification(user_id)
    activity = db.get_weekly_activity(user_id)
    from datetime import date, timedelta
    days_map = {r['day']: r['cards'] for r in activity}
    week_str = ""
    for i in range(6, -1, -1):
        d = str(date.today() - timedelta(days=i))
        cnt = days_map.get(d, 0)
        bar = pbar(min(cnt, 30), 5)
        week_str += f"`{d[5:]}` {bar} {cnt}\n"
    last = (stats.get('last_studied') or '')[:10] or 'Никогда'
    total_min = stats.get('total_time_s', 0) // 60
    text = (f"📊 *Ваша статистика*\n\n"
            f"{Gamification.format_level(user_id)}\n\n"
            f"📚 *Обучение:*\n"
            f"• Колод: {stats.get('decks_count',0)}\n"
            f"• Сессий: {stats.get('total_sessions',0)}\n"
            f"• Правильных: {stats.get('total_correct',0)}\n"
            f"• Точность: {stats.get('accuracy',0)}%\n"
            f"• Время: {total_min} мин\n"
            f"• Последний раз: {last}\n\n"
            f"🔥 Серия: {g.get('current_streak',0)} дн. (рекорд: {g.get('max_streak',0)})\n"
            f"📅 Всего дней: {g.get('total_study_days',0)}\n\n"
            f"📆 *7 дней:*\n{week_str}")
    markup = kb([[btn("🏅 Достижения", "achievements"),
                  btn("🏆 Рейтинг",    "leaderboard")],
                 [btn("📋 Задания", "daily_tasks")],
                 [btn("⬅️ Назад", "main_menu")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

async def show_achievements(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    text = f"🏅 *Достижения*\n\n{Gamification.format_achievements(user_id)}"
    await query.edit_message_text(text,
        reply_markup=kb([[btn("⬅️ Назад", "my_stats")]]),
        parse_mode="Markdown")
    return MAIN_MENU

async def show_daily_tasks(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    streak = db.get_gamification(user_id).get('current_streak', 0)
    text = (f"📋 *Задания на сегодня*\n🔥 Серия: {streak} дней\n\n"
            f"{Gamification.format_daily_tasks(user_id)}\n\n"
            f"_Выполняйте каждый день для поддержания серии!_")
    await query.edit_message_text(text,
        reply_markup=kb([[btn("📚 К колодам", "my_decks")],
                         [btn("⬅️ Назад", "main_menu")]]),
        parse_mode="Markdown")
    return MAIN_MENU

async def show_leaderboard(update, context):
    query = update.callback_query
    leaders = db.get_leaderboard(10)
    medals = ['🥇','🥈','🥉','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    text = "🏆 *Таблица лидеров*\n\n"
    if not leaders:
        text += "Пока никого нет — будьте первым!"
    else:
        for i, l in enumerate(leaders):
            name = l.get('first_name') or l.get('username') or f"Игрок {i+1}"
            em, _ = LEVEL_NAMES.get(l.get('level', 1), ('⭐', ''))
            text += (f"{medals[i]} *{name}*\n"
                     f"   {em} Ур.{l.get('level',1)} | "
                     f"⭐{l.get('total_points',0)} | 🔥{l.get('current_streak',0)}д\n")
    await query.edit_message_text(text,
        reply_markup=kb([[btn("⬅️ Назад", "main_menu")]]),
        parse_mode="Markdown")
    return MAIN_MENU

async def show_srs_all(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    decks = db.get_user_decks(user_id)
    if not decks:
        await query.edit_message_text("📚 Нет колод. Создайте первую!",
            reply_markup=kb([[btn("⬅️ Назад", "main_menu")]])); return MAIN_MENU
    text = "🧠 *SRS — сводка по всем колодам:*\n\n"
    buttons = []
    total_due = 0
    for d in decks:
        st = db.get_deck_srs_stats(user_id, d['deck_id'])
        due = st.get('due', 0); total_due += due
        bar = pbar(st.get('progress', 0), 6)
        if due > 0:
            text += f"🔔 *{d['name']}* — {due} к повторению\n   {bar}\n"
            buttons.append([btn(f"🔔 {d['name']} ({due})", f"study_srs_{d['deck_id']}")])
        else:
            text += f"✅ *{d['name']}* — повторено\n   {bar}\n"
    text += f"\n📊 Итого: *{total_due}* карточек к повторению" if total_due else "\n✅ *Всё повторено на сегодня!*"
    buttons.append([btn("⬅️ Назад", "main_menu")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")
    return MAIN_MENU

# ── Настройки ─────────────────────────────────────────────────────────────────

async def show_settings(update, context):
    uid = update.callback_query.from_user.id if update.callback_query else update.effective_user.id
    s = db.get_settings(uid)
    notif = "✅" if s.get('notifications', 1) else "❌"
    hints = "✅" if s.get('show_hints', 1) else "❌"
    rev   = "✅" if s.get('reverse_mode', 0) else "❌"
    diff_map = {'easy':'🟢 Лёгкий','medium':'🟡 Средний','hard':'🔴 Сложный'}
    diff = diff_map.get(s.get('difficulty','medium'), '🟡 Средний')
    text = (f"⚙️ *Настройки*\n\n"
            f"🔔 Уведомления: {notif}\n"
            f"💡 Подсказки: {hints}\n"
            f"🔃 Реверс (ответ→вопрос): {rev}\n"
            f"🎯 Сложность: {diff}\n"
            f"🎴 Карточек за сессию: {s.get('cards_per_session',20)}")
    markup = kb([
        [btn(f"🔔 Уведомления {notif}", "toggle_notifications"),
         btn(f"💡 Подсказки {hints}", "toggle_hints")],
        [btn(f"🔃 Реверс {rev}", "toggle_reverse"),
         btn(f"🎯 {diff}", "cycle_difficulty")],
        [btn("➖ Меньше карточек", "cards_less"),
         btn("➕ Больше карточек", "cards_more")],
        [btn("⬅️ Назад", "main_menu")],
    ])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return SETTINGS

async def handle_settings_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    s = db.get_settings(user_id)
    if data == "toggle_notifications":
        db.update_setting(user_id, 'notifications', 0 if s.get('notifications') else 1)
    elif data == "toggle_hints":
        db.update_setting(user_id, 'show_hints', 0 if s.get('show_hints', 1) else 1)
    elif data == "toggle_reverse":
        db.update_setting(user_id, 'reverse_mode', 0 if s.get('reverse_mode') else 1)
    elif data == "cycle_difficulty":
        cycle = {'easy':'medium','medium':'hard','hard':'easy'}
        db.update_setting(user_id, 'difficulty', cycle.get(s.get('difficulty','medium'),'medium'))
    elif data == "cards_less":
        db.update_setting(user_id, 'cards_per_session', max(5, s.get('cards_per_session',20)-5))
    elif data == "cards_more":
        db.update_setting(user_id, 'cards_per_session', min(50, s.get('cards_per_session',20)+5))
    await query.answer("✅ Сохранено")
    return await show_settings(update, context)

# ── Помощь ────────────────────────────────────────────────────────────────────

async def show_help(update, context):
    text = (
        "❓ *QuizletBot — Помощь*\n\n"
        "*Команды:* /start /stats /help /cancel\n\n"
        "*🧠 Умные режимы:*\n"
        "🧠 *SRS* — интервальный алгоритм SM-2\n"
        "📦 *Лейтнер* — 5 ящиков, классика\n\n"
        "*🎯 Режимы проверки:*\n"
        "🎴 *Карточки* — переворот, самооценка\n"
        "✍️ *Письменный* — введите ответ\n"
        "🎯 *Тест* — 4 варианта\n"
        "🔡 *Первая буква* — подсказка по началу\n"
        "📖 *Пересказ* — проверка ключевых слов\n\n"
        "*🎮 Игровые:*\n"
        "🔗 *Найди пару* — соедините вопрос с ответом\n"
        "🔤 *Анаграмма* — угадайте перемешанное слово\n\n"
        "*⚡ Скоростные:*\n"
        "⚡ *Спринт* — 20 карточек за 60 секунд\n"
        "🏃 *Марафон* — вся колода без остановки\n"
        "🎮 *Смешанный* — чередование режимов\n\n"
        "*👁 Пассивные:*\n"
        "👁 *Чтение* — просмотр без оценки\n"
        "💪 *Ошибки* — фокус на слабых местах\n\n"
        "*Формат карточек:*\n"
        "`Вопрос | Ответ`\n"
        "`Вопрос | Ответ | Подсказка`\n\n"
        "*Совет:* Начинайте каждый день с SRS — "
        "алгоритм покажет именно то, что пора повторить!"
    )
    markup = kb([[btn("⬅️ Назад", "main_menu")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

# ── Fallbacks ─────────────────────────────────────────────────────────────────

async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("❌ Отменено", reply_markup=get_main_kb())
    return MAIN_MENU

async def message_handler(update, context):
    s = _s(context)
    mode = s.get('mode') if s else None
    write_modes = ('write', 'mixed', 'weak', 'anagram',
                   'first_letter', 'retelling', 'sprint')
    if s and mode in write_modes:
        return await check_write_answer(update, context)
    await update.message.reply_text("Используйте кнопки 👇", reply_markup=get_main_kb())
    return MAIN_MENU
