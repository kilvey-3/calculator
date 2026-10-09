const expression = document.getElementById("expression");
const answer = document.getElementById("answer");
const screenLabel = document.getElementById("screenLabel");
const stepsPanel = document.getElementById("stepsPanel");
const steps = document.getElementById("steps");
const statsPanel = document.getElementById("statsPanel");
const statsGrid = document.getElementById("statsGrid");
const batchPanel = document.getElementById("batchPanel");
const batchResults = document.getElementById("batchResults");
const smartInfo = document.getElementById("smartInfo");
const historyPanel = document.getElementById("historyPanel");
const historyList = document.getElementById("historyList");
const toast = document.getElementById("toast");

let currentMode = "Smart";

function insertAtCursor(value) {
    const start = expression.selectionStart ?? expression.value.length;
    const end = expression.selectionEnd ?? expression.value.length;
    expression.value = expression.value.slice(0, start) + value + expression.value.slice(end);
    const cursor = start + value.length;
    expression.focus();
    expression.setSelectionRange(cursor, cursor);
}

function clearAll() {
    expression.value = "";
    answer.textContent = "0";
    stepsPanel.classList.add("hidden");
    statsPanel.classList.add("hidden");
    batchPanel.classList.add("hidden");
    expression.focus();
}

function backspace() {
    const start = expression.selectionStart ?? expression.value.length;
    const end = expression.selectionEnd ?? expression.value.length;
    if (start !== end) {
        expression.value = expression.value.slice(0, start) + expression.value.slice(end);
        expression.setSelectionRange(start, start);
    } else if (start > 0) {
        expression.value = expression.value.slice(0, start - 1) + expression.value.slice(start);
        expression.setSelectionRange(start - 1, start - 1);
    }
    expression.focus();
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 1500);
}

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll(".mode").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.mode === mode);
    });
    screenLabel.textContent = mode.toUpperCase() + " MODE";
    stepsPanel.classList.toggle("hidden", mode !== "Smart");
    statsPanel.classList.toggle("hidden", mode !== "Statistics");
    batchPanel.classList.toggle("hidden", mode !== "Batch");
    smartInfo.classList.toggle("hidden", mode !== "Smart");
    if (mode === "Statistics") {
        smartInfo.classList.remove("hidden");
        smartInfo.querySelector("strong").textContent = "STATISTICS";
        smartInfo.querySelector("span").textContent = "Enter many numbers separated by commas. Example: 10,20,30,40,50";
    } else if (mode === "Batch") {
        smartInfo.classList.remove("hidden");
        smartInfo.querySelector("strong").textContent = "BATCH CALCULATION";
        smartInfo.querySelector("span").textContent = "Enter multiple complete expressions separated by a new line or semicolon.";
    } else if (mode === "Scientific") {
        smartInfo.classList.remove("hidden");
        smartInfo.querySelector("strong").textContent = "SCIENTIFIC";
        smartInfo.querySelector("span").textContent = "Use the same single expression field for scientific functions.";
    } else {
        smartInfo.classList.remove("hidden");
        smartInfo.querySelector("strong").textContent = "SMART SOLVE";
        smartInfo.querySelector("span").textContent = "Enter one long expression and the calculator can also show a calculation breakdown.";
    }
    expression.focus();
}

async function calculate() {
    const value = expression.value.trim();
    if (!value) {
        answer.textContent = "0";
        showToast("Enter an expression first.");
        return;
    }

    answer.textContent = "...";
    try {
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({expression: value, mode: currentMode})
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Calculation failed.");
        }

        answer.textContent = data.result || "Done";
        steps.innerHTML = "";
        statsGrid.innerHTML = "";
        batchResults.innerHTML = "";

        if (currentMode === "Smart") {
            (data.steps || []).forEach(step => {
                const div = document.createElement("div");
                div.textContent = step;
                steps.appendChild(div);
            });
            stepsPanel.classList.remove("hidden");
        }

        if (currentMode === "Statistics") {
            const labels = {
                count: "Count", sum: "Sum", mean: "Mean", median: "Median",
                mode: "Mode", minimum: "Minimum", maximum: "Maximum",
                range: "Range", variance: "Variance", standard_deviation: "Std. Deviation"
            };
            Object.entries(data.statistics || {}).forEach(([key, val]) => {
                const card = document.createElement("div");
                card.className = "stat";
                card.innerHTML = `<span>${labels[key] || key}</span><strong>${Array.isArray(val) ? (val.length ? val.join(", ") : "No mode") : val}</strong>`;
                statsGrid.appendChild(card);
            });
            statsPanel.classList.remove("hidden");
        }

        if (currentMode === "Batch") {
            (data.batch || []).forEach(item => {
                const row = document.createElement("div");
                row.className = "batch-item";
                row.innerHTML = `<span>${item.expression}</span><strong>${item.result}</strong>`;
                batchResults.appendChild(row);
            });
            batchPanel.classList.remove("hidden");
        }

        showToast("Calculation saved to history.");
    } catch (error) {
        answer.textContent = "ERROR";
        showToast(error.message);
    }
}

async function loadHistory() {
    const response = await fetch("/api/history");
    const data = await response.json();
    historyList.innerHTML = "";

    if (!data.history.length) {
        historyList.innerHTML = '<div class="empty">No calculations yet.</div>';
        return;
    }

    data.history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `
            <div class="history-expression">${escapeHtml(item.expression)}</div>
            <div class="history-result">${escapeHtml(item.result)}</div>
            <div class="history-meta">${escapeHtml(item.mode)} · ${escapeHtml(item.created_at)}</div>
        `;
        div.addEventListener("click", () => {
            expression.value = item.expression;
            expression.focus();
            historyPanel.classList.add("hidden");
        });
        historyList.appendChild(div);
    });
}

async function clearHistory() {
    if (!confirm("Clear all calculation history?")) return;
    await fetch("/api/history/clear", {method: "POST"});
    await loadHistory();
    showToast("History cleared.");
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[ch]));
}

document.querySelectorAll("[data-insert]").forEach(button => {
    button.addEventListener("click", () => insertAtCursor(button.dataset.insert));
});
document.querySelector("[data-action='clear']").addEventListener("click", clearAll);
document.querySelector("[data-action='backspace']").addEventListener("click", backspace);
document.querySelector("[data-action='calculate']").addEventListener("click", calculate);

document.querySelectorAll(".mode").forEach(button => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
});

expression.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        calculate();
    } else if (event.key === "Escape") {
        clearAll();
    }
});

document.getElementById("historyToggle").addEventListener("click", async () => {
    historyPanel.classList.remove("hidden");
    await loadHistory();
});
document.getElementById("closeHistory").addEventListener("click", () => historyPanel.classList.add("hidden"));
document.getElementById("clearHistory").addEventListener("click", clearHistory);

setMode("Smart");
expression.focus();
