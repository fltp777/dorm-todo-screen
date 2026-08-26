(function createAuthGuard(global) {
  "use strict";

  const ALLOWED_PAGES = new Set(["editor.html", "display.html"]);

  function getSafeNext(value) {
    return ALLOWED_PAGES.has(value) ? value : "editor.html";
  }

  function redirectToLogin(nextPage) {
    const safeNext = getSafeNext(nextPage);
    global.location.replace(`login.html?next=${encodeURIComponent(safeNext)}`);
  }

  async function requireSession(nextPage) {
    try {
      const session = await global.authStore.getSession();

      if (!session) {
        redirectToLogin(nextPage);
        return null;
      }

      global.authStore.onAuthStateChange((event) => {
        if (event === "SIGNED_OUT") redirectToLogin(nextPage);
      });

      return session;
    } catch (error) {
      console.error("检查登录状态失败：", error);
      redirectToLogin(nextPage);
      return null;
    }
  }

  function revealPage() {
    document.body.classList.remove("auth-pending");
  }

  global.authGuard = Object.freeze({ getSafeNext, requireSession, revealPage });
})(window);
