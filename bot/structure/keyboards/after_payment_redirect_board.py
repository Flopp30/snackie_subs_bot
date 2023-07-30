from aiogram.utils.keyboard import InlineKeyboardBuilder

builder = InlineKeyboardBuilder()

builder.button(
    text="Программа “Зал для начинающих”", url="https://t.me/snackiebird_bot"
)
builder.button(
    text="Программа “Зал для уверенных” ", url="https://t.me/ProWorkoutSnackiebirdBot"
)
builder.button(
    text="Тренировки с гантелями дом/зал", url="https://t.me/Roooookie_bot"
)
builder.button(
    text="Тренировки с резинками", url="https://t.me/snackiebird_bandsBot"
)
builder.button(
    text="Записи зарядок - пятиминуток", url="https://t.me/+g8xFELc9K6RkYTEy"
)
builder.button(
    text="Чат клуба", url="https://t.me/+skGO0YDZYpVkMDli"
)
builder.adjust(1)

AFTER_PAYMENT_REDIRECT_BOARD = builder.as_markup()
