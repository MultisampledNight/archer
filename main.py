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

import logging
import random
import re
import shlex

import discord
from discord.utils import get


HELP_MSG = """\
```md
# ARCHER(1)

## NAME
    Archer - Einfach nur ein Bot

## SYNOPSIS
    <prefix><command> [arguments]

## DESCRIPTION
    Ein Bot für den deutschen Arch Linux Server

## COMMANDS
    help
        Zeigt diese Hilfe an.

    prefix <new-prefix>
        Setzt ein neues Präfix.

    whoami
        Zeigt an, ob du Einstellungen am Bot verändern darfst.

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

## BUGS
    Es können nur Custom Emojis als Reaction Roles verwendet werden.
    Manchmal verselbstständigt er sich. Aber nur manchmal.

## REPORTING BUGS
    Sende einfach eine Nachricht auf dem Arch Linux Discord, und pinge einen von
    uns gleich mit. Wir werden es aber (je nach Tageszeit und Tag)
    wahrscheinlich auch ohne Ping schnell sehen.

## AUTHORS
    /home/donald4444#3512, TornaxO7#7596, MultisampledNight#2425, 

April 2021
```
"""
LOGFORMAT = "[%(asctime)s] <%(levelname)s> %(message)s"
EMOJI_REGEX = re.compile("<:.+:([0-9]+)>")
ARCH_RESPONSES = [
    "ARCH IS THE BEST!",
    "Arch ist toll.",
    "I use Arch btw.",
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARCH!:wq",
    "arch?"
]


intents = discord.Intents(members=True, emojis=True, messages=True, reactions=True, guilds=True)
client = discord.Client(intents=intents)
prefix = "archer "
roles_msg = None  # the message where roles are given by reactions
roles_channel = None  # the channel where the message is in
mod_role = None
roles = {}  # key is the reaction emoji, value is the role


def get_sudo_denied_message(user: discord.Member) -> str:
    user_formatted = f"{user.name}#{user.discriminator} ({user.id})"
    logging.warning(f"{user_formatted} failed to authenticate as root.")
    return f"{user_formatted} ist nicht in der sudoers Datei. Dieser Vorfall wird gemeldet."


def user_has_mod_perm(guild: discord.Guild, user_id: int) -> bool:
    user = guild.get_member(user_id)
    return user_id == 817468254255054908 or mod_role in user.roles


@client.event
async def on_ready():
    logging.info(f"Login as {client.user}")


@client.event
async def on_message(message):
    global prefix
    global mod_role
    global roles_msg
    global roles_channel
    is_command = False

    if message.author == client.user:
        return

    if message.guild is None:
        await message.channel.send("Du kannst diesen Bot nicht in Direktnachrichten benutzen.")
        return

    # for "scripts"
    lines = message.content.splitlines()
    for line in lines:
        if line.startswith(prefix):
            is_command = True
            command = line[len(prefix):]  # strip the prefix
            command = shlex.split(command)  # shlex allows easy shell-like parsing

            logging.info(f"Command issued by {message.author.name}#{message.author.discriminator}: {command}")

            if not command:  # e.g. just 'archer' or 'archer '
                continue

            elif command[0].lower() == "help":
                await message.channel.send(HELP_MSG)

            elif command[0].lower() == "prefix":
                if not user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(get_sudo_denied_message(message.author))
                    return

                if len(command) < 2:
                    await message.channel.send("Kein neues Präfix angegeben.")
                    return
                prefix = command[1]
                await message.channel.send(f"Neues Präfix ist nun `{prefix}`.")

            elif command[0].lower() == "whoami":
                if user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(f"Du darfst Einstellungen vornehmen.")
                else:
                    await message.channel.send(f"Du darfst keine Einstellungen vornehmen.")

            elif command[0].lower() == "set-mod-role":
                if not user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(get_sudo_denied_message(message.author))
                    return

                role = get(message.guild.roles, name=command[1])
                if role is None:
                    await message.channel.send("Diese Rolle scheint es nicht zu geben.")
                    return

                mod_role = role
                await message.channel.send("Moderator-Rolle erfolgreich gesetzt.")

            elif command[0].lower() == "send-role-message":
                if not user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(get_sudo_denied_message(message.author))
                    return

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
                roles_msg = message.id
                roles_channel = channel.id
                # add reactions to easily click on them
                for emoji in map(lambda id: get(message.guild.emojis, id=int(id)), roles.keys()):
                    await message.add_reaction(emoji)

            elif command[0].lower() == "add-role":
                if not user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(get_sudo_denied_message(message.author))
                    return

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
                if role in roles.values():
                    await message.channel.send("Die Rolle ist bereits verlinkt.")
                    return

                roles[emoji_id] = role
                await message.channel.send("Rolle verlinkt.")

                # add the new role to the message, if it was sent yet
                if roles_msg is None:
                    return
                channel = client.get_channel(roles_channel)
                message = await channel.fetch_message(roles_msg)
                emoji = get(message.guild.emojis, id=int(emoji_id))
                await message.add_reaction(emoji)

            elif command[0].lower() == "remove-role":
                if not user_has_mod_perm(message.guild, message.author.id):
                    await message.channel.send(get_sudo_denied_message(message.author))
                    return

                if len(command) < 2:
                    await message.channel.send("Kein Emoji angegeben.")
                    return

                emoji_match = EMOJI_REGEX.match(command[1])
                if emoji_match is None:
                    await message.channel.send("Das Argument scheint kein custom Emoji sein.")
                    return
                emoji_id = emoji_match.group(1)

                if emoji_id not in roles.keys():
                    await message.channel.send("Es gibt gar keine Rolle für diesen Emoji.")
                    return

                del roles[emoji_id]
                await message.channel.send("Rolle gelöscht.")

                if roles_msg is None:
                    return
                channel = client.get_channel(roles_channel)
                message = await channel.fetch_message(roles_msg)
                emoji = get(message.guild.emojis, id=int(emoji_id))
                await message.remove_reaction(emoji, message.author)

            else:
                await message.channel.send(f"Unbekannter Befehl. Benutze `{prefix}help` für Hilfe.")
                return

    if "arch" in message.content.lower() and not is_command:
        await message.channel.send(random.choice(ARCH_RESPONSES))


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        # avoid applying roles to self
        return

    emoji_matches = str(payload.emoji.id) in roles.keys()
    message_matches = payload.message_id == roles_msg
    if emoji_matches and message_matches:
        # can't use get_user here because we need a Member, not a User
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = roles[str(payload.emoji.id)]
        await member.add_roles(role, reason="Automatically through Reaction Roles")


@client.event
async def on_raw_reaction_remove(payload):
    emoji_matches = str(payload.emoji.id) in roles.keys()
    message_matches = payload.message_id == roles_msg
    if emoji_matches and message_matches:
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = roles[str(payload.emoji.id)]
        await member.remove_roles(role, reason="Automatically through Reaction Roles")


if __name__ == "__main__":
    with open("TOKEN") as fh:
        token = fh.read()

    logging.basicConfig(encoding="utf-8", format=LOGFORMAT, level=logging.INFO)
    client.run(token)
