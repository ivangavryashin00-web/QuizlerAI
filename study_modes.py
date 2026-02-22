import random
from difflib import SequenceMatcher
from database import Database

db = Database()


class StudyModes:

    @staticmethod
    def prepare_cards(user_id: int, deck_id: int, mode: str = 'flashcard',
                      limit: int = 20, settings: dict = None) -> list:
        """Get cards for a study session, sorted by priority"""
        cards = db.get_deck_cards(deck_id)
        if not cards:
            return []

        # Optionally reverse (answer -> question)
        if settings and settings.get('reverse_mode'):
            for c in cards:
                c['question'], c['answer'] = c['answer'], c['question']

        # Apply difficulty filter from settings
        if settings:
            diff = settings.get('difficulty', 'medium')
            limit = settings.get('cards_per_session', limit)

        random.shuffle(cards)
        return cards[:limit]

    @staticmethod
    def prepare_srs_cards(user_id: int, deck_id: int, limit: int = 50) -> list:
        """Get cards due for SRS review"""
        due = db.get_due_cards(user_id, deck_id)
        return due[:limit]

    @staticmethod
    def prepare_weak_cards(user_id: int, deck_id: int, limit: int = 20) -> list:
        """Get hardest cards (lowest accuracy)"""
        weak = db.get_weak_cards(user_id, deck_id, limit)
        # Fill with random cards if not enough weak ones
        if len(weak) < limit:
            all_cards = db.get_deck_cards(deck_id)
            weak_ids = {c['card_id'] for c in weak}
            others = [c for c in all_cards if c['card_id'] not in weak_ids]
            random.shuffle(others)
            weak.extend(others[:limit - len(weak)])
        return weak

    @staticmethod
    def calculate_similarity(a: str, b: str) -> float:
        a = a.strip().lower()
        b = b.strip().lower()
        # Exact match
        if a == b:
            return 1.0
        # Remove common punctuation
        import re
        a_clean = re.sub(r'[^\w\s]', '', a)
        b_clean = re.sub(r'[^\w\s]', '', b)
        if a_clean == b_clean:
            return 1.0
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def generate_quiz_options(correct_card: dict, all_cards: list, num_options: int = 4) -> list:
        correct = correct_card['answer']
        options = [correct]
        others = [c['answer'] for c in all_cards if c['card_id'] != correct_card['card_id']]
        random.shuffle(others)
        for o in others:
            if o not in options:
                options.append(o)
            if len(options) >= num_options:
                break
        random.shuffle(options)
        return options

    @staticmethod
    def get_hint(answer: str, level: int = 1) -> str:
        """
        level 1: show first letter + length
        level 2: show first 30%
        level 3: show first 50%
        """
        if not answer:
            return '?'
        n = len(answer)
        if level == 1:
            return answer[0] + '_' * (n - 1) + f' ({n} букв)'
        elif level == 2:
            show = max(1, n // 3)
            return answer[:show] + '·' * (n - show)
        else:
            show = max(1, n // 2)
            return answer[:show] + '·' * (n - show)

    @staticmethod
    def check_answer(user_answer: str, correct_answer: str) -> tuple:
        """Returns (verdict, similarity) verdict: 'correct'|'close'|'wrong'"""
        sim = StudyModes.calculate_similarity(user_answer, correct_answer)
        if sim >= 0.90:
            return 'correct', sim
        elif sim >= 0.60:
            return 'close', sim
        else:
            return 'wrong', sim
