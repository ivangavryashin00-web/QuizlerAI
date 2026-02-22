"""
QuizletBot — handlers.py
All Telegram handlers: menus, study modes, gamification, stats.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from study_modes import StudyModes
from spaced_repetition import SM2, QUALITY_LABELS, AGAIN, HARD, GOOD, EASY
from gamification import Gamification, ACHIEVEMENTS, LEVEL_NAMES
from datetime import datetime
import random

db = Database()

# ── States ──────────────────────────────────────────────────────────────────
(
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE,
    STUDY_WRITE, STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU,
    EDIT_CARD, SETTINGS, IMPORT_CARDS, BROWSE_DICTIONARY,
    STUDY_SRS, STUDY_WEAK, STUDY_MATCH
) = range(15)

# ── Collections (built-in dictionary) ────────────────────────────────────────
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
        ("Bonjour","Здравствуйте"),("Merci","Спасибо"),("S'il vous plaît","Пожалуйста"),
        ("Oui","Да"),("Non","Нет"),("Au revoir","До свидания"),
        ("Eau","Вода"),("Maison","Дом"),("Livre","Книга"),("Ami","Друг"),
        ("Famille","Семья"),("Travail","Работа"),("Ville","Город"),
        ("Pays","Страна"),("Bien","Хорошо"),("Mal","Плохо"),
        ("Voiture","Машина"),("Temps","Время"),("Argent","Деньги"),("Vie","Жизнь"),
    ]),
    "math": ("📐 Математика", [
        ("Формула периметра прямоугольника","P = 2(a+b)"),
        ("Формула площади прямоугольника","S = a·b"),
        ("Формула площади круга","S = πr²"),
        ("Теорема Пифагора","a² + b² = c²"),
        ("Формула дискриминанта","D = b² − 4ac"),
        ("Корни квадратного уравнения","x = (−b ± √D) / 2a"),
        ("Сумма углов треугольника","180°"),
        ("π ≈","3.14159"),("e ≈","2.71828"),
        ("sin²α + cos²α =","1"),
        ("Производная x^n","n·x^(n−1)"),
        ("∫ x dx","x²/2 + C"),
        ("Число Авогадро","6.022 × 10²³"),
        ("Формула объёма шара","V = 4/3·π·r³"),
        ("Формула длины окружности","L = 2πr"),
    ]),
    "it_terms": ("💻 IT и программирование", [
        ("Algorithm","Пошаговый набор инструкций для решения задачи"),
        ("API","Интерфейс программирования приложений"),
        ("Backend","Серверная часть приложения"),
        ("Frontend","Клиентская часть (интерфейс пользователя)"),
        ("Database","База данных — хранилище структурированных данных"),
        ("Git","Система контроля версий"),
        ("HTTP","Протокол передачи гипертекста"),
        ("JSON","JavaScript Object Notation — формат данных"),
        ("REST API","Архитектурный стиль для веб-сервисов"),
        ("OOP","Объектно-ориентированное программирование"),
        ("CI/CD","Непрерывная интеграция и доставка"),
        ("SDK","Набор инструментов разработчика"),
        ("UI/UX","Интерфейс и пользовательский опыт"),
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
        ("Самая большая страна по площади","Россия"),
        ("Самая населённая страна","Индия"),
        ("Самая глубокая точка океана","Марианская впадина (11 км)"),
    ]),
    "biology": ("🧬 Биология", [
        ("ДНК","Дезоксирибонуклеиновая кислота — носитель генетической информации"),
        ("Функция митохондрий","Выработка энергии (АТФ)"),
        ("Фотосинтез","Преобразование CO₂+H₂O+свет → глюкоза+O₂"),
        ("Ген","Участок ДНК, кодирующий признак или белок"),
        ("Хромосома","Структура из ДНК и белков, несущая гены"),
        ("Клеточная мембрана","Оболочка клетки, регулирует обмен веществ"),
        ("Рибосома","Органелла синтеза белка"),
        ("Мейоз","Деление клетки с уменьшением числа хромосом вдвое"),
        ("Митоз","Деление клетки с сохранением числа хромосом"),
        ("Экосистема","Сообщество организмов и их среда обитания"),
        ("Гемоглобин","Белок крови, переносит кислород"),
        ("Вирус","Неклеточный агент, размножается внутри клеток"),
    ]),
    "history": ("📜 История России", [
        ("Год основания Москвы","1147"),
        ("Куликовская битва","1380 год — победа над Мамаем"),
        ("Иван Грозный — первый царь","1547"),
        ("Основание Санкт-Петербурга","1703, Пётр I"),
        ("Война с Наполеоном","Отечественная война 1812 года"),
        ("Отмена крепостного права","1861, Александр II"),
        ("Революция","1917 год — Октябрьская революция"),
        ("Начало ВОВ","22 июня 1941"),
        ("Конец ВОВ","9 мая 1945"),
        ("Полёт Гагарина в космос","12 апреля 1961"),
        ("Распад СССР","26 декабря 1991"),
        ("Первый президент России","Борис Ельцин (1991)"),
    ]),
    "business": ("💼 Бизнес и экономика", [
        ("ROI","Return on Investment — возврат на инвестиции"),
        ("KPI","Key Performance Indicator — ключевой показатель"),
        ("B2B","Business to Business — бизнес для бизнеса"),
        ("B2C","Business to Consumer — бизнес для потребителя"),
        ("MVP","Minimum Viable Product — минимально жизнеспособный продукт"),
        ("SWOT","Анализ: Strengths, Weaknesses, Opportunities, Threats"),
        ("Маржинальность","Отношение прибыли к выручке"),
        ("Ликвидность","Способность актива быстро стать деньгами"),
        ("Диверсификация","Распределение рисков по разным активам"),
        ("Оборотный капитал","Активы, используемые в операционной деятельности"),
        ("Дебиторская задолженность","Долги контрагентов перед компанией"),
        ("Unit-экономика","Прибыль/убыток на единицу продукта"),
    ]),
}

# ── Keyboard helpers ──────────────────────────────────────────────────────────

def kb(buttons: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(buttons)

def btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text, callback_data=data)

def progress_bar(pct: int, length: int = 8) -> str:
    filled = round(pct / 100 * length)
    return '█' * filled + '░' * (length - filled)

def mode_emoji(mode: str) -> str:
    return {'flashcard': '🎴', 'write': '✍️', 'quiz': '🎯',
            'srs': '🧠', 'mixed': '🎮', 'weak': '💪', 'match': '🔗'}.get(mode, '📖')

# ── Entry point ───────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)
    db.init_gamification(user.id)
    g = db.get_gamification(user.id)
    lvl = g.get('level', 1)
    emoji, lvl_name = LEVEL_NAMES.get(lvl, ('🌱', 'Новичок'))
    streak = g.get('current_streak', 0)

    text = (
        f"🎓 *Добро пожаловать, {user.first_name or 'друг'}!*\n\n"
        f"{emoji} Уровень {lvl} — {lvl_name}   "
        f"{'🔥 ' + str(streak) + ' дн.' if streak > 0 else '🆕 Начнём!'}\n\n"
        f"*QuizletBot* — умный тренажёр памяти с:\n"
        f"• 🧠 Интервальным повторением (SM-2)\n"
        f"• 🎴 Карточками, тестами, письменным режимом\n"
        f"• 💪 Работой над ошибками\n"
        f"• 🏆 Достижениями и уровнями\n"
        f"• 📋 Ежедневными заданиями\n"
        f"• 📊 Детальной аналитикой\n\n"
        f"_Выберите действие:_"
    )
    markup = get_main_keyboard()
    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

def get_main_keyboard():
    return kb([
        [btn("📚 Мои колоды", "my_decks"),       btn("➕ Создать колоду", "create_deck")],
        [btn("🧠 SRS — повторение", "srs_all"),   btn("📋 Задания дня", "daily_tasks")],
        [btn("📖 Словарь", "browse_dict"),        btn("📊 Статистика", "my_stats")],
        [btn("🏆 Рейтинг", "leaderboard"),        btn("⚙️ Настройки", "settings")],
        [btn("❓ Помощь", "help")],
    ])

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    dispatch = {
        "my_decks":     show_decks_menu,
        "create_deck":  start_create_deck,
        "browse_dict":  browse_dictionary,
        "my_stats":     show_full_stats,
        "settings":     show_settings,
        "help":         show_help,
        "main_menu":    start,
        "daily_tasks":  show_daily_tasks,
        "leaderboard":  show_leaderboard,
        "srs_all":      show_srs_all,
        "achievements": show_achievements,
    }
    if data in dispatch:
        return await dispatch[data](update, context)
    return MAIN_MENU

# ── My Decks ──────────────────────────────────────────────────────────────────

async def show_decks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    decks = db.get_user_decks(user_id)

    if not decks:
        await update.callback_query.edit_message_text(
            "📚 *У вас пока нет колод*\n\nСоздайте первую или выберите из словаря!",
            reply_markup=kb([
                [btn("➕ Создать колоду", "create_deck")],
                [btn("📖 Словарь готовых", "browse_dict")],
                [btn("⬅️ Назад", "main_menu")],
            ]),
            parse_mode="Markdown"
        )
        return MAIN_MENU

    text = "📚 *Ваши колоды:*\n\n"
    buttons = []
    for d in decks:
        stats = db.get_deck_srs_stats(user_id, d['deck_id'])
        due = stats.get('due', 0)
        bar = progress_bar(stats.get('progress', 0))
        due_tag = f" 🔔{due}" if due > 0 else ""
        text += (
            f"{d.get('emoji','📖')} *{d['name']}*\n"
            f"  {bar} {stats.get('progress',0)}%  "
            f"✅{stats.get('mastered',0)} 🔄{stats.get('learning',0)} 🆕{stats.get('new_cards',0)}"
            f"{due_tag}\n\n"
        )
        label = f"{d.get('emoji','📖')} {d['name']}"
        if due > 0:
            label += f" 🔔{due}"
        buttons.append([btn(label, f"deck_menu_{d['deck_id']}")])

    buttons.append([btn("➕ Создать", "create_deck"), btn("📖 Словарь", "browse_dict")])
    buttons.append([btn("⬅️ Назад", "main_menu")])

    await update.callback_query.edit_message_text(
        text, reply_markup=kb(buttons), parse_mode="Markdown"
    )
    return MAIN_MENU

# ── Deck Menu ─────────────────────────────────────────────────────────────────

async def deck_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # ── deck_menu_<id> ─
    if data.startswith("deck_menu_"):
        deck_id = int(data.split("_")[2])
        context.user_data['current_deck_id'] = deck_id
        return await show_deck_menu(update, context, deck_id)

    # ── study actions ─
    elif data.startswith("study_flash_"):
        return await start_flashcard_mode(update, context)
    elif data.startswith("study_write_"):
        return await start_write_mode(update, context)
    elif data.startswith("study_quiz_"):
        return await start_quiz_mode(update, context)
    elif data.startswith("study_mixed_"):
        return await start_mixed_mode(update, context)
    elif data.startswith("study_srs_"):
        return await start_srs_mode(update, context)
    elif data.startswith("study_weak_"):
        return await start_weak_mode(update, context)
    elif data.startswith("study_select_"):
        return await select_study_mode(update, context)

    # ── card management ─
    elif data.startswith("add_cards_"):
        return await start_add_cards(update, context)
    elif data.startswith("list_cards_"):
        return await list_cards(update, context)
    elif data.startswith("deck_stats_"):
        return await show_deck_stats(update, context)
    elif data.startswith("delete_deck_"):
        return await confirm_delete_deck(update, context)
    elif data.startswith("confirm_delete_"):
        return await do_delete_deck(update, context)

    # ── in-session actions ─
    elif data == "flip_card":
        return await handle_flip(update, context)
    elif data.startswith("rate_"):
        return await handle_rate(update, context)
    elif data == "next_card":
        return await handle_next(update, context)
    elif data == "retry_card":
        return await handle_retry(update, context)
    elif data.startswith("hint_"):
        return await handle_hint(update, context)
    elif data == "stop_study":
        return await stop_session(update, context)
    elif data.startswith("quiz_ans_"):
        return await handle_quiz_answer(update, context)

    return DECK_MENU

async def show_deck_menu(update, context, deck_id):
    user_id = update.effective_user.id
    di = db.get_deck_info(deck_id)
    if not di:
        await update.callback_query.edit_message_text("❌ Колода не найдена")
        return MAIN_MENU

    stats = db.get_deck_srs_stats(user_id, deck_id)
    bar = progress_bar(stats.get('progress', 0))
    due = stats.get('due', 0)
    history = db.get_deck_history(user_id, deck_id, 3)
    hist_str = ""
    if history:
        for h in history:
            total = h['correct'] + h['wrong']
            acc = round(h['correct'] / total * 100) if total else 0
            hist_str += f"  {mode_emoji(h['mode'])} {h['correct']}/{total} ({acc}%) — {h['started_at'][:10]}\n"

    text = (
        f"{di.get('emoji','📖')} *{di['name']}*\n\n"
        f"📊 {bar} {stats.get('progress',0)}%\n"
        f"✅ Выучено: {stats.get('mastered',0)}  "
        f"🔄 Учится: {stats.get('learning',0)}  "
        f"🆕 Новые: {stats.get('new_cards',0)}\n"
        f"{'🔔 К повторению: *' + str(due) + '*' if due > 0 else '👌 Всё повторено!'}\n"
        + (f"\n📈 *Последние сессии:*\n{hist_str}" if hist_str else "") +
        f"\n*Выберите режим:*"
    )

    markup = kb([
        [btn(f"🧠 SRS повторение{' 🔔' if due else ''}", f"study_srs_{deck_id}")],
        [btn("🎴 Карточки",     f"study_flash_{deck_id}"),
         btn("✍️ Письменный",   f"study_write_{deck_id}")],
        [btn("🎯 Тест",         f"study_quiz_{deck_id}"),
         btn("🎮 Смешанный",   f"study_mixed_{deck_id}")],
        [btn("💪 Работа над ошибками", f"study_weak_{deck_id}")],
        [btn("➕ Добавить карточки",   f"add_cards_{deck_id}")],
        [btn("📋 Список карточек",    f"list_cards_{deck_id}"),
         btn("📊 Аналитика",          f"deck_stats_{deck_id}")],
        [btn("🗑 Удалить колоду",     f"delete_deck_{deck_id}")],
        [btn("⬅️ К колодам",          "my_decks")],
    ])
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return DECK_MENU

async def select_study_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    context.user_data['current_deck_id'] = deck_id
    text = (
        "🎓 *Выберите режим обучения:*\n\n"
        "🧠 *SRS* — умное интервальное повторение (рекомендуется)\n"
        "🎴 *Карточки* — переворот и самооценка\n"
        "✍️ *Письменный* — вводите ответ с клавиатуры\n"
        "🎯 *Тест* — 4 варианта ответа\n"
        "🎮 *Смешанный* — разные режимы вперемешку\n"
        "💪 *Ошибки* — только слова, в которых ошибаетесь"
    )
    markup = kb([
        [btn("🧠 SRS", f"study_srs_{deck_id}")],
        [btn("🎴 Карточки", f"study_flash_{deck_id}"),
         btn("✍️ Письменный", f"study_write_{deck_id}")],
        [btn("🎯 Тест", f"study_quiz_{deck_id}"),
         btn("🎮 Смешанный", f"study_mixed_{deck_id}")],
        [btn("💪 Работа над ошибками", f"study_weak_{deck_id}")],
        [btn("⬅️ Назад", f"deck_menu_{deck_id}")],
    ])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return STUDY_SELECT_MODE

# ── Session helpers ───────────────────────────────────────────────────────────

def _init_session(context, mode, deck_id, cards):
    context.user_data['study_session'] = {
        'mode':       mode,
        'deck_id':    deck_id,
        'cards':      cards,
        'current':    0,
        'correct':    0,
        'wrong':      0,
        'flipped':    False,
        'hint_level': 0,
        'streak':     0,
        'started_at': datetime.now().timestamp(),
        'session_id': db.start_session(
            context._user_id if hasattr(context, '_user_id') else 0,
            deck_id, mode
        ),
    }

def _session(context) -> dict:
    return context.user_data.get('study_session', {})

def _current_card(context) -> dict:
    s = _session(context)
    cards = s.get('cards', [])
    idx = s.get('current', 0)
    return cards[idx] if idx < len(cards) else {}

# ── Flashcard mode ────────────────────────────────────────────────────────────

async def start_flashcard_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    settings = db.get_settings(user_id)
    cards = StudyModes.prepare_cards(user_id, deck_id, 'flashcard', settings=settings)

    if not cards:
        await query.answer("❌ В колоде нет карточек", show_alert=True)
        return DECK_MENU

    _init_session(context, 'flashcard', deck_id, cards)
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'flashcard')
    await _render_flashcard(query, context)
    return STUDY_FLASHCARD

async def _render_flashcard(query, context):
    s = _session(context)
    card = _current_card(context)
    idx = s['current']
    total = len(s['cards'])

    if s.get('flipped'):
        text = (
            f"🎴 *{idx+1}/{total}*\n\n"
            f"❓ {card['question']}\n\n"
            f"✅ *{card['answer']}*\n\n"
            f"*Насколько хорошо знали?*"
        )
        markup = kb([
            [btn("😰 Снова", "rate_0"), btn("😓 Трудно", "rate_1"),
             btn("🙂 Знаю", "rate_2"),  btn("😄 Легко", "rate_3")],
            [btn("⏹ Завершить", "stop_study")],
        ])
    else:
        hint_text = ""
        if card.get('hint'):
            hint_text = f"\n💡 _{card['hint']}_"
        text = (
            f"🎴 *{idx+1}/{total}*\n\n"
            f"❓ *{card['question']}*{hint_text}\n\n"
            f"_Вспомните ответ и переверните_"
        )
        markup = kb([
            [btn("🔄 Показать ответ", "flip_card")],
            [btn("⏹ Завершить", "stop_study")],
        ])

    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def handle_flip(update, context):
    s = _session(context)
    if not s:
        return MAIN_MENU
    s['flipped'] = True
    await _render_flashcard(update.callback_query, context)
    return STUDY_FLASHCARD

async def handle_rate(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _session(context)
    if not s:
        return MAIN_MENU

    quality = int(query.data.split("_")[1])
    card = _current_card(context)

    # SRS update
    db.init_card_progress(user_id, card['card_id'])
    SM2.process_answer(user_id, card['card_id'], quality)

    if quality >= GOOD:
        s['correct'] += 1
        s['streak'] += 1
    else:
        s['wrong'] += 1
        s['streak'] = 0

    db.update_daily_task(user_id, 'study_cards', 1)

    s['current'] += 1
    s['flipped'] = False
    s['hint_level'] = 0

    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)

    await _render_flashcard(query, context)
    return STUDY_FLASHCARD

# ── SRS mode ──────────────────────────────────────────────────────────────────

async def start_srs_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_srs_cards(user_id, deck_id)

    if not cards:
        await query.edit_message_text(
            "🧠 *SRS — Нечего повторять!*\n\n"
            "✅ Все карточки повторены по расписанию.\n"
            "Возвращайтесь позже или учите новый материал в обычном режиме.",
            reply_markup=kb([[btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
            parse_mode="Markdown"
        )
        return DECK_MENU

    _init_session(context, 'srs', deck_id, cards)
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'srs')
    await _render_srs(query, context)
    return STUDY_SRS

async def _render_srs(query, context):
    s = _session(context)
    card = _current_card(context)
    idx = s['current']
    total = len(s['cards'])
    due_info = ""
    if card.get('interval_days'):
        due_info = f"\n_Интервал: {card['interval_days']} дн. | Уровень SRS: {card.get('level',0)}_"

    if s.get('flipped'):
        text = (
            f"🧠 *SRS {idx+1}/{total}*\n\n"
            f"❓ {card['question']}\n\n"
            f"✅ *{card['answer']}*{due_info}\n\n"
            f"*Как хорошо знали?*"
        )
        markup = kb([
            [btn("😰 Снова", "rate_0"), btn("😓 Трудно", "rate_1"),
             btn("🙂 Знаю", "rate_2"),  btn("😄 Легко", "rate_3")],
            [btn("⏹ Завершить", "stop_study")],
        ])
    else:
        text = (
            f"🧠 *SRS {idx+1}/{total}*\n\n"
            f"❓ *{card['question']}*\n\n"
            f"_Вспомните ответ:_"
        )
        markup = kb([
            [btn("🔄 Показать ответ", "flip_card")],
            [btn("⏹ Завершить", "stop_study")],
        ])

    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

# ── Write mode ────────────────────────────────────────────────────────────────

async def start_write_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    settings = db.get_settings(user_id)
    cards = StudyModes.prepare_cards(user_id, deck_id, 'write', settings=settings)

    if not cards:
        await query.answer("❌ В колоде нет карточек", show_alert=True)
        return DECK_MENU

    _init_session(context, 'write', deck_id, cards)
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'write')
    await _render_write(query, context)
    return STUDY_WRITE

async def _render_write(query_or_msg, context, is_message=False):
    s = _session(context)
    card = _current_card(context)
    idx = s['current']
    total = len(s['cards'])
    streak = s.get('streak', 0)
    streak_str = f" 🔥{streak}" if streak >= 3 else ""

    hint_text = ""
    if card.get('hint'):
        hint_text = f"\n💡 _{card['hint']}_"

    text = (
        f"✍️ *{idx+1}/{total}*{streak_str}\n\n"
        f"❓ *{card['question']}*{hint_text}\n\n"
        f"_Напишите ответ:_"
    )
    markup = kb([
        [btn("💡 Подсказка", f"hint_{idx}"), btn("⏹ Завершить", "stop_study")]
    ])

    if is_message:
        await query_or_msg.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await query_or_msg.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def check_write_answer(update, context):
    user_id = update.effective_user.id
    s = _session(context)
    if not s or s.get('mode') not in ('write', 'mixed', 'weak'):
        await update.message.reply_text("Используйте меню:", reply_markup=get_main_keyboard())
        return MAIN_MENU

    user_ans = update.message.text.strip()
    card = _current_card(context)
    verdict, sim = StudyModes.check_answer(user_ans, card['answer'])

    db.init_card_progress(user_id, card['card_id'])

    if verdict == 'correct':
        s['correct'] += 1
        s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        db.update_daily_task(user_id, 'correct_streak', 1)
        streak = s.get('streak', 0)
        pts_action = 'correct_write'
        text = (
            f"✅ *Правильно!*\n\n"
            f"Ваш ответ: _{user_ans}_\n"
            f"Правильный: *{card['answer']}*\n\n"
            f"{'🔥 Серия: ' + str(streak) + '!' if streak >= 3 else ''}"
        )
        markup = kb([[btn("➡️ Далее", "next_card")]])

    elif verdict == 'close':
        s['correct'] += 0.5
        SM2.process_answer(user_id, card['card_id'], HARD)
        text = (
            f"⚠️ *Почти правильно!* ({round(sim*100)}% совпадение)\n\n"
            f"Ваш: _{user_ans}_\n"
            f"Правильный: *{card['answer']}*"
        )
        markup = kb([
            [btn("🔄 Ещё раз", "retry_card"), btn("➡️ Далее", "next_card")]
        ])

    else:
        s['wrong'] += 1
        s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
        text = (
            f"❌ *Неправильно*\n\n"
            f"Ваш: _{user_ans}_\n"
            f"Правильный: *{card['answer']}*"
        )
        markup = kb([
            [btn("🔄 Ещё раз", "retry_card"), btn("➡️ Далее", "next_card")]
        ])

    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    mode_state = {'write': STUDY_WRITE, 'mixed': STUDY_FLASHCARD, 'weak': STUDY_WEAK}
    return mode_state.get(s.get('mode'), STUDY_WRITE)

# ── Quiz mode ─────────────────────────────────────────────────────────────────

async def start_quiz_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    settings = db.get_settings(user_id)
    all_cards = db.get_deck_cards(deck_id)

    if len(all_cards) < 2:
        await query.answer("❌ Нужно минимум 2 карточки", show_alert=True)
        return DECK_MENU

    cards = StudyModes.prepare_cards(user_id, deck_id, 'quiz', settings=settings)
    _init_session(context, 'quiz', deck_id, cards)
    context.user_data['study_session']['all_cards'] = all_cards
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'quiz')
    await _render_quiz(query, context)
    return STUDY_QUIZ

async def _render_quiz(query, context):
    s = _session(context)
    card = _current_card(context)
    idx = s['current']
    total = len(s['cards'])
    all_cards = s.get('all_cards', s['cards'])
    streak = s.get('streak', 0)
    streak_str = f" 🔥{streak}" if streak >= 3 else ""

    options = StudyModes.generate_quiz_options(card, all_cards, 4)
    s['_quiz_options'] = options

    text = (
        f"🎯 *Тест {idx+1}/{total}*{streak_str}\n\n"
        f"❓ *{card['question']}*\n\n"
        f"_Выберите правильный ответ:_"
    )

    buttons = []
    for i, opt in enumerate(options):
        label = opt[:40] + "…" if len(opt) > 40 else opt
        buttons.append([btn(label, f"quiz_ans_{i}")])
    buttons.append([btn("⏹ Завершить", "stop_study")])

    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")

async def handle_quiz_answer(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _session(context)
    if not s:
        return MAIN_MENU

    idx = int(query.data.split("_")[2])
    card = _current_card(context)
    options = s.get('_quiz_options', [])
    chosen = options[idx] if idx < len(options) else ""
    correct = chosen == card['answer']

    db.init_card_progress(user_id, card['card_id'])

    if correct:
        s['correct'] += 1
        s['streak'] += 1
        SM2.process_answer(user_id, card['card_id'], GOOD)
        db.update_daily_task(user_id, 'study_cards', 1)
        db.update_daily_task(user_id, 'correct_streak', 1)
        streak = s.get('streak', 0)
        await query.answer(f"✅ Правильно!{' 🔥' + str(streak) if streak >= 3 else ''}")
    else:
        s['wrong'] += 1
        s['streak'] = 0
        SM2.process_answer(user_id, card['card_id'], AGAIN)
        db.update_daily_task(user_id, 'study_cards', 1)
        await query.answer(f"❌ Неверно! Правильный: {card['answer']}", show_alert=True)

    s['current'] += 1
    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)

    await _render_quiz(query, context)
    return STUDY_QUIZ

# ── Mixed mode ────────────────────────────────────────────────────────────────

async def start_mixed_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    settings = db.get_settings(user_id)
    cards = StudyModes.prepare_cards(user_id, deck_id, 'mixed', settings=settings)

    if not cards:
        await query.answer("❌ В колоде нет карточек", show_alert=True)
        return DECK_MENU

    modes = ['flashcard', 'write', 'quiz'] if len(cards) >= 2 else ['flashcard']
    for c in cards:
        c['sub_mode'] = random.choice(modes)

    _init_session(context, 'mixed', deck_id, cards)
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'mixed')
    context.user_data['study_session']['all_cards'] = cards
    db.update_daily_task(user_id, 'use_mode', 1)
    return await _dispatch_mixed(query, context)

async def _dispatch_mixed(query, context):
    s = _session(context)
    card = _current_card(context)
    sub = card.get('sub_mode', 'flashcard')
    if sub == 'write':
        await _render_write(query, context)
        return STUDY_WRITE
    elif sub == 'quiz':
        await _render_quiz(query, context)
        return STUDY_QUIZ
    else:
        s['flipped'] = False
        await _render_flashcard(query, context)
        return STUDY_FLASHCARD

# ── Weak cards mode ───────────────────────────────────────────────────────────

async def start_weak_mode(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    user_id = query.from_user.id
    cards = StudyModes.prepare_weak_cards(user_id, deck_id)

    if not cards:
        await query.answer("❌ Нет данных об ошибках", show_alert=True)
        return DECK_MENU

    _init_session(context, 'weak', deck_id, cards)
    context.user_data['study_session']['session_id'] = db.start_session(user_id, deck_id, 'weak')

    s = _session(context)
    card = cards[0]
    acc = round(card.get('accuracy', 0) * 100) if 'accuracy' in card else '?'
    text = (
        f"💪 *Работа над ошибками*\n\n"
        f"Карточек для отработки: *{len(cards)}*\n"
        f"Самая сложная: _{card['question']}_ (точность {acc}%)\n\n"
        f"Начнём?"
    )
    markup = kb([
        [btn("▶️ Начать", "flip_card")],
        [btn("⬅️ Назад", f"deck_menu_{deck_id}")],
    ])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    s['flipped'] = False
    await _render_flashcard(query, context)
    return STUDY_WEAK

# ── SRS all decks ─────────────────────────────────────────────────────────────

async def show_srs_all(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    decks = db.get_user_decks(user_id)

    if not decks:
        await query.edit_message_text(
            "📚 У вас нет колод для повторения.\nСоздайте колоду первым делом!",
            reply_markup=kb([[btn("⬅️ Назад", "main_menu")]]),
        )
        return MAIN_MENU

    text = "🧠 *SRS — что повторить сегодня:*\n\n"
    buttons = []
    total_due = 0
    for d in decks:
        stats = db.get_deck_srs_stats(user_id, d['deck_id'])
        due = stats.get('due', 0)
        total_due += due
        bar = progress_bar(stats.get('progress', 0), 6)
        if due > 0:
            text += f"🔔 *{d['name']}* — {due} к повторению\n   {bar}\n"
            buttons.append([btn(f"🔔 {d['name']} ({due})", f"study_srs_{d['deck_id']}")])
        else:
            text += f"✅ *{d['name']}* — всё повторено\n   {bar}\n"

    if total_due == 0:
        text += "\n✅ *Отлично! Всё повторено на сегодня.*\nЗаходите завтра!"
    else:
        text += f"\n📊 Итого к повторению: *{total_due}* карточек"

    buttons.append([btn("⬅️ Назад", "main_menu")])
    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")
    return MAIN_MENU

# ── Session navigation ────────────────────────────────────────────────────────

async def handle_next(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    s = _session(context)
    if not s:
        return MAIN_MENU

    s['current'] += 1
    s['hint_level'] = 0

    if s['current'] >= len(s['cards']):
        return await _finish(query, context, user_id)

    mode = s.get('mode')
    if mode == 'write':
        await _render_write(query, context)
        return STUDY_WRITE
    elif mode == 'quiz':
        await _render_quiz(query, context)
        return STUDY_QUIZ
    elif mode == 'mixed':
        return await _dispatch_mixed(query, context)
    elif mode == 'srs':
        s['flipped'] = False
        await _render_srs(query, context)
        return STUDY_SRS
    else:
        s['flipped'] = False
        await _render_flashcard(query, context)
        return STUDY_FLASHCARD

async def handle_retry(update, context):
    query = update.callback_query
    s = _session(context)
    if not s:
        return MAIN_MENU
    mode = s.get('mode', 'write')
    if mode in ('write', 'mixed', 'weak'):
        await _render_write(query, context)
        return STUDY_WRITE
    return STUDY_FLASHCARD

async def handle_hint(update, context):
    query = update.callback_query
    s = _session(context)
    if not s:
        return STUDY_WRITE
    card = _current_card(context)
    level = s.get('hint_level', 0) + 1
    s['hint_level'] = level
    hint = StudyModes.get_hint(card['answer'], level)
    await query.answer(f"💡 {hint}", show_alert=True)
    return STUDY_WRITE

async def stop_session(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    return await _finish(query, context, user_id)

async def _finish(query, context, user_id):
    s = _session(context)
    if not s:
        await query.edit_message_text("Сессия завершена!", reply_markup=kb([[btn("🏠 Главная", "main_menu")]]))
        return MAIN_MENU

    correct = int(s.get('correct', 0))
    wrong   = s.get('wrong', 0)
    total   = correct + wrong
    deck_id = s.get('deck_id', 0)
    mode    = s.get('mode', '')
    started = s.get('started_at', datetime.now().timestamp())
    duration = int(datetime.now().timestamp() - started)

    # Save session
    sid = s.get('session_id')
    if sid:
        db.finish_session(sid, correct, wrong, duration)

    # Gamification
    events = Gamification.after_session(user_id, correct, wrong, total, mode, duration)
    streak = events.get('streak', 0)
    level  = events.get('level', 1)
    em, lname = LEVEL_NAMES.get(level, ('⭐', ''))
    acc = round(correct / total * 100) if total > 0 else 0

    # Bar
    bar = progress_bar(acc)

    lines = [
        f"🏁 *Сессия завершена!*\n",
        f"{mode_emoji(mode)} Режим: {mode}",
        f"✅ Правильно: {correct}/{total}",
        f"📊 Точность: {bar} {acc}%",
        f"⏱ Время: {duration // 60}м {duration % 60}с",
        f"🔥 Серия: {streak} дней",
        f"{em} Уровень: {level} — {lname}",
    ]

    if events.get('perfect'):
        lines.append("🏆 *+50 бонус за идеальный результат!*")
    if events.get('speed'):
        lines.append("⚡ *Скоростной бонус!*")
    if events.get('achievements'):
        for a in events['achievements']:
            info = ACHIEVEMENTS.get(a, {})
            lines.append(f"🎖 *Достижение: {info.get('name', a)}!*")

    # Motivational tip
    if acc >= 90:
        lines.append("\n🌟 _Превосходно! Вы на верном пути!_")
    elif acc >= 70:
        lines.append("\n👍 _Хороший результат, продолжайте!_")
    else:
        lines.append("\n💪 _Практика — путь к мастерству!_")

    context.user_data.pop('study_session', None)

    markup = kb([
        [btn("🔄 Ещё раз", f"study_select_{deck_id}"),
         btn("🧠 SRS", f"study_srs_{deck_id}")],
        [btn("📊 Аналитика", f"deck_stats_{deck_id}"),
         btn("📚 Колоды", "my_decks")],
        [btn("🏠 Главная", "main_menu")],
    ])
    await query.edit_message_text("\n".join(lines), reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

# ── Deck stats ────────────────────────────────────────────────────────────────

async def show_deck_stats(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    stats = db.get_deck_srs_stats(user_id, deck_id)
    history = db.get_deck_history(user_id, deck_id, 7)
    weak = db.get_weak_cards(user_id, deck_id, 5)

    bar = progress_bar(stats.get('progress', 0))
    hist_lines = ""
    for h in history:
        total = h['correct'] + h['wrong']
        acc = round(h['correct'] / total * 100) if total else 0
        mins = h['duration_s'] // 60
        hist_lines += f"  {mode_emoji(h['mode'])} {h['correct']}/{total} ({acc}%) {mins}м — {h['started_at'][:10]}\n"

    weak_lines = ""
    for w in weak[:3]:
        acc = round(w.get('accuracy', 0) * 100)
        weak_lines += f"  ❗ _{w['question']}_ — {acc}% верных\n"

    text = (
        f"📊 *Аналитика: {di['name']}*\n\n"
        f"📈 Прогресс: {bar} {stats.get('progress',0)}%\n"
        f"✅ Выучено: {stats.get('mastered',0)}\n"
        f"🔄 Изучается: {stats.get('learning',0)}\n"
        f"🆕 Новые: {stats.get('new_cards',0)}\n"
        f"🔔 К повторению: {stats.get('due',0)}\n\n"
        + (f"📅 *Последние сессии:*\n{hist_lines}\n" if hist_lines else "") +
        (f"⚠️ *Сложные карточки:*\n{weak_lines}" if weak_lines else "")
    )

    markup = kb([
        [btn("💪 Отработать слабые", f"study_weak_{deck_id}")],
        [btn("🧠 SRS повторение", f"study_srs_{deck_id}")],
        [btn("⬅️ Назад", f"deck_menu_{deck_id}")],
    ])
    await query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return DECK_MENU

# ── Card management ───────────────────────────────────────────────────────────

async def start_add_cards(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = di['name'] if di else 'Колода'

    text = (
        f"➕ *Добавление карточек*\n\n"
        f"Колода: *{di['name']}*\n\n"
        f"Формат: `Вопрос | Ответ`\n"
        f"С подсказкой: `Вопрос | Ответ | Подсказка`\n\n"
        f"Примеры:\n"
        f"`Hello | Привет`\n"
        f"`Столица Японии | Токио | Остров Хонсю`\n\n"
        f"Напишите «*готово*» или нажмите кнопку для завершения."
    )
    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown"
    )
    return ADD_CARD

async def list_cards(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    cards = db.get_deck_cards(deck_id)
    di = db.get_deck_info(deck_id)

    if not cards:
        await query.answer("В колоде нет карточек", show_alert=True)
        return DECK_MENU

    text = f"📋 *{di['name']}* — {len(cards)} карточек:\n\n"
    for i, c in enumerate(cards[:25], 1):
        q = c['question'][:35] + "…" if len(c['question']) > 35 else c['question']
        a = c['answer'][:35] + "…"   if len(c['answer']) > 35   else c['answer']
        text += f"*{i}.* {q}\n   ✅ {a}\n"

    if len(cards) > 25:
        text += f"\n_...и ещё {len(cards)-25} карточек_"

    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("⬅️ Назад", f"deck_menu_{deck_id}")]]),
        parse_mode="Markdown"
    )
    return DECK_MENU

async def confirm_delete_deck(update, context):
    query = update.callback_query
    deck_id = int(query.data.split("_")[2])
    di = db.get_deck_info(deck_id)
    text = (
        f"⚠️ *Удалить колоду «{di['name']}»?*\n\n"
        f"Это удалит *{di['card_count']}* карточек и весь прогресс.\n"
        f"*Действие необратимо!*"
    )
    await query.edit_message_text(
        text,
        reply_markup=kb([
            [btn("🗑 Да, удалить", f"confirm_delete_{deck_id}"),
             btn("❌ Отмена", f"deck_menu_{deck_id}")]
        ]),
        parse_mode="Markdown"
    )
    return DECK_MENU

async def do_delete_deck(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    deck_id = int(query.data.split("_")[2])
    db.delete_deck(deck_id, user_id)
    await query.answer("✅ Колода удалена")
    return await show_decks_menu(update, context)

# ── Create deck ───────────────────────────────────────────────────────────────

DECK_EMOJIS = ["📖","🌍","🔬","💻","🎵","🏛","📐","💼","🌿","🎨","🏆","🔤"]

async def start_create_deck(update, context):
    query = update.callback_query
    await query.answer()
    text = (
        "➕ *Создание новой колоды*\n\n"
        "Введите название колоды:\n"
        "_Например: «Английский B2», «Анатомия», «История»_"
    )
    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("❌ Отмена", "main_menu")]]),
        parse_mode="Markdown"
    )
    return CREATE_DECK

async def create_deck_name(update, context):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Слишком короткое. Введите снова:")
        return CREATE_DECK
    if len(name) > 50:
        await update.message.reply_text("❌ Слишком длинное (макс. 50 символов):")
        return CREATE_DECK

    emoji = random.choice(DECK_EMOJIS)
    deck_id = db.create_deck(user_id, name, emoji=emoji)
    context.user_data['new_deck_id'] = deck_id
    context.user_data['new_deck_name'] = name

    text = (
        f"✅ *{emoji} Колода «{name}» создана!*\n\n"
        f"Добавьте карточки.\n"
        f"Формат: `Вопрос | Ответ`\n"
        f"С подсказкой: `Вопрос | Ответ | Подсказка`\n\n"
        f"Напишите «готово» для завершения."
    )
    await update.message.reply_text(
        text,
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown"
    )
    return ADD_CARD

async def add_card_to_deck(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() in ('готово', 'done', 'stop'):
        return await finish_adding_cards(update, context)

    if '|' not in text:
        await update.message.reply_text(
            "❌ Формат: `Вопрос | Ответ` или `Вопрос | Ответ | Подсказка`",
            parse_mode="Markdown"
        )
        return ADD_CARD

    parts = [p.strip() for p in text.split('|')]
    question = parts[0]
    answer   = parts[1] if len(parts) > 1 else ''
    hint     = parts[2] if len(parts) > 2 else None

    if not question or not answer:
        await update.message.reply_text("❌ Вопрос и ответ не могут быть пустыми!")
        return ADD_CARD

    deck_id = context.user_data.get('new_deck_id')
    if not deck_id:
        await update.message.reply_text("❌ Ошибка: начните заново /start")
        return MAIN_MENU

    card_id = db.add_card(deck_id, question, answer, hint)
    db.init_card_progress(user_id, card_id)
    count = len(db.get_deck_cards(deck_id))

    hint_str = f"\n💡 _{hint}_" if hint else ""
    reply = (
        f"✅ *Карточка {count} добавлена!*\n\n"
        f"❓ {question}\n"
        f"✅ {answer}{hint_str}\n\n"
        f"Следующую или «готово»:"
    )
    await update.message.reply_text(
        reply,
        reply_markup=kb([[btn("✅ Завершить", "finish_adding")]]),
        parse_mode="Markdown"
    )
    return ADD_CARD

async def finish_adding_cards(update, context):
    deck_id = context.user_data.get('new_deck_id')
    name    = context.user_data.get('new_deck_name', 'Колода')
    di = db.get_deck_info(deck_id) if deck_id else None
    count = di['card_count'] if di else 0

    text = (
        f"🎉 *Колода «{name}» готова!*\n\n"
        f"📝 Карточек: {count}\n\n"
        f"_Совет: начните с режима SRS — он запомнит всё за вас!_"
    )
    markup = kb([
        [btn("🧠 SRS — начать", f"study_srs_{deck_id}")],
        [btn("🎴 Карточки",     f"study_flash_{deck_id}"),
         btn("🎯 Тест",         f"study_quiz_{deck_id}")],
        [btn("📚 Мои колоды", "my_decks")],
    ])

    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

# ── Dictionary ────────────────────────────────────────────────────────────────

async def browse_dictionary(update, context):
    query = update.callback_query
    if query.data.startswith("import_collection_"):
        return await import_collection(update, context)

    text = "📖 *Готовые коллекции*\n\nВыберите и добавьте в свои колоды:"
    buttons = []
    for key, (name, cards) in COLLECTIONS.items():
        buttons.append([btn(f"{name} ({len(cards)} карт.)", f"import_collection_{key}")])
    buttons.append([btn("⬅️ Назад", "main_menu")])

    await query.edit_message_text(text, reply_markup=kb(buttons), parse_mode="Markdown")
    return BROWSE_DICTIONARY

async def import_collection(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    key = query.data.replace("import_collection_", "")
    col = COLLECTIONS.get(key)
    if not col:
        await query.answer("❌ Не найдено", show_alert=True)
        return BROWSE_DICTIONARY

    name, cards = col
    deck_id = db.create_deck(user_id, name, emoji="📖")
    for q, a in cards:
        cid = db.add_card(deck_id, q, a)
        db.init_card_progress(user_id, cid)

    text = (
        f"✅ *Импортировано!*\n\n"
        f"📖 {name}\n"
        f"📝 {len(cards)} карточек добавлено\n\n"
        f"_Начните с режима SRS для умного повторения!_"
    )
    await query.edit_message_text(
        text,
        reply_markup=kb([
            [btn("🧠 SRS — начать", f"study_srs_{deck_id}")],
            [btn("📖 Ещё коллекции", "browse_dict"),
             btn("📚 Мои колоды", "my_decks")],
        ]),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# ── Stats ─────────────────────────────────────────────────────────────────────

async def show_full_stats(update, context):
    if update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        user_id = update.effective_user.id

    stats = db.get_user_stats(user_id)
    g     = db.get_gamification(user_id)
    level = g.get('level', 1)
    em, lname = LEVEL_NAMES.get(level, ('⭐', ''))
    activity = db.get_weekly_activity(user_id)

    # Weekly chart (text)
    from datetime import date, timedelta
    days_map = {r['day']: r['cards'] for r in activity}
    week_str = ""
    for i in range(6, -1, -1):
        d = str(date.today() - timedelta(days=i))
        cnt = days_map.get(d, 0)
        bar = progress_bar(min(cnt, 50), 5)
        short = d[5:]
        week_str += f"`{short}` {bar} {cnt}\n"

    total_min = stats.get('total_time_s', 0) // 60
    last = stats.get('last_studied', '')
    last_str = last[:10] if last else 'Никогда'

    text = (
        f"📊 *Ваша статистика*\n\n"
        f"{Gamification.format_level(user_id)}\n\n"
        f"📚 *Обучение:*\n"
        f"• Колод: {stats.get('decks_count',0)}\n"
        f"• Сессий: {stats.get('total_sessions',0)}\n"
        f"• Правильных: {stats.get('total_correct',0)}\n"
        f"• Точность: {stats.get('accuracy',0)}%\n"
        f"• Время в боте: {total_min} мин\n"
        f"• Последнее занятие: {last_str}\n\n"
        f"🔥 *Серия:* {g.get('current_streak',0)} дней (рекорд: {g.get('max_streak',0)})\n"
        f"📅 *Всего дней:* {g.get('total_study_days',0)}\n\n"
        f"📆 *Активность за 7 дней:*\n{week_str}"
    )

    markup = kb([
        [btn("🏅 Достижения", "achievements"),
         btn("🏆 Рейтинг",    "leaderboard")],
        [btn("📋 Задания дня", "daily_tasks")],
        [btn("⬅️ Назад", "main_menu")],
    ])

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    return MAIN_MENU

# ── Achievements ──────────────────────────────────────────────────────────────

async def show_achievements(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    text = f"🏅 *Достижения*\n\n{Gamification.format_achievements(user_id)}"
    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("⬅️ Назад", "my_stats")]]),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# ── Daily Tasks ───────────────────────────────────────────────────────────────

async def show_daily_tasks(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    tasks_str = Gamification.format_daily_tasks(user_id)
    streak = db.get_gamification(user_id).get('current_streak', 0)

    text = (
        f"📋 *Задания на сегодня*\n"
        f"🔥 Серия: {streak} дней\n\n"
        f"{tasks_str}\n\n"
        f"_Выполняйте задания каждый день для поддержания серии!_"
    )
    await query.edit_message_text(
        text,
        reply_markup=kb([
            [btn("📚 К колодам", "my_decks")],
            [btn("⬅️ Назад", "main_menu")],
        ]),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# ── Leaderboard ───────────────────────────────────────────────────────────────

async def show_leaderboard(update, context):
    query = update.callback_query
    leaders = db.get_leaderboard(10)

    if not leaders:
        text = "🏆 *Рейтинг пуст* — будьте первым!"
    else:
        medals = ['🥇','🥈','🥉'] + ['4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
        text = "🏆 *Таблица лидеров*\n\n"
        for i, l in enumerate(leaders):
            name = l.get('first_name') or l.get('username') or f"Игрок {i+1}"
            em, _ = LEVEL_NAMES.get(l.get('level', 1), ('⭐', ''))
            text += (
                f"{medals[i]} *{name}*\n"
                f"   {em} Ур.{l.get('level',1)} | "
                f"⭐{l.get('total_points',0)} | 🔥{l.get('current_streak',0)}д\n"
            )

    await query.edit_message_text(
        text,
        reply_markup=kb([[btn("⬅️ Назад", "main_menu")]]),
        parse_mode="Markdown"
    )
    return MAIN_MENU

# ── Settings ──────────────────────────────────────────────────────────────────

async def show_settings(update, context):
    if update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        user_id = update.effective_user.id

    s = db.get_settings(user_id)
    notif = "✅ Вкл" if s.get('notifications', 1) else "❌ Выкл"
    hints = "✅ Вкл" if s.get('show_hints', 1) else "❌ Выкл"
    rev   = "✅ Вкл" if s.get('reverse_mode', 0) else "❌ Выкл"
    diff_map = {'easy': '🟢 Лёгкий', 'medium': '🟡 Средний', 'hard': '🔴 Сложный'}
    diff = diff_map.get(s.get('difficulty', 'medium'), '🟡 Средний')

    text = (
        f"⚙️ *Настройки*\n\n"
        f"• 🔔 Уведомления: {notif}\n"
        f"• 💡 Подсказки: {hints}\n"
        f"• 🔃 Реверс (ответ→вопрос): {rev}\n"
        f"• 🎯 Сложность: {diff}\n"
        f"• 🎴 Карточек за сессию: {s.get('cards_per_session', 20)}"
    )
    markup = kb([
        [btn(f"🔔 Уведомления: {notif}", "toggle_notifications")],
        [btn(f"💡 Подсказки: {hints}", "toggle_hints")],
        [btn(f"🔃 Реверс: {rev}", "toggle_reverse")],
        [btn("🎯 Сложность: ← →", "cycle_difficulty")],
        [btn("➖ 5 карточек", "cards_less"),
         btn("➕ 5 карточек", "cards_more")],
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
        cycle = {'easy': 'medium', 'medium': 'hard', 'hard': 'easy'}
        db.update_setting(user_id, 'difficulty', cycle.get(s.get('difficulty', 'medium'), 'medium'))
    elif data == "cards_less":
        db.update_setting(user_id, 'cards_per_session', max(5, s.get('cards_per_session', 20) - 5))
    elif data == "cards_more":
        db.update_setting(user_id, 'cards_per_session', min(50, s.get('cards_per_session', 20) + 5))

    await query.answer("✅ Сохранено")
    return await show_settings(update, context)

# ── Help ──────────────────────────────────────────────────────────────────────

async def show_help(update, context):
    text = (
        "❓ *QuizletBot — Помощь*\n\n"
        "*Команды:*\n"
        "/start — главное меню\n"
        "/stats — статистика\n"
        "/help — эта страница\n"
        "/cancel — отмена\n\n"
        "*Режимы обучения:*\n"
        "🧠 *SRS* — умный алгоритм SM-2: показывает карточки в нужный момент. Чем лучше знаете — тем реже повторяете\n"
        "🎴 *Карточки* — переворачивайте и оценивайте себя\n"
        "✍️ *Письменный* — вводите ответ, допускаются опечатки до 10%\n"
        "🎯 *Тест* — 4 варианта ответа, быстро и весело\n"
        "🎮 *Смешанный* — чередование всех режимов\n"
        "💪 *Ошибки* — фокус на самых сложных карточках\n\n"
        "*Создание карточек:*\n"
        "`Вопрос | Ответ`\n"
        "`Вопрос | Ответ | Подсказка`\n\n"
        "*Советы:*\n"
        "• Занимайтесь каждый день — это важнее длительности\n"
        "• SRS сам напомнит что повторить и когда\n"
        "• Используйте «Ошибки» для прокачки слабых мест\n"
        "• Выполняйте ежедневные задания для бонусов\n"
        "• Следите за прогрессом в Аналитике колоды"
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
    await update.message.reply_text("❌ Отменено", reply_markup=get_main_keyboard())
    return MAIN_MENU

async def message_handler(update, context):
    s = _session(context)
    if s and s.get('mode') in ('write', 'mixed', 'weak'):
        return await check_write_answer(update, context)
    await update.message.reply_text(
        "Используйте кнопки меню 👇",
        reply_markup=get_main_keyboard()
    )
    return MAIN_MENU
