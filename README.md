# snackie_subs_bot
Subscribe bot

op.bulk_insert(
        subs_table,
        [
            {
                'id': 1,
                'humanize_name': 'Только потрогать',
                'payment_name': '1 месяц',
                'payment_amount': 990,
                'payment_currency': 'RUB',
                'sub_period': 1
            },
            {
                'id': 2,
                'humanize_name': 'Уверенный',
                'payment_name': '3 месяца',
                'payment_amount': 2500,
                'payment_currency': 'RUB',
                'sub_period': 3
            },
            {
                'id': 3,
                'humanize_name': 'Машина фитнеса',
                'payment_name': '1 год',
                'payment_amount': 9990,
                'payment_currency': 'RUB',
                'sub_period': 12
            },
        ]
    )

