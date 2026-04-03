import os
import discord
from discord.ext import tasks
from datetime import datetime, time
from zoneinfo import ZoneInfo

TOKEN = "PYsP1FCxLItrwpxnQAZuN22r-nf46yx4"

print("TOKEN exists:", TOKEN is not None)
print("TOKEN repr:", repr(TOKEN))

JST = ZoneInfo("Asia/Tokyo")

JST = ZoneInfo("Asia/Tokyo")

# 対象チャンネル（雑談）
TARGET_CHANNEL_ID = 1489489148191576194

# 平日（0=月〜4=金）
WORKDAYS = {0, 1, 2, 3, 4}

# 制限ルール
BLOCK_RULES = [
    {"name": "勤務時間", "days": WORKDAYS, "start": time(9, 0), "end": time(17, 0)},
    {"name": "深夜", "days": {0,1,2,3,4,5,6}, "start": time(23, 0), "end": time(7, 0)},
]

intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

current_lock = None

def is_in_range(now_t, start_t, end_t):
    if start_t < end_t:
        return start_t <= now_t < end_t
    else:
        return now_t >= start_t or now_t < end_t

def should_lock():
    now = datetime.now(JST)
    weekday = now.weekday()
    now_t = now.time()

    for rule in BLOCK_RULES:
        if weekday in rule["days"] and is_in_range(now_t, rule["start"], rule["end"]):
            return True, rule["name"]
    return False, ""

async def apply_lock(channel, enabled):
    everyone = channel.guild.default_role
    overwrite = channel.overwrites_for(everyone)
    overwrite.send_messages = False if enabled else None

    await channel.set_permissions(
        everyone,
        overwrite=overwrite,
        reason=f"雑談制限 {'ON' if enabled else 'OFF'}"
    )

@tasks.loop(minutes=1)
async def scheduler():
    global current_lock

    enabled, reason = should_lock()

    if current_lock == enabled:
        return

    for guild in client.guilds:
        channel = guild.get_channel(TARGET_CHANNEL_ID)
        if channel:
            await apply_lock(channel, enabled)
            current_lock = enabled
            print(f"{guild.name}: {'ON' if enabled else 'OFF'} {reason}")

@scheduler.before_loop
async def before():
    await client.wait_until_ready()

@client.event
async def on_ready():
    print(f"ログイン成功: {client.user}")
    scheduler.start()

client.run(TOKEN)
