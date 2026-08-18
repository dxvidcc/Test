import asyncio
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

# Kanal für das Admin-Panel. Ohne eigenen Eintrag landet es im Admin-Log-Kanal.
ADMIN_PANEL_CHANNEL_ID = int(
    os.getenv("ADMIN_PANEL_CHANNEL_ID") or ADMIN_LOG_CHANNEL_ID
)

# TEST_MODE=true → RCON wird übersprungen, alles andere funktioniert normal
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

WHITELIST_FILE = "whitelisted.json"
LIST_STATE_FILE = "list_message.json"
INSTRUCTIONS_STATE_FILE = "instructions_message.json"
PANEL_STATE_FILE = "panel_message.json"
DIMENSIONS_FILE = "dimensions.json"

# Dimensionen, die das Panel schalten kann — Schlüssel muss zur Permission passen.
DIMENSIONS = {
    "nether": {"label": "Nether", "caps": "ɴᴇᴛʜᴇʀ"},
    "end": {"label": "End", "caps": "ᴇɴᴅ"},
}

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


def schedule_delete(interaction, delay=20):
    """Räumt die private Antwort des Bots nach `delay` Sekunden weg."""

    async def _delete():
        await asyncio.sleep(delay)
        try:
            await interaction.delete_original_response()
        except discord.HTTPException:
            pass  # User hat sie selbst verworfen oder sie ist abgelaufen

    asyncio.create_task(_delete())


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
            "Klicke **Mein Eintrag** — dort siehst du deinen eigenen Namen und "
            "kannst ihn entfernen. Danach trägst du dich im Whitelist-Kanal neu ein."
        ),
        inline=False,
    )
    embed.set_footer(text=f"{len(whitelisted)} Spieler gewhitelistet")
    return embed


async def fetch_tracked_message(channel, state_file):
    """Holt die gemerkte Bot-Nachricht, oder None wenn sie nicht mehr existiert."""
    state = _load_json(state_file, {})
    if state.get("channel_id") != channel.id or not state.get("message_id"):
        return None
    try:
        return await channel.fetch_message(state["message_id"])
    except discord.NotFound:
        return None
    except Exception:
        traceback.print_exc()
        return None


def save_tracked_message(state_file, channel, message):
    _save_json(state_file, {"channel_id": channel.id, "message_id": message.id})


async def update_list_message():
    channel = bot.get_channel(WHITELIST_LIST_CHANNEL_ID)
    if channel is None:
        print(f"Listen-Kanal {WHITELIST_LIST_CHANNEL_ID} nicht gefunden")
        return

    message = await fetch_tracked_message(channel, LIST_STATE_FILE)
    embed = build_list_embed()
    try:
        if message:
            await message.edit(embed=embed, view=ListView())
        else:
            message = await channel.send(embed=embed, view=ListView())
            save_tracked_message(LIST_STATE_FILE, channel, message)
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
        await interaction.response.defer()

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
        await close_panel(interaction, "\n".join(parts) or "Nichts geändert.")


class EphemeralPanel(discord.ui.View):
    """Privates Panel, das sich nach Gebrauch bzw. bei Nichtbenutzung selbst entfernt."""

    def __init__(self, origin, timeout=120):
        super().__init__(timeout=timeout)
        self.origin = origin

    async def on_timeout(self):
        try:
            await self.origin.delete_original_response()
        except discord.HTTPException:
            pass


async def close_panel(interaction, text, delay=20):
    """Ersetzt das Panel durch das Ergebnis und räumt es danach weg."""
    try:
        await interaction.edit_original_response(content=text, embed=None, view=None)
    except discord.HTTPException:
        traceback.print_exc()  # Panel schon weg — die Aktion selbst ist trotzdem gelaufen
        return
    schedule_delete(interaction, delay)


class AdminRemoveView(EphemeralPanel):
    def __init__(self, whitelisted, guild, origin):
        super().__init__(origin)
        self.add_item(AdminRemoveSelect(whitelisted, guild))


class MyEntryView(EphemeralPanel):
    """Private Ansicht des eigenen Eintrags mit Entfernen-Button."""

    def __init__(self, name, origin):
        super().__init__(origin)
        self.name = name

    @discord.ui.button(
        label="Von der Whitelist entfernen",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
    )
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            name = await remove_entry(
                interaction.guild, str(interaction.user.id), interaction.user
            )
        except Exception:
            traceback.print_exc()
            await close_panel(
                interaction,
                "❌ Fehler beim Verbinden mit dem Server. Bitte kontaktiere einen Admin.",
            )
            return

        if name is None:
            await close_panel(
                interaction, "Dein Eintrag wurde zwischenzeitlich bereits entfernt."
            )
            return

        await update_list_message()
        await close_panel(
            interaction,
            f"✅ **{name}** wurde entfernt.\nDu kannst dich jetzt im Whitelist-Kanal neu eintragen.",
        )


