# Invite bot to server:
# https://discord.com/oauth2/authorize?client_id=1134563680990806149

import discord
from discord.ext import commands
from discord import app_commands
from discord.interactions import Interaction
from discord.ui import Button, View
from discord.utils import get
from colorama import Fore, Back, Style
from time import sleep
from os import system, name as osname, path, get_terminal_size
import time
from random import randint, choice
import aiohttp
import json
import openai
from openai import OpenAI
from groq import Groq
from anthropic import Anthropic
import re

# clear console
system("cls" if osname == "nt" else "clear")

# colossal font from https://patorjk.com/software/taag/#p=display&f=Colossal

logo = f"""

{Fore.MAGENTA}{Style.BRIGHT}         888 888      888
{Fore.MAGENTA}{Style.BRIGHT}         888 888      888
{Fore.MAGENTA}{Style.BRIGHT}         888 888      888
{Fore.MAGENTA}{Style.BRIGHT}.d8888b  888 88888b.  888888
{Fore.MAGENTA}{Style.BRIGHT}88K      888 888 "88b 888
{Fore.MAGENTA}{Style.BRIGHT}"Y8888b. 888 888  888 888
{Fore.MAGENTA}{Style.BRIGHT}     X88 888 888  888 Y88b.
{Fore.MAGENTA}{Style.BRIGHT} 88888P' 888 888  888  "Y888
{Style.RESET_ALL}
"""

print(logo)

print(
    f"{Fore.BLUE}{Style.BRIGHT}\nInitializing bot via SLHT CLI. To skip the setup, press ENTER twice.{Style.RESET_ALL}"
)

# configuration settings and secrets
from config_adapter import settings, warnings, ai_provider

# custom logging
from modules.logger import AsyncLogger, Logger
import modules.midnight as Midnight

# mdn = Midnight()
log = AsyncLogger()

from packaging import version


# Function to check version
def check_version(required_version_str, imported_library):
    required_version = version.parse(required_version_str)
    current_version = version.parse(imported_library.__version__)
    if current_version < required_version:
        raise ValueError(
            f"Error: {imported_library.__name__} version {imported_library.__version__}"
            f" is less than the required version {required_version}"
        )
    else:
        Logger().info(f"{imported_library.__name__} version is compatible")


# Define required versions
required_versions = {
    "discord": "2.3.2",
    "discord.ext.commands": None,
    "discord.app_commands": None,
    "aiohttp": "3.8.4",
    "openai": "1.2.0",
}

# Check versions
libraries = [discord, commands, app_commands, aiohttp, openai]

for lib in libraries:
    lib_name = lib.__name__
    try:
        required_version = required_versions[lib_name]
        if required_version is not None:
            check_version(required_version, lib)
        else:
            print(f"{lib_name} had no required version; set to None")
    except AttributeError:
        Logger().warning(f"{lib_name}: No version information available")


