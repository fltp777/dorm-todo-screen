const loginForm = document.querySelector("#login-form");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const loginButton = document.querySelector("#login-button");
const loginStatus = document.querySelector("#login-status");

const requestedNext = new URLSearchParams(window.location.search).get("next");
const nextPage = window.authGuard.getSafeNext(requestedNext);

function setLoginStatus(message, type = "") {
  loginStatus.textContent = message;
  loginStatus.className = "save-status";
  if (message) loginStatus.classList.add("is-visible");
  if (type) loginStatus.classList.add(`is-${type}`);
}

async function initializeLogin() {
  try {
    const session = await window.authStore.getSession();
    if (session) {
      window.location.replace(nextPage);
      return;
    }

    window.authGuard.revealPage();
    emailInput.focus();
  } catch (error) {
    console.error("初始化登录页失败：", error);
    window.authGuard.revealPage();
    setLoginStatus(error.publicMessage || "暂时无法检查登录状态", "error");
    loginButton.disabled = true;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginButton.disabled = true;
  setLoginStatus("正在登录…", "loading");

  try {
    await window.authStore.signIn(emailInput.value.trim(), passwordInput.value);
    window.location.replace(nextPage);
  } catch (error) {
    console.error("登录失败：", error);
    setLoginStatus("邮箱或密码不正确", "error");
    passwordInput.select();
    loginButton.disabled = false;
  }
});

initializeLogin();
