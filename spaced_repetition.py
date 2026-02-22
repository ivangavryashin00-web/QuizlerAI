from datetime import datetime, timedelta
from database import Database

db = Database()

# Quality ratings
AGAIN = 0   # complete blackout
HARD  = 1   # incorrect but correct on recall
GOOD  = 2   # correct with significant difficulty
EASY  = 3   # correct with perfect recall

QUALITY_LABELS = {
    AGAIN: ('😰 Забыл', 'rate_0'),
    HARD:  ('😓 Трудно', 'rate_1'),
    GOOD:  ('🙂 Знаю',  'rate_2'),
    EASY:  ('😄 Легко', 'rate_3'),
}


class SM2:
    """
    SuperMemo 2 algorithm implementation.
    Intervals: 1 → 6 → EF*prev ...
    Ease factor adjusts based on quality.
    """

    @staticmethod
    def calculate(quality: int, ease_factor: float, interval: int, level: int):
        """
        Returns (new_level, new_ease_factor, new_interval_days, next_review_dt)
        quality: 0=again, 1=hard, 2=good, 3=easy
        """
        if quality == AGAIN:
            new_level = 0
            new_interval = 1
            new_ef = max(1.3, ease_factor - 0.2)
        elif quality == HARD:
            new_level = max(0, level - 1)
            new_interval = max(1, round(interval * 1.2))
            new_ef = max(1.3, ease_factor - 0.15)
        elif quality == GOOD:
            new_level = level + 1
            if level == 0:
                new_interval = 1
            elif level == 1:
                new_interval = 6
            else:
                new_interval = round(interval * ease_factor)
            new_ef = ease_factor + 0.1
        else:  # EASY
            new_level = level + 2
            if level == 0:
                new_interval = 4
            elif level == 1:
                new_interval = 10
            else:
                new_interval = round(interval * ease_factor * 1.3)
            new_ef = ease_factor + 0.15

        new_ef = round(min(4.0, max(1.3, new_ef)), 2)
        new_interval = min(new_interval, 365)
        next_review = datetime.now() + timedelta(days=new_interval)
        return new_level, new_ef, new_interval, next_review

    @staticmethod
    def process_answer(user_id: int, card_id: int, quality: int):
        """Apply SM-2 and persist progress"""
        prog = db.get_card_progress(user_id, card_id)
        if not prog:
            db.init_card_progress(user_id, card_id)
            prog = {'level': 0, 'ease_factor': 2.5, 'interval_days': 1}

        new_level, new_ef, new_interval, next_review = SM2.calculate(
            quality,
            prog.get('ease_factor', 2.5),
            prog.get('interval_days', 1),
            prog.get('level', 0)
        )

        correct = quality >= GOOD
        db.update_card_progress(user_id, card_id, new_level, new_ef, new_interval, next_review, correct)
        return new_level, new_interval, next_review

    @staticmethod
    def get_due_count(user_id: int, deck_id: int) -> int:
        due = db.get_due_cards(user_id, deck_id)
        return len(due)

    @staticmethod
    def get_deck_stats(user_id: int, deck_id: int) -> dict:
        return db.get_deck_srs_stats(user_id, deck_id)