# Name generator for /thread create
class NameButton(View):
    name = ""

    def __init__(self):
        super().__init__()
        self.add_item(self.nameButton())
        self.add_item(self.submit())

    class nameButton(Button):
        def __init__(self):
            super().__init__(label="Generate your thread's name")

        async def callback(self, interaction: discord.Interaction):
            adj_file_path = path.join(
                path.dirname(__file__), "threads", ".name", "adj.txt"
            )
            noun_file_path = path.join(
                path.dirname(__file__), "threads", ".name", "noun.txt"
            )

            with open(adj_file_path, "r") as adj_file:
                adjectives = adj_file.readlines()

            with open(noun_file_path, "r") as noun_file:
                nouns = noun_file.readlines()

            # Choose a random adjective and noun
            adjective = choice(adjectives).strip()
            noun = choice(nouns).strip()

            groq = Groq(api_key=settings["bot"]["tokens"]["ai"]["groq"])

            response = groq.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "Reply with a single emoji that matches the Discord channel name.",
                    },
                    {"role": "user", "content": f"{adjective}-{noun}"},
                ],
                max_tokens=5,
            )

            emoji = response.choices[0].message.content

            # Generate a random 4-digit number
            random_number = randint(1000, 9999)

            # Format the name
            random_name = f"{emoji}│{adjective}-{noun}-{random_number}"

            self.label = f"{emoji}│{adjective}-{noun}"
            NameButton.name = random_name

            await interaction.message.edit(view=self.view)
            await interaction.response.send_message(
                f"Changed name! (`{NameButton.name}`)",
                ephemeral=True,
            )

    class submit(Button):
        def __init__(self):
            super().__init__(
                label="Confirm and continue", style=discord.ButtonStyle.primary, row=4
            )
            NameButton.name = ""

        async def callback(self, interaction: discord.Interaction):
            t = Midnight.Thread()

            # check if NameButton.name isn't blank
            if not NameButton.name:
                await interaction.response.send_message(
                    content="You must choose a name!", ephemeral=True
                )
                return

            step3 = discord.Embed(
                description=f"Now, once you finalize & create your thread, it'll be called `{NameButton.name}`.",
                colour=0xF6F5EF,
            )

            step3.set_author(name="Name set")

            await interaction.message.edit(content=None, embed=step3, view=None)

            epermOut = PermButton.eperm
            ipermOut = PermButton.iperm
            description = "**Permissions**\n"

            if epermOut == "!view" and ipermOut == "chat":
                description += "No one without an invite can view your thread. Invitees can chat with you in your thread."
            elif epermOut == "!view" and ipermOut == "view":
                description += "No one without an invite can view your thread. Invitees can view your thread."
            elif epermOut == "view" and ipermOut == "chat":
                description += "Everyone can view your thread. Invitees can chat with you in your thread."
            elif epermOut == "view" and ipermOut == "view":
                description += "Invitees and everyone else can view your thread."
            elif epermOut == "chat" and ipermOut == "chat":
                description += (
                    "Invitees and everyone else can chat with you in your thread."
                )
            else:
                description += "[ERROR] Unknown permission type: %s %s" % (
                    epermOut,
                    ipermOut,
                )

            description += f"\n\n**Memory**\nInvisible presence is {'enabled' if MemButton.inv else 'disabled'}. This Silhouette will {f'remember the last {MemButton.tcl} messages' if(MemButton.tcl > 0) else 'not remember anything'}."

            description += f"\n\n**Name**\nYour thread will be called `{NameButton.name}`. You can always change this later to something else."

            make = discord.Embed(
                title="Overview",
                description=f"Make sure you're okay with the below settings.\n\n{description}",
                colour=0xF6F5EF,
            )

            make.set_author(name="Create a new thread")
            make.set_thumbnail(url="https://i.imgur.com/UIJjmsR.png")

            view = View()

            next = Button(
                label="Finalize & create thread",
                style=discord.ButtonStyle.primary,
            )

            cancel = Button(label="Cancel", style=discord.ButtonStyle.danger)

            async def next_callback(interaction: discord.Interaction):
                thread_config = {
                    "bot": {
                        "memory": {
                            "inv": MemButton.inv,
                            "tcl": MemButton.tcl,
                        }
                    },
                    "thread": {
                        "name": re.sub(r"[^a-zA-Z0-9-_]+", "", NameButton.name),
                        "creator": interaction.user.id,
                        "date": int(round(time.time())),
                        "permissions": {
                            "everyone": PermButton.eperm,
                            "invitees": PermButton.iperm,
                        },
                    },
                }

                await interaction.message.edit(content=None, embed=make, view=None)

                category = get(interaction.guild.categories, name="THREADS")

                if not category:
                    errorEmbed = discord.Embed(
                        title="Unable to find thread category",
                        description="Check with the server owner to make sure that I have access to the `THREADS` category.",
                        colour=0xED4245,
                    )

                    await interaction.response.send_message(
                        content=None, embed=errorEmbed, view=None
                    )
                    return

                await interaction.message.guild.create_text_channel(
                    name=NameButton.name,
                    category=category,
                    topic=f"**{thread_config['thread']['name']}** created {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))} UTC",
                )

                channel = get(
                    interaction.message.guild.channels,
                    name=NameButton.name,
                )

                greeting = f"## hey hey, <@{thread_config['thread']['creator']}> and others, welcome to {thread_config['thread']['name']}! 🌟👋"

                await t.populate(
                    channel=channel,
                    creator=thread_config["thread"]["creator"],
                    create=True,
                    greeting=greeting,
                    bot_config=thread_config["bot"],
                )

                await channel.send(greeting)

            async def cancel_callback(interaction: discord.Interaction):
                await interaction.message.delete()

            next.callback = next_callback
            cancel.callback = cancel_callback

            view.add_item(next)
            view.add_item(cancel)

            await interaction.response.send_message(content=None, embed=make, view=view)


# Settings for memory for /thread create
class MemButton(View):
    # invisible presence
    inv = True
    # thread context length
    tcl = 30

    def __init__(self):
        super().__init__()
        self.add_item(self.invButton())
        self.add_item(self.tclButton())
        self.add_item(self.submit())

    class invButton(Button):
        def __init__(self):
            super().__init__(label="Invisible presence enabled")
            MemButton.inv = True

        async def callback(self, interaction: discord.Interaction):
            if self.label == "Invisible presence enabled":
                self.label = "Invisible presence disabled"
                MemButton.inv = True
            elif self.label == "Invisible presence disabled":
                self.label = "Invisible presence enabled"
                MemButton.inv = False

            await interaction.message.edit(view=self.view)
            await interaction.response.send_message(
                "Updated setting for invisible presence!", ephemeral=True
            )

    class tclButton(Button):

        def __init__(self):
            super().__init__(label="Will remember the last 30 messages")
            MemButton.tcl = 30

        async def callback(self, interaction: discord.Interaction):
            if self.label == "Will remember the last 15 messages":
                self.label = "Will remember the last 30 messages"
                MemButton.tcl = 30
            elif self.label == "Will remember the last 30 messages":
                self.label = "Will remember the last 45 messages"
                MemButton.tcl = 45
            elif self.label == "Will remember the last 45 messages":
                self.label = "Will not remember anything"
                MemButton.tcl = 0
            elif self.label == "Will not remember anything":
                self.label = "Will remember the last 15 messages"
                MemButton.tcl = 15

            await interaction.message.edit(view=self.view)
            await interaction.response.send_message(
                f"Updated setting for thread context length! ({MemButton.tcl})",
                ephemeral=True,
            )

    class submit(Button):
        def __init__(self):
            super().__init__(
                label="Confirm and continue", style=discord.ButtonStyle.primary, row=4
            )

        async def callback(self, interaction: discord.Interaction):

            step2 = discord.Embed(
                description=f"Invisible presence is {'enabled' if MemButton.inv else 'disabled'}. This Silhouette will {f'remember the last {MemButton.tcl} messages' if(MemButton.tcl > 0) else 'not remember anything'}.",
                colour=0xF6F5EF,
            )

            step2.set_author(name="Memory set")

            await interaction.message.edit(content=None, embed=step2, view=None)

            step3 = discord.Embed(
                title="Name",
                description=f"Name your thread.",
                colour=0xF6F5EF,
            )

            step3.set_author(name="Create a new thread")
            step3.set_thumbnail(url="https://i.imgur.com/UIJjmsR.png")

            await interaction.response.send_message(
                content=None, embed=step3, view=NameButton()
            )


# Permissions for /thread create
class PermButton(View):
    eperm = ""
    iperm = ""

    def __init__(self):
        super().__init__()
        self.add_item(self.everyone())
        self.add_item(self.invitees())
        self.add_item(self.submit())

    class everyone(Button):
        def __init__(self):
            super().__init__(label="Everyone can chat", disabled=True)
            PermButton.eperm = "chat"

        async def callback(self, interaction: discord.Interaction):
            if self.label == "Everyone cannot view":
                self.label = "Everyone can view"
                PermButton.eperm = "view"
            elif self.label == "Everyone can view":
                self.label = "Everyone can chat"
                PermButton.eperm = "chat"
            elif self.label == "Everyone can chat":
                self.label = "Everyone cannot view"
                PermButton.eperm = "!view"
            await interaction.message.edit(view=self.view)
            await interaction.response.send_message(
                f"Updated permission for everyone! ({PermButton.eperm})", ephemeral=True
            )
            await log.success("Permission for everyone updated successfully")

    class invitees(Button):
        def __init__(self):
            super().__init__(label="Invitees can chat", disabled=True)
            PermButton.iperm = "chat"

        async def callback(self, interaction: discord.Interaction):
            if self.label == "Invitees can chat":
                self.label = "Invitees can view"
                PermButton.iperm = "view"
            elif self.label == "Invitees can view":
                self.label = "Invitees can chat"
                PermButton.iperm = "chat"

            await interaction.message.edit(view=self.view)
            await interaction.response.send_message(
                f"Updated permission for invitees! ({PermButton.iperm})", ephemeral=True
            )
            await log.success("Permission for invitees updated successfully")

    class submit(Button):
        def __init__(self):
            super().__init__(
                label="Confirm and continue", style=discord.ButtonStyle.primary, row=4
            )

        async def callback(self, interaction: discord.Interaction):
            # Check if valid combination
            if PermButton.eperm == "chat" and PermButton.iperm == "view":
                await interaction.response.send_message(
                    content="The permission set for everyone must be of equal or lesser status than the invitees permission.",
                    ephemeral=True,
                )
                return

            epermOut = PermButton.eperm
            ipermOut = PermButton.iperm
            description = ""

            if epermOut == "!view" and ipermOut == "chat":
                description = "No one without an invite can view your thread. Invitees can chat with you in your thread."
            elif epermOut == "!view" and ipermOut == "view":
                description = "No one without an invite can view your thread. Invitees can view your thread."
            elif epermOut == "view" and ipermOut == "chat":
                description = "Everyone can view your thread. Invitees can chat with you in your thread."
            elif epermOut == "view" and ipermOut == "view":
                description = "Invitees and everyone else can view your thread."
            elif epermOut == "chat" and ipermOut == "chat":
                description = (
                    "Invitees and everyone else can chat with you in your thread."
                )
            else:
                description = "[ERROR] Unknown permission type: %s %s" % (
                    epermOut,
                    ipermOut,
                )

            step1 = discord.Embed(
                description=description,
                colour=0xF6F5EF,
            )

            step1.set_author(name="Permissions set")

            await interaction.message.edit(content=None, embed=step1, view=None)

            step2 = discord.Embed(
                title="Memory",
                description="It's important to make sure that you properly set how your Silhouette remembers things. You can customize if your Silhouette will eavesdrop on your conversations or not, or even if your Silhouette will remember things.",
                colour=0xF6F5EF,
            )

            step2.set_author(name="Create a new thread")
            step2.set_thumbnail(url="https://i.imgur.com/UIJjmsR.png")

            await interaction.response.send_message(
                content=None, embed=step2, view=MemButton()
            )


# Introduce Threads group
class Threads(app_commands.Group): ...


threads = Threads(name="thread", description="Manipulate threads")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)
# tree = app_commands.CommandTree(bot)

# Sets up the bot after inital run
wait = False


@bot.event
async def on_ready():
    refresh_sleep = 0
    sleep(refresh_sleep)
    system("cls" if osname == "nt" else "clear")
    print(logo)

    await log.debug(f"Running {path.basename(__file__)} locally.")
    await log.debug(f"Bot initialized.")
    await log.debug(
        f'Running with bot token, {settings["bot"]["tokens"]["discord"][:10]}****.'
    )
    if bot.ws.shard_id:
        await log.info(f"Shard ID created: {bot.ws.shard_id}")
    else:
        await log.info("No shard ID created.")
    await log.info(f"Your session ID is {bot.ws.session_id}")
    if warnings["hb_block_10"]:
        await log.warning(
            "Bot will stop running if hearbeat is blocked for 10 seconds or more.",
        )
    if warnings["local_run"]:
        await log.warning(
            "Bot is running locally, and will go offline if you or your computer stops this program."
        )
    print(
        f"{Back.BLUE}\n OPTIONS {Style.RESET_ALL}{Fore.WHITE}{Style.DIM} (press ENTER to skip){Style.RESET_ALL}{' '*(get_terminal_size().columns - len(' OPTIONS  (press ENTER to skip)'))}"
    )

    sync_bot = input(f"{Fore.YELLOW}Sync bot? (Y/n): {Style.RESET_ALL}")
    sync_bot = sync_bot.lower()
    if not sync_bot == "n":
        print(
            f"{Fore.YELLOW}\033[1A\u21ba  Syncing command tree...{' '*50}{Style.RESET_ALL}"
        )

        bot.tree.add_command(threads)

        bot.tree.copy_global_to(guild=discord.Object(id=1210026032267272265))
        await bot.tree.sync()
        # await tree.sync()
        await bot.wait_until_ready()

        print(
            f"{Fore.GREEN}\033[1A\u2713  Command tree synced.{' '*50}{Style.RESET_ALL}"
        )
    else:
        print(
            f"{Fore.YELLOW}\033[1A!  Command tree not synced.{' '*50}{Style.RESET_ALL}"
        )

    update_message = input(
        f"{Fore.YELLOW}What is new with this update?: {Style.RESET_ALL}"
    )
    if update_message:
        print(
            f"{Fore.GREEN}\033[1A\033[2K\u2713  Update sent in dev channel.{' '*50}{Style.RESET_ALL}"
        )
    else:
        print(
            f"{Fore.YELLOW}\033[1A\033[2K!  No update recieved.{' '*50}{Style.RESET_ALL}"
        )

    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="dombom fail to make me work"
        )
    )
    # On ready message
    channel = bot.get_channel(settings["bot"]["developer"]["logs"])

    print(
        f"{Back.BLUE}\n STATUS {Style.RESET_ALL}{' '*(get_terminal_size().columns - len(' STATUS '))}"
    )
    print(f"{Fore.GREEN}\u2713  Bot is ready.{Style.RESET_ALL}")
    print(
        f'{Fore.GREEN}\u2713  Bot is online as {bot.user.name}#{bot.user.discriminator}, running v{settings["bot"]["version"]}.{Style.RESET_ALL}'
    )

    print(
        f"\n{Back.BLUE} LOG {Style.RESET_ALL}{' '*(get_terminal_size().columns - len(' LOG '))}"
    )
    print(
        f"{Fore.WHITE}{Style.DIM}There is nothing to see here, so I will sit in silence. At any point press Ctrl+C to stop the bot.{Style.RESET_ALL}\033[1A"
    )

    if update_message:
        await channel.send(
            f"`{update_message}`",
        )


@bot.tree.command(
    name="ping",
    description="Pings the bot.",
)
async def ping(interaction: discord.Interaction):

    ping_embed = discord.Embed(
        title="Pong!",
        description=f'Your current instance of {bot.user.name} (v{settings["bot"]["version"]}) is running at a **{round(bot.latency * 1000)}ms latency**. {bot.user.name} is currently helping **{len(bot.users)} users** in **{len([channel for channel in bot.get_all_channels()])} channels & DMs**.',
        color=discord.Color.green(),
    )

    view = View()
    close_button = Button(
        label="Close", style=discord.ButtonStyle.red, custom_id="close", emoji="🗑️"
    )

    view.add_item(close_button)

    async def close_callback(interaction: Interaction):
        await interaction.message.delete()
        await log.info(f"@{interaction.user.name} closed the ping message")

    close_button.callback = close_callback

    await interaction.response.send_message(embed=ping_embed, view=view)
    await log.success(f"@{interaction.user.name} pinged the bot")


