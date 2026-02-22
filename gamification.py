"""
gamification.py — уровни, достижения, задания дня, очки
"""
import json
from database import Database

db = Database()

LEVEL_NAMES = {
    1:  ('🌱', 'Новичок'),    2: ('📗', 'Ученик'),
    3:  ('📘', 'Знаток'),     4: ('📙', 'Опытный'),
    5:  ('🥈', 'Умелец'),     6: ('🥇', 'Эксперт'),
    7:  ('💎', 'Мастер'),     8: ('👑', 'Гроссмейстер'),
    9:  ('🔮', 'Мудрец'),    10: ('⭐', 'Легенда'),
}
LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]

ACHIEVEMENTS = {
    'first_card':   {'emoji': '🎯', 'name': 'Первый шаг',      'desc': 'Ответьте на первую карточку'},
    'streak_3':     {'emoji': '🔥', 'name': 'Три дня',         'desc': '3 дня подряд'},
    'streak_7':     {'emoji': '🔥', 'name': 'Неделя',          'desc': '7 дней подряд'},
    'streak_30':    {'emoji': '🌟', 'name': 'Месяц',           'desc': '30 дней подряд'},
    'cards_10':     {'emoji': '📗', 'name': 'Десятка',         'desc': '10 правильных ответов'},
    'cards_50':     {'emoji': '📘', 'name': 'Полтинник',       'desc': '50 правильных ответов'},
    'cards_100':    {'emoji': '💯', 'name': 'Сотня',           'desc': '100 правильных ответов'},
    'cards_500':    {'emoji': '🏆', 'name': 'Пятисотка',       'desc': '500 правильных ответов'},
    'perfect':      {'emoji': '🎯', 'name': 'Снайпер',         'desc': 'Сессия без ошибок (5+ карт)'},
    'speed':        {'emoji': '⚡', 'name': 'Спринтер',         'desc': '20 карточек за 5 минут'},
    'collector':    {'emoji': '📚', 'name': 'Коллекционер',    'desc': '5 колод создано'},
    'all_modes':    {'emoji': '🎮', 'name': 'Многогранный',    'desc': 'Попробуйте 5 режимов'},
    'match_win':    {'emoji': '🔗', 'name': 'Матчмейкер',      'desc': 'Завершите режим Пары'},
    'anagram_10':   {'emoji': '🔤', 'name': 'Эрудит',          'desc': '10 анаграмм угадано'},
    'night_owl':    {'emoji': '🦉', 'name': 'Сова',            'desc': 'Занятие после 23:00'},
    'early_bird':   {'emoji': '🐦', 'name': 'Жаворонок',       'desc': 'Занятие до 7:00'},
    'write_20':     {'emoji': '✍️', 'name': 'Каллиграф',       'desc': '20 верных в письменном'},
    'daily_done':   {'emoji': '📋', 'name': 'Дисциплина',      'desc': 'Все задания за день'},
    'retelling_5':  {'emoji': '📖', 'name': 'Рассказчик',      'desc': '5 пересказов'},
    'leitner_full': {'emoji': '📦', 'name': 'Ящики Лейтнера',  'desc': 'Пройдите все 5 ящиков'},
    'marathon':     {'emoji': '🏃', 'name': 'Марафонец',       'desc': 'Марафон — вся колода'},
    'sprint_20':    {'emoji': '🚀', 'name': 'Реактивный',      'desc': 'Спринт — 20 карточек'},
}

POINTS = {
    'correct_flashcard': 5,
    'correct_write':    12,
    'correct_quiz':      8,
    'correct_srs':      10,
    'correct_match':    15,
    'correct_anagram':  10,
    'correct_first_letter': 8,
    'correct_retelling': 12,
    'correct_sprint':    6,
    'perfect_session':  50,
    'daily_bonus':      20,
    'achievement':      30,
}

