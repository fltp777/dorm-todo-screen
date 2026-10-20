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
      dailyReminderText: typeof row.daily_reminder_text === "string" ? row.daily_reminder_text : "",
      yijingPosition: Number.isInteger(row.yijing_position) && row.yijing_position >= 0 ? row.yijing_position : 0,
      updatedAt: row.updated_at,
    };
  }

  async function loadScreen() {
    const { data, error } = await global
      .getSupabaseClient()
      .from(TABLE_NAME)
      .select("text, daily_reminder_text, yijing_position, updated_at")
      .eq("id", SCREEN_ID)
      .single();

    if (error) {
      throw new ScreenStoreError(error.message, "暂时无法读取屏幕内容");
    }

    return normalizeRow(data);
  }

  function assertScreenState(state) {
    if (!state || typeof state.text !== "string" || typeof state.dailyReminderText !== "string") {
      throw new TypeError("Screen state must contain text fields.");
    }
    if (!Number.isInteger(state.yijingPosition) || state.yijingPosition < 0) {
      throw new TypeError("Yijing position must be a non-negative integer.");
    }
  }

  async function saveScreen(state) {
    assertScreenState(state);

    const { data, error } = await global
      .getSupabaseClient()
      .from(TABLE_NAME)
      .update({
        text: state.text,
        daily_reminder_text: state.dailyReminderText,
        yijing_position: state.yijingPosition,
      })
      .eq("id", SCREEN_ID)
      .select("text, daily_reminder_text, yijing_position, updated_at")
      .single();

    if (error) {
      throw new ScreenStoreError(error.message, "同步失败，请重试");
    }

    return normalizeRow(data);
  }

  global.screenStore = Object.freeze({ loadScreen, saveScreen });
})(window);
