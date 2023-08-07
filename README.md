# Subscribe bot

### Tools

1) <a href="https://yookassa.ru/developers/payment-acceptance/scenario-extensions/recurring-payments">Yookassa api</a>
2) <a href="https://docs.aiogram.dev/en/dev-3.x/">Aiogram 3.x </a>
3) <a href="https://apscheduler.readthedocs.io/en/3.x/">Apscheduler (AsyncIOScheduler)</a>
4) Postgresql (async)
5) SqlAlchemy (async)
6) Aiohttp (async)
7) Redis (aioredis)

### Modules

1) DB
    - CRUD - crud for models
    - migration - migrations
    - base
    - engine
    - models
2) Handlers
    - __init__ - init all handlers
    - administration - admin's handlers
    - help
    - start
    - subscription - subscription's with sub logic
    - unsubscription
3) Middleware
    - apscheduler - added scheduler to bot's handlers
    - register check - init new users in db
    - throttling = antispam
4) Structure
    - keyboards
        - admin_board
        - after_payment_redirect_board
        - get_payment_board
        - payment_type_board
        - send_message_accept_board
        - start_board
        - unsub_board
        - user's_groups_board
    - callback_data_states - using for accept callback by inline keyboard's
      buttons <a href="https://docs.aiogram.dev/en/dev-3.x/dispatcher/filters/callback_data.html">read here</a>
    - fsm_groups (Finite State Machine groups) - using for set state into context for handler's
      groups <a href="https://docs.aiogram.dev/en/dev-3.x/dispatcher/finite_state_machine/index.html">read here</a>
5) Utils
    - apsched - apscheduler's tasks
    - apsched_utils - utils for apscheduler's tasks
    - statistic - admin's statistic
    - utils - other utils
6) settings.py
7) __main__.py
8) text_for_messages.py

### Installation
1) Create ```.env``` file in root folder
2) ```docker-compose up -f docker-compose-exclude-bot.yaml ``` (u can change postgres_db port if u need)
3) Create ```alembic.ini``` file in root folder
4) ```pip install --upgrade pip && pip install -r requirements.txt```
5) Paste this in ```alembic.ini``` (if u changed port in docker-compose-file - change port and here)
    ```
   [alembic]
   
   script_location = bot/db/migration
   
   prepend_sys_path = .
   
   version_path_separator = os # Use os.pathsep. Default configuration used for new projects.
   
   sqlalchemy.url = postgresql+asyncpg://admin:password@localhost:5433/subs_bot
   
   [post_write_hooks]
   
   [loggers]
   keys = root,sqlalchemy,alembic
   
   [handlers]
   keys = console
   
   [formatters]
   keys = generic
   
   [logger_root]
   level = WARN
   handlers = console
   qualname =
   
   [logger_sqlalchemy]
   level = WARN
   handlers =
   qualname = sqlalchemy.engine
   
   [logger_alembic]
   level = INFO
   handlers =
   qualname = alembic
   
   [handler_console]
   class = StreamHandler
   args = (sys.stderr,)
   level = NOTSET
   formatter = generic
   
   [formatter_generic]
   format = %(levelname)-5.5s [%(name)s] %(message)s
   datefmt = %H:%M:%S

   ```
6) ```alembic upgrade head```
7) ```python -m bot```