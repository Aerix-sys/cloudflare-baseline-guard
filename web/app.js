let csrf = "";
let report = "";
const $ = (selector) => document.querySelector(selector);

async function initialize() {
  try {
    const response = await fetch("/api/status", {cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось проверить состояние приложения");
    const status = await response.json();
    csrf = status.csrf;
    document.querySelectorAll('[data-mode="live"], [data-mode="live_ddos"]').forEach((button) => button.disabled = !status.live_ready);
    $("#live-tag").textContent = status.live_ready ? "готова" : "не подключена";
    $("#ddos-live-tag").textContent = status.live_ready ? "готова" : "не подключена";
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
  const state = check.status === "PASS" ? "pass" : check.status === "FAIL" ? "fail" : "unknown";
  icon.className = `check-icon ${state}`;
  icon.textContent = check.status === "PASS" ? "✓" : check.status === "FAIL" ? "!" : "?";
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
  badge.className = `row-badge ${state}`;
  badge.textContent = check.status === "PASS" ? "ПРОЙДЕНО" : check.status === "FAIL" ? "ПРОБЛЕМА" : check.status === "WARN" ? "РЕКОМЕНДАЦИЯ" : "НЕТ ДАННЫХ";
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
  $("#summary-badge").textContent = healthy ? "ВСЁ В ПОРЯДКЕ" : `${data.total - data.passed} ТРЕБУЮТ ПРОВЕРКИ`;
  $("#summary-badge").className = `badge ${healthy ? "healthy" : "attention"}`;
  $("#summary-title").textContent = healthy ? "Выбранная политика соблюдена" : "Есть настройки, требующие внимания";
  $("#summary-description").textContent = healthy ? "Все проверяемые параметры соответствуют выбранной политике безопасности." : "Посмотрите проблемы, рекомендации и пункты без данных ниже.";
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
    document.querySelectorAll("[data-mode]").forEach((button) => {button.disabled = ["live", "live_ddos"].includes(button.dataset.mode) && $("#live-tag").textContent !== "готова";});
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
