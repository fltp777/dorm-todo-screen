(function createScreenStore(global) {
  "use strict";

  const TABLE_NAME = "screen_state";
  const SCREEN_ID = "main";

  class ScreenStoreError extends Error {
    constructor(message, publicMessage) {
      super(message);
      this.name = "ScreenStoreError";
      this.publicMessage = publicMessage;
    }
  }

  function normalizeRow(row) {
    return {
      text: typeof row.text === "string" ? row.text : "",
      updatedAt: row.updated_at,
    };
  }

  async function loadScreen() {
    const { data, error } = await global
      .getSupabaseClient()
      .from(TABLE_NAME)
      .select("text, updated_at")
      .eq("id", SCREEN_ID)
      .single();

    if (error) {
      throw new ScreenStoreError(error.message, "暂时无法读取屏幕内容");
    }

    return normalizeRow(data);
  }

  async function saveScreen(text) {
    if (typeof text !== "string") {
      throw new TypeError("Screen text must be a string.");
    }

    const { data, error } = await global
      .getSupabaseClient()
      .from(TABLE_NAME)
      .update({ text })
      .eq("id", SCREEN_ID)
      .select("text, updated_at")
      .single();

    if (error) {
      throw new ScreenStoreError(error.message, "同步失败，请重试");
    }

    return normalizeRow(data);
  }

  global.screenStore = Object.freeze({ loadScreen, saveScreen });
})(window);
