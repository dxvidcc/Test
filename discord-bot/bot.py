import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
WHITELIST_CHANNEL_ID = int(os.getenv("WHITELIST_CHANNEL_ID"))
ADMIN_LOG_CHANNEL_ID = int(os.getenv("ADMIN_LOG_CHANNEL_ID"))
WHITELIST_ROLE_ID = int(os.getenv("WHITELIST_ROLE_ID"))

# Kanal für die Live-Liste der gewhitelisteten Spieler.
# Ohne eigenen Eintrag landet die Liste im Whitelist-Kanal.
WHITELIST_LIST_CHANNEL_ID = int(
    os.getenv("WHITELIST_LIST_CHANNEL_ID") or WHITELIST_CHANNEL_ID
)

# TEST_MODE=true → RCON wird übersprungen, alles andere funktioniert normal
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

WHITELIST_FILE = "whitelisted.json"
LIST_STATE_FILE = "list_message.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_whitelisted():
    return _load_json(WHITELIST_FILE, {})


def save_whitelisted(data):
    _save_json(WHITELIST_FILE, data)


def rcon_command(command):
    if TEST_MODE:
        print(f"[TEST MODE] RCON übersprungen: {command}")
        return
    from mcrcon import MCRcon
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        return mcr.command(command)


async def send_admin_log(embed):
    channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
    if channel is None:
        print(f"Admin-Log-Kanal {ADMIN_LOG_CHANNEL_ID} nicht gefunden")
        return
    try:
        await channel.send(embed=embed)
    except Exception:
        traceback.print_exc()


async def remove_entry(guild, user_id, actor):
    """Entfernt einen Spieler von Whitelist, Rolle und Bot-Liste.

    Gibt den Minecraft-Namen zurück, None wenn der Spieler nicht eingetragen war,
    oder wirft weiter wenn RCON fehlschlägt.
    """
    whitelisted = load_whitelisted()
    name = whitelisted.get(user_id)
    if name is None:
        return None

    rcon_command(f"whitelist remove {name}")

    del whitelisted[user_id]
    save_whitelisted(whitelisted)

    role = guild.get_role(WHITELIST_ROLE_ID)
    member = guild.get_member(int(user_id))
    if role and member:
        try:
            await member.remove_roles(role)
        except Exception:
            traceback.print_exc()

    log = discord.Embed(
        description=f"🗑️ <@{user_id}> (**{name}**) wurde von der Whitelist entfernt — durch {actor.mention}",
        color=0xE74C3C,
    )
    await send_admin_log(log)
    return name


# ---------------------------------------------------------------- Live-Liste


def build_list_embed():
    whitelisted = load_whitelisted()
    if whitelisted:
        description = "\n".join(
            f"<@{uid}> — **{name}**" for uid, name in whitelisted.items()
        )
    else:
        description = "_Noch niemand gewhitelistet._"

    embed = discord.Embed(
        title="🔮 Gewhitelistete Spieler",
        description=description,
        color=0x9B59B6,
    )
    embed.add_field(
        name="Eigenen Eintrag korrigieren",
        value=(
            "Vertippt? Klicke **Meinen Eintrag entfernen** und whiteliste dich "
            "danach im Whitelist-Kanal neu."
        ),
        inline=False,
    )
    embed.set_footer(text=f"{len(whitelisted)} Spieler gewhitelistet")
    return embed


async def update_list_message():
    channel = bot.get_channel(WHITELIST_LIST_CHANNEL_ID)
    if channel is None:
        print(f"Listen-Kanal {WHITELIST_LIST_CHANNEL_ID} nicht gefunden")
        return

    state = _load_json(LIST_STATE_FILE, {})
    message = None
    if state.get("channel_id") == channel.id and state.get("message_id"):
        try:
            message = await channel.fetch_message(state["message_id"])
        except discord.NotFound:
            message = None
        except Exception:
            traceback.print_exc()
            return

    embed = build_list_embed()
    try:
        if message:
            await message.edit(embed=embed, view=ListView())
        else:
            message = await channel.send(embed=embed, view=ListView())
            _save_json(
                LIST_STATE_FILE,
                {"channel_id": channel.id, "message_id": message.id},
            )
    except Exception:
        traceback.print_exc()


