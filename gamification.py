import json
from database import Database

db = Database()

LEVEL_NAMES = {
    1:  ('🌱', 'Новичок'),
    2:  ('📗', 'Ученик'),
    3:  ('📘', 'Знаток'),
    4:  ('📙', 'Опытный'),
    5:  ('🥈', 'Умелец'),
    6:  ('🥇', 'Эксперт'),
    7:  ('💎', 'Мастер'),
    8:  ('👑', 'Гроссмейстер'),
    9:  ('🔮', 'Мудрец'),
    10: ('⭐', 'Легенда'),
}

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]

ACHIEVEMENTS = {
    'first_card':     {'emoji': '🎯', 'name': 'Первый шаг',      'desc': 'Ответьте на первую карточку'},
    'streak_3':       {'emoji': '🔥', 'name': 'Трёхдневка',      'desc': '3 дня подряд'},
    'streak_7':       {'emoji': '🔥', 'name': 'Неделя',          'desc': '7 дней подряд'},
    'streak_30':      {'emoji': '🌟', 'name': 'Месяц без пауз',  'desc': '30 дней подряд'},
    'cards_10':       {'emoji': '📗', 'name': 'Десятка',         'desc': 'Выучите 10 карточек'},
    'cards_50':       {'emoji': '📘', 'name': 'Полтинник',       'desc': 'Выучите 50 карточек'},
    'cards_100':      {'emoji': '💯', 'name': 'Сотня',           'desc': 'Выучите 100 карточек'},
    'cards_500':      {'emoji': '🏆', 'name': 'Пятисотка',       'desc': 'Выучите 500 карточек'},
    'perfect_quiz':   {'emoji': '🎯', 'name': 'Снайпер',         'desc': 'Тест на 100%'},
    'deck_complete':  {'emoji': '✅', 'name': 'Завершитель',      'desc': 'Выучите всю колоду'},
    'speed_demon':    {'emoji': '⚡', 'name': 'Спринтер',         'desc': '20 карточек за 5 минут'},
    'collector':      {'emoji': '📚', 'name': 'Коллекционер',    'desc': 'Создайте 5 колод'},
    'all_modes':      {'emoji': '🎮', 'name': 'Многогранный',    'desc': 'Попробуйте все режимы'},
    'srs_master':     {'emoji': '🧠', 'name': 'Мастер памяти',   'desc': '50 повторений по SRS'},
    'night_owl':      {'emoji': '🦉', 'name': 'Сова',            'desc': 'Занимайтесь после 23:00'},
    'early_bird':     {'emoji': '🐦', 'name': 'Жаворонок',       'desc': 'Занимайтесь до 7:00'},
    'write_master':   {'emoji': '✍️', 'name': 'Каллиграф',       'desc': '20 верных в письм. режиме'},
    'daily_tasks':    {'emoji': '📋', 'name': 'Дисциплина',      'desc': 'Выполните все дневные задания'},
}

POINTS = {
    'correct_flashcard': 5,
    'correct_write':     12,
    'correct_quiz':      8,
    'srs_correct':       10,
    'perfect_session':   50,
    'daily_bonus':       20,
    'streak_bonus':      15,
    'achievement':       30,
}


