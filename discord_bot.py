import os
import discord
import yfinance as yf
import traceback
import pandas as pd
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# some colours to depict up or down movement of a stock.
UP = "🟢 "
DOWN = "🔴 "

# List of different tickers (ASX ones will get '.AX' appended)
TICKERS = {
    "BA": "Boeing",
    "TSLA": "Tesla",
    "BP": "British Petroleum",
    "AMD": "AMD",
    "CBA.AX": "Commbank",
    "SHEL": "Shell",
    "GOOG": "Google",
    "BHP.AX": "BHP",
    "STO.AX": "Santos",
    "TLS.AX": "Telstra",
    "NVDA": "Nvidia",
    "COKE": "Coca Cola",
    "QAN.AX": "Qantas",
    "PFE": "Pfizer",
    "MCD": "McDonald's",
    "JNJ": "Johnson & Johnson",
    "MSFT": "Microsoft",
    "TTWO": "Take Two",
    "RTX": "Raytheon",
    "JPM": "JP Morgan",
    "LMT": "Lockheed Martin",
    "CSCO": "Cisco",
    "NOC": "Northrop Grumman",
    "MPL.AX": "Medibank",
    "CRWD": "Crowdstrike",
    "AAPL": "Apple",
    "MA": "Mastercard",
    "ANZ.AX": "ANZ Bank",
    "ORCL": "Oracle",
    "VGN.AX": "Virgin Australia",
    "WBC.AX": "Westpac Banking"
}

HELP_CONTENT = """
  Hi, this is Stonkbot. See below for guidelines on using the bot.

Features:
This bot features commands to let you lookup stock prices with a rough 15-minute delay from real-time... close enough, also give you a summary.
    
  Example Commands:
  - /help: show this help message
  - /stonk AAPL: show the latest stock price of AAPL
  - /stonk bhp.ax: show latest stock price of bhp from the ASX
  Indicators/metrics (using Max's Curated list):
  - /today: show summary of top 10 best and worst performing stocks today

"""

# load token from place ye ye
load_dotenv(dotenv_path="token.env")
stonk_bot_token = os.getenv('STONK_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="$", intents=intents)
tree = client.tree  # for slash commands

def format_price(price):
    return "${:,.5f}".format(price)

def format_growth_rate(growth):
    direction = UP if growth > 0 else DOWN
    growth_pc = growth * 100
    sign = "+" if growth_pc > 0 else ""
    return f" | {direction}{sign}{growth_pc:.2f}%"

# Using the yfinance library thingy
def use_yahoo(symbol):
    try:
        price, growth, name = fetch_stock_price_data(symbol)
    except Exception as error:
        print(f"Failed to fetch data from Yahoo! Finance: {error}")
        traceback.print_exc()
        return None, False
    return (price, growth, name), True

def get_daily_changes():
    changes = []

    for symbol, name in TICKERS.items():
        try:
            data = yf.download(symbol, period="2d", interval="1d", progress=False, auto_adjust=True)
            if data.empty or len(data) < 2:
                continue

            prev_close = data['Close'].iloc[-2]
            curr_close = data['Close'].iloc[-1]

            # ensure scalar values
            if isinstance(prev_close, pd.Series):
                prev_close = prev_close.item()
            if isinstance(curr_close, pd.Series):
                curr_close = curr_close.item()
            if prev_close == 0 or pd.isna(prev_close) or pd.isna(curr_close):
                continue

            pct_change = (curr_close - prev_close) / prev_close
            changes.append((symbol, name, pct_change))
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue

    sorted_changes = sorted(changes, key=lambda x: x[2], reverse=True)
    top_10 = sorted_changes[:10]
    bottom_10 = sorted(changes, key=lambda x: x[2])[:10]
    asx_changes = [c for c in changes if c[0].endswith(".AX")]
    sorted_asx = sorted(asx_changes, key=lambda x: x[2], reverse=True)

    return top_10, bottom_10, sorted_asx

def close_price(data):
    # Return the last closing price as a float
    return data['Close'].iloc[-1].item()

def growth_rate(data):
    if len(data) < 2:
        return None  # not enough data to calculate growth

    try:
        today = data['Close'].iloc[-1].item()
        yesterday = data['Close'].iloc[-2].item()
        if yesterday == 0 or pd.isna(today) or pd.isna(yesterday):
            return None
        return (today - yesterday) / yesterday
    except (IndexError, ValueError, TypeError):
        return None

def fetch_stock_price_data(symbol):
    symbol = symbol.upper()
    data = yf.download(symbol, period='5d', interval='1d')
    info = yf.Ticker(symbol).info

    if data.empty:
        raise Exception(f"No data found for symbol: {symbol}")

    price = close_price(data)       # float
    growth = growth_rate(data)      # float
    name = info.get("shortName", symbol)

    return price, growth, name

# setting up slash commands for discord to pick up.
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# /help command on discord
@tree.command(name="help", description="Show help for Max's StonkBot")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(HELP_CONTENT, ephemeral=True)

# /stonk command on discord
@tree.command(name="stonk", description="Get stock price for a ticker symbol")
@app_commands.describe(symbol="Ticker symbol like AAPL or BHP.AX")
async def stonk_command(interaction: discord.Interaction, symbol: str):
    await interaction.response.defer(thinking=True)

    try:
        results, success = use_yahoo(symbol)
        if success:
            price, growth, name = results
            msg = f"{symbol.upper()} ({name}): {format_price(price)} {format_growth_rate(growth)}"
        else:
            msg = (
                f"Cannot get data for `{symbol}`. Did you type it correctly? "
                "Try something like `bhp.ax` if it's an ASX stock."
            )

    except Exception as e:
        print(f"Error in /stonk command: {e}")
        msg = "Something went wrong while fetching data. Please try again later."
    await interaction.followup.send(msg, ephemeral=True)

# /today command on discord
@tree.command(name="today", description="Top 10 best and worst performing stocks today")
async def today_command(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    top, bottom, asx_sorted = get_daily_changes()

    def format_line(symbol, name, pct, price):
        emoji = "🟢" if pct > 0 else "🔴"
        sign = "+" if pct > 0 else ""
        return f"{symbol} ({name}): ${price:.2f}  | {emoji} {sign}{pct:.2%}"


    lines_top = [format_line(s, n, p, yf.Ticker(s).history(period="1d")["Close"].iloc[-1]) for s, n, p in top]
    lines_bot = [format_line(s, n, p, yf.Ticker(s).history(period="1d")["Close"].iloc[-1]) for s, n, p in bottom]
    asx_lines  = [format_line(s, n, p, yf.Ticker(s).history(period="1d")["Close"].iloc[-1]) for s, n, p in asx_sorted]

    msg = (
        "**📈 Top 10 Winners:**\n" + "\n".join(lines_top) +
        "\n\n**📉 Top 10 Losers:**\n" + "\n".join(lines_bot) +
        "\n\n**🇦🇺 ASX Stocks Ranked:**\n" + "\n".join(asx_lines)
    )

    await interaction.followup.send(msg)

client.run(stonk_bot_token)