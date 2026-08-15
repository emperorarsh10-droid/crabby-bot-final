import os
import discord
from discord.ext import commands
import asyncio

TOKEN = os.getenv('BOT_TOKEN')
PING_CHANNEL_ID = 1538311605388050524  # Your channel ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    print(f'✅ Self-ping channel: {PING_CHANNEL_ID}')
    bot.loop.create_task(self_ping())

async def self_ping():
    await bot.wait_until_ready()
    channel = bot.get_channel(PING_CHANNEL_ID)
    if not channel:
        print(f'❌ Channel {PING_CHANNEL_ID} not found!')
        return
    while not bot.is_closed():
        try:
            await channel.send('🦀 Crabby Bot is alive! [Koyeb Self-Ping]')
            print('✅ Self-ping sent to Discord')
        except Exception as e:
            print(f'❌ Self-ping failed: {e}')
        await asyncio.sleep(600)  # 10 minutes

@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! {round(bot.latency * 1000)}ms')

# Add your other commands here if needed

if __name__ == "__main__":
    bot.run(TOKEN)