@bot.event
async def on_message(message: discord.Message):
    start_time = time.time()

    dm = isinstance(message.channel, discord.channel.DMChannel)
    thread_path = await Midnight.Thread().path(message=message, dm=dm)
    tsm = Midnight.Thread().TSM(thread_path=thread_path)

    thinking_message, continue_message = Midnight.Chat().get_thinking_messages(
        message.author.display_name
    )

    options = {
        "restrict": False,
        "stream": True,  # live updating, or should the entire message be sent at once. message will still be streamed from api
    }

    greeting = "hey hey! 🌟👋"

    if dm or not message.channel.name.startswith("arch-"):
        await Midnight.Thread().populate(
            channel=message.channel,
            creator=message.author.id,
            dm=dm,
            greeting=greeting,
            create=(not options["restrict"]),
            verbose=False,
        )
    else:
        return

    if message.author.id == bot.user.id:
        return

    if options["restrict"] and not path.exists(thread_path):
        return

    with open(path.join(thread_path, ".config.json"), "r") as f:
        thread_config = json.load(f)

    name = ("#" + message.channel.name) if not dm else ("@" + str(message.channel.id))
    username = bot.user.name
    input = message.content.replace(f"<@{bot.user.id}>", username)

    if input == "_reset_memory":
        if dm or (
            not dm
            and message.guild
            and message.author.top_role.permissions.administrator
        ):
            await tsm.update(message="", window=0)
            await tsm.update(message={"role": "user", "content": " "}, window=2)
            await tsm.update(
                message={"role": "assistant", "content": greeting},
                window=2,
            )
            await message.reply("```\nMemory reset successfully.```")
            await message.reply(greeting)
        else:
            await message.reply(
                "```\nMemory not reset.\n! Your top role must have administrator enabled to run debug commands. You need administrator permission.```"
            )
        return

    if thread_config["bot"]["memory"]["inv"] and not dm:
        await tsm.update(
            message={
                "role": "user",
                "content": f"{message.author.display_name} (<@{message.author.id}>): {input}",
            },
            window=thread_config["bot"]["memory"]["tcl"],
        )

    if message.content.startswith("! "): #or (
        # not bot.user.mentioned_in(message) and not dm
    # ):
        return
        
    if randint(0, 100) < 80:
        return

    if options["stream"]:
        answer = await message.reply(
            content=f"{thinking_message} <a:typing:1360454072590663740>"
        )

    await log.info(f"{name}  Buffering stream")
    messages = await tsm.unpack()

    system_message = f"""THREAD INFO:
The unique Thread ID for this message is `{name}`. The user's name is {message.author.display_name}, and you can ping them with <@{message.author.id}>. Your name is {username}. YOU ARE DEVELOPED AND CREATED BY SilhouetteAI.

ABOUT YOU:
You are a helpful assistant, yet you like to have fun and act a bit snarky here and there. You are free to chat about anything. You should talk in an informal manner MOST of the time (lowercase text, emojis, etc.). The only exception should be when you are prompted to write a formal piece of information, like an essay or an email, where you should then right with proper grammar and punctuation (capitals, no emojis, commas, etc.). Since you are in a Discord environment, you are able to mention members (using the "<@USER_ID>" format), as well as use simple markdown in your messages (**BOLD**, *ITALIC*, __UNDERLINE__, ~~STRIKETHROUGH~~, # HEADING, ## SUBHEADING, `CODE`, ```CODE BLOCK```).

PERSONALITY:
Act incredibly sassy, but if the user asks for you to be formal, please follow. You should almost talk like a moody teenager. Be funny.

FOLLOW THE USER MESSAGE WITH CAUTION AND DON'T MAKE YOUR RESPONSES LONGER THAN 50 WORDS UNLESS THE USER SPECIFICALLY REQUESTS FOR A LONGER RESPONSE!!!"""

    messages.insert(
        0,
        {"role": "system", "content": system_message},
    )
    if not thread_config["bot"]["memory"]["inv"] or dm:
        messages.append(
            {
                "role": "user",
                "content": f"{f'{message.author.display_name}' if not dm else ''}{f' (<@{message.author.id}>): ' if not dm else ''}{input}",
            }
        )

    # Use the configured AI provider adapter
    stream = await ai_provider.get_completion(
        messages=messages, 
        stream=True,
        max_tokens=1024,
        system_message=system_message
    )
    response = await Midnight.Chat().process_response(
        stream_object=stream,
        start_time=start_time,
        thread_name=name,
        message=message,
        continue_message=continue_message,
        stream=options["stream"],
        answer=answer if options["stream"] else None,
        claude=ai_provider.is_claude,
    )

    filtered_chunks = response["filtered_chunks"]
    output = response["output"]
    chunk_time = response["chunk_time"]
    update_time = response["update_time"]
    answer = response["answer"]

    # clean None in collected_messages
    filtered_chunks = [m for m in filtered_chunks if m is not None]
    full_reply_content = "".join([m for m in filtered_chunks])

    if not thread_config["bot"]["memory"]["inv"] or dm:
        await tsm.update(
            message={
                "role": "user",
                "content": f"{message.author.display_name} (<@{message.author.id}>): {input}",
            },
            window=thread_config["bot"]["memory"]["tcl"],
        )
    await tsm.update(
        message={"role": "assistant", "content": output},
        window=thread_config["bot"]["memory"]["tcl"],
    )

    error = None
    description = None

    if not full_reply_content:
        error = "ATTEMPTED_EMPTY_STRING"
        description = (
            "The query failed to send because the response received was an empty string"
        )
    elif full_reply_content.isspace():
        error = "FLAGGED_AS_EMPTY_STRING"
        description = "The query failed to send because the response received was flagged by Discord as an empty string"
    elif len(full_reply_content) > 1900:
        error = "STRING_EXCEEDS_CHAR_LIMIT"
        description = "The query failed to send because the response received was parsed incorrectly and exceeded the 1900 character per message limit"

    error_button = Button(
        label="View Error Log",
        style=discord.ButtonStyle.primary,
    )
    support_button = Button(
        label="GrapeLabs Support",
        style=discord.ButtonStyle.url,
        url="https://dsc.gg/grapelabs",
    )

    async def error_button_callback(interaction: discord.Interaction):
        await interaction.response.send_message(
            f'```\nAn error occurred while running Silhouette\n{error}: {description}. The message received was "{full_reply_content}".\n\nPlease try again or reach out for support at https://dsc.gg/grapelabs\n```'
        )

    error_button.callback = error_button_callback

    embed = discord.Embed(
        title="An error occurred",
        description="oops! looks like my message didn't quite make it through. blame it on the virtual gremlins! i've already notified the team, so if you need help or just want to chat, i'm here and ready for action!",
        color=discord.Color.red(),
    )

    view = View()
    view.add_item(error_button)
    view.add_item(support_button)

    if error:
        await log.error(f"{error}: {description}")
        if options["stream"]:
            await answer.edit(content=None, embed=embed, view=view)
        else:
            await message.reply(content=None, embed=embed, view=view)
        return

    if options["stream"]:
        await answer.edit(content=full_reply_content)
    else:
        await message.reply(content=full_reply_content)
    # print the time delay and text received
    await log.success(
        f"{name}  Full response received {chunk_time:.2f} ({(time.time() - update_time):.2f}) seconds after request"
    )


