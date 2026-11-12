package org.bukkit.entity;
public interface Player {
    boolean isOnline();
    boolean hasPermission(String name);
    java.util.UUID getUniqueId();
    String getName();
    void kickPlayer(String message);
    java.util.Set<String> getListeningPluginChannels();
}
