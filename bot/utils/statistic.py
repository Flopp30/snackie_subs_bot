import csv
import datetime
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud import user_crud, payment_crud


async def get_user_stat(session: AsyncSession) -> bytes:
    """
    Gather stat by users
    :param session:
    :return:
    """
    users = await user_crud.get_multi(session)
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
            writer.writerow(
                [
                    idx + 1,
                    user.id,
                    user.username,
                    user.is_active,
                    user.first_sub_date.strftime('%d.%m.%Y'),
                    user.unsubscribe_date.strftime('%d.%m.%Y'),
                    user.subscription.payment_name if user.subscription else "Non sub",
                    len(user.payments),
                    sum(payment.payment_amount for payment in user.payments) if user.payments else 0,
                ])

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()

    return file_content


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
            if user.unsubscribe_date >= date_now and user.subscription:
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

