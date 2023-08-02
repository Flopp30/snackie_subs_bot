import csv
import datetime
import logging
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud import user_crud, payment_crud


async def get_user_stat(session: AsyncSession) -> (str, bytes):
    """
    Gather stat by users
    """
    users = await user_crud.get_multi(session)
    user_report_message = ("Всего пользователей: {len_user}\n"
                           "Подписанных пользователей: {len_active_user}\n"
                           "Недельки: {sub_week_count}\n"
                           "Месяц: {sub_month_count}\n"
                           "3 месяца: {sub_three_month_count}\n"
                           "Год (вряд ли, конечно, но чисто по фану): {sub_year_count}\n"
                           "Недельки, которые продлили: {week_sub_renewal_count}")
    len_active_user = 0
    sub_week_count = 0
    sub_month_count = 0
    sub_three_month_count = 0
    sub_year_count = 0
    week_sub_renewal_count = 0

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as csvfile:
        csv_filename = csvfile.name

        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "#",
                "TG_ID",
                'Username',
                'Is Active',
                'First Subscription Date',
                'Unsub date',
                'Sub type',
                'Number of payments',
                'Total income'
            ])

        for idx, user in enumerate(users):
            len_active_user += 1 if user.is_active else 0
            if user.subscription:
                sub_week_count += 1 if user.subscription.payment_name == "7 дней" else 0
                sub_month_count += 1 if user.subscription.payment_name == "1 месяц" else 0
                sub_three_month_count += 1 if user.subscription.payment_name == "3 месяца" else 0
                sub_year_count += 1 if user.subscription.payment_name == "1 год" else 0
                if len(user.payments) > 1:
                    week_sub_renewal_count = sum(
                        1 for payment in user.payments if payment.payment_amount == 490)
            writer.writerow(
                [
                    idx + 1,
                    user.id,
                    user.username,
                    user.is_active,
                    user.first_sub_date.strftime('%d.%m.%Y') if user.first_sub_date else '',
                    user.unsubscribe_date.strftime('%d.%m.%Y') if user.first_sub_date else '',
                    user.subscription.payment_name if user.subscription else "Non sub",
                    len(user.payments),
                    sum(payment.payment_amount for payment in user.payments) if user.payments else 0,
                ])

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()
    user_report_message = user_report_message.format(
        len_user=len(users),
        len_active_user=len_active_user,
        sub_week_count=sub_week_count,
        sub_month_count=sub_month_count,
        sub_three_month_count=sub_three_month_count,
        sub_year_count=sub_year_count,
        week_sub_renewal_count=week_sub_renewal_count,
    )
    return user_report_message, file_content


async def get_payment_stat(session: AsyncSession) -> (str, bytes):
    """
    Gather stat by payments
    :param session:
    :return:
    """
    date_now = datetime.datetime.now()
    will_be_paid = 0

    users = await user_crud.get_expired_sub_this_month_users(session)
    this_month_payments = await payment_crud.get_this_month_multi(session=session)
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as csvfile:
        csv_filename = csvfile.name

        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "#",
                "Payment date",
                'Sum',
            ])
        for idx, user in enumerate(users):
            if user.unsubscribe_date >= date_now and user.subscription and not user.subscription.is_trial:
                will_be_paid += user.subscription.payment_amount
                writer.writerow(
                    [
                        idx + 1,
                        user.unsubscribe_date.strftime('%d.%m.%Y'),
                        f"{user.subscription.payment_amount} rub",
                    ])

        already_paid = sum(payment.payment_amount for payment in this_month_payments)
        report_message = ("В этом месяцев суммарно (без учета новых подписок) "
                          f"должно получиться: {already_paid + will_be_paid} rub.\n"
                          f"Уже выплачено: {already_paid} rub.\n"
                          f"Будет позже: {will_be_paid} rub")

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()

    return report_message, file_content
