# stonk-bot

Bot to fetch stock price and give an overview of stock prices for the day.
Inspired by this bot: https://github.com/seanluong/stonk-bot
Based on this guide: https://medium.com/sltc-sean-learns-to-code/hosting-a-discord-bot-on-google-cloud-ca0dea5df988

## Installation guide

First, clone the code in this repo to your local machine and install all the needed requirements.

```
> pip3 install -r requirements.txt
```

Then, do the following:

- Create your bot in Discord
- Add it to your Discord server
- Check out this repo
- replace the token in `token.env` file with your secret discord token

```
STONK_BOT_TOKEN=<put your token here>
```

Now you can run the bot using the following command

```
> python3 discord_bot.py
```

## useful commands for hosting within a linux box:

tmux (headless client hosting)
tmux new -s bot - new bot
python3 main.py - run proj
Ctrl + B, then D - detach from session
tmux attach -t bot - reattach to session
tmux ls - list all sessions
tmux kill-session -t bot - kill session called bot

venv (virtual env)
python3 -m venv venv - establishes/installs venv
source venv/bin/activate - active venv
pip install -r requirements.txt - uses req.txt to install dependancies
which python - will show which py version is running, expected value within venv is something like /home/usr/mypy/venv/bin/py
exit - leaves venv

## the discord commands:

Example Commands:

- /help: show help message
- /stonk AAPL: show the latest stock price of AAPL
- /stonk bhp.ax: show latest stock price of bhp from the ASX
  Indicators/metrics (using Max's Curated list):
- /today: show summary of top 10 best and worst performing stocks today