class ListView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Mein Eintrag",
        style=discord.ButtonStyle.primary,
        emoji="👤",
        custom_id="whitelist_my_entry",
    )
    async def my_entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        name = load_whitelisted().get(str(interaction.user.id))

        if name is None:
            await interaction.response.send_message(
                "Du bist aktuell **nicht** gewhitelistet.\n"
                "Trage dich im Whitelist-Kanal über den 🔮 Button ein.",
                ephemeral=True,
            )
            schedule_delete(interaction)
            return

        embed = discord.Embed(
            title="👤 Dein Eintrag",
            description=f"Du bist als **{name}** gewhitelistet.",
            color=0x9B59B6,
        )
        embed.set_footer(text="Falscher Name? Entfernen und im Whitelist-Kanal neu eintragen.")
        await interaction.response.send_message(
            embed=embed, view=MyEntryView(name, interaction), ephemeral=True
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
                "Deinen eigenen Eintrag entfernst du über **Mein Eintrag**.",
                ephemeral=True,
            )
            schedule_delete(interaction)
            return

        whitelisted = load_whitelisted()
        if not whitelisted:
            await interaction.response.send_message(
                "Die Whitelist ist leer.", ephemeral=True
            )
            schedule_delete(interaction)
            return

        await interaction.response.send_message(
            "Wen möchtest du entfernen?",
            view=AdminRemoveView(whitelisted, interaction.guild, interaction),
            ephemeral=True,
        )


# --------------------------------------------------------------- Admin-Panel


def load_dimensions():
    """Gemerkter Zustand der Dimensionen. Standard: alles gesperrt."""
    stored = _load_json(DIMENSIONS_FILE, {})
    return {key: bool(stored.get(key, False)) for key in DIMENSIONS}


def set_dimension(key, unlocked):
    """Schaltet eine Dimension für die Gruppe `default` frei oder sperrt sie."""
    node = f"dimensionaccess.access.{key}"
    if unlocked:
        rcon_command(f"lp group default permission set {node} true")
    else:
        rcon_command(f"lp group default permission unset {node}")

    state = load_dimensions()
    state[key] = unlocked
    _save_json(DIMENSIONS_FILE, state)


def get_online_players():
    """Namen der aktuell verbundenen Spieler, aus der Antwort von `list`."""
    response = rcon_command("list") or ""
    if ":" not in response:
        return []
    names = response.split(":", 1)[1]
    return [name.strip() for name in names.split(",") if name.strip()]


def build_panel_embed(guild=None):
    state = load_dimensions()

    try:
        players = get_online_players()
        online = f"👥 {len(players)}" + (f"\n{', '.join(players[:5])}" if players else "\nniemand")
    except Exception:
        traceback.print_exc()
        online = "👥 —\nnicht erreichbar"

    embed = discord.Embed(title="ᴀᴅᴍɪɴ-ᴘᴀɴᴇʟ", color=0x9D4EDD)
    if guild and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    for key, meta in DIMENSIONS.items():
        embed.add_field(
            name=meta["caps"],
            value="🟢 offen" if state[key] else "🔴 gesperrt",
            inline=True,
        )
    embed.add_field(name="ᴏɴʟɪɴᴇ", value=online, inline=True)

    embed.set_footer(text=f"{RCON_HOST}:25565")
    embed.timestamp = discord.utils.utcnow()
    return embed


async def update_panel_message():
    channel = bot.get_channel(ADMIN_PANEL_CHANNEL_ID)
    if channel is None:
        print(f"Admin-Panel-Kanal {ADMIN_PANEL_CHANNEL_ID} nicht gefunden")
        return

    message = await fetch_tracked_message(channel, PANEL_STATE_FILE)
    embed = build_panel_embed(channel.guild)
    try:
        if message:
            await message.edit(embed=embed, view=AdminPanelView())
        else:
            message = await channel.send(embed=embed, view=AdminPanelView())
            save_tracked_message(PANEL_STATE_FILE, channel, message)
    except Exception:
        traceback.print_exc()


