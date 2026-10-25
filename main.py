import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime , timedelta
import asyncio
import pyautogui
import os

TOKEN = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

schedule = {}
reminder = {}

with open("date.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        if "IGNORE" in line:
            continue
        parts = line.strip().split(" ")
        day_str = parts[0]
        time_venue = parts[1].split("😒")
        time_str = time_venue[0]
        venue = time_venue[1] if len(time_venue) > 1 else "Unknown Venue"

        day_map = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

        if day_str in day_map:
            day = day_map[day_str]
            hour, minute = map(int, time_str.split(":"))
            schedule[(day, hour, minute)] = venue

schedule = dict(sorted(schedule.items()))
print(schedule)

with open("reminder.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        parts = line.strip().split("😒")
        date_str = parts[0]
        context = parts[1] if len(parts) > 1 else "No Context"

        month, date = map(int, date_str.split("/"))
        reminder[(month, date)] = context

reminder = dict(sorted(reminder.items()))
print(reminder)

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands
    print(f'We have logged in as {bot.user}')
    channel_id = 1415676336948641924  
    channel = bot.get_channel(channel_id)
    member_id = 758800875572428811  
    member = await bot.fetch_user(member_id)
    await channel.send(f"{member.mention}")

    check_classes.start()
    check_reminders.start()

# reminder
@tasks.loop(seconds=10)
async def check_classes():
    now = datetime.now()
    now = now.replace(second=0, microsecond=0) + timedelta(minutes=30)
    key = (now.weekday(), now.hour, now.minute)
    # print(key)
    if key in schedule:
        channel_id = 1411975951943860354  
        channel = bot.get_channel(channel_id)
        member_id = 758800875572428811  
        member = await bot.fetch_user(member_id)

        embed = discord.Embed(
            title="📢 Reminder",
            description=f"{member.mention} class at {schedule[key]}",
            color=discord.Color.blue()
        )
        message = await channel.send(embed=embed)

        await asyncio.sleep(900)
        embed = discord.Embed(
            title="Get your ass out the room",
            description=f"{member.mention} class at {schedule[key]}",
            color=discord.Color.blue()
        )
        message2 = await channel.send(embed=embed)

        await asyncio.sleep(3600)
        await message.delete()
        await message2.delete()

# day
async def setDate(interaction: discord.Interaction, current: str):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return [
        discord.app_commands.Choice(name=d, value=d)
        for d in days if current.lower() in d.lower() or current == ""
    ]

# hour
async def setHour(interaction: discord.Interaction, current: str):
    hours = [str(i) for i in range(24)]
    return [
        discord.app_commands.Choice(name=h, value=h)
        for h in hours if current in h or current == ""
    ]

# minute
async def setMinute(interaction: discord.Interaction, current: str):
    minutes = [str(i) for i in range(0, 61, 5)]
    return [
        discord.app_commands.Choice(name=m, value=m)
        for m in minutes if current in m or current == ""
    ]

# add weekly reminder
@bot.tree.command(name="add-date", description="Set a date and time")
@discord.app_commands.autocomplete(date=setDate, hour=setHour, minute=setMinute)
async def adddate(interaction: discord.Interaction, date: str, hour: str, minute: str, venue: str):
    await interaction.response.send_message(f"Set class on {date} {hour}:{minute} at {venue}")
    with open("date.txt", "a", encoding="utf-8") as f:
        f.write(f"{date} {hour}:{minute}😒{venue}\n")
    with open("date.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split(" ")
            day_str = parts[0]
            time_venue = parts[1].split("😒")
            time_str = time_venue[0]
            venue = time_venue[1] if len(time_venue) > 1 else "Unknown Venue"

            day_map = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6
            }

            if day_str in day_map:
                day = day_map[day_str]
                hour, minute = map(int, time_str.split(":"))
                global schedule
                schedule[(day, hour, minute)] = venue
                schedule = dict(sorted(schedule.items()))
                # print(schedule)

@bot.tree.command(name="view-schedule", description="View current schedule")
async def viewschedule(interaction: discord.Interaction):
    days_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }
    days, times, venues = [], [], []
    for (day, hour, minute), venue in schedule.items():
        days.append(days_map[day])
        times.append(f"{hour:02d}:{minute:02d}")
        venues.append(venue)

    col_widths = [
        max(len("Day"), max((len(d) for d in days), default=3)),
        max(len("Time"), max((len(t) for t in times), default=4)),
        max(len("Venue"), max((len(v) for v in venues), default=5)),
    ]

    table  = "╔" + "╦".join("═" * (w + 2) for w in col_widths) + "╗\n"
    table += "║ " + f"{'Day':<{col_widths[0]}}" + " ║ " + f"{'Time':<{col_widths[1]}}" + " ║ " + f"{'Venue':<{col_widths[2]}}" + " ║\n"
    table += "╠" + "╬".join("═" * (w + 2) for w in col_widths) + "╣\n"

    for d, t, v in zip(days, times, venues):
        table += "║ " + f"{d:<{col_widths[0]}}" + " ║ " + f"{t:<{col_widths[1]}}" + " ║ " + f"{v:<{col_widths[2]}}" + " ║\n"

    table += "╚" + "╩".join("═" * (w + 2) for w in col_widths) + "╝"

    embed = discord.Embed(
        title="📅 Timetable",
        description=f"```{table}```",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="delete-all", description="Delete all schedule")
async def deleteall(interaction: discord.Interaction):
    await interaction.response.send_message("Deleted all schedule")
    with open("date.txt", "w", encoding="utf-8") as f:
        f.write("")
    global schedule
    schedule = {}

async def setMonth(interaction: discord.Interaction, current: str):
    months = [str(i) for i in range(1, 13)]
    return [
        discord.app_commands.Choice(name=m, value=m)
        for m in months if current in m or current == ""
    ]

@bot.tree.command(name="add-1-time-reminder", description="Add a one-time reminder")
@discord.app_commands.autocomplete(month=setMonth)
async def addreminder(interaction: discord.Interaction, month: str, date: str, context: str):
    try:
        month = int(month)
        date = int(date)
        if not (1 <= month <= 12) or not (1 <= date <= 31):
            raise ValueError
        else:
            await interaction.response.send_message(f"Set reminder on {month}/{date} {context}")
            with open("reminder.txt", "a", encoding="utf-8") as f:
                f.write(f"{month}/{date}😒{context}\n")
                global reminder
                reminder[(month, date)] = context
                reminder = dict(sorted(reminder.items()))
    except ValueError:
        await interaction.response.send_message("Invalid month or date. Please enter valid integers.")
        return
    
@bot.tree.command(name="view-reminder", description="View current reminders")
async def viewreminder(interaction: discord.Interaction):
    months, dates, contexts = [], [], []
    for (month, date), context in reminder.items():
        months.append(f"{month:02d}")
        dates.append(f"{date:02d}")
        contexts.append(context)

    col_widths = [
        max(len("Month"), max((len(m) for m in months), default=5)),
        max(len("Date"), max((len(d) for d in dates), default=4)),
        max(len("Context"), max((len(c) for c in contexts), default=7)),
    ]

    table  = "╔" + "╦".join("═" * (w + 2) for w in col_widths) + "╗\n"
    table += "║ " + f"{'Month':<{col_widths[0]}}" + " ║ " + f"{'Date':<{col_widths[1]}}" + " ║ " + f"{'Context':<{col_widths[2]}}" + " ║\n"
    table += "╠" + "╬".join("═" * (w + 2) for w in col_widths) + "╣\n"

    for m, d, c in zip(months, dates, contexts):
        table += "║ " + f"{m:<{col_widths[0]}}" + " ║ " + f"{d:<{col_widths[1]}}" + " ║ " + f"{c:<{col_widths[2]}}" + " ║\n"

    table += "╚" + "╩".join("═" * (w + 2) for w in col_widths) + "╝"

    embed = discord.Embed(
        title="📅 Reminders",
        description=f"```{table}```",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@tasks.loop(seconds=10)
async def check_reminders(): # seperate the waiting 
    now = datetime.now() + timedelta(days=1)
    month = now.month
    day = now.day
    key = (month, day)
    # print(key)
    if key in reminder:
        channel_id = 1353777434750746717  
        channel = bot.get_channel(channel_id)
        member_id = 758800875572428811  
        member = await bot.fetch_user(member_id)

        del reminder[key]
        with open("reminder.txt", "w", encoding="utf-8") as f:
            for (m, d), c in reminder.items():
                f.write(f"{m}/{d}😒{c}\n")
        reminder = dict(sorted(reminder.items()))

        embed = discord.Embed(
            title="📢 One-Time Reminder 1",  # 12am
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.green()
        )
        message = await channel.send(embed=embed)
        await asyncio.sleep(21600) 

        embed = discord.Embed(
            title="📢 One-Time Reminder 2", # 6am
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.green()
        )

        message2 = await channel.send(embed=embed)
        await asyncio.sleep(21600)

        embed = discord.Embed(
            title="📢 One-Time Reminder 3", # 12pm
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.green()
        )

        message3 = await channel.send(embed=embed)
        await asyncio.sleep(21600)

        embed = discord.Embed(
            title="Last Reminder", # 6pm
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.red()
        )

        message4 = await channel.send(embed=embed)
        await asyncio.sleep(21600)

        await message4.delete()
        await message3.delete()
        await message2.delete()
        await message.delete()

        embed = discord.Embed(
            title="Today",
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.blue()
        )

        msg = await channel.send(embed=embed)
        await asyncio.sleep(21600)
        await msg.delete()

        embed = discord.Embed(
            title="Now",
            description=f"{member.mention} {reminder[key]}",
            color=discord.Color.blue()
        )

        msg2 = await channel.send(embed=embed)
        await asyncio.sleep(21600)
        await msg2.delete()

@bot.tree.command(name="shutdown-bot", description="Shutdown bot")
async def shutdown(interaction: discord.Interaction):
    channel_id = 1353777434750746717  
    channel = bot.get_channel(channel_id)
    member_id = 758800875572428811  
    member = await bot.fetch_user(member_id)

    msg = await channel.send(f"{member.mention} Shutting down bot")
    await asyncio.sleep(60)
    msg.delete()
    
    await bot.close()
    print("Shutting down")

def delay_msg_deletion(message, delay):
    async def delete_later():
        await asyncio.sleep(delay)
        await message.delete()
    asyncio.create_task(delete_later())

@bot.tree.command(name="ss", description="Send ss of screen")
async def screenshot(interaction: discord.Interaction):
    screenshot = pyautogui.screenshot()
    path = "screenshot.png"
    screenshot.save(path)

    try:
        await interaction.response.send_message(file=discord.File(path))
        msg = await interaction.original_response()
        async def delete_later(message_obj, file_path, delay=60):
            await asyncio.sleep(delay)
            try:
                await message_obj.delete()
            except Exception as e:
                print(f"Failed to delete message: {e}")
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to remove file: {e}")

        asyncio.create_task(delete_later(msg, path, 60))

    except Exception as e:
        try:
            await interaction.followup.send("Failed to send screenshot.")
        except Exception:
            pass
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Failed to remove file after error: {e}")



bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
