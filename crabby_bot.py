import os
import discord
from discord.ext import commands
import json
import random as rand
from datetime import datetime, timedelta
import asyncio
import io
import shutil
import zipfile

# ============================
# CONFIGURATION
# ============================
TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = 1449183301775527940
OWNER_ID = 1079842580856058086
MAX_TICKETS = 2
PING_CHANNEL_ID = 1538311605388050524  # Self-ping channel

# ============================
# CHANNEL IDS
# ============================
VERIFY_CH = 1449183302974967940
WELCOME_CH = 1449183303427948626
RULES_CH = 1449183303427948625
ROLES_CH = 1449183303889584298
COUNTING_CH = 1536881709646225469
TICKET_CH = 1449183303889584291
TICKET_CAT = 1536859976587288596
TRANSCRIPT_CH = 1536883686270836756
HELP_CH = 1449183303427948632
STATUS_CH = 1449183303427948630
RANK_ANNOUNCE_CH = 1449183303889584297
LOG_CH = 1536860016475381862

# ============================
# ROLE IDS
# ============================
VERIFIED_ROLE = 1449183302157336679
UNVERIFIED_ROLE = 1449183301775527941
MOD_ROLE = 1536883323161411665

# Game Roles
GAME_ROLES = {
    '🎯': 1536879043729694792,
    '🏗️': 1449183302174117982,
    '🎨': 1449183302157336686,
    '🏎️': 1449183302157336687,
    '⛏️': 1536878148292059277,
    '🕹️': 1536879315143237723,
    '📺': 1449183302157336678,
    '🤝': 1536878469085011978,
}

# Rank Roles
RANK_ROLES = {
    150: 1449183302174117989,
    500: 1449183302174117988,
    1000: 1449183302174117987,
    10000: 1449183302174117986,
}

# Strike Roles
STRIKE_ROLES = [
    1536885141832470628,
    1536885178818101330,
    1536885226108616785,
]

# ============================
# DATA MANAGEMENT
# ============================
data = {}

def load_data():
    global data
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except:
        data = {
            'counting': {'count': 0, 'last': None, 'top': {}},
            'ranks': {},
            'tickets': {},
            'strikes': {},
            'warns': {},
            'economy': {},
            'invites': {},
            'server_stats': {'daily_active': {}, 'total_messages': 0},
            'birthdays': {},
            'streaks': {},
            'notes': {},
            'polls': {},
            'suggestions': {},
            'voice_time': {},
            'mod_logs': []
        }
        save_data()

def save_data():
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

load_data()