class AdminRemoveSelect(discord.ui.Select):
    def __init__(self, whitelisted, guild):
        options = []
        # Discord erlaubt maximal 25 Einträge pro Auswahlmenü
        for uid, name in list(whitelisted.items())[:25]:
            member = guild.get_member(int(uid))
            options.append(
                discord.SelectOption(
                    label=name,
                    value=uid,
                    description=str(member) if member else f"Discord ID {uid}",
                )
            )
        super().__init__(
            placeholder="Spieler auswählen…",
            options=options,
            min_values=1,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        removed, failed = [], []
        for uid in self.values:
            try:
                name = await remove_entry(interaction.guild, uid, interaction.user)
                if name:
                    removed.append(name)
            except Exception:
                traceback.print_exc()
                failed.append(uid)

        await update_list_message()

        parts = []
        if removed:
            parts.append("✅ Entfernt: " + ", ".join(f"**{n}**" for n in removed))
        if failed:
            parts.append(
                "❌ Fehlgeschlagen (Serververbindung): "
                + ", ".join(f"<@{uid}>" for uid in failed)
            )
        await interaction.followup.send("\n".join(parts) or "Nichts geändert.", ephemeral=True)


class AdminRemoveView(discord.ui.View):
    def __init__(self, whitelisted, guild):
        super().__init__(timeout=120)
        self.add_item(AdminRemoveSelect(whitelisted, guild))


class ListView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Meinen Eintrag entfernen",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
        custom_id="whitelist_self_remove",
    )
    async def self_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        if user_id not in load_whitelisted():
            await interaction.response.send_message(
                "Du bist aktuell nicht gewhitelistet.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            name = await remove_entry(interaction.guild, user_id, interaction.user)
        except Exception:
            traceback.print_exc()
            await interaction.followup.send(
                "❌ Fehler beim Verbinden mit dem Server. Bitte kontaktiere einen Admin.",
                ephemeral=True,
            )
            return

        await update_list_message()
        await interaction.followup.send(
            f"✅ **{name}** wurde entfernt.\nDu kannst dich jetzt im Whitelist-Kanal neu eintragen.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Spieler entfernen",
        style=discord.ButtonStyle.secondary,
        emoji="🛠️",
        custom_id="whitelist_admin_remove",
    )
    async def admin_remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Dieser Button ist nur für Admins. "
                "Deinen eigenen Eintrag entfernst du mit dem roten Button.",
                ephemeral=True,
            )
            return

        whitelisted = load_whitelisted()
        if not whitelisted:
            await interaction.response.send_message(
                "Die Whitelist ist leer.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Wen möchtest du entfernen?",
            view=AdminRemoveView(whitelisted, interaction.guild),
            ephemeral=True,
        )


# ------------------------------------------------------------------ Eintragen


class WhitelistModal(discord.ui.Modal, title="🔮 Whitelist"):
    minecraft_name = discord.ui.TextInput(
        label="Dein Minecraft Benutzername",
        placeholder="z.B. Notch",
        min_length=3,
        max_length=16,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        name = self.minecraft_name.value.strip()
        whitelisted = load_whitelisted()
        user_id = str(interaction.user.id)

        if user_id in whitelisted:
            await interaction.response.send_message(
                f"❌ Du bist bereits als **{whitelisted[user_id]}** gewhitelistet!\n"
                "Falls der Name falsch ist: entferne deinen Eintrag über den Button "
                "in der Spielerliste und trage dich neu ein.",
                ephemeral=True,
            )
            return

        # Minecraft-Name validieren
        clean = name.replace("_", "")
        if not clean.isalnum():
            await interaction.response.send_message(
                "❌ Ungültiger Minecraft Name!\nNur Buchstaben, Zahlen und `_` erlaubt.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Minecraft-Whitelist per RCON — schlägt das fehl, brechen wir ab
        try:
            rcon_command(f"whitelist add {name}")
        except Exception:
            traceback.print_exc()
            await interaction.followup.send(
                "❌ Fehler beim Verbinden mit dem Server. Bitte kontaktiere einen Admin.",
                ephemeral=True,
            )
            return

        whitelisted[user_id] = name
        save_whitelisted(whitelisted)

        # Rolle vergeben — scheitert das (z.B. Rollen-Hierarchie), läuft der Rest trotzdem weiter
        role = interaction.guild.get_role(WHITELIST_ROLE_ID)
        role_hint = ""
        if role is None:
            role_hint = "\n⚠️ Rolle nicht gefunden — prüfe `WHITELIST_ROLE_ID`."
            print(f"Rolle {WHITELIST_ROLE_ID} existiert nicht auf diesem Server")
        else:
            try:
                await interaction.user.add_roles(role)
            except Exception:
                traceback.print_exc()
                role_hint = (
                    f"\n⚠️ Die Rolle **{role.name}** konnte nicht vergeben werden — "
                    "die Bot-Rolle muss in den Servereinstellungen darüber stehen."
                )

        await interaction.followup.send(
            f"✅ **{name}** wurde erfolgreich zur Whitelist hinzugefügt!\n"
            "Du kannst jetzt dem Server beitreten." + role_hint,
            ephemeral=True,
        )

        log = discord.Embed(
            description=f"✅ {interaction.user.mention} (`{interaction.user}`) wurde als **{name}** gewhitelistet",
            color=0x2ECC71,
        )
        log.set_footer(text=f"Discord ID: {interaction.user.id}")
        await send_admin_log(log)

        await update_list_message()


class WhitelistButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Whitelisten",
        style=discord.ButtonStyle.primary,
        emoji="🔮",
        custom_id="whitelist_button",
    )
    async def whitelist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WhitelistModal())


