# Shana-Kay Gardener - Ken Ganley CDJR Bedford Lead System

Sales agent details are already built in:

- Name: Shana-Kay Gardener
- Business phone: +1 (848) 298-9384
- Dealership email: Sgardener@ganleyauto.com
- Dealership website: https://www.kenganleycdjrbedford.com/

## Telegram connection

1. In Telegram, open `@BotFather`.
2. Send `/newbot`.
3. Create your bot and copy the token.
4. Create a private Telegram group for the leads if desired.
5. Add your new bot to that group.
6. Send at least one message in the group.
7. Get the group's numeric Chat ID using Telegram Bot API `getUpdates`.
8. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as private environment variables on your hosting service.

Do not put the Telegram bot token inside public HTML or post it publicly.

## Referral tracking

Use a different `source` in each shared link:

`https://YOUR-LINK.com/?source=Facebook`
`https://YOUR-LINK.com/?source=Instagram`
`https://YOUR-LINK.com/?source=WhatsApp`
`https://YOUR-LINK.com/?source=TikTok`

Every submitted lead gets a unique ID and is stored in `leads.csv` as well as sent to Telegram.

## Run

`pip install -r requirements.txt`

Then:

`python app.py`

For a production host, start with:

`gunicorn app:app`
