package org.bukkit.plugin.java;
public abstract class JavaPlugin implements org.bukkit.plugin.Plugin {
    public void onEnable() {}
    public java.util.logging.Logger getLogger() { throw new UnsupportedOperationException(); }
}
