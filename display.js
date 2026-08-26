const POLL_INTERVAL_MS = 10_000;

const screenContent = document.querySelector("#screen-content");
const screenUpdatedAt = document.querySelector("#screen-updated-at");

let lastRenderedState = null;
let hasSuccessfulLoad = false;
let requestInProgress = false;

function formatTime(isoTime) {
  if (!isoTime) return "";

  const date = new Date(isoTime);
  if (Number.isNaN(date.getTime())) return "";

  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function renderScreen(screen) {
  const nextState = `${screen.text}\u0000${screen.updatedAt ?? ""}`;
  if (nextState === lastRenderedState) return;

  screenContent.textContent = screen.text === "" ? "暂无内容" : screen.text;
  screenContent.classList.toggle("is-empty", screen.text === "");

  const formattedTime = formatTime(screen.updatedAt);
  screenUpdatedAt.textContent = formattedTime ? `更新于 ${formattedTime}` : "";
  lastRenderedState = nextState;
}

function renderInitialError(error) {
  screenContent.textContent = error.publicMessage || "暂时无法读取屏幕内容";
  screenContent.classList.add("is-empty");
  screenUpdatedAt.textContent = "";
}

async function refreshScreen() {
  if (requestInProgress) return;
  requestInProgress = true;

  try {
    const screen = await window.screenStore.loadScreen();
    renderScreen(screen);
    hasSuccessfulLoad = true;
  } catch (error) {
    console.error("刷新屏幕内容失败：", error);
    if (!hasSuccessfulLoad) renderInitialError(error);
  } finally {
    requestInProgress = false;
  }
}

async function initializeDisplay() {
  const session = await window.authGuard.requireSession("display.html");
  if (!session) return;

  window.authGuard.revealPage();
  await refreshScreen();
  window.setInterval(refreshScreen, POLL_INTERVAL_MS);
}

initializeDisplay();
