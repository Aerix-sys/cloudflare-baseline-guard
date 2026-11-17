let examples = null;
let report = "";
const $ = (selector) => document.querySelector(selector);

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
  $("#summary-title").textContent = healthy ? "Пример соответствует политике" : "В примере есть слабые места";
  $("#summary-description").textContent = "Результат рассчитан заранее на открытых демонстрационных данных, без обращения к Cloudflare API.";
  $("#source-label").textContent = `Источник: ${data.source}`;
  $("#check-list").replaceChildren(...data.checks.map(makeCheck));
  $("#checks").scrollIntoView({behavior: "smooth", block: "start"});
}

async function initialize() {
  try {
    const response = await fetch("./data.json", {cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось загрузить примеры");
    examples = await response.json();
  } catch (error) {
    showError(error.message);
  }
}

document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => {
  const result = examples?.[button.dataset.mode];
  if (!result) return showError("Пример пока не загружен. Обновите страницу.");
  render(result);
}));
$("#download").addEventListener("click", () => {
  if (!report) return;
  const url = URL.createObjectURL(new Blob([report], {type: "text/markdown;charset=utf-8"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "cloudflare-demo-report.md";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
initialize();
