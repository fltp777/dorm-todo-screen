(function createAuthStore(global) {
  "use strict";

  class AuthStoreError extends Error {
    constructor(message, publicMessage) {
      super(message);
      this.name = "AuthStoreError";
      this.publicMessage = publicMessage;
    }
  }

  async function getSession() {
    const { data, error } = await global.getSupabaseClient().auth.getSession();

    if (error) {
      throw new AuthStoreError(error.message, "暂时无法检查登录状态");
    }

    return data.session;
  }

  async function signIn(email, password) {
    const { data, error } = await global.getSupabaseClient().auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw new AuthStoreError(error.message, "邮箱或密码不正确");
    }

    return data.session;
  }

  async function signOut() {
    const { error } = await global.getSupabaseClient().auth.signOut({ scope: "local" });

    if (error) {
      throw new AuthStoreError(error.message, "退出失败，请重试");
    }
  }

  function onAuthStateChange(callback) {
    const { data } = global.getSupabaseClient().auth.onAuthStateChange(callback);
    return data.subscription;
  }

  global.authStore = Object.freeze({ getSession, signIn, signOut, onAuthStateChange });
})(window);
