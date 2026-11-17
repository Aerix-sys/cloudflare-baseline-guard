let csrf = "";
let report = "";
const $ = (selector) => document.querySelector(selector);

async function initialize() {
  try {
    const response = await fetch("/api/status", {cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось проверить состояние приложения");
    const status = await response.json();
    csrf = status.csrf;
    const liveButton = $('[data-mode="live"]');
    liveButton.disabled = !status.live_ready;
    $("#live-tag").textContent = status.live_ready ? "готова" : "не подключена";
  } catch (error) {
    showError(error.message);
  }
}

function showError(message) {
  $("#error").textContent = message;
  $("#error").hidden = false;
}

function makeCheck(check) {
  const row = document.createElement("article");
  row.className = "check-row";
  const icon = document.createElement("div");
  icon.className = `check-icon ${check.status === "PASS" ? "pass" : "fail"}`;
  icon.textContent = check.status === "PASS" ? "✓" : "!";
  const details = document.createElement("div");
  details.className = "check-details";
  const title = document.createElement("strong");
  title.textContent = check.check;
  const setting = document.createElement("small");
  setting.textContent = check.setting;
  details.append(title, setting);
  const value = document.createElement("div");
  value.className = "check-value";
  const actual = document.createElement("strong");
  actual.textContent = String(check.actual);
  const expected = document.createElement("small");
  expected.textContent = `Ожидается: ${check.expected}`;
  value.append(actual, expected);
  const badge = document.createElement("span");
  badge.className = `row-badge ${check.status === "PASS" ? "pass" : "fail"}`;
  badge.textContent = check.status === "PASS" ? "ПРОЙДЕНО" : "ТРЕБУЕТ ВНИМАНИЯ";
  row.append(icon, details, value, badge);
  return row;
}

function render(data) {
  report = data.report;
  $("#empty").hidden = true;
  $("#error").hidden = true;
  $("#result-content").hidden = false;
  $("#download").disabled = false;
  $("#score-number").textContent = data.passed;
  $("#score-total").textContent = data.total;
  const healthy = data.passed === data.total;
  $("#summary-badge").textContent = healthy ? "ВСЁ В ПОРЯДКЕ" : `${data.total - data.passed} ОТКЛОНЕНИЯ`;
  $("#summary-badge").className = `badge ${healthy ? "healthy" : "attention"}`;
  $("#summary-title").textContent = healthy ? "Выбранная политика соблюдена" : "Есть настройки, требующие внимания";
  $("#summary-description").textContent = healthy ? "Все проверяемые параметры соответствуют выбранной политике безопасности." : "Посмотрите фактические значения ниже и оцените изменения для вашей зоны.";
  $("#source-label").textContent = `Источник: ${data.source}`;
  $("#check-list").replaceChildren(...data.checks.map(makeCheck));
  $("#checks").scrollIntoView({behavior: "smooth", block: "start"});
}

async function run(mode) {
  if (!csrf) return showError("Приложение не готово. Обновите страницу.");
  document.querySelectorAll("[data-mode]").forEach((button) => button.disabled = true);
  $("#error").hidden = true;
  try {
    const response = await fetch("/api/audit", {method: "POST", headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf}, body: JSON.stringify({mode})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Проверка не выполнена");
    render(data);
  } catch (error) {
    showError(error.message);
  } finally {
    document.querySelectorAll("[data-mode]").forEach((button) => {button.disabled = button.dataset.mode === "live" && $("#live-tag").textContent !== "готова";});
  }
}

document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => run(button.dataset.mode)));
$("#download").addEventListener("click", () => {
  if (!report) return;
  const url = URL.createObjectURL(new Blob([report], {type: "text/markdown;charset=utf-8"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "cloudflare-baseline-report.md";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
initialize();
