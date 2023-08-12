import csv
import datetime
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud import user_crud, payment_crud, sales_crud
from bot.utils import CustomCounter


async def get_user_stat(session: AsyncSession) -> (str, bytes):
    """
        Gather stat by users
    """
    users = await user_crud.get_multi(session=session)
    user_report_message = (
        "Всего пользователей: {len_users}\n"
        "Подписанных пользователей: {active_users}\n"
        "Недельки: {sub_week_count}\n"
        "Месяц: {sub_month_count}\n"
        "3 месяца: {sub_three_month_count}\n"
        "Год (вряд ли, конечно, но чисто по фану): {sub_year_count}\n"
        "Недельки, которые продлили: {week_sub_renewal_count}"
    )
    counters = {
        "len_users": len(users),
        "active_users": CustomCounter(),
        "sub_week_count": CustomCounter(),
        "sub_month_count": CustomCounter(),
        "sub_three_month_count": CustomCounter(),
        "sub_year_count": CustomCounter(),
        "week_sub_renewal_count": CustomCounter(),
    }

    subscription_counts = {
        "7 дней": "sub_week_count",
        "1 месяц": "sub_month_count",
        "3 месяца": "sub_three_month_count",
        "1 год": "sub_year_count",
    }

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
            if user.subscription:
                counters["active_users"].increment()

                if name_counters := subscription_counts.get(user.subscription.payment_name):
                    counters[name_counters].increment()

                if len(user.payments) > 1:
                    payments_statuses = [payment.status for payment in user.payments]
                    payments_amounts = [payment.payment_amount for payment in user.payments]

                    if payments_statuses.count("succeeded") > 1 and 490 in payments_amounts:
                        counters["week_sub_renewal_count"].increment()

            writer.writerow(
                [
                    idx + 1,
                    user.id,
                    user.username,
                    user.is_active,
                    user.first_sub_date.strftime('%d.%m.%Y') if user.first_sub_date else '',
                    user.unsubscribe_date.strftime('%d.%m.%Y') if user.unsubscribe_date else '',
                    user.subscription.payment_name if user.subscription else "Non sub",
                    len(user.payments),
                    sum(payment.payment_amount for payment in user.payments
                        if payment.status == 'succeeded') if user.payments else 0,
                ])

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()

    user_report_message = user_report_message.format(
        **counters
    )
    return user_report_message, file_content


async def get_payment_stat(session: AsyncSession) -> (str, bytes):
    """
        Gather stat by payments
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

        already_paid = sum(payment.payment_amount for payment in this_month_payments if payment.status == "succeeded")
        report_message = ("В этом месяцев суммарно (без учета новых подписок) "
                          f"должно получиться: {already_paid + will_be_paid} rub.\n"
                          f"Уже выплачено: {already_paid} rub.\n"
                          f"Будет позже: {will_be_paid} rub")

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()

    return report_message, file_content


async def get_sales_dates_info(session: AsyncSession) -> (str, bytes):
    """
        Prepair sales periods info
    """
    sales_dates = await sales_crud.get_multi(session=session)
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as csvfile:
        csv_filename = csvfile.name

        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "#",
                "Start date",
                "Finish date",
                'Status',
            ])
        for idx, sale in enumerate(sorted(sales_dates, key=lambda sale: sale.sales_start)):
            writer.writerow(
                [
                    idx + 1,
                    sale.sales_start.strftime('%d.%m.%Y'),
                    sale.sales_finish.strftime('%d.%m.%Y'),
                    ['not active', 'active'][sale.is_active],
                ])

    with open(csv_filename, 'rb') as csvfile:
        file_content = csvfile.read()

    return file_content
