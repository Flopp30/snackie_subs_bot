import json
import uuid
from datetime import datetime

from aiogram.fsm.context import FSMContext
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Payment as Yoo_Payment

from bot.db.crud import sub_crud, user_crud
from bot.db.models import Subscription, User
from bot.settings import TG_BOT_URL
from bot.text_for_messages import TEXT_TARIFFS, TEXT_TARIFFS_DETAIL


async def get_tariffs_text(session: AsyncSession, state: FSMContext, with_trials: bool = True) -> str:
    subscriptions = await sub_crud.get_multi(session, with_trials=with_trials)
    text = TEXT_TARIFFS
    subscriptions_for_state = []
    crossed_amount = ""
    for sub in subscriptions:
        current_crossed_amount = crossed_amount * int(sub.sub_period)

        text += TEXT_TARIFFS_DETAIL.format(
            humanize_name=sub.humanize_name,
            payment_period_name=sub.payment_name,
            crossed_out_price=current_crossed_amount,
            payment_amount=sub.payment_amount,
            payment_currency=sub.payment_currency)

        if crossed_amount == "" and not sub.is_trial:
            crossed_amount = sub.payment_amount

        subscriptions_for_state.append(sub.to_dict())
    await state.update_data(subscriptions=subscriptions_for_state)
    return text


async def get_beautiful_sub_date(first_sub_date: datetime) -> str | None:
    current_date = datetime.now()
    date_diff = relativedelta(current_date, first_sub_date)
    time_units = {
        "years": ("год", "года", "лет"),
        "months": ("месяц", "месяца", "месяцев"),
        "days": ("день", "дня", "дней"),
        "hours": ("час", "часа", "часов"),
        "minutes": ("минуту", "минуты", "минут"),
    }

    res = ""
    for unit, (unit_singular, unit_plural_2_4, unit_plural_5plus) in time_units.items():
        value = getattr(date_diff, unit)
        if value:
            res += f"{value} "
            if value % 10 == 1 and value % 100 != 11:
                res += unit_singular
            elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
                res += unit_plural_2_4
            else:
                res += unit_plural_5plus
            res += ", "

    res = res.rstrip(", ")
    if not res:
        return res
    res = "Ты с нами уже: " + res + " 🏆"
    return res


async def get_yoo_payment(sub: dict):
    idempotence_key = str(uuid.uuid4())
    payment = Yoo_Payment.create({
        "save_payment_method": True,
        "amount": {
            "value": sub.get("payment_amount"),
            "currency": sub.get("payment_currency"),
        },
        "metadata": {
            "sub_id": sub.get("id"),
            "sub_period": sub.get("sub_period"),
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": TG_BOT_URL,
        },
        "capture": True,
        "description": f"Оформление подписки по тарифу '{sub.get('humanize_name')}' на срок {sub.get('payment_name')}",
    }, idempotence_key)

    return json.loads(payment.json())


def get_auto_payment(sub: Subscription, user: User):
    idempotence_key = str(uuid.uuid4())
    payment = Yoo_Payment.create(
        {
            "amount": {
                "value": sub.payment_amount,
                "currency": sub.payment_currency,
            },
            "capture": True,
            "payment_method_id": user.verified_payment_id,
            "description": f"Продление подписки по тарифу '{sub.humanize_name}' на срок {sub.payment_name}",
        }, idempotence_key
    )
    return json.loads(payment.json())


async def get_users_by_group(group: int, session: AsyncSession):
    users = None
    match group:
        case 0:
            users = await user_crud.get_multi(session)
        case 1:
            users = await user_crud.get_multi_by_attribute(session=session, attr_name='is_active', attr_value=False)
        case 2:
            users = await user_crud.get_multi_by_attribute(session=session, attr_name='is_active', attr_value=True)
        case 3:
            all_active_users = await user_crud.get_multi_by_attribute(
                session=session,
                attr_name='is_active',
                attr_value=True)
            users = [user for user in all_active_users if user.subscription.payment_name == "7 дней"]
        case 4:
            all_active_users = await user_crud.get_multi_by_attribute(
                session=session,
                attr_name='is_active',
                attr_value=True
            )
            users = [user for user in all_active_users if user.subscription.payment_name == "1 месяц"]
        case 5:
            all_active_users = await user_crud.get_multi_by_attribute(
                session=session,
                attr_name='is_active',
                attr_value=True
            )
            users = [user for user in all_active_users if user.subscription.payment_name == "3 месяца"]
        case 3:
            all_active_users = await user_crud.get_by_attribute(
                session=session,
                attr_name='is_active',
                attr_value=True
            )
            users = [user for user in all_active_users if user.subscription.payment_name == "1 год"]

    return users
