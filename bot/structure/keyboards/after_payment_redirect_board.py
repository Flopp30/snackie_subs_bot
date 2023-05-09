from aiogram.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()
builder.button(
    text="Программа с гантелями", url="https://t.me/Roooookie_bot"
)
builder.button(
    text="Чат гантелисток", url="https://t.me/+WMF9d0eP4hhjMWMy"
)
builder.button(
    text="Программа для зала", url="https://t.me/snackiebird_bot"
)
builder.button(
    text="Чат зальных девчат", url="https://t.me/+968F6Eap5_AxNThi"
)
builder.button(
    text="Памятка атлетки", url="https://clck.ru/32LfWK "
)
builder.adjust(1)

AFTER_PAYMENT_REDIRECT_BOARD = builder.as_markup()
