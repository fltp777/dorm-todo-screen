(function createSharedSupabaseClient(global) {
  "use strict";

  let client;

  class SupabaseClientError extends Error {
    constructor(message, publicMessage) {
      super(message);
      this.name = "SupabaseClientError";
      this.publicMessage = publicMessage;
    }
  }

  function isLegacyServiceRoleKey(key) {
    if (!key.startsWith("eyJ")) return false;

    try {
      const payload = key.split(".")[1];
      const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
      const normalized = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
      const decoded = JSON.parse(global.atob(normalized));
      return decoded.role === "service_role";
    } catch {
      return false;
    }
  }

  function getConfig() {
    const config = global.SUPABASE_CONFIG;
    const url = config?.url?.trim();
    const publishableKey = config?.publishableKey?.trim();

    if (
      !url ||
      !publishableKey ||
      url === "YOUR_SUPABASE_URL" ||
      publishableKey === "YOUR_SUPABASE_PUBLISHABLE_KEY"
    ) {
      throw new SupabaseClientError("Supabase configuration is missing.", "请先配置 Supabase");
    }

    if (publishableKey.startsWith("sb_secret_") || isLegacyServiceRoleKey(publishableKey)) {
      throw new SupabaseClientError(
        "A secret or service_role key cannot be used in browser code.",
        "配置错误：请使用 publishable key",
      );
    }

    return { url, publishableKey };
  }

  function getSupabaseClient() {
    if (client) return client;

    const { url, publishableKey } = getConfig();

    if (!global.supabase?.createClient) {
      throw new SupabaseClientError("Supabase browser library failed to load.", "无法加载云同步组件");
    }

    // Supabase JS 浏览器 client 默认持久化并自动刷新 session。
    client = global.supabase.createClient(url, publishableKey);
    return client;
  }

  global.getSupabaseClient = getSupabaseClient;
})(window);
