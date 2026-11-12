package de.mcserver.voicerequired;

import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import org.bukkit.Bukkit;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.event.player.PlayerRegisterChannelEvent;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * Kickt Spieler, die ohne die Simple-Voice-Chat-Mod joinen.
 *
 * Die Mod meldet beim Verbinden ihre Netzwerkkanäle ("voicechat:...") an. Kommt
 * innerhalb der Wartezeit keiner davon, fehlt die Mod. Wer die Berechtigung
 * voicerequired.bypass hat, darf auch ohne Mod spielen.
 */
public final class VoiceRequired extends JavaPlugin implements Listener {

    private static final String CHANNEL_PREFIX = "voicechat:";
    private static final String BYPASS_PERMISSION = "voicerequired.bypass";
    /** Die Kanäle kommen meist sofort, auf langsamen Verbindungen etwas später. */
    private static final long CHECK_DELAY_TICKS = 20L * 8;

    private static final String KICK_MESSAGE =
            "§cAuf diesem Server ist Voice-Chat Pflicht.\n\n"
            + "§fBitte installiere die Mod §eSimple Voice Chat §f(Fabric)\n"
            + "§fpassend zu deiner Minecraft-Version:\n"
            + "§bmodrinth.com/plugin/simple-voice-chat\n\n"
            + "§7Danach kannst du direkt wieder joinen.";

    /** Spieler, deren Client einen Voice-Chat-Kanal angemeldet hat. */
    private final Set<UUID> withVoiceChat = ConcurrentHashMap.newKeySet();

    @Override
    public void onEnable() {
        Bukkit.getPluginManager().registerEvents(this, this);
    }

    @EventHandler
    public void onRegisterChannel(PlayerRegisterChannelEvent event) {
        if (event.getChannel().startsWith(CHANNEL_PREFIX)) {
            withVoiceChat.add(event.getPlayer().getUniqueId());
        }
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        Player player = event.getPlayer();
        Bukkit.getScheduler().runTaskLater(this, () -> check(player), CHECK_DELAY_TICKS);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        withVoiceChat.remove(event.getPlayer().getUniqueId());
    }

    private void check(Player player) {
        if (!player.isOnline() || player.hasPermission(BYPASS_PERMISSION)) {
            return;
        }
        if (withVoiceChat.contains(player.getUniqueId()) || hasVoiceChannel(player)) {
            return;
        }
        getLogger().info(player.getName() + " hat Simple Voice Chat nicht installiert und wurde gekickt.");
        player.kickPlayer(KICK_MESSAGE);
    }

    /** Falls die Kanäle schon vor dem Join angemeldet wurden, ist das Event bereits vorbei. */
    private static boolean hasVoiceChannel(Player player) {
        for (String channel : player.getListeningPluginChannels()) {
            if (channel.startsWith(CHANNEL_PREFIX)) {
                return true;
            }
        }
        return false;
    }
}
