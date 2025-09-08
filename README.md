# Valera Bot

Valera Bot is a lightweight Telegram assistant built with [aiogram](https://docs.aiogram.dev) and the [OpenAI API](https://platform.openai.com/docs/api-reference).  
It supports text and image generation, token balance tracking, a simple referral system, and a friendly menu to guide users.

## Features

- **Start bonus:** New users receive a configurable number of free tokens when they register.
- **Referral rewards:** Share your personal referral link; when a friend generates their first response, both of you earn bonus tokens.
- **Token accounting:** Each generation request deducts a configurable number of tokens from the user's balance.
- **Cooldown:** Prevent spam by enforcing a short delay between generation requests.
- **Image support:** Users can send photos or links to images; the bot will forward them to the OpenAI API in addition to text prompts.
- **Persistent storage:** User balances and referral relationships are stored in a database (SQLite by default, Postgres supported via `DATABASE_URL`).

## Running locally

1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in `TELEGRAM_BOT_TOKEN` and `OPENAI_API_KEY`.  
   Optionally set `DATABASE_URL` to connect to Postgres instead of the default SQLite database.
3. Start the bot:
   ```bash
   python -m app.main
   ```
4. Interact with the bot on Telegram and enjoy!

## Deployment on Heroku

The project includes a `Procfile` and `runtime.txt` for easy deployment on Heroku.  
Set the following config vars in the Heroku dashboard or via the CLI:

- `TELEGRAM_BOT_TOKEN` – your bot's token
- `OPENAI_API_KEY` – your OpenAI API key
- `DATABASE_URL` – Postgres connection string (automatically set when using the Heroku Postgres addon)
- `START_BONUS`, `REF_BONUS`, `GENERATE_COST`, `COOLDOWN_SECONDS`, `ALLOWED_USER_IDS` – optional overrides for default settings

Then push the repository to Heroku and scale a worker dyno:

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:mini
git push heroku main
heroku ps:scale worker=1
```

## Environment variables

The bot reads its configuration from environment variables.  See `.env.example` for a full list and descriptions of each variable.

## Code structure

```
valera_bot_clean/
├── app/
│   ├── __init__.py      # marks the folder as a package
│   ├── config.py        # configuration using env vars
│   ├── db.py            # database logic (SQLite/Postgres)
│   ├── logic.py         # prompt definitions and helper functions
│   ├── handlers.py      # bot handlers and business logic
│   └── main.py          # entry point: sets up and runs the bot
├── requirements.txt     # Python dependencies
├── Procfile             # Heroku process declaration
├── runtime.txt          # specifies Python version for Heroku
├── .env.example         # environment variable template
└── README.md            # this file
```

## License

This project is provided without a specific license. Feel free to use, modify and distribute it at your own risk.