async def deny_non_admin(interaction):
    """True wenn abgelehnt wurde — dann ist die Interaktion bereits beantwortet."""
    if interaction.user.guild_permissions.administrator:
        return False
    await interaction.response.send_message(
        "❌ Das Admin-Panel ist nur für Admins.", ephemeral=True
    )
    schedule_delete(interaction)
    return True


class KickSelect(discord.ui.Select):
    def __init__(self, players):
        super().__init__(
            placeholder="Spieler auswählen…",
            options=[discord.SelectOption(label=name) for name in players[:25]],
            min_values=1,
            max_values=min(len(players), 25),
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        kicked, failed = [], []
        for name in self.values:
            try:
                rcon_command(f"kick {name} Vom Server entfernt")
                kicked.append(name)
            except Exception:
                traceback.print_exc()
                failed.append(name)

        if kicked:
            await send_admin_log(
                discord.Embed(
                    description=f"👢 {interaction.user.mention} hat gekickt: "
                    + ", ".join(f"**{n}**" for n in kicked),
                    color=0xE67E22,
                )
            )

        parts = []
        if kicked:
            parts.append("✅ Gekickt: " + ", ".join(f"**{n}**" for n in kicked))
        if failed:
            parts.append("❌ Fehlgeschlagen: " + ", ".join(failed))
        await close_panel(interaction, "\n".join(parts) or "Nichts geändert.")


class KickView(EphemeralPanel):
    def __init__(self, players, origin):
        super().__init__(origin)
        self.add_item(KickSelect(players))


class BanModal(discord.ui.Modal, title="🔨 Spieler bannen"):
    player = discord.ui.TextInput(label="Minecraft Name", max_length=16)
    reason = discord.ui.TextInput(
        label="Grund",
        required=False,
        placeholder="optional",
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        name = self.player.value.strip()
        reason = self.reason.value.strip() or "Gebannt"
        try:
            rcon_command(f"ban {name} {reason}")
        except Exception:
            traceback.print_exc()
            await close_panel(
                interaction, "❌ Fehler beim Verbinden mit dem Server."
            )
            return

        await send_admin_log(
            discord.Embed(
                description=f"🔨 {interaction.user.mention} hat **{name}** gebannt — {reason}",
                color=0xE74C3C,
            )
        )
        await close_panel(interaction, f"✅ **{name}** wurde gebannt.")


class UnbanModal(discord.ui.Modal, title="♻️ Bann aufheben"):
    player = discord.ui.TextInput(label="Minecraft Name", max_length=16)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        name = self.player.value.strip()
        try:
            rcon_command(f"pardon {name}")
        except Exception:
            traceback.print_exc()
            await close_panel(
                interaction, "❌ Fehler beim Verbinden mit dem Server."
            )
            return

        await send_admin_log(
            discord.Embed(
                description=f"♻️ {interaction.user.mention} hat den Bann von **{name}** aufgehoben",
                color=0x2ECC71,
            )
        )
        await close_panel(interaction, f"✅ Bann von **{name}** aufgehoben.")


class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle(self, interaction, key):
        if await deny_non_admin(interaction):
            return

        await interaction.response.defer()
        unlocked = not load_dimensions()[key]
        try:
            set_dimension(key, unlocked)
        except Exception:
            traceback.print_exc()
            await interaction.followup.send(
                "❌ Fehler beim Verbinden mit dem Server.", ephemeral=True
            )
            return

        label = DIMENSIONS[key]["label"]
        await send_admin_log(
            discord.Embed(
                description=f"{'🟢' if unlocked else '🔴'} {interaction.user.mention} hat "
                f"**{label}** {'geöffnet' if unlocked else 'gesperrt'}",
                color=0x2ECC71 if unlocked else 0xE74C3C,
            )
        )
        await update_panel_message()

    @discord.ui.button(label="Nether", style=discord.ButtonStyle.secondary, custom_id="panel_toggle_nether")
    async def toggle_nether(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "nether")

    @discord.ui.button(label="End", style=discord.ButtonStyle.secondary, custom_id="panel_toggle_end")
    async def toggle_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle(interaction, "end")

    @discord.ui.button(label="Kicken", style=discord.ButtonStyle.primary, custom_id="panel_kick")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await deny_non_admin(interaction):
            return

        try:
            players = get_online_players()
        except Exception:
            traceback.print_exc()
            await interaction.response.send_message(
                "❌ Fehler beim Verbinden mit dem Server.", ephemeral=True
            )
            schedule_delete(interaction)
            return

        if not players:
            await interaction.response.send_message(
                "Gerade ist niemand online.", ephemeral=True
            )
            schedule_delete(interaction)
            return

        await interaction.response.send_message(
            "Wen möchtest du kicken?",
            view=KickView(players, interaction),
            ephemeral=True,
        )

    @discord.ui.button(label="Bannen", style=discord.ButtonStyle.danger, custom_id="panel_ban")
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await deny_non_admin(interaction):
            return
        await interaction.response.send_modal(BanModal())

    @discord.ui.button(label="Entbannen", style=discord.ButtonStyle.success, custom_id="panel_unban")
    async def unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await deny_non_admin(interaction):
            return
        await interaction.response.send_modal(UnbanModal())


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
                "Falls der Name falsch ist: entferne deinen Eintrag über **Mein Eintrag** "
                "in der Spielerliste und trage dich neu ein.",
                ephemeral=True,
            )
            schedule_delete(interaction)
            return

        # Minecraft-Name validieren
        clean = name.replace("_", "")
        if not clean.isalnum():
            await interaction.response.send_message(
                "❌ Ungültiger Minecraft Name!\nNur Buchstaben, Zahlen und `_` erlaubt.",
                ephemeral=True,
            )
            schedule_delete(interaction)
            return

        # thinking=True ist Pflicht: ohne das quittiert discord.py einen Modal-Submit
        # als Update der Nachricht, an der der Button hängt — die Antwort würde dann
        # die öffentliche Anleitung überschreiben statt ein eigenes Fenster zu öffnen.
        await interaction.response.defer(ephemeral=True, thinking=True)

        # Minecraft-Whitelist per RCON — schlägt das fehl, brechen wir ab
        try:
            rcon_command(f"whitelist add {name}")
        except Exception:
            traceback.print_exc()
            await close_panel(
                interaction,
                "❌ Fehler beim Verbinden mit dem Server. Bitte kontaktiere einen Admin.",
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

        await close_panel(
            interaction,
            f"✅ **{name}** wurde erfolgreich zur Whitelist hinzugefügt!\n"
            "Du kannst jetzt dem Server beitreten." + role_hint,
            delay=30,
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


async def ensure_instructions():
    """Hält genau eine Anleitungs-Nachricht im Whitelist-Kanal aktuell."""
    channel = bot.get_channel(WHITELIST_CHANNEL_ID)
    if channel is None:
        print(f"Whitelist-Kanal {WHITELIST_CHANNEL_ID} nicht gefunden")
        return

    message = await fetch_tracked_message(channel, INSTRUCTIONS_STATE_FILE)
    embed = build_instructions_embed()
    try:
        if message:
            await message.edit(embed=embed, view=WhitelistButton())
            return

        message = await channel.send(embed=embed, view=WhitelistButton())
        save_tracked_message(INSTRUCTIONS_STATE_FILE, channel, message)
        try:
            await message.pin()
        except discord.HTTPException:
            traceback.print_exc()  # Anpinnen ist nur Komfort, kein Grund neu zu posten
    except Exception:
        traceback.print_exc()


@bot.event
async def on_ready():
    bot.add_view(WhitelistButton())
    bot.add_view(ListView())
    bot.add_view(AdminPanelView())
    await bot.tree.sync()
    print(f"🔮 Bot ist online als {bot.user}")

    await ensure_instructions()
    await update_list_message()
    await update_panel_message()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in (
        WHITELIST_CHANNEL_ID,
        WHITELIST_LIST_CHANNEL_ID,
        ADMIN_PANEL_CHANNEL_ID,
    ) and message.channel.id != ADMIN_LOG_CHANNEL_ID:
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
        await close_panel(
            interaction, f"❌ **{minecraft_name}** steht nicht auf der Whitelist."
        )
        return

    try:
        name = await remove_entry(interaction.guild, user_id, interaction.user)
    except Exception:
        traceback.print_exc()
        await close_panel(interaction, "❌ Fehler beim Entfernen von der Whitelist.")
        return

    await update_list_message()
    await close_panel(interaction, f"✅ **{name}** wurde von der Whitelist entfernt.")


@bot.tree.command(name="whitelist-liste", description="Zeigt alle gewhitelisteten Spieler (nur Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def whitelist_list(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_list_embed(), ephemeral=True)
    schedule_delete(interaction, 60)


bot.run(DISCORD_TOKEN)