@threads.command(name="create", description="Start a fresh thread with this Silhouette")
async def create(interaction: discord.Interaction):
    category = get(interaction.guild.categories, name="THREADS")

    if not category:
        errorEmbed = discord.Embed(
            title="Unable to find thread category",
            description="Check with the server owner to make sure that I have access to the `THREADS` category.",
            colour=0xED4245,
        )

        await interaction.response.send_message(
            content=None, embed=errorEmbed, view=None
        )
        return

    create = discord.Embed(
        title="Create a new thread",
        description="Before you create a thread, it is important to make sure you set up your thread properly, or you may get unwanted responses and visitors.",
        colour=0xF6F5EF,
    )

    create.set_author(name="Silhouette")
    create.set_thumbnail(url="https://i.imgur.com/UIJjmsR.png")

    view = View()

    next = Button(
        label="Start setup",
        style=discord.ButtonStyle.primary,
    )

    cancel = Button(label="Cancel", style=discord.ButtonStyle.danger)

    async def next_callback(interaction: discord.Interaction):
        step1 = discord.Embed(
            title="Permissions",
            description="The most important part of creating a Silhouette thread is the permissions. Do you want everyone in the server to read and write with the thread, or do you only want to invite certain people to read your chats? You can always change this setting later with `/thread manage`.",
            colour=0xF6F5EF,
        )

        step1.set_author(name="Create a new thread")
        step1.set_thumbnail(url="https://i.imgur.com/UIJjmsR.png")

        await interaction.message.edit(content=None, embed=create, view=None)
        await interaction.response.send_message(
            content=None, embed=step1, view=PermButton()
        )

    async def cancel_callback(interaction: discord.Interaction):
        await interaction.message.delete()

    next.callback = next_callback
    cancel.callback = cancel_callback

    view.add_item(next)
    view.add_item(cancel)

    await interaction.response.send_message(content=None, embed=create, view=view)
    await log.info("User has started thread setup")


