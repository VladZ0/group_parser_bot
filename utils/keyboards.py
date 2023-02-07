from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

PARSE_СOMMAND = "Парсити"
CHANGE_KEYWORDS = "Змінити ключові слова"
CHECK_URLS = "Перевірити адреси"
CHECK_KEYWORDS = "Перевірити ключові слова"

# Main keyboard markup

__main_kb_button1 = KeyboardButton(CHECK_KEYWORDS)
__main_kb_button2 = KeyboardButton(CHANGE_KEYWORDS)
__main_kb_button3 = KeyboardButton(CHECK_URLS)
__main_kb_button4 = KeyboardButton(PARSE_СOMMAND)

main_kb_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(__main_kb_button1, __main_kb_button2, \
                                                __main_kb_button3, __main_kb_button4)