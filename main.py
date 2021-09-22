#!/usr/bin/env python3
#
#   Copyright (c) 2021    MultisampledNight
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import json
import logging
import os
import random
import re
import shlex

import discord
import lxml.html
import requests
from discord.utils import get


HELP_MSG = ["""\
```md
# ARCHER(1)

## NAME
    Archer - Einfach nur ein Bot

## SYNOPSIS
    <prefix><command> [arguments]

## DESCRIPTION
    Ein Bot für den deutschen Arch Linux Server
```""",
"""\
```md
## COMMANDS
    help
        Zeigt diese Hilfe an.

    prefix <new-prefix>
        Setzt ein neues Präfix.

    whoami
        Zeigt an, ob du Einstellungen am Bot verändern darfst.

    show
        Zeigt die aktuellen Einstellungen (Moderator-Rolle, Präfix...) an.

    leetify <args>...
        1337iziert alle gegebenen Argumente und sendet das Ergebnis zurück.

    borkify <args>...
        Macht die gegebenen Argumente kaputt, indem Anfangs- und Endbuchstaben
        vertauscht werden.

    lookup <package>
        Sucht nach dem angegebenen Paket auf https://archlinux.org/packages/ und
        gibt die Version, die Größe und das Erstellungsdatum zurück.

    set-mod-role <role-name>
        Setzt die Moderationsrolle, welche für das Verändern von Einstellungen
        benötigt wird.

    send-role-message <channel-id>
        Sendet die Nachricht mit der Rollenauswahl in den angegebenen Channel.

    add-role <emoji> <role-name>
        Fügt eine Verlinkung zu der gegebenen Rolle hinzu, welche mithilfe des
        Emojis bei der Nachricht von send-role-message hinzugefügt werden kann.

    remove-role <emoji>
        Entfernt die Verlinkung der Rolle mit dem Emoji.

    distraction-probability <probability>
        Setzt eine neue Ablenkungswahrscheinlichkeit. Die Wahrscheinlichkeit
        sollte zum Beispiel für 50 % als 50 angegeben werden, also ohne das
        Prozentzeichen.
```""",
"""\
```md
## BUGS
    Es können nur Custom Emojis als Reaction Roles verwendet werden.
    Manchmal verselbstständigt er sich. Aber nur manchmal.

## REPORTING BUGS
    Sende einfach eine Nachricht auf dem Arch Linux Discord, und pinge einen von
    uns gleich mit. Wir werden es aber (je nach Tageszeit und Tag)
    wahrscheinlich auch ohne Ping schnell sehen.

## AUTHORS
    /home/donald4444#3512, TornaxO7#7596, MultisampledNight#2425

April 2021
```"""]

VERSION = "0.1.7"
PERSISTENT_PATH= os.path.join(os.path.dirname(os.path.realpath(__file__)), "persistent")
SAVEFILE = os.path.join(PERSISTENT_PATH, "settings")
LOGFORMAT = "[%(asctime)s] <%(levelname)s> %(message)s"
EMOJI_REGEX = re.compile("<:.+:([0-9]+)>")
ARCH_RESPONSES = [
    "ARCH IS THE BEST!",
    "Arch ist toll.",
    "I use Arch btw.",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARCH!:wq",
    "arch?",
    "Habe ich Arch gehört?",
    "Schonmal Arch installiert?",
    "Arch for the win!"
]

RM_RESPONSES = [
    "YOLO!!!!!! ||Nur ein Witz. Wer würde denn auch so verrückt sein und einfach etwas löschen. _Erinnert sich an sein Legacy-Backup_||",
    "*Uno reverse card*",
    "No u!",
    "uwu",
    "***aRe yOU sUrE AbOUt thAT?***"
]


class Package:
    def __init__(
            self,
            name: str,
            version: str,
            size: int,
            creation_date: datetime.date,
            publish_date: datetime.date):
        self.name = name
        self.version = version
        self.size = size
        self.creation_date = creation_date
        self.publish_date = publish_date

    def by_name(name: str):
        """
        Returns a new Arch-Package for the given package name. Note that this
        only searchs in the standard repositories, not in the AUR.
        """
        # first search for the package using the "search packages" site
        response = requests.get(f"https://archlinux.org/packages/?q={name}", stream=True)
        if response.status_code != 200:
            return None
        response.raw.decode_content = True

        tree = lxml.html.parse(response.raw)
        element = tree.xpath("/html/body/div[2]/div[3]/table/tbody/tr/td[3]/a")
        if not element:
            return None
        
        # then actually get the package contents
        package_url = f"https://archlinux.org{element[0].get('href')}"
        response = requests.get(package_url, stream=True)
        if response.status_code != 200:
            return None
        response.raw.decode_content = True

        tree = lxml.html.parse(response.raw)
        name = tree.xpath("/html/body/div[2]/div[2]/div[2]/meta[1]")[0].get("content")
        version = tree.xpath("/html/body/div[2]/div[2]/div[2]/meta[2]")[0].get("content")
        size = int(tree.xpath("/html/body/div[2]/div[2]/div[2]/meta[4]")[0].get("content"))
        creation_date = datetime.date.fromisoformat(tree.xpath("/html/body/div[2]/div[2]/div[2]/meta[5]")[0].get("content"))
        publish_date = datetime.date.fromisoformat(tree.xpath("/html/body/div[2]/div[2]/div[2]/meta[6]")[0].get("content"))
        return Package(name, version, size, creation_date, publish_date)
    
    def __repr__(self):
        # do we need to represent in MiB?
        mibsize = self.size / (1024.0 ** 2)
        if int(mibsize):
            size = f"{round(mibsize, 4)} MiB"
        else:
            # nope, display in KiB
            size = f"{round(self.size / 1024.0, 4)} KiB"
        return f"""\
Name: `{self.name}`
Version: `{self.version}`
Größe: `{size}`
Erstellungsdatum: `{self.creation_date.strftime("%d.%m.%Y, %B")}`
"""


class Settings:
    prefix = "archer "
    roles_msg = None  # the message where roles are given by reactions
    roles_channel = None  # the channel where the message is in
    mod_role = None
    roles = {}  # key is the reaction emoji, value is the role
    distraction_probability = 100
    loaded = False

    def save(self):
        if self.mod_role is None:
            mod_role = None
        else:
            mod_role = self.mod_role.id
        as_dict = {
            "prefix": self.prefix,
            "roles_msg": self.roles_msg,
            "roles_channel": self.roles_channel,
            "mod_role": mod_role,
            "distraction_probability": self.distraction_probability,
            "roles": {emoji: role.id for emoji, role in self.roles.items()},
        }
        with open(SAVEFILE, "w") as fh:
            fh.write(json.dumps(as_dict))

    def load(self, guild: discord.Guild):
        """ Load the settings from our settings-file. """
        try:
            with open(SAVEFILE) as fh:
                as_dict = json.loads(fh.read())

            self.prefix = as_dict.get("prefix", "archer ")
            self.roles_msg = as_dict.get("roles_msg", None)
            self.roles_channel = as_dict.get("roles_channel", None)

            if as_dict.get("mod_role", None):
                self.mod_role = guild.get_role(as_dict["mod_role"])
            else:
                self.mod_role = None

            self.distraction_probability = as_dict.get(
                "distraction_probability", 100)
            self.roles = {emoji: guild.get_role(
                role) for emoji, role in as_dict.get("roles", {}).items()}
        except:
            # it probably just doesn't exist yet
            pass
        self.loaded = True


intents = discord.Intents(members=True, emojis=True,
                          messages=True, reactions=True, guilds=True)
client = discord.Client(intents=intents)
settings = Settings()


def get_sudo_denied_message(user: discord.Member) -> str:
    user_formatted = f"{user.name}#{user.discriminator} ({user.id})"
    logging.warning(f"{user_formatted} failed to authenticate as root.")
    return f"{user_formatted} ist nicht in der sudoers Datei. Dieser Vorfall wird gemeldet."


def user_has_mod_perm(guild: discord.Guild, user_id: int) -> bool:
    user = guild.get_member(user_id)
    return user_id == admin_id or settings.mod_role in user.roles


async def reaction_roles_message() -> discord.Message:
    channel = client.get_channel(settings.roles_channel)
    message = await channel.fetch_message(settings.roles_msg)
    return message


def pretty_role_emoji_assoc() -> str:
    return "\n".join(map(
        lambda pair: f"  {client.get_emoji(int(pair[0]))} → `{pair[1].name}`",
        settings.roles.items()
    ))


async def edit_reaction_roles_message():
    if settings.roles_msg and settings.roles_channel:
        message = await reaction_roles_message()
        new_content = f"Benutze die Reaktionen unter dieser Nachricht, um dir selber Rollen zu geben.\n{pretty_role_emoji_assoc()}"
        await message.edit(content=new_content)


async def help(command, message):
    # split up into 2000 chars per message because 2000 is the limit
    for part in HELP_MSG:
        await message.channel.send(part)


async def set_prefix(command, message):
    if len(command) < 2:
        await message.channel.send("Kein neues Präfix angegeben.")
        return
    settings.prefix = command[1]
    settings.save()
    await message.channel.send(f"Neues Präfix ist nun `{settings.prefix}`.")


async def show(command, message):
    if settings.mod_role:
        mod_role = settings.mod_role.name
    else:
        mod_role = "Noch nicht gesetzt."
    await message.channel.send(f"""\
- Version: `{VERSION}`
- Moderator-Rolle: `{settings.mod_role.name}`
- Ablenkungswahrscheinlichkeit: `{settings.distraction_probability} %`
- Präfix: `{settings.prefix}`
- Reaction Roles:
{pretty_role_emoji_assoc()}""")


async def whoami(command, message):
    if user_has_mod_perm(message.guild, message.author.id):
        await message.channel.send(f"Du darfst Einstellungen vornehmen.")
    else:
        await message.channel.send(f"Du darfst keine Einstellungen vornehmen.")


async def leetify(command, message):
    if len(command) < 2:
        await message.channel.send("Mindestens ein Argument ist zum leetifien benötigt.")
        return

    lame = " ".join(command[1:])
    leetified = lame\
        .replace("l", "1")\
        .replace("L", "1")\
        .replace("i", "1")\
        .replace("I", "1")\
        .replace("t", "7")\
        .replace("T", "7")\
        .replace("e", "3")\
        .replace("E", "3")\
        .replace("a", "4")\
        .replace("A", "4")\
        .replace("b", "8")\
        .replace("B", "8")\
        .replace("o", "0")\
        .replace("O", "0")
    await message.channel.send(leetified)


async def borkify(command, message):
    if len(command) < 2:
        await message.channel.send("Mindestens ein Argument ist zum borkifien benötigt.")

    words = " ".join(command[1:]).split(" ")  # avoid weird use of " because of shlex
    borkified = []
    for word in words:
        new_word = f"{word[-1]}{word[1:-1]}{word[0]}"
        borkified.append(new_word)
    await message.channel.send(" ".join(borkified))


async def lookup(command, message):
    if len(command) < 2:
        await message.channel.send("Es wurde kein Paket zum Nachschauen angegeben.")
        return

    package = Package.by_name(command[1])
    if package is None:
        await message.channel.send("Das Paket scheint nicht zu existieren.")
        return
    await message.channel.send(repr(package))


async def rm(command, message):
    await message.channel.send(random.choice(RM_RESPONSES))


async def set_mod_role(command, message):
    role = get(message.guild.roles, name=command[1])
    if role is None:
        await message.channel.send("Diese Rolle scheint es nicht zu geben.")
        return

    settings.mod_role = role
    settings.save()
    await message.channel.send("Moderator-Rolle erfolgreich gesetzt.")


async def send_role_message(command, message):
    if len(command) < 2:
        await message.channel.send("Kein Channel angegeben.")
        return
    if not command[1].isdigit():
        await message.channel.send("Die Channel-ID scheint keine Zahl zu sein. IDs in Discord sind immer Zahlen.")
        return
    channel = client.get_channel(int(command[1]))
    if channel is None:
        await message.channel.send("Der Channel scheint nicht zu existieren.")
        return

    message = await channel.send("Benutze die Reaktionen unter dieser Nachricht, um dir selber Rollen zu geben.")
    settings.roles_msg = message.id
    settings.roles_channel = channel.id
    settings.save()
    # add reactions to easily click on them
    for emoji in map(lambda id: get(message.guild.emojis, id=int(id)), settings.roles.keys()):
        await message.add_reaction(emoji)
    await edit_reaction_roles_message()


async def add_role(command, message):
    if len(command) < 3:
        await message.channel.send("Es wurden zu wenig Argumente angegeben.")
        return

    emoji_match = EMOJI_REGEX.match(command[1])
    if emoji_match is None:
        await message.channel.send("Das erste Argument scheint kein custom Emoji sein.")
        return
    emoji_id = emoji_match.group(1)

    role = get(message.guild.roles, name=command[2])
    if role is None:
        await message.channel.send("Diese Rolle scheint es nicht zu geben.")
        return
    if role in settings.roles.values():
        await message.channel.send("Die Rolle ist bereits verlinkt.")
        return

    # check if the emoji exists at all in the guild
    emoji = get(message.guild.emojis, id=int(emoji_id))
    if emoji is None:
        await message.channel.send("Der Emoji existiert nicht auf diesem Server.")
        return

    settings.roles[emoji_id] = role
    settings.save()
    await message.channel.send("Rolle verlinkt.")

    # add the new role to the message, if it was sent yet
    if settings.roles_msg is None:
        return
    message = await reaction_roles_message()
    await message.add_reaction(emoji)
    await edit_reaction_roles_message()


async def remove_role(command, message):
    if len(command) < 2:
        await message.channel.send("Kein Emoji angegeben.")
        return

    emoji_match = EMOJI_REGEX.match(command[1])
    if emoji_match is None:
        await message.channel.send("Das Argument scheint kein custom Emoji sein.")
        return
    emoji_id = emoji_match.group(1)

    if emoji_id not in settings.roles.keys():
        await message.channel.send("Es gibt gar keine Rolle für diesen Emoji.")
        return

    del settings.roles[emoji_id]
    settings.save()
    await message.channel.send("Rolle gelöscht.")

    if settings.roles_msg is None:
        return
    message = await reaction_roles_message()
    emoji = get(message.guild.emojis, id=int(emoji_id))
    await message.remove_reaction(emoji, message.author)
    await edit_reaction_roles_message()


async def distraction_probability(command, message):
    if len(command) < 2:
        await message.channel.send("Keine Wahrscheinlichkeit angegeben.")
        return

    # Do some checks first if the given argument is valid or not
    if not command[1].isdigit():
        await message.channel.send("Die Wahrscheinlichkeit scheint keine Zahl zu sein.")
        return

    new_distract_num = int(command[1])

    if (new_distract_num > 100):
        await message.channel.send("Bitte eine Zahl im Bereich von 0-100.")
        return

    settings.distraction_probability = new_distract_num
    settings.save()
    await message.channel.send(f"Ablenkungswahrscheinlichkeit auf `{settings.distraction_probability} %` gesetzt.")


COMMANDS = {
    "help": {"fn": help, "requires_mod": False},
    "prefix": {"fn": set_prefix, "requires_mod": True},
    "show": {"fn": show, "requires_mod": False},
    "whoami": {"fn": whoami, "requires_mod": False},
    "leetify": {"fn": leetify, "requires_mod": False},
    "borkify": {"fn": borkify, "requires_mod": False},
    "lookup": {"fn": lookup, "requires_mod": False},
    "rm": {"fn": rm, "requires_mod": False},
    "set-mod-role": {"fn": set_mod_role, "requires_mod": True},
    "send-role-message": {"fn": send_role_message, "requires_mod": True},
    "add-role": {"fn": add_role, "requires_mod": True},
    "remove-role": {"fn": remove_role, "requires_mod": True},
    "distraction-probability": {"fn": distraction_probability, "requires_mod": True}
}


@client.event
async def on_ready():
    logging.info(f"Login as {client.user}")


@client.event
async def on_message(message):
    global settings
    if not settings.loaded:
        settings.load(message.guild)
    is_command = False

    if message.author == client.user:
        return

    if message.guild is None:
        await message.channel.send("Du kannst diesen Bot nicht in Direktnachrichten benutzen.")
        return

    if any(map(lambda user: user.id == client.user.id, message.mentions)):
        await message.channel.send(f"Der derzeitige Prefix ist `{settings.prefix}`.")
        return

    # for "scripts"
    lines = message.content.splitlines()
    for line in lines:
        if line.startswith(settings.prefix):
            is_command = True
            command = line[len(settings.prefix):]  # strip the prefix
            # shlex allows easy shell-like parsing
            command = shlex.split(command)

            logging.info(
                f"Command issued by {message.author.name}#{message.author.discriminator}: {command}")

            if not command:  # e.g. just 'archer' or 'archer '
                continue

            if command[0] in COMMANDS.keys():
                if COMMANDS[command[0]]["requires_mod"]:
                    if not user_has_mod_perm(message.guild, message.author.id):
                        await message.channel.send(get_sudo_denied_message(message.author))
                        return
                await COMMANDS[command[0]]["fn"](command, message)
            else:
                await message.channel.send(f"Unbekannter Befehl. Benutze `{settings.prefix}help` für Hilfe.")
                return

    if "arch" in message.content.lower() and \
            not is_command and \
            random.randint(1, 100) < settings.distraction_probability:
        await message.channel.send(random.choice(ARCH_RESPONSES))


@client.event
async def on_raw_reaction_add(payload):
    if not settings.loaded:
        settings.load(client.get_guild(payload.guild_id))
    if payload.user_id == client.user.id:
        # avoid applying roles to self
        return

    emoji_matches = str(payload.emoji.id) in settings.roles.keys()
    message_matches = payload.message_id == settings.roles_msg
    if emoji_matches and message_matches:
        # can't use get_user here because we need a Member, not a User
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = settings.roles[str(payload.emoji.id)]
        await member.add_roles(role, reason="Automatically through Reaction Roles")


@client.event
async def on_raw_reaction_remove(payload):
    if not settings.loaded:
        settings.load(client.get_guild(payload.guild_id))
    emoji_matches = str(payload.emoji.id) in settings.roles.keys()
    message_matches = payload.message_id == settings.roles_msg
    if emoji_matches and message_matches:
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = settings.roles[str(payload.emoji.id)]
        await member.remove_roles(role, reason="Automatically through Reaction Roles")


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    admin_id = os.getenv("ADMIN_ID")

    if token is None:
        with open(os.path.join(PERSISTENT_PATH, "TOKEN")) as fh:
            token = fh.read()

    if admin_id is None:
        with open(os.path.join(PERSISTENT_PATH, "ADMIN-ID")) as fh:
            admin_id = int(fh.read())

    logging.basicConfig(encoding="utf-8", format=LOGFORMAT, level=logging.INFO)
    client.run(token)
