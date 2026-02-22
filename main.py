import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from database import Database
from handlers import (
    start, main_menu_callback, deck_menu_callback, message_handler,
    start_flashcard_mode, start_write_mode, start_quiz_mode,
    start_mixed_mode, start_srs_mode, start_weak_mode,
    select_study_mode, start_create_deck, create_deck_name,
    add_card_to_deck, finish_adding_cards,
    show_full_stats, browse_dictionary, show_settings,
    handle_settings_callback, show_help, cancel,
    show_daily_tasks, show_leaderboard, show_achievements,
    show_srs_all,
    MAIN_MENU, CREATE_DECK, ADD_CARD, STUDY_SELECT_MODE,
    STUDY_WRITE, STUDY_QUIZ, STUDY_FLASHCARD, DECK_MENU,
    SETTINGS, BROWSE_DICTIONARY, STUDY_SRS, STUDY_WEAK,
)


def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return

    db = Database()
    db.init_db()

    app = Application.builder().token(TOKEN).build()

    # All callback patterns that go to deck_menu_callback
    DECK_CB = "^(deck_menu_|study_flash_|study_write_|study_quiz_|study_mixed_|study_srs_|study_weak_|study_select_|add_cards_|list_cards_|deck_stats_|delete_deck_|confirm_delete_|flip_card|rate_|next_card|retry_card|hint_|stop_study|quiz_ans_)"

    # Settings patterns
    SETTINGS_CB = "^(toggle_notifications|toggle_hints|toggle_reverse|cycle_difficulty|cards_less|cards_more)$"

    # Main menu patterns
    MAIN_CB = "^(my_decks|create_deck|browse_dict|my_stats|settings|help|main_menu|daily_tasks|leaderboard|srs_all|achievements)$"

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(browse_dictionary, pattern="^import_collection_"),
            ],
            DECK_MENU: [
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_SELECT_MODE: [
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_FLASHCARD: [
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_SRS: [
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_WRITE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_QUIZ: [
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            STUDY_WEAK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
                CallbackQueryHandler(deck_menu_callback, pattern=DECK_CB),
                CallbackQueryHandler(main_menu_callback, pattern=MAIN_CB),
            ],
            CREATE_DECK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_deck_name),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
            ADD_CARD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_card_to_deck),
                CallbackQueryHandler(finish_adding_cards, pattern="^finish_adding$"),
                CallbackQueryHandler(deck_menu_callback, pattern="^(study_srs_|study_flash_|study_quiz_|my_decks)"),
            ],
            SETTINGS: [
                CallbackQueryHandler(handle_settings_callback, pattern=SETTINGS_CB),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
            BROWSE_DICTIONARY: [
                CallbackQueryHandler(browse_dictionary, pattern="^import_collection_"),
                CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help",  show_help))
    app.add_handler(CommandHandler("stats", show_full_stats))

    logger.info("🚀 QuizletBot запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
