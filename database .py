import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import json


class Database:
    def __init__(self, db_name='quizlet_bot.db'):
        self.db_name = db_name

    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS decks (
                deck_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                name        TEXT NOT NULL,
                description TEXT,
                emoji       TEXT DEFAULT "📖",
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cards (
                card_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id    INTEGER NOT NULL,
                question   TEXT NOT NULL,
                answer     TEXT NOT NULL,
                hint       TEXT,
                difficulty INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS card_progress (
                progress_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                card_id       INTEGER NOT NULL,
                level         INTEGER DEFAULT 0,
                ease_factor   REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 1,
                next_review   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                correct_count INTEGER DEFAULT 0,
                wrong_count   INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP,
                UNIQUE(user_id, card_id)
            );
            CREATE TABLE IF NOT EXISTS study_sessions (
                session_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                deck_id     INTEGER NOT NULL,
                mode        TEXT NOT NULL,
                correct     INTEGER DEFAULT 0,
                wrong       INTEGER DEFAULT 0,
                duration_s  INTEGER DEFAULT 0,
                started_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_gamification (
                user_id          INTEGER PRIMARY KEY,
                total_points     INTEGER DEFAULT 0,
                current_streak   INTEGER DEFAULT 0,
                max_streak       INTEGER DEFAULT 0,
                last_study_date  DATE,
                total_study_days INTEGER DEFAULT 0,
                achievements     TEXT DEFAULT "[]",
                level            INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id           INTEGER PRIMARY KEY,
                notifications     INTEGER DEFAULT 1,
                difficulty        TEXT DEFAULT "medium",
                cards_per_session INTEGER DEFAULT 20,
                reminder_time     TEXT DEFAULT "20:00",
                show_hints        INTEGER DEFAULT 1,
                reverse_mode      INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS daily_tasks (
                task_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                date      DATE NOT NULL,
                task_type TEXT NOT NULL,
                target    INTEGER NOT NULL,
                current   INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                UNIQUE(user_id, date, task_type)
            );
        ''')
        conn.commit()
        conn.close()

    # ── USERS ──────────────────────────────────────────────────────────────
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE user_id=?', (user_id,))
        if c.fetchone():
            c.execute('UPDATE users SET username=?, first_name=? WHERE user_id=?',
                      (username, first_name, user_id))
        else:
            c.execute('INSERT INTO users (user_id, username, first_name) VALUES (?,?,?)',
                      (user_id, username, first_name))
        conn.commit()
        conn.close()

    # ── DECKS ──────────────────────────────────────────────────────────────
    def create_deck(self, user_id: int, name: str, description: str = None, emoji: str = '📖') -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO decks (user_id, name, description, emoji) VALUES (?,?,?,?)',
                  (user_id, name, description, emoji))
        did = c.lastrowid
        conn.commit()
        conn.close()
        return did

    def get_user_decks(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT d.*, COUNT(ca.card_id) as card_count
            FROM decks d LEFT JOIN cards ca ON d.deck_id=ca.deck_id
            WHERE d.user_id=? GROUP BY d.deck_id ORDER BY d.updated_at DESC
        ''', (user_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_deck_info(self, deck_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT d.*, COUNT(ca.card_id) as card_count
            FROM decks d LEFT JOIN cards ca ON d.deck_id=ca.deck_id
            WHERE d.deck_id=? GROUP BY d.deck_id
        ''', (deck_id,))
        r = c.fetchone()
        conn.close()
        return dict(r) if r else None

    def delete_deck(self, deck_id: int, user_id: int) -> bool:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT user_id FROM decks WHERE deck_id=?', (deck_id,))
        r = c.fetchone()
        if not r or r['user_id'] != user_id:
            conn.close()
            return False
        c.execute('DELETE FROM card_progress WHERE card_id IN (SELECT card_id FROM cards WHERE deck_id=?)', (deck_id,))
        c.execute('DELETE FROM cards WHERE deck_id=?', (deck_id,))
        c.execute('DELETE FROM study_sessions WHERE deck_id=?', (deck_id,))
        c.execute('DELETE FROM decks WHERE deck_id=?', (deck_id,))
        conn.commit()
        conn.close()
        return True

    def touch_deck(self, deck_id: int):
        conn = self.get_connection()
        conn.execute('UPDATE decks SET updated_at=? WHERE deck_id=?', (datetime.now(), deck_id))
        conn.commit()
        conn.close()

    # ── CARDS ──────────────────────────────────────────────────────────────
    def add_card(self, deck_id: int, question: str, answer: str, hint: str = None) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO cards (deck_id, question, answer, hint) VALUES (?,?,?,?)',
                  (deck_id, question, answer, hint))
        cid = c.lastrowid
        conn.execute('UPDATE decks SET updated_at=? WHERE deck_id=?', (datetime.now(), deck_id))
        conn.commit()
        conn.close()
        return cid

    def get_deck_cards(self, deck_id: int) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM cards WHERE deck_id=? ORDER BY card_id', (deck_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_card(self, card_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM cards WHERE card_id=?', (card_id,))
        r = c.fetchone()
        conn.close()
        return dict(r) if r else None

    def delete_card(self, card_id: int):
        conn = self.get_connection()
        conn.execute('DELETE FROM card_progress WHERE card_id=?', (card_id,))
        conn.execute('DELETE FROM cards WHERE card_id=?', (card_id,))
        conn.commit()
        conn.close()

    # ── CARD PROGRESS (SM-2) ───────────────────────────────────────────────
    def init_card_progress(self, user_id: int, card_id: int):
        conn = self.get_connection()
        conn.execute('INSERT OR IGNORE INTO card_progress (user_id, card_id) VALUES (?,?)',
                     (user_id, card_id))
        conn.commit()
        conn.close()

    def get_card_progress(self, user_id: int, card_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM card_progress WHERE user_id=? AND card_id=?', (user_id, card_id))
        r = c.fetchone()
        conn.close()
        return dict(r) if r else None

    def update_card_progress(self, user_id: int, card_id: int,
                              level: int, ease_factor: float,
                              interval_days: int, next_review,
                              correct: bool):
        field = 'correct_count' if correct else 'wrong_count'
        conn = self.get_connection()
        conn.execute(f'''
            UPDATE card_progress
            SET level=?, ease_factor=?, interval_days=?, next_review=?,
                {field}={field}+1, last_reviewed=?
            WHERE user_id=? AND card_id=?
        ''', (level, ease_factor, interval_days, next_review, datetime.now(), user_id, card_id))
        conn.commit()
        conn.close()

    def get_due_cards(self, user_id: int, deck_id: int) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT ca.*, cp.level, cp.ease_factor, cp.interval_days,
                   cp.correct_count, cp.wrong_count, cp.next_review
            FROM cards ca
            LEFT JOIN card_progress cp ON ca.card_id=cp.card_id AND cp.user_id=?
            WHERE ca.deck_id=?
              AND (cp.next_review IS NULL OR cp.next_review <= datetime('now'))
            ORDER BY COALESCE(cp.level, 0) ASC, RANDOM()
        ''', (user_id, deck_id))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_deck_srs_stats(self, user_id: int, deck_id: int) -> Dict:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN cp.level >= 5 THEN 1 END) as mastered,
                COUNT(CASE WHEN cp.level BETWEEN 2 AND 4 THEN 1 END) as learning,
                COUNT(CASE WHEN cp.level < 2 OR cp.level IS NULL THEN 1 END) as new_cards,
                COUNT(CASE WHEN cp.next_review <= datetime('now') OR cp.next_review IS NULL THEN 1 END) as due
            FROM cards ca
            LEFT JOIN card_progress cp ON ca.card_id=cp.card_id AND cp.user_id=?
            WHERE ca.deck_id=?
        ''', (user_id, deck_id))
        r = c.fetchone()
        conn.close()
        d = dict(r) if r else {'total': 0, 'mastered': 0, 'learning': 0, 'new_cards': 0, 'due': 0}
        total = d.get('total', 1) or 1
        d['progress'] = round((d.get('mastered', 0) / total) * 100)
        return d

    def get_weak_cards(self, user_id: int, deck_id: int, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT ca.*, cp.correct_count, cp.wrong_count,
                CASE WHEN (cp.correct_count+cp.wrong_count)=0 THEN 0.0
                     ELSE CAST(cp.correct_count AS REAL)/(cp.correct_count+cp.wrong_count) END as accuracy
            FROM cards ca
            JOIN card_progress cp ON ca.card_id=cp.card_id AND cp.user_id=?
            WHERE ca.deck_id=? AND (cp.correct_count+cp.wrong_count) > 0
            ORDER BY accuracy ASC LIMIT ?
        ''', (user_id, deck_id, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    # ── SESSIONS ───────────────────────────────────────────────────────────
    def start_session(self, user_id: int, deck_id: int, mode: str) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO study_sessions (user_id, deck_id, mode) VALUES (?,?,?)',
                  (user_id, deck_id, mode))
        sid = c.lastrowid
        conn.commit()
        conn.close()
        return sid

    def finish_session(self, session_id: int, correct: int, wrong: int, duration_s: int):
        conn = self.get_connection()
        conn.execute('''
            UPDATE study_sessions SET correct=?, wrong=?, duration_s=?, finished_at=?
            WHERE session_id=?
        ''', (correct, wrong, duration_s, datetime.now(), session_id))
        conn.commit()
        conn.close()

    def get_user_stats(self, user_id: int) -> Dict:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(DISTINCT deck_id) as decks_sessions,
                   COUNT(*) as total_sessions,
                   COALESCE(SUM(correct),0) as total_correct,
                   COALESCE(SUM(wrong),0) as total_wrong,
                   COALESCE(SUM(correct+wrong),0) as total_attempts,
                   COALESCE(SUM(duration_s),0) as total_time_s,
                   MAX(finished_at) as last_studied
            FROM study_sessions WHERE user_id=? AND finished_at IS NOT NULL
        ''', (user_id,))
        r = c.fetchone()
        d = dict(r) if r else {}
        total = d.get('total_attempts', 0) or 1
        d['accuracy'] = round(d.get('total_correct', 0) / total * 100, 1)
        c.execute('SELECT COUNT(*) as cnt FROM decks WHERE user_id=?', (user_id,))
        r2 = c.fetchone()
        d['decks_count'] = r2['cnt'] if r2 else 0
        conn.close()
        return d

    def get_weekly_activity(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT DATE(started_at) as day,
                   COALESCE(SUM(correct+wrong),0) as cards,
                   COUNT(*) as sessions
            FROM study_sessions
            WHERE user_id=? AND finished_at IS NOT NULL
              AND started_at >= DATE('now','-6 days')
            GROUP BY DATE(started_at)
        ''', (user_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_deck_history(self, user_id: int, deck_id: int, limit: int = 5) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT mode, correct, wrong, duration_s, started_at
            FROM study_sessions
            WHERE user_id=? AND deck_id=? AND finished_at IS NOT NULL
            ORDER BY started_at DESC LIMIT ?
        ''', (user_id, deck_id, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    # ── GAMIFICATION ───────────────────────────────────────────────────────
    def init_gamification(self, user_id: int):
        conn = self.get_connection()
        conn.execute('INSERT OR IGNORE INTO user_gamification (user_id) VALUES (?)', (user_id,))
        conn.execute('INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)', (user_id,))
        conn.commit()
        conn.close()

    def get_gamification(self, user_id: int) -> Dict:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM user_gamification WHERE user_id=?', (user_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            self.init_gamification(user_id)
            return {'total_points': 0, 'current_streak': 0, 'max_streak': 0,
                    'total_study_days': 0, 'achievements': '[]', 'level': 1}
        return dict(r)

    def add_points(self, user_id: int, points: int) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('UPDATE user_gamification SET total_points=total_points+? WHERE user_id=?',
                  (points, user_id))
        c.execute('SELECT total_points FROM user_gamification WHERE user_id=?', (user_id,))
        r = c.fetchone()
        conn.commit()
        conn.close()
        return r['total_points'] if r else 0

    def update_streak(self, user_id: int) -> int:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT last_study_date, current_streak, max_streak, total_study_days FROM user_gamification WHERE user_id=?', (user_id,))
        r = c.fetchone()
        if not r:
            conn.close()
            return 0
        today = datetime.now().date()
        last = r['last_study_date']
        streak = r['current_streak']
        study_days = r['total_study_days']
        if last:
            last_date = date.fromisoformat(str(last))
            diff = (today - last_date).days
            if diff == 0:
                conn.close()
                return streak
            elif diff == 1:
                streak += 1
                study_days += 1
            else:
                streak = 1
                study_days += 1
        else:
            streak = 1
            study_days = 1
        max_s = max(r['max_streak'], streak)
        c.execute('''
            UPDATE user_gamification
            SET current_streak=?, max_streak=?, last_study_date=?, total_study_days=?
            WHERE user_id=?
        ''', (streak, max_s, str(today), study_days, user_id))
        conn.commit()
        conn.close()
        return streak

    def unlock_achievement(self, user_id: int, ach: str) -> bool:
        g = self.get_gamification(user_id)
        achieved = json.loads(g.get('achievements', '[]'))
        if ach in achieved:
            return False
        achieved.append(ach)
        conn = self.get_connection()
        conn.execute('UPDATE user_gamification SET achievements=? WHERE user_id=?',
                     (json.dumps(achieved), user_id))
        conn.commit()
        conn.close()
        return True

    def calc_level(self, user_id: int) -> int:
        g = self.get_gamification(user_id)
        pts = g.get('total_points', 0)
        thresholds = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000]
        level = 1
        for i, t in enumerate(thresholds):
            if pts >= t:
                level = i + 1
        conn = self.get_connection()
        conn.execute('UPDATE user_gamification SET level=? WHERE user_id=?', (level, user_id))
        conn.commit()
        conn.close()
        return level

    # ── SETTINGS ───────────────────────────────────────────────────────────
    def get_settings(self, user_id: int) -> Dict:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM user_settings WHERE user_id=?', (user_id,))
        r = c.fetchone()
        conn.close()
        if not r:
            self.init_gamification(user_id)
            return {'notifications': 1, 'difficulty': 'medium', 'cards_per_session': 20,
                    'reminder_time': '20:00', 'show_hints': 1, 'reverse_mode': 0}
        return dict(r)

    def update_setting(self, user_id: int, key: str, value):
        allowed = {'notifications', 'difficulty', 'cards_per_session',
                   'reminder_time', 'show_hints', 'reverse_mode'}
        if key not in allowed:
            return
        self.init_gamification(user_id)
        conn = self.get_connection()
        conn.execute(f'UPDATE user_settings SET {key}=? WHERE user_id=?', (value, user_id))
        conn.commit()
        conn.close()

    # aliases for backward compat
    def get_user_settings(self, u): return self.get_settings(u)
    def update_user_setting(self, u, k, v): self.update_setting(u, k, v)

    # ── DAILY TASKS ────────────────────────────────────────────────────────
    def get_or_create_daily_tasks(self, user_id: int) -> List[Dict]:
        import random
        today = str(datetime.now().date())
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM daily_tasks WHERE user_id=? AND date=?', (user_id, today))
        rows = [dict(r) for r in c.fetchall()]
        if not rows:
            tasks = [
                ('study_cards', random.choice([10, 15, 20])),
                ('correct_streak', random.choice([3, 5, 7])),
                ('use_mode', 1),
            ]
            for tt, tgt in tasks:
                c.execute('INSERT OR IGNORE INTO daily_tasks (user_id,date,task_type,target) VALUES (?,?,?,?)',
                          (user_id, today, tt, tgt))
            conn.commit()
            c.execute('SELECT * FROM daily_tasks WHERE user_id=? AND date=?', (user_id, today))
            rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def update_daily_task(self, user_id: int, task_type: str, increment: int = 1):
        today = str(datetime.now().date())
        conn = self.get_connection()
        conn.execute('''
            UPDATE daily_tasks
            SET current=MIN(current+?,target),
                completed=CASE WHEN current+?>=target THEN 1 ELSE completed END
            WHERE user_id=? AND date=? AND task_type=? AND completed=0
        ''', (increment, increment, user_id, today, task_type))
        conn.commit()
        conn.close()

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT u.username, u.first_name, g.total_points, g.current_streak, g.level
            FROM user_gamification g JOIN users u ON g.user_id=u.user_id
            ORDER BY g.total_points DESC LIMIT ?
        ''', (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