MODE_USED_KEY = 'modes_used'


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
        events = {}

        # Streak
        streak = db.update_streak(user_id)
        events['streak'] = streak

        # Points per correct answer
        action_map = {
            'flashcard':    'correct_flashcard',
            'write':        'correct_write',
            'quiz':         'correct_quiz',
            'srs':          'correct_srs',
            'mixed':        'correct_flashcard',
            'weak':         'correct_flashcard',
            'match':        'correct_match',
            'anagram':      'correct_anagram',
            'first_letter': 'correct_first_letter',
            'retelling':    'correct_retelling',
            'sprint':       'correct_sprint',
            'marathon':     'correct_flashcard',
            'reading':      'correct_flashcard',
            'leitner':      'correct_srs',
        }
        pts_each = POINTS.get(action_map.get(mode, 'correct_flashcard'), 5)
        total_pts = correct * pts_each
        if total_pts > 0:
            db.add_points(user_id, total_pts)
        events['points'] = total_pts

        # Perfect bonus
        if total >= 5 and wrong == 0:
            db.add_points(user_id, POINTS['perfect_session'])
            events['perfect'] = True

        # Streak milestone bonus
        if streak in (3, 7, 14, 30, 60, 100):
            bonus = streak * 2
            db.add_points(user_id, bonus)
            events['streak_bonus'] = bonus

        # Daily tasks
        db.update_daily_task(user_id, 'study_cards', total)
        db.update_daily_task(user_id, 'use_mode', 1)

        # Track modes used
        Gamification._track_mode(user_id, mode)

        # Speed check
        if total >= 20 and duration_s > 0 and duration_s <= 300:
            events['speed'] = True

        # Level
        events['level'] = db.calc_level(user_id)

        # Achievements
        events['achievements'] = Gamification.check_achievements(user_id, {
            'streak': streak, 'correct': correct,
            'total': total, 'wrong': wrong,
            'mode': mode, 'duration_s': duration_s,
        })
        return events

    @staticmethod
    def _track_mode(user_id: int, mode: str):
        """Track which modes the user has tried"""
        import json
        g = db.get_gamification(user_id)
        try:
            used = json.loads(g.get('achievements', '[]'))
        except Exception:
            used = []
        key = f'mode_{mode}'
        if key not in used:
            conn = db.get_connection()
            # Store in a separate lightweight way — reuse achievements field trick
            # Actually we just check if they tried 5 modes via a helper
            conn.close()

    @staticmethod
    def check_achievements(user_id: int, data: dict) -> list:
        new = []
        stats = db.get_user_stats(user_id)
        g = db.get_gamification(user_id)

        def unlock(k):
            if db.unlock_achievement(user_id, k):
                db.add_points(user_id, POINTS['achievement'])
                new.append(k)

        tc = stats.get('total_correct', 0)
        streak = data.get('streak', 0)

        if tc >= 1:    unlock('first_card')
        if streak >= 3:  unlock('streak_3')
        if streak >= 7:  unlock('streak_7')
        if streak >= 30: unlock('streak_30')
        if tc >= 10:   unlock('cards_10')
        if tc >= 50:   unlock('cards_50')
        if tc >= 100:  unlock('cards_100')
        if tc >= 500:  unlock('cards_500')

        if data.get('wrong', 1) == 0 and data.get('total', 0) >= 5:
            unlock('perfect')
        if data.get('total', 0) >= 20 and 0 < data.get('duration_s', 9999) <= 300:
            unlock('speed')
        if stats.get('decks_count', 0) >= 5:
            unlock('collector')

        mode = data.get('mode', '')
        if mode == 'match':    unlock('match_win')
        if mode == 'marathon': unlock('marathon')
        if mode == 'sprint':   unlock('sprint_20')

        from datetime import datetime
        h = datetime.now().hour
        if h >= 23 or h < 1:  unlock('night_owl')
        if 5 <= h < 7:        unlock('early_bird')

        return new

    @staticmethod
    def format_level(user_id: int) -> str:
        g = db.get_gamification(user_id)
        lvl = g.get('level', 1)
        em, name = LEVEL_NAMES.get(lvl, ('⭐', 'Легенда'))
        pts = g.get('total_points', 0)
        thr = LEVEL_THRESHOLDS
        if lvl < len(thr):
            prev, nxt = thr[lvl - 1], thr[lvl]
            pct = min(100, round((pts - prev) / max(1, nxt - prev) * 100))
        else:
            pct = 100
        bar = '█' * (pct // 10) + '░' * (10 - pct // 10)
        return f"{em} Уровень {lvl} — {name}\n{bar} {pct}%  ({pts} очков)"

    @staticmethod
    def format_achievements(user_id: int) -> str:
        g = db.get_gamification(user_id)
        achieved = json.loads(g.get('achievements', '[]'))
        done, locked = [], []
        for k, info in ACHIEVEMENTS.items():
            line = f"{info['emoji']} *{info['name']}* — {info['desc']}"
            if k in achieved:
                done.append(f"✅ {line}")
            else:
                locked.append(f"🔒 _{info['name']}_ — {info['desc']}")
        parts = []
        if done:
            parts.append("*Получено:*\n" + '\n'.join(done))
        if locked:
            parts.append("*Заблокировано:*\n" + '\n'.join(locked))
        return '\n\n'.join(parts) or 'Пока нет достижений'

    @staticmethod
    def format_daily_tasks(user_id: int) -> str:
        tasks = db.get_or_create_daily_tasks(user_id)
        labels = {
            'study_cards':    '📝 Ответить на {} карточек',
            'correct_streak': '🎯 {} верных ответов подряд',
            'use_mode':       '🎮 Попробовать любой режим',
        }
        lines = []
        all_done = all(t['completed'] for t in tasks)
        for t in tasks:
            label = labels.get(t['task_type'], t['task_type']).format(t['target'])
            if t['task_type'] == 'use_mode':
                mark = '✅' if t['completed'] else '⬜'
                lines.append(f"{mark} {label}")
            else:
                pct = min(100, round(t['current'] / t['target'] * 100)) if t['target'] else 0
                bar = '█' * (pct // 20) + '░' * (5 - pct // 20)
                mark = '✅' if t['completed'] else '⬜'
                lines.append(f"{mark} {label}\n   {bar} {t['current']}/{t['target']}")
        if all_done:
            lines.append('\n🎉 *Все задания выполнены! +20 очков*')
        return '\n'.join(lines)
