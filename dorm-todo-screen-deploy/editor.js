const textArea = document.querySelector("#todo-text");
const charCount = document.querySelector("#char-count");
const updateButton = document.querySelector("#update-button");
const logoutButton = document.querySelector("#logout-button");
const saveStatus = document.querySelector("#save-status");

let statusTimer;

function updateCharacterCount() {
  charCount.textContent = `${textArea.value.length} / ${textArea.maxLength}`;
}

function setStatus(message, type = "") {
  window.clearTimeout(statusTimer);
  saveStatus.textContent = message;
  saveStatus.className = "save-status";

  if (message) saveStatus.classList.add("is-visible");
  if (type) saveStatus.classList.add(`is-${type}`);
}

async function loadCurrentScreen() {
  updateButton.disabled = true;
  setStatus("正在连接…", "loading");

  try {
    const screen = await window.screenStore.loadScreen();
    textArea.value = screen.text;
    updateCharacterCount();
    setStatus("");
  } catch (error) {
    console.error("加载屏幕内容失败：", error);
    setStatus(error.publicMessage || "暂时无法读取屏幕内容", "error");
  } finally {
    updateButton.disabled = false;
  }
}

async function saveScreenContent() {
  updateButton.disabled = true;
  setStatus("正在更新…", "loading");

  try {
    await window.screenStore.saveScreen(textArea.value);
    setStatus("✓ 已同步", "success");
    statusTimer = window.setTimeout(() => setStatus(""), 2200);
  } catch (error) {
    console.error("同步屏幕内容失败：", error);
    setStatus(error.publicMessage || "同步失败，请重试", "error");
  } finally {
    updateButton.disabled = false;
  }
}

async function logOut() {
  logoutButton.disabled = true;

  try {
    await window.authStore.signOut();
    window.location.replace("login.html");
  } catch (error) {
    console.error("退出登录失败：", error);
    setStatus(error.publicMessage || "退出失败，请重试", "error");
    logoutButton.disabled = false;
  }
}

async function initializeEditor() {
  const session = await window.authGuard.requireSession("editor.html");
  if (!session) return;

  window.authGuard.revealPage();
  updateCharacterCount();
  await loadCurrentScreen();
}

textArea.addEventListener("input", updateCharacterCount);
updateButton.addEventListener("click", saveScreenContent);
logoutButton.addEventListener("click", logOut);

initializeEditor();