# ============================
# BOT SETUP
# ============================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# ============================
# TICKET SYSTEM - FIXED
# ============================
class TicketView(discord.ui.View):
    def __init__(self, num, user, channel):
        super().__init__(timeout=None)  # No timeout!
        self.num = num
        self.user = user
        self.channel = channel
        self.closed = False

    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.closed:
            return await interaction.response.send_message('❌ Already closed!', ephemeral=True)
        
        mod_role = interaction.guild.get_role(MOD_ROLE)
        if mod_role not in interaction.user.roles:
            return await interaction.response.send_message('❌ Staff only!', ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        self.closed = True
        
        try:
            transcript = f'🎫 Ticket #{self.num} Transcript\n'
            transcript += '='*40 + '\n'
            transcript += f'Closed by: {interaction.user}\n'
            transcript += f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
            transcript += '='*40 + '\n\n'
            
            async for msg in self.channel.history(limit=50, oldest_first=False):
                transcript += f'[{msg.created_at.strftime("%H:%M")}] {msg.author.name}: {msg.content[:100]}\n'
            
            tc = interaction.guild.get_channel(TRANSCRIPT_CH)
            if tc:
                file = discord.File(io.BytesIO(transcript.encode()), f'ticket-{self.num}.txt')
                await tc.send(f'📄 Ticket #{self.num} closed by {interaction.user.mention}', file=file)
            
            await self.channel.delete()
            
            data['tickets'][str(self.num)]['open'] = False
            save_data()
            
            await interaction.followup.send('✅ Ticket closed!', ephemeral=True)
        except Exception as e:
            self.closed = False
            try:
                await interaction.followup.send('❌ Error closing ticket', ephemeral=True)
            except:
                pass

    @discord.ui.button(label='📄 Transcript', style=discord.ButtonStyle.secondary)
    async def transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.closed:
            return await interaction.response.send_message('❌ Ticket closed!', ephemeral=True)
        
        mod_role = interaction.guild.get_role(MOD_ROLE)
        if mod_role not in interaction.user.roles:
            return await interaction.response.send_message('❌ Staff only!', ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            transcript = f'🎫 Ticket #{self.num} Transcript\n'
            transcript += '='*40 + '\n'
            transcript += f'Created: {self.user}\n'
            transcript += f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
            transcript += '='*40 + '\n\n'
            
            async for msg in self.channel.history(limit=50, oldest_first=False):
                transcript += f'[{msg.created_at.strftime("%H:%M")}] {msg.author.name}: {msg.content[:100]}\n'
            
            file = discord.File(io.BytesIO(transcript.encode()), f'ticket-{self.num}.txt')
            await interaction.followup.send('📄 Transcript:', file=file, ephemeral=True)
        except:
            await interaction.followup.send('❌ Error generating transcript', ephemeral=True)

class CreateTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='🎫 Create Ticket', style=discord.ButtonStyle.primary, emoji='🎫')
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        open_tickets = sum(1 for t in data['tickets'].values() 
                          if t.get('user_id') == interaction.user.id and t.get('open', True))
        if open_tickets >= MAX_TICKETS:
            return await interaction.followup.send(f'❌ You already have {MAX_TICKETS} open tickets!', ephemeral=True)
        
        num = 1
        for key in data['tickets'].keys():
            try:
                if int(key) >= num:
                    num = int(key) + 1
            except:
                pass
        
        cat = interaction.guild.get_channel(TICKET_CAT)
        mod = interaction.guild.get_role(MOD_ROLE)
        
        if not cat or not mod:
            return await interaction.followup.send('❌ Server setup incomplete!', ephemeral=True)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            mod: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        try:
            channel = await interaction.guild.create_text_channel(
                f'ticket-{num}',
                category=cat,
                overwrites=overwrites
            )
        except Exception as e:
            return await interaction.followup.send(f'❌ Failed: {str(e)[:100]}', ephemeral=True)
        
        data['tickets'][str(num)] = {
            'user_id': interaction.user.id,
            'channel_id': channel.id,
            'open': True,
            'created': str(datetime.now())
        }
        save_data()
        
        await interaction.followup.send(f'✅ Ticket created! {channel.mention}', ephemeral=True)
        
        embed = discord.Embed(
            title=f'🎫 Ticket #{num}',
            description=f'**Created by:** {interaction.user.mention}\n**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\nPlease describe your issue. Staff will assist you shortly.',
            color=0x2ECC71
        )
        embed.set_footer(text='Crabby Cult • Support')
        
        view = TicketView(num, interaction.user, channel)
        await channel.send(embed=embed, view=view)
        await channel.send(f'{interaction.user.mention} Welcome to your ticket!', delete_after=5)

# ============================
# STATUS UPDATER
# ============================
async def status_update(msg):
    ch = bot.get_channel(STATUS_CH)
    if ch:
        embed = discord.Embed(
            title='🦀 Status Update',
            description=msg,
            color=0x9B59B6,
            timestamp=datetime.now()
        )
        await ch.send(embed=embed)

# ============================
# LOGGING SYSTEM
# ============================
async def log_action(embed):
    log_ch = bot.get_channel(LOG_CH)
    if log_ch:
        await log_ch.send(embed=embed)

async def log_mod_action(action):
    try:
        embed = discord.Embed(
            title='🛡️ Mod Action Logged',
            description=action,
            color=0x9B59B6,
            timestamp=datetime.now()
        )
        embed.set_footer(text='Crabby Cult • Moderation Log')
        await log_action(embed)
        
        if 'mod_logs' not in data:
            data['mod_logs'] = []
        data['mod_logs'].append({
            'action': action,
            'time': str(datetime.now())
        })
        if len(data['mod_logs']) > 1000:
            data['mod_logs'] = data['mod_logs'][-1000:]
        save_data()
    except Exception as e:
        print(f'Log error: {e}')

# ============================
# SELF-PING TASK (24/7)
# ============================
async def self_ping():
    await bot.wait_until_ready()
    channel = bot.get_channel(PING_CHANNEL_ID)
    if not channel:
        print(f'❌ Channel {PING_CHANNEL_ID} not found!')
        return
    while not bot.is_closed():
        try:
            await channel.send('🦀 Crabby Bot is alive! [Railway Self-Ping]')
            print('✅ Self-ping sent to Discord')
        except Exception as e:
            print(f'❌ Self-ping failed: {e}')
        await asyncio.sleep(600)  # 10 minutes

# ============================
# UPDATE VC COUNTERS
# ============================
async def update_vc_counters():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    members_vc = guild.get_channel(MEMBERS_COUNT_VC)
    if members_vc:
        member_count = len([m for m in guild.members if not m.bot])
        await members_vc.edit(name=f'👥 Members: {member_count}')

# ============================
# HELPER FUNCTIONS
# ============================
def is_mod():
    async def predicate(ctx):
        return MOD_ROLE in [r.id for r in ctx.author.roles] or ctx.author.id == OWNER_ID
    return commands.check(predicate)

def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

# ============================
# HIDDEN OWNER COMMANDS (not shown in help)
# ============================
@bot.command(name='close_all', hidden=True)
@is_owner()
async def close_all(ctx):
    await ctx.defer()
    closed = 0
    for tid, info in data['tickets'].items():
        if info.get('open', True):
            channel = ctx.guild.get_channel(info['channel_id'])
            if channel:
                try:
                    await channel.delete()
                    closed += 1
                except:
                    pass
            info['open'] = False
    save_data()
    await ctx.send(f'✅ Closed {closed} tickets')
    await status_update(f'🗑️ All tickets closed by {ctx.author.mention}')
    await log_mod_action(f'🗑️ All {closed} tickets closed by {ctx.author.mention}')

@bot.command(name='mass_role', hidden=True)
@is_owner()
async def mass_role(ctx, role: discord.Role, *, members: commands.Greedy[discord.Member]):
    if not members:
        return await ctx.send('❌ Usage: `!mass_role @role @user1 @user2 ...`')
    added = 0
    for member in members:
        if role not in member.roles:
            try:
                await member.add_roles(role)
                added += 1
            except:
                pass
    await ctx.send(f'✅ Added {role.name} to {added} members')
    await log_mod_action(f'🎭 {ctx.author.mention} mass added {role.name} to {added} members')

@bot.command(name='set_role', hidden=True)
@is_owner()
async def set_role(ctx, role: discord.Role, confirm: str = None):
    if confirm != 'confirm':
        return await ctx.send(f'❌ Type `!set_role {role.name} confirm` to give to all members')
    members = [m for m in ctx.guild.members if not m.bot and role not in m.roles]
    added = 0
    for member in members:
        try:
            await member.add_roles(role)
            added += 1
        except:
            pass
    await ctx.send(f'✅ Gave {role.name} to {added} members')
    await status_update(f'🎭 Mass role {role.name} assigned by {ctx.author.mention}')
    await log_mod_action(f'🎭 {ctx.author.mention} gave {role.name} to {added} members')

@bot.command(name='nuke', hidden=True)
@is_owner()
async def nuke(ctx):
    await ctx.defer()
    channel = ctx.channel
    pos = channel.position
    cat = channel.category
    await channel.delete()
    new = await cat.create_text_channel(channel.name, position=pos)
    await new.send('🦀 Channel nuked!')
    await log_mod_action(f'💥 {ctx.author.mention} nuked {channel.name}')

@bot.command(name='pull', hidden=True)
@is_owner()
async def pull(ctx):
    await ctx.defer()
    vc = ctx.guild.get_channel(CRAB_OFFICE_VC)
    if not vc:
        return await ctx.send('❌ VC not found!')
    members = [m for m in ctx.guild.members if not m.bot and m.voice and m.voice.channel]
    moved = 0
    for member in members:
        try:
            await member.move_to(vc)
            moved += 1
            await asyncio.sleep(0.5)
        except:
            pass
    await ctx.send(f'✅ Pulled {moved} members to {vc.mention}!')
    await log_mod_action(f'🔊 {ctx.author.mention} pulled {moved} members to {vc.name}')

# ============================
# ON READY - SENDS SETUP CODE
# ============================
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    await status_update(f'✅ Bot online! {bot.user.mention} ready.')
    await update_vc_counters()
    
    # Start self-ping
    bot.loop.create_task(self_ping())
    
    guild = bot.get_guild(GUILD_ID)
    
    if guild:
        invites = await guild.invites()
        data['invites'] = {i.code: i.uses or 0 for i in invites}
        save_data()
    
    # SEND SETUP MESSAGES ON STARTUP
    ch = bot.get_channel(VERIFY_CH)
    if ch:
        async for msg in ch.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title='🦀 Welcome to Crabby Cult 🦀',
                description='We are a branch of the **Crabby Minecraft Civilization** server - We are based on making other games events, such as **Roblox, Fortnite, R6**, and other games the community suggests.\n\n'
                           '📌 **React with 🦀 to get verified!**',
                color=0x9B59B6
            )
            embed.set_footer(text='Crabby Cult • Verification')
            msg = await ch.send(embed=embed)
            await msg.add_reaction('🦀')
    
    # Rules
    ch = bot.get_channel(RULES_CH)
    if ch:
        async for msg in ch.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title='🦀 Server Rules 🦀',
                description='**1.** Be respectful. No harassment, slurs, or targeted insults.\n\n'
                           '**2.** No NSFW content — keep it SFW everywhere.\n\n'
                           '**3.** Use the right channel for the right topic.\n\n'
                           '**4.** No spam, raids, or excessive caps/emojis.\n\n'
                           '**5.** No self-promo without staff approval — ask first.\n\n'
                           '**6.** Follow Discord ToS. Staff has final say on edge cases.\n\n'
                           '*By being here, you agree to follow these rules. Staff decisions are final.*',
                color=0x9B59B6
            )
            embed.set_footer(text='Crabby Cult • Rules')
            await ch.send(embed=embed)
    
    # Role Selection
    ch = bot.get_channel(ROLES_CH)
    if ch:
        async for msg in ch.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title='🎮 Pick Your Game Roles!',
                description='React to get roles for your favorite games:\n\n'
                           '🎯 – **Rainbow Six Siege**\n'
                           '🏗️ – **Roblox**\n'
                           '🎨 – **Fortnite**\n'
                           '🏎️ – **GTA**\n'
                           '⛏️ – **Minecraft**\n'
                           '🕹️ – **Other Games**\n'
                           '📺 – **YouTube Pings**\n'
                           '🤝 – **Partner Ping**\n\n'
                           '*Remove your reaction to remove the role.*',
                color=0x3498DB
            )
            embed.set_footer(text='Crabby Cult • Roles')
            msg = await ch.send(embed=embed)
            for emoji in GAME_ROLES.keys():
                await msg.add_reaction(emoji)
    
    # Ticket System
    ch = bot.get_channel(TICKET_CH)
    if ch:
        async for msg in ch.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title='🎫 Support Tickets',
                description=f'Click the **Create Ticket** button below.\n\n**Max {MAX_TICKETS} tickets per user.**\n\nA staff member will assist you shortly.',
                color=0x2ECC71
            )
            embed.set_footer(text='Crabby Cult • Support')
            await ch.send(embed=embed, view=CreateTicketView())
    
    # Help
    ch = bot.get_channel(HELP_CH)
    if ch:
        async for msg in ch.history(limit=5):
            if msg.author == bot.user:
                break
        else:
            embed = discord.Embed(
                title='🦀 Crabby Cult Commands 🦀',
                description='**━━━━━━━━━━━━━━━━━━━━━━━━━**\n'
                           '**📌 GENERAL COMMANDS**\n'
                           '`!ping` – Check bot latency\n'
                           '`!stats` – Server statistics\n'
                           '`!crab` – Random crab fact\n'
                           '`!rank` – Check your rank\n'
                           '`!leaderboard` – Top members\n'
                           '`!counting` – Counting stats\n'
                           '`!roleinfo` – Get role info\n'
                           '━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                           '**💰 GAMBLING**\n'
                           '`!daily` – Claim daily coins\n'
                           '`!balance` – Check your coins\n'
                           '`!bet <amount>` – Gamble your coins\n'
                           '`!slots <amount>` – Play slots\n'
                           '`!give @user <amount>` – Give coins\n'
                           '`!rich` – Richest members\n'
                           '━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                           '**🎮 FUN COMMANDS**\n'
                           '`!rps <rock/paper/scissors>` – Play RPS\n'
                           '`!randnum <min> <max>` – Random number\n'
                           '`!remind <minutes> <message>` – Set reminder\n'
                           '`!note <message>` – Save a note\n'
                           '`!poll <question>` – Create a poll\n'
                           '`!suggest <suggestion>` – Submit suggestion\n'
                           '`!countdown <seconds>` – Start countdown\n'
                           '━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                           '**🔧 STAFF COMMANDS**\n'
                           '`!warn @user <reason>` – Warn user\n'
                           '`!strike @user` – Give strike\n'
                           '`!kick @user <reason>` – Kick user\n'
                           '`!ban @user <reason>` – Ban user\n'
                           '`!clear <amount>` – Clear messages\n'
                           '`!botstatus <message>` – Status update\n'
                           '`!lockdown #channel` – Lock channel\n'
                           '`!unlock #channel` – Unlock channel\n'
                           '`!embed <title> #color <desc>` – Custom embed\n'
                           '━━━━━━━━━━━━━━━━━━━━━━━━━',
                color=0x9B59B6
            )
            embed.set_footer(text='Crabby Cult • Help')
            await ch.send(embed=embed)
    
    # Init data
    if not data.get('counting'):
        data['counting'] = {'count': 0, 'last': None, 'top': {}}
        save_data()
    if not data.get('ranks'):
        data['ranks'] = {}
        save_data()
    if 'mod_logs' not in data:
        data['mod_logs'] = []
        save_data()
    
    print('✅ All systems ready!')
    await log_mod_action(f'✅ Bot online! {bot.user.mention} ready.')

# ============================
# REST OF YOUR COMMANDS
# ============================
# (All your existing commands go here - embed, warn, strike, etc.)
# I've included the key ones, add the rest from your original file

# ============================
# RUN BOT
# ============================
if __name__ == "__main__":
    bot.run(TOKEN)