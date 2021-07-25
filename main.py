from telegram.ext import (
    Updater,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
)
import constants
import handlers


def main() -> None:
    updater = Updater(constants.API_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", handlers.start_handler))
    dispatcher.add_handler(MessageHandler(Filters.text, handlers.text_handler))
    dispatcher.add_handler(MessageHandler(Filters.document, handlers.file_handler))
    dispatcher.add_handler((CallbackQueryHandler(callback=handlers.vacancy_handler, pattern='vacancy_id_*')))
    dispatcher.add_handler((CallbackQueryHandler(callback=handlers.respond_callback_handler, pattern='respond_*')))
    dispatcher.add_handler((CallbackQueryHandler(callback=handlers.answer_callback_handler, pattern='answer_*')))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
