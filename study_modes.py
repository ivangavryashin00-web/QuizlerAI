"""
study_modes.py — логика всех режимов обучения
"""
import random
import re
from difflib import SequenceMatcher
from database import Database

db = Database()


class StudyModes:

    # ── Подготовка карточек ────────────────────────────────────────────────

    @staticmethod
    def prepare_cards(user_id: int, deck_id: int, mode: str = 'flashcard',
                      limit: int = 20, settings: dict = None) -> list:
        cards = db.get_deck_cards(deck_id)
        if not cards:
            return []
        if settings:
            limit = settings.get('cards_per_session', limit)
            if settings.get('reverse_mode'):
                for c in cards:
                    c['question'], c['answer'] = c['answer'], c['question']
        random.shuffle(cards)
        return cards[:limit]

    @staticmethod
    def prepare_srs_cards(user_id: int, deck_id: int, limit: int = 50) -> list:
        return db.get_due_cards(user_id, deck_id)[:limit]

    @staticmethod
    def prepare_weak_cards(user_id: int, deck_id: int, limit: int = 20) -> list:
        weak = db.get_weak_cards(user_id, deck_id, limit)
        if len(weak) < 4:
            all_cards = db.get_deck_cards(deck_id)
            weak_ids = {c['card_id'] for c in weak}
            others = [c for c in all_cards if c['card_id'] not in weak_ids]
            random.shuffle(others)
            weak.extend(others[:limit - len(weak)])
        return weak

    # ── Проверка ответа ────────────────────────────────────────────────────

    @staticmethod
    def calculate_similarity(a: str, b: str) -> float:
        a = a.strip().lower()
        b = b.strip().lower()
        if a == b:
            return 1.0
        a_c = re.sub(r'[^\w\s]', '', a)
        b_c = re.sub(r'[^\w\s]', '', b)
        if a_c == b_c:
            return 1.0
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def check_answer(user_answer: str, correct_answer: str) -> tuple:
        sim = StudyModes.calculate_similarity(user_answer, correct_answer)
        if sim >= 0.90:
            return 'correct', sim
        elif sim >= 0.60:
            return 'close', sim
        return 'wrong', sim

    # ── Подсказки ──────────────────────────────────────────────────────────

    @staticmethod
    def get_hint(answer: str, level: int = 1) -> str:
        if not answer:
            return '?'
        n = len(answer)
        if level == 1:
            return answer[0] + '＿' * (n - 1) + f'  ({n} букв)'
        elif level == 2:
            show = max(1, n // 3)
            return answer[:show] + '·' * (n - show)
        else:
            show = max(1, n // 2)
            return answer[:show] + '·' * (n - show)

    # ── Quiz ───────────────────────────────────────────────────────────────

    @staticmethod
    def generate_quiz_options(correct_card: dict, all_cards: list,
                               num_options: int = 4) -> list:
        correct = correct_card['answer']
        options = [correct]
        others = [c['answer'] for c in all_cards
                  if c['card_id'] != correct_card['card_id']]
        random.shuffle(others)
        for o in others:
            if o not in options:
                options.append(o)
            if len(options) >= num_options:
                break
        random.shuffle(options)
        return options

    # ── Match (найди пару) ─────────────────────────────────────────────────

    @staticmethod
    def prepare_match_round(cards: list, pair_count: int = 5) -> dict:
        """
        Возвращает dict для одного раунда Match.
        items — перемешанный список {'id', 'text', 'type': 'q'|'a', 'card_id'}
        """
        selected = random.sample(cards, min(pair_count, len(cards)))
        items = []
        for c in selected:
            items.append({'id': f"q_{c['card_id']}", 'text': c['question'],
                          'type': 'q', 'card_id': c['card_id']})
            items.append({'id': f"a_{c['card_id']}", 'text': c['answer'],
                          'type': 'a', 'card_id': c['card_id']})
        random.shuffle(items)
        return {
            'items': items,
            'pairs': {c['card_id']: False for c in selected},
            'selected': None,   # id первого нажатого
            'mistakes': 0,
            'matched': 0,
            'total': len(selected),
        }

    # ── Анаграмма ──────────────────────────────────────────────────────────

    @staticmethod
    def make_anagram(word: str) -> str:
        """Перемешать буквы слова (не совпадает с оригиналом если возможно)"""
        chars = list(word)
        for _ in range(20):
            random.shuffle(chars)
            shuffled = ''.join(chars)
            if shuffled != word:
                return shuffled
        return ''.join(chars)

    # ── Первая буква ───────────────────────────────────────────────────────

    @staticmethod
    def first_letter_hint(answer: str) -> str:
        if not answer:
            return '?'
        words = answer.split()
        return ' '.join(w[0] + '_' * (len(w) - 1) for w in words)

    # ── Пересказ (ключевые слова) ──────────────────────────────────────────

    @staticmethod
    def check_retelling(user_text: str, answer: str, min_coverage: float = 0.5) -> tuple:
        """
        Проверяет пересказ по ключевым словам.
        Возвращает (ok: bool, found: list, missing: list)
        """
        keywords = [w.lower().strip('.,!?;:')
                    for w in answer.split() if len(w) > 3]
        if not keywords:
            keywords = answer.lower().split()

        user_lower = user_text.lower()
        found = []
        missing = []
        for kw in keywords:
            if kw in user_lower or SequenceMatcher(None, kw, user_lower).ratio() > 0.7:
                found.append(kw)
            else:
                missing.append(kw)

        coverage = len(found) / len(keywords) if keywords else 1.0
        return coverage >= min_coverage, found, missing
