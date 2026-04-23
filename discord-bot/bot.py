import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from mcrcon import MCRcon
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
WHITELIST_CHANNEL_ID = int(os.getenv("WHITELIST_CHANNEL_ID"))
ADMIN_LOG_CHANNEL_ID = int(os.getenv("ADMIN_LOG_CHANNEL_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))

WHITELIST_FILE = "whitelisted.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def load_whitelisted():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            return json.load(f)
    return {}


def save_whitelisted(data):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def rcon_command(command):
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        return mcr.command(command)


def build_instructions_embed():
    embed = discord.Embed(
        title="🔮 Whitelist",
        description="Um dem Minecraft Server beizutreten, whiteliste dich einmalig mit dem Command unten.",
        color=0x9B59B6,
    )
    embed.add_field(
        name="Anleitung",
        value=(
            "1. Schreibe den Command unten in diesen Kanal\n"
            "2. Gib deinen **exakten** Minecraft-Benutzernamen an\n"
            "3. Du wirst automatisch gewhitelistet und bekommst die Rolle\n"
            "4. Du kannst dich nur **einmal** whitelisten"
        ),
        inline=False,
    )
    embed.add_field(
        name="Command",
        value="`/whitelist <dein_minecraft_name>`",
        inline=False,
    )
    embed.add_field(
        name="Beispiel",
        value="`/whitelist Notch`",
        inline=False,
    )
    embed.set_footer(text="🔮 | Bei Problemen wende dich an einen Admin")
    return embed


async def ensure_instructions(channel):
    """Löscht alle Nachrichten im Kanal und postet die Anleitung neu."""
    await channel.purge(limit=100)
    msg = await channel.send(embed=build_instructions_embed())
    await msg.pin()


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔮 Bot ist online als {bot.user}")

    channel = bot.get_channel(WHITELIST_CHANNEL_ID)
    if channel:
        # Prüfen ob bereits eine angepinnte Bot-Anleitung existiert
        pins = await channel.pins()
        bot_pin = any(p.author == bot.user for p in pins)
        if not bot_pin:
            await ensure_instructions(channel)


@bot.event
async def on_message(message):
    # Nachrichten von Bots ignorieren
    if message.author.bot:
        return

    # Im Whitelist-Kanal alle User-Nachrichten sofort löschen
    if message.channel.id == WHITELIST_CHANNEL_ID:
        await message.delete()
        return

    await bot.process_commands(message)


@bot.tree.command(name="whitelist", description="Whitelistet dich auf dem Minecraft Server")
@app_commands.describe(minecraft_name="Dein Minecraft Benutzername")
async def whitelist(interaction: discord.Interaction, minecraft_name: str):
    whitelisted = load_whitelisted()
    user_id = str(interaction.user.id)

    if user_id in whitelisted:
        await interaction.response.send_message(
            f"❌ Du bist bereits als **{whitelisted[user_id]}** gewhitelistet!",
            ephemeral=True,
        )
        return

    # Minecraft-Name validieren (3-16 Zeichen, nur Buchstaben/Zahlen/Unterstrich)
    clean = minecraft_name.replace("_", "")
    if not clean.isalnum() or not (3 <= len(minecraft_name) <= 16):
        await interaction.response.send_message(
            "❌ Ungültiger Minecraft Name!\nNur Buchstaben, Zahlen und `_` erlaubt (3–16 Zeichen).",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        rcon_command(f"whitelist add {minecraft_name}")

        # Speichern
        whitelisted[user_id] = minecraft_name
        save_whitelisted(whitelisted)

        # Whitelisted-Rolle vergeben
        role = interaction.guild.get_role(WHITELIST_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.followup.send(
            f"✅ **{minecraft_name}** wurde erfolgreich zur Whitelist hinzugefügt!\nDu hast die Rolle {role.mention if role else '**Whitelisted**'} erhalten und kannst jetzt dem Server beitreten.",
            ephemeral=True,
        )

        # Log im Admin-Kanal
        admin_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
        if admin_channel:
            log = discord.Embed(
                description=f"✅ {interaction.user.mention} (`{interaction.user}`) wurde als **{minecraft_name}** gewhitelistet",
                color=0x2ECC71,
            )
            log.set_footer(text=f"Discord ID: {interaction.user.id}")
            await admin_channel.send(embed=log)

    except Exception as e:
        print(f"RCON Fehler: {e}")
        await interaction.followup.send(
            "❌ Fehler beim Verbinden mit dem Server. Bitte kontaktiere einen Admin.",
            ephemeral=True,
        )


@bot.tree.command(name="whitelist-entfernen", description="Entfernt einen Spieler von der Whitelist (nur Admin)")
@app_commands.describe(minecraft_name="Minecraft Benutzername der entfernt werden soll")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_remove(interaction: discord.Interaction, minecraft_name: str):
    await interaction.response.defer(ephemeral=True)

    try:
        rcon_command(f"whitelist remove {minecraft_name}")

        # Aus lokaler Datei entfernen und Rolle wegnehmen
        whitelisted = load_whitelisted()
        role = interaction.guild.get_role(WHITELIST_ROLE_ID)

        for uid, name in list(whitelisted.items()):
            if name.lower() == minecraft_name.lower():
                del whitelisted[uid]
                save_whitelisted(whitelisted)

                # Rolle wegnehmen
                if role:
                    member = interaction.guild.get_member(int(uid))
                    if member:
                        await member.remove_roles(role)
                break

        await interaction.followup.send(
            f"✅ **{minecraft_name}** wurde von der Whitelist entfernt.",
            ephemeral=True,
        )

        # Log im Admin-Kanal
        admin_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
        if admin_channel:
            log = discord.Embed(
                description=f"🗑️ **{minecraft_name}** wurde von der Whitelist entfernt von {interaction.user.mention}",
                color=0xE74C3C,
            )
            await admin_channel.send(embed=log)

    except Exception as e:
        print(f"RCON Fehler: {e}")
        await interaction.followup.send(
            "❌ Fehler beim Entfernen von der Whitelist.",
            ephemeral=True,
        )


@bot.tree.command(name="whitelist-liste", description="Zeigt alle gewhitelisteten Spieler (nur Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_list(interaction: discord.Interaction):
    whitelisted = load_whitelisted()

    if not whitelisted:
        await interaction.response.send_message("Die Whitelist ist leer.", ephemeral=True)
        return

    entries = "\n".join(
        [f"<@{uid}> → **{name}**" for uid, name in whitelisted.items()]
    )
    embed = discord.Embed(
        title="🔮 Whitelist",
        description=entries,
        color=0x9B59B6,
    )
    embed.set_footer(text=f"{len(whitelisted)} Spieler gewhitelistet")
    await interaction.response.send_message(embed=embed, ephemeral=True)


bot.run(DISCORD_TOKEN)