class Gamification:

    @staticmethod
    def reward(user_id: int, action: str) -> int:
        pts = POINTS.get(action, 5)
        db.add_points(user_id, pts)
        db.calc_level(user_id)
        return pts

    @staticmethod
    def after_session(user_id: int, correct: int, wrong: int,
                      total: int, mode: str, duration_s: int) -> dict:
        """Call after any study session. Returns events dict for notification."""
        events = {}

        # Streak
        streak = db.update_streak(user_id)
        events['streak'] = streak

        # Points for correct answers
        action_map = {
            'flashcard': 'correct_flashcard',
            'write':     'correct_write',
            'quiz':      'correct_quiz',
            'srs':       'srs_correct',
            'mixed':     'correct_flashcard',
            'weak':      'correct_flashcard',
        }
        action = action_map.get(mode, 'correct_flashcard')
        pts = 0
        for _ in range(correct):
            pts += db.add_points(user_id, POINTS.get(action, 5)) - (db.get_gamification(user_id)['total_points'] - POINTS.get(action, 5))

        # Simpler: just add all at once
        pts = correct * POINTS.get(action, 5)
        db.add_points(user_id, pts)
        events['points'] = pts

        # Perfect session bonus
        if total >= 5 and wrong == 0:
            db.add_points(user_id, POINTS['perfect_session'])
            events['perfect'] = True

        # Streak bonus
        if streak in (3, 7, 14, 30, 60, 100):
            db.add_points(user_id, POINTS['streak_bonus'] * streak // 3)
            events['streak_bonus'] = True

        # Daily tasks
        db.update_daily_task(user_id, 'study_cards', total)
        db.update_daily_task(user_id, 'use_mode', 1)

        # Speed bonus
        if total >= 20 and duration_s <= 300:
            events['speed'] = True

        # Level
        level = db.calc_level(user_id)
        events['level'] = level

        # Check achievements
        new_achs = Gamification.check_achievements(user_id, {
            'streak': streak,
            'correct': correct,
            'total': total,
            'wrong': wrong,
            'mode': mode,
            'duration_s': duration_s,
        })
        events['achievements'] = new_achs

        return events

    @staticmethod
    def check_achievements(user_id: int, data: dict) -> list:
        new = []
        g = db.get_gamification(user_id)
        achieved = json.loads(g.get('achievements', '[]'))
        stats = db.get_user_stats(user_id)

        def unlock(k):
            if db.unlock_achievement(user_id, k):
                db.add_points(user_id, POINTS['achievement'])
                new.append(k)

        # First card
        if stats.get('total_correct', 0) >= 1:
            unlock('first_card')

        # Streaks
        streak = data.get('streak', 0)
        if streak >= 3:  unlock('streak_3')
        if streak >= 7:  unlock('streak_7')
        if streak >= 30: unlock('streak_30')

        # Cards learned (total correct across all time)
        tc = stats.get('total_correct', 0)
        if tc >= 10:  unlock('cards_10')
        if tc >= 50:  unlock('cards_50')
        if tc >= 100: unlock('cards_100')
        if tc >= 500: unlock('cards_500')

        # Perfect session
        if data.get('wrong', 1) == 0 and data.get('total', 0) >= 5:
            unlock('perfect_quiz')

        # Speed
        if data.get('total', 0) >= 20 and data.get('duration_s', 9999) <= 300:
            unlock('speed_demon')

        # Write master
        if data.get('mode') == 'write' and data.get('correct', 0) >= 20:
            unlock('write_master')

        # Decks collector
        if stats.get('decks_count', 0) >= 5:
            unlock('collector')

        # Night owl / early bird
        from datetime import datetime
        hour = datetime.now().hour
        if hour >= 23 or hour < 1:
            unlock('night_owl')
        if 5 <= hour < 7:
            unlock('early_bird')

        return new

    @staticmethod
    def format_level(user_id: int) -> str:
        g = db.get_gamification(user_id)
        lvl = g.get('level', 1)
        emoji, name = LEVEL_NAMES.get(lvl, ('⭐', 'Легенда'))
        pts = g.get('total_points', 0)
        thresholds = LEVEL_THRESHOLDS
        if lvl < len(thresholds):
            next_t = thresholds[lvl]
            bar_pct = min(100, round((pts - thresholds[lvl-1]) / max(1, next_t - thresholds[lvl-1]) * 100))
        else:
            bar_pct = 100
            next_t = pts
        bar = '█' * (bar_pct // 10) + '░' * (10 - bar_pct // 10)
        return f"{emoji} Уровень {lvl} — {name}\n{bar} {bar_pct}%  ({pts} очков)"

    @staticmethod
    def format_achievements(user_id: int) -> str:
        g = db.get_gamification(user_id)
        achieved = json.loads(g.get('achievements', '[]'))
        lines = []
        for key, info in ACHIEVEMENTS.items():
            if key in achieved:
                lines.append(f"{info['emoji']} *{info['name']}* — {info['desc']}")
            else:
                lines.append(f"🔒 _{info['name']}_ — {info['desc']}")
        return '\n'.join(lines) if lines else 'Пока нет достижений'

    @staticmethod
    def format_daily_tasks(user_id: int) -> str:
        tasks = db.get_or_create_daily_tasks(user_id)
        labels = {
            'study_cards':    '📝 Ответьте на {} карточек',
            'correct_streak': '🎯 {} верных ответов подряд',
            'use_mode':       '🎮 Попробуйте любой режим',
        }
        lines = []
        all_done = True
        for t in tasks:
            label = labels.get(t['task_type'], t['task_type']).format(t['target'])
            done = t['completed']
            if not done:
                all_done = False
            if t['task_type'] == 'use_mode':
                mark = '✅' if done else '⬜'
                lines.append(f"{mark} {label}")
            else:
                pct = min(100, round(t['current'] / t['target'] * 100))
                bar = '█' * (pct // 20) + '░' * (5 - pct // 20)
                mark = '✅' if done else '⬜'
                lines.append(f"{mark} {label}\n   {bar} {t['current']}/{t['target']}")
        if all_done:
            lines.append('\n🎉 *Все задания выполнены! +20 очков*')
        return '\n'.join(lines)