def build_instructions_embed():
    embed = discord.Embed(
        title="🔮 Whitelist",
        description="Um dem Minecraft Server beizutreten, whiteliste dich einmalig über den Button unten.",
        color=0x9B59B6,
    )
    embed.add_field(
        name="Anleitung",
        value=(
            "1. Klicke auf den **Whitelisten** Button\n"
            "2. Gib deinen **exakten** Minecraft-Benutzernamen ein\n"
            "3. Du wirst automatisch gewhitelistet und bekommst die Rolle\n"
            "4. Vertippt? Entferne deinen Eintrag in der Spielerliste und trage dich neu ein"
        ),
        inline=False,
    )
    embed.set_footer(text="🔮 | Bei Problemen wende dich an einen Admin")
    return embed


async def ensure_instructions(channel):
    await channel.purge(limit=100)
    msg = await channel.send(embed=build_instructions_embed(), view=WhitelistButton())
    await msg.pin()


@bot.event
async def on_ready():
    bot.add_view(WhitelistButton())
    bot.add_view(ListView())
    await bot.tree.sync()
    print(f"🔮 Bot ist online als {bot.user}")

    channel = bot.get_channel(WHITELIST_CHANNEL_ID)
    if channel:
        bot_pin = False
        async for message in channel.pins():
            if message.author == bot.user:
                bot_pin = True
                break
        if not bot_pin:
            await ensure_instructions(channel)

    await update_list_message()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in (WHITELIST_CHANNEL_ID, WHITELIST_LIST_CHANNEL_ID):
        await message.delete()
        return

    await bot.process_commands(message)


@bot.tree.command(name="whitelist-entfernen", description="Entfernt einen Spieler von der Whitelist (nur Admin)")
@app_commands.describe(minecraft_name="Minecraft Benutzername der entfernt werden soll")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_remove(interaction: discord.Interaction, minecraft_name: str):
    await interaction.response.defer(ephemeral=True)

    user_id = next(
        (uid for uid, name in load_whitelisted().items() if name.lower() == minecraft_name.lower()),
        None,
    )
    if user_id is None:
        await interaction.followup.send(
            f"❌ **{minecraft_name}** steht nicht auf der Whitelist.", ephemeral=True
        )
        return

    try:
        name = await remove_entry(interaction.guild, user_id, interaction.user)
    except Exception:
        traceback.print_exc()
        await interaction.followup.send(
            "❌ Fehler beim Entfernen von der Whitelist.", ephemeral=True
        )
        return

    await update_list_message()
    await interaction.followup.send(
        f"✅ **{name}** wurde von der Whitelist entfernt.", ephemeral=True
    )


@bot.tree.command(name="whitelist-liste", description="Zeigt alle gewhitelisteten Spieler (nur Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_list(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_list_embed(), ephemeral=True)


bot.run(DISCORD_TOKEN)