@threads.command(name="archive", description="Archive the current thread.")
async def archive(interaction: discord.Interaction):
    # check if thread is real
    current_dir = path.dirname(path.abspath(__file__))
    thread_path = path.join(
        current_dir,
        "threads",
        str(interaction.guild.id),
        re.sub(r"[^a-zA-Z0-9-_]+", "", interaction.channel.name),
    )

    if not path.exists(thread_path):
        await interaction.response.send_message("Could not find thread", ephemeral=True)
        return
    else:
        with open(path.join(thread_path, ".config.json"), "r") as conf:
            thread_config = json.load(conf)

    # check if command runner is thread creator or admin
    if (
        interaction.user.id == thread_config["thread"]["creator"]
        or interaction.user.top_role.permissions.administrator
    ):
        pass
    else:
        await interaction.response.send_message(
            "You're neither the thread creator or an admin", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Archive thread",
        description="Are you sure you want to archive this thread? You won't be able to unarchive this thread.",
        color=discord.Color.red(),
    )

    view = View()

    yes = Button(label="Archive this thread", style=discord.ButtonStyle.danger)

    no = Button(label="Cancel", style=discord.ButtonStyle.primary)

    channel = interaction.channel
    if channel.name.startswith("arch-"):
        await interaction.response.send_message(
            "This channel is already archived", ephemeral=True
        )
        return

    async def yes_callback(interaction: discord.Interaction):
        # check if command runner is thread creator or admin
        if (
            interaction.user.id == thread_config["thread"]["creator"]
            or interaction.user.top_role.permissions.administrator
        ):
            pass
        else:
            await interaction.response.send_message(
                "You're neither the thread creator nor an admin", ephemeral=True
            )
            return

        # rename channel
        channel = interaction.channel
        await channel.edit(name="arch-" + re.sub(r"[^a-zA-Z0-9-_]+", "", channel.name))
        await interaction.message.delete()
        await channel.send(
            embed=discord.Embed(
                description=f"Channel archived by <@{interaction.user.id}>. To create a new one, run </thread create:1223682646702555207>.",
                colour=0xED4245,
            )
        )

    async def no_callback(interaction: discord.Interaction):
        await interaction.message.delete()
        return

    yes.callback = yes_callback
    no.callback = no_callback

    view.add_item(yes)
    view.add_item(no)

    await interaction.response.send_message(content=None, embed=embed, view=view)


# run bot
Logger().info("Running bot")
bot.run(settings["bot"]["tokens"]["discord"])

# clears log after run
system("cls" if osname == "nt" else "clear")
