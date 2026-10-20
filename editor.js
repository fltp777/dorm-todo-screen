const textArea = document.querySelector("#todo-text");
const charCount = document.querySelector("#char-count");
const reminderTextArea = document.querySelector("#daily-reminder-text");
const reminderCharCount = document.querySelector("#reminder-char-count");
const updateButton = document.querySelector("#update-button");
const logoutButton = document.querySelector("#logout-button");
const saveStatus = document.querySelector("#save-status");
const previousYijingButton = document.querySelector("#yijing-previous-button");
const nextYijingButton = document.querySelector("#yijing-next-button");
const yijingCurrent = document.querySelector("#yijing-current");

let statusTimer;
let yijingPosition = 0;

function updateCharacterCount() {
  charCount.textContent = `${textArea.value.length} / ${textArea.maxLength}`;
  reminderCharCount.textContent = `${reminderTextArea.value.length} / ${reminderTextArea.maxLength}`;
}

function renderYijingPosition() {
  const page = window.yijingCatalog.pageAt(yijingPosition);
  yijingCurrent.textContent = `${yijingPosition + 1} / ${window.yijingCatalog.pages.length} · ${page.label}：${page.summary}`;
  previousYijingButton.disabled = yijingPosition === 0;
  nextYijingButton.disabled = yijingPosition === window.yijingCatalog.pages.length - 1;
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
    reminderTextArea.value = screen.dailyReminderText;
    yijingPosition = Math.min(screen.yijingPosition, window.yijingCatalog.pages.length - 1);
    updateCharacterCount();
    renderYijingPosition();
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
    await window.screenStore.saveScreen({
      text: textArea.value,
      dailyReminderText: reminderTextArea.value,
      yijingPosition,
    });
    setStatus("✓ 已同步", "success");
    statusTimer = window.setTimeout(() => setStatus(""), 2200);
  } catch (error) {
    console.error("同步屏幕内容失败：", error);
    setStatus(error.publicMessage || "同步失败，请重试", "error");
  } finally {
    updateButton.disabled = false;
  }
}

function moveYijingPosition(direction) {
  const nextPosition = yijingPosition + direction;
  if (nextPosition < 0 || nextPosition >= window.yijingCatalog.pages.length) return;
  yijingPosition = nextPosition;
  renderYijingPosition();
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

  try {
    setStatus("正在读取易经目录…", "loading");
    await window.yijingCatalog.load();
  } catch (error) {
    console.error("加载易经目录失败：", error);
    updateButton.disabled = true;
    previousYijingButton.disabled = true;
    nextYijingButton.disabled = true;
    setStatus("易经目录暂时无法读取", "error");
    return;
  }

  window.authGuard.revealPage();
  updateCharacterCount();
  renderYijingPosition();
  await loadCurrentScreen();
}

textArea.addEventListener("input", updateCharacterCount);
reminderTextArea.addEventListener("input", updateCharacterCount);
updateButton.addEventListener("click", saveScreenContent);
logoutButton.addEventListener("click", logOut);
previousYijingButton.addEventListener("click", () => moveYijingPosition(-1));
nextYijingButton.addEventListener("click", () => moveYijingPosition(1));

initializeEditor();
