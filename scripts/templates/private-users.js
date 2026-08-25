const state = { snapshot: null, filter: "pending", search: "", busy: false };

const translations = {
    zh: {
        brand: "Telegram 下载 Bot", title: "用户管理", dashboard: "运行面板", logout: "退出登录",
        pending: "待审批", dynamic: "动态授权", static: "固定授权", blacklist: "永久黑名单", admins: "管理员",
        add_label: "直接授权 Telegram 数字 ID", add_placeholder: "例如 123456789", add: "添加用户",
        search: "搜索", search_placeholder: "姓名、用户名或数字 ID", allowed: "已授权", blacklist_short: "黑名单", all: "全部",
        loading: "正在读取用户数据...", empty: "当前筛选条件下没有用户。", user: "用户", status: "状态",
        time_source: "时间 / 来源", actions: "操作", downloads: "下载记录", history: "用户历史",
        admin: "管理员", config: "固定授权", request: "待审批", blacklist_label: "永久拉黑",
        history_action: "日志", approve: "批准", reject: "拒绝", block: "拉黑", revoke: "撤销权限", unblock: "解除拉黑",
        no_time: "无时间记录", user_prefix: "用户", id: "ID", login_expired: "登录已过期", failed: "操作失败",
        load_failed: "读取失败", done: "操作已完成", block_reason: "可选：填写拉黑原因（最多 200 字）",
        confirm_remove: "确认撤销这个用户的 Bot 使用权限？", confirm_reject: "确认拒绝这次申请？用户 24 小时内不能重复申请。",
        confirm_block: "确认永久拉黑？该用户的权限和申请都会被移除。", confirm_unblock: "确认解除永久拉黑？用户之后可以重新申请。",
        history_loading: "正在读取下载记录...", history_empty: "暂无下载记录。", missing_url: "未记录链接",
        result_added: "用户已授权，立即生效。", result_already_allowed: "该用户已经拥有权限。", result_blacklisted: "用户已永久拉黑。",
        result_already_blacklisted: "该用户已经在永久黑名单中。", result_unblacklisted: "永久拉黑已解除。", result_not_blacklisted: "该用户不在永久黑名单中。",
        result_removed: "用户权限已撤销。", result_not_dynamic: "该用户不在动态授权名单中。", result_approved: "申请已批准，权限立即生效。",
        result_rejected: "申请已拒绝，24 小时内不能重复申请。", result_not_pending: "这项申请已被处理或不存在。", result_protected: "该用户受配置保护，不能执行此操作。",
        nav_aria: "后台导航", language_aria: "语言切换", summary_aria: "用户数量概览", tools_aria: "用户管理工具", status_aria: "用户状态", close_aria: "关闭",
    },
    en: {
        brand: "Telegram Download Bot", title: "User management", dashboard: "Operations", logout: "Log out",
        pending: "Pending", dynamic: "Dynamic access", static: "Configured access", blacklist: "Permanent blacklist", admins: "Administrators",
        add_label: "Authorize a numeric Telegram ID", add_placeholder: "For example 123456789", add: "Add user",
        search: "Search", search_placeholder: "Name, username, or numeric ID", allowed: "Authorized", blacklist_short: "Blacklist", all: "All",
        loading: "Loading user data...", empty: "No users match the current filters.", user: "User", status: "Status",
        time_source: "Time / source", actions: "Actions", downloads: "Download records", history: "User history",
        admin: "Administrator", config: "Configured access", request: "Pending", blacklist_label: "Permanently blacklisted",
        history_action: "History", approve: "Approve", reject: "Reject", block: "Blacklist", revoke: "Revoke access", unblock: "Unblacklist",
        no_time: "No timestamp", user_prefix: "User", id: "ID", login_expired: "Your login expired", failed: "Operation failed",
        load_failed: "Could not load", done: "Operation completed", block_reason: "Optional: blacklist reason (maximum 200 characters)",
        confirm_remove: "Revoke this user's Bot access?", confirm_reject: "Reject this request? The user cannot apply again for 24 hours.",
        confirm_block: "Permanently blacklist this user? Access and pending requests will be removed.", confirm_unblock: "Remove the permanent blacklist? The user can apply again.",
        history_loading: "Loading download records...", history_empty: "No download records.", missing_url: "URL not recorded",
        result_added: "User authorized; access is effective immediately.", result_already_allowed: "This user already has access.", result_blacklisted: "User permanently blacklisted.",
        result_already_blacklisted: "This user is already permanently blacklisted.", result_unblacklisted: "Permanent blacklist removed.", result_not_blacklisted: "This user is not permanently blacklisted.",
        result_removed: "User access revoked.", result_not_dynamic: "This user is not dynamically authorized.", result_approved: "Request approved; access is effective immediately.",
        result_rejected: "Request rejected; the user cannot apply again for 24 hours.", result_not_pending: "This request was already handled or does not exist.", result_protected: "This user is configuration-protected.",
        nav_aria: "Dashboard navigation", language_aria: "Language switch", summary_aria: "User count summary", tools_aria: "User management tools", status_aria: "User status", close_aria: "Close",
    },
};
let currentLanguage = localStorage.getItem("adminLanguage") || (navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en");
const ui = (key) => translations[currentLanguage][key] || translations.en[key] || key;

function applyLanguage() {
    document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((element) => { element.textContent = ui(element.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => { element.placeholder = ui(element.dataset.i18nPlaceholder); });
    document.querySelectorAll("[data-i18n-aria]").forEach((element) => { element.setAttribute("aria-label", ui(element.dataset.i18nAria)); });
    document.querySelectorAll("[data-ui-language]").forEach((button) => button.classList.toggle("active", button.dataset.uiLanguage === currentLanguage));
    document.title = `${ui("title")} - Telegram Download Bot`;
    render();
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
    })[char]);
}

async function requestJSON(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    if (response.status === 401) {
        window.location.href = "/login";
        throw new Error(ui("login_expired"));
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(ui("failed"));
    return data;
}

function showStatus(message, isError = false) {
    const element = document.getElementById("status-message");
    element.textContent = message;
    element.classList.toggle("error", isError);
    element.hidden = false;
    window.clearTimeout(showStatus.timer);
    showStatus.timer = window.setTimeout(() => { element.hidden = true; }, 4500);
}

function formatTime(timestamp) {
    const numeric = Number(timestamp);
    if (!numeric) return ui("no_time");
    return new Intl.DateTimeFormat(currentLanguage === "zh" ? "zh-CN" : "en", {
        year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
    }).format(new Date(numeric * 1000));
}

function allRows() {
    if (!state.snapshot) return [];
    return [
        ...state.snapshot.pending_requests,
        ...state.snapshot.allowed_users,
        ...state.snapshot.static_users,
        ...state.snapshot.admins,
        ...state.snapshot.blacklisted_users,
    ];
}

function matchesFilter(entry) {
    if (state.filter === "all") return true;
    if (state.filter === "pending") return entry.source === "request";
    if (state.filter === "blacklisted") return entry.source === "blacklist";
    return ["admin", "config", "dynamic"].includes(entry.source);
}

function displayName(entry) {
    const name = [entry.first_name, entry.last_name].filter(Boolean).join(" ");
    return name || (entry.username ? `@${entry.username}` : `${ui("user_prefix")} ${entry.user_id}`);
}

function rowTime(entry) {
    const timestamp = entry.submitted_at || entry.added_at || entry.blocked_at;
    const labelKey = entry.source === "blacklist" ? "blacklist_label" : entry.source;
    return `${formatTime(timestamp)} · ${ui(labelKey)}`;
}

function actionButton(action, userId, text, style = "neutral") {
    return `<button class="button button--small button--${style}" type="button" data-action="${action}" data-user-id="${userId}">${text}</button>`;
}

function rowActions(entry) {
    const buttons = [actionButton("history", entry.user_id, ui("history_action"))];
    if (entry.source === "request") {
        buttons.push(actionButton("approve", entry.user_id, ui("approve"), "primary"));
        buttons.push(actionButton("reject", entry.user_id, ui("reject")));
        buttons.push(actionButton("blacklist", entry.user_id, ui("block"), "danger"));
    } else if (entry.source === "dynamic") {
        buttons.push(actionButton("remove", entry.user_id, ui("revoke")));
        buttons.push(actionButton("blacklist", entry.user_id, ui("block"), "danger"));
    } else if (entry.source === "config") {
        buttons.push(actionButton("blacklist", entry.user_id, ui("block"), "danger"));
    } else if (entry.source === "blacklist") {
        buttons.push(actionButton("unblacklist", entry.user_id, ui("unblock"), "primary"));
    }
    return buttons.join("");
}

function render() {
    if (!state.snapshot) return;
    const counts = state.snapshot.counts;
    Object.entries(counts).forEach(([key, value]) => {
        const element = document.getElementById(`count-${key}`);
        if (element) element.textContent = value;
    });

    const query = state.search.trim().toLowerCase();
    const rows = allRows().filter((entry) => {
        const haystack = `${entry.user_id} ${entry.first_name || ""} ${entry.last_name || ""} ${entry.username || ""}`.toLowerCase();
        return matchesFilter(entry) && (!query || haystack.includes(query));
    });
    const body = document.getElementById("users-body");
    body.innerHTML = rows.map((entry) => {
        const username = entry.username ? `@${escapeHtml(entry.username)} · ` : "";
        const badgeClass = entry.source === "request" ? "pending" : entry.source === "blacklist" ? "blacklisted" : "allowed";
        const labelKey = entry.source === "blacklist" ? "blacklist_label" : entry.source;
        return `<tr>
            <td><div class="user-name">${escapeHtml(displayName(entry))}</div><div class="user-meta">${username}${ui("id")} ${entry.user_id}</div></td>
            <td><span class="badge badge--${badgeClass}">${escapeHtml(ui(labelKey))}</span></td>
            <td><div class="time-meta">${escapeHtml(rowTime(entry))}</div></td>
            <td><div class="actions">${rowActions(entry)}</div></td>
        </tr>`;
    }).join("");
    document.getElementById("users-loading").hidden = true;
    document.getElementById("users-empty").hidden = rows.length !== 0;
    document.getElementById("users-table-wrap").hidden = rows.length === 0;
}

async function loadUsers() {
    try {
        state.snapshot = await requestJSON("/api/private-users");
        render();
    } catch (error) {
        document.getElementById("users-loading").textContent = `${ui("load_failed")}: ${error.message}`;
    }
}

async function performAction(action, userId) {
    if (state.busy) return;
    let reason = null;
    if (action === "blacklist") {
        reason = window.prompt(ui("block_reason"), "web_admin");
        if (reason === null) return;
    }
    const confirmations = {
        remove: ui("confirm_remove"), reject: ui("confirm_reject"), blacklist: ui("confirm_block"), unblacklist: ui("confirm_unblock"),
    };
    if (confirmations[action] && !window.confirm(confirmations[action])) return;

    state.busy = true;
    try {
        const result = await requestJSON(`/api/private-users/${action}`, {
            method: "POST",
            body: JSON.stringify({ user_id: Number(userId), reason }),
        });
        showStatus(ui(`result_${result.result}`) || result.message || ui("done"));
        await loadUsers();
    } catch (error) {
        showStatus(error.message, true);
    } finally {
        state.busy = false;
    }
}

async function showHistory(userId) {
    const dialog = document.getElementById("history-dialog");
    const content = document.getElementById("history-content");
    document.getElementById("history-title").textContent = `${ui("user_prefix")} ${userId}`;
    content.innerHTML = `<div class="state-box">${ui("history_loading")}</div>`;
    dialog.showModal();
    try {
        const history = await requestJSON(`/api/user-history?user_id=${userId}&period=all&limit=100`);
        if (!Array.isArray(history) || history.length === 0) {
            content.innerHTML = `<div class="state-box">${ui("history_empty")}</div>`;
            return;
        }
        content.innerHTML = history.map((item) => {
            const url = item.url || item.URL || item.link || item.domain || ui("missing_url");
            const timestamp = item.timestamp || item.time || item.created_at;
            const detail = Object.entries(item)
                .filter(([key]) => !["url", "URL", "link", "timestamp", "time", "created_at"].includes(key))
                .slice(0, 5)
                .map(([key, value]) => `${key}: ${value}`)
                .join(" · ");
            return `<div class="history-item"><div class="history-url">${escapeHtml(url)}</div><div class="history-detail">${escapeHtml(formatTime(timestamp))}${detail ? ` · ${escapeHtml(detail)}` : ""}</div></div>`;
        }).join("");
    } catch (error) {
        content.innerHTML = `<div class="state-box">${ui("load_failed")}: ${escapeHtml(error.message)}</div>`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-ui-language]").forEach((button) => button.addEventListener("click", () => {
        currentLanguage = button.dataset.uiLanguage;
        localStorage.setItem("adminLanguage", currentLanguage);
        applyLanguage();
    }));
    applyLanguage();
    document.querySelectorAll("[data-filter]").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            state.filter = button.dataset.filter;
            render();
        });
    });
    document.getElementById("user-search").addEventListener("input", (event) => {
        state.search = event.target.value;
        render();
    });
    document.getElementById("add-user-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const input = document.getElementById("add-user-id");
        await performAction("add", input.value);
        input.value = "";
    });
    document.getElementById("users-body").addEventListener("click", (event) => {
        const button = event.target.closest("[data-action]");
        if (!button) return;
        if (button.dataset.action === "history") showHistory(button.dataset.userId);
        else performAction(button.dataset.action, button.dataset.userId);
    });
    document.getElementById("history-close").addEventListener("click", () => document.getElementById("history-dialog").close());
    document.getElementById("logout-button").addEventListener("click", async () => {
        await requestJSON("/api/logout", { method: "POST", body: "{}" }).catch(() => {});
        window.location.href = "/login";
    });
    loadUsers();
});
