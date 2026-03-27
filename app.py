# app.py v2 — Posit Cloud Implementation Assistant
# Shiny for Python
# v2 changes: scope escalation choice, handoff dedup, copy buttons,
#   natural language session end, escalation tab fix, PS summary formatting,
#   proactive project awareness, transparency disclosure, role-adaptive opening,
#   source citation, topic tags, source confidence, micro-feedback,
#   follow-up indicators prominent, email-ready summary, per-role scoping,
#   unresolved question log (session only).

from shiny import App, reactive, render, ui
from datetime import datetime
import re

from api import (
    call_claude,
    generate_handoff_summary,
    generate_session_summary,
    update_unresolved_count,
    should_escalate,
    detect_role,
    check_scope_question,
    check_session_end_intent,
    check_unresolved_response,
)
from system_prompt import build_system_prompt

# ===========================================================================
# STYLES
# ===========================================================================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'IBM Plex Sans', sans-serif;
    background: #F4F6F9;
    color: #1C2333;
    font-size: 14px;
    height: 100vh;
    overflow: hidden;
}

/* ---- Root layout ---- */
.app-shell {
    display: grid;
    grid-template-columns: 220px 1fr 300px;
    grid-template-rows: 52px 1fr;
    height: 100vh;
    overflow: hidden;
}

/* ---- Top bar ---- */
.top-bar {
    grid-column: 1 / -1;
    background: #1C2333;
    color: white;
    display: flex;
    align-items: center;
    padding: 0 1.25rem;
    gap: 1rem;
    border-bottom: 2px solid #447099;
}
.top-bar-logo { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #447099; }
.top-bar-title { font-size: 0.9rem; font-weight: 500; color: #E8EDF5; }
.top-bar-sub { font-size: 0.72rem; color: #6B7A99; margin-left: 0.5rem; }
.top-bar-badge {
    margin-left: auto;
    background: rgba(68,112,153,0.2);
    color: #447099;
    border: 1px solid rgba(68,112,153,0.35);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ---- Left sidebar ---- */
.left-sidebar {
    background: #FFFFFF;
    border-right: 1px solid #E2E6EF;
    padding: 1.1rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}
.sidebar-label {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9BA8BF;
    margin-top: 1rem;
    margin-bottom: 0.35rem;
}
.sidebar-label:first-child { margin-top: 0; }

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 600;
}
.chip-waiting  { background: #EEF2FF; color: #4361EE; }
.chip-active   { background: #E8F5E9; color: #2E7D32; }
.chip-ended    { background: #FFF3E0; color: #E65100; }
.chip-escalated { background: #FFF0F0; color: #C62828; }

.escalation-banner {
    background: #FFF8E1;
    border: 1px solid #FFD54F;
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    font-size: 0.72rem;
    color: #5D4037;
    line-height: 1.4;
}

.sidebar-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.75rem 0; }

.end-btn {
    width: 100%;
    background: #FFF0F0 !important;
    color: #C62828 !important;
    border: 1px solid #FFCDD2 !important;
    border-radius: 6px !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    padding: 0.45rem !important;
    cursor: pointer;
    font-family: inherit !important;
    transition: background 0.15s;
}
.end-btn:hover { background: #FFEBEE !important; }
.end-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.meta-block { font-size: 0.72rem; color: #6B7A99; line-height: 1.7; }

/* ---- Chat panel ---- */
.chat-panel {
    display: flex;
    flex-direction: column;
    background: #F4F6F9;
    overflow: hidden;
    min-height: 0;
}

.chat-window {
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    scroll-behavior: smooth;
    min-height: 0;
}

/* ---- Message bubbles ---- */
.msg-row { display: flex; align-items: flex-start; gap: 0.6rem; max-width: 100%; }
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 30px; height: 30px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 700;
    flex-shrink: 0; margin-top: 2px;
}
.avatar-ai   { background: #1C2333; color: #447099; }
.avatar-user { background: #E2E6EF; color: #6B7A99; }

.bubble {
    max-width: 76%;
    padding: 0.65rem 0.9rem;
    border-radius: 12px;
    font-size: 0.845rem;
    line-height: 1.6;
}
.bubble-ai {
    background: #FFFFFF;
    border: 1px solid #E2E6EF;
    border-top-left-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-user {
    background: #1C2333;
    color: #E8EDF5;
    border-top-right-radius: 3px;
}

/* Transparency notice inside bubble */
.transparency-notice {
    background: #EEF4FA;
    border-left: 3px solid #447099;
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
    font-size: 0.78rem;
    color: #2D4A63;
    margin-bottom: 0.75rem;
    line-height: 1.5;
}

/* Scope choice prompt */
.scope-choice {
    background: #FFF8E1;
    border: 1px solid #FFD54F;
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
    margin-top: 0.5rem;
    font-size: 0.82rem;
}
.scope-choice-btns { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.scope-btn {
    padding: 0.3rem 0.85rem;
    border-radius: 5px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    font-family: inherit;
    transition: background 0.15s;
}
.scope-btn-escalate { background: #447099; color: white; }
.scope-btn-escalate:hover { background: #355880; }
.scope-btn-dismiss  { background: #E2E6EF; color: #4A5568; }
.scope-btn-dismiss:hover { background: #CBD2E0; }

/* Source confidence badge */
.source-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.68rem;
    color: #6B7A99;
    margin-top: 0.4rem;
    padding: 2px 6px;
    background: #F4F6F9;
    border-radius: 4px;
    border: 1px solid #E2E6EF;
}

/* Feedback thumbs */
.feedback-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.4rem;
}
.feedback-label { font-size: 0.68rem; color: #9BA8BF; }
.thumb-btn {
    background: none;
    border: 1px solid #E2E6EF;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.1s;
    line-height: 1.4;
}
.thumb-btn:hover { background: #F4F6F9; border-color: #CBD2E0; }
.thumb-btn.active-up   { background: #E8F5E9; border-color: #72994E; }
.thumb-btn.active-down { background: #FFEBEE; border-color: #C62828; }

.msg-ts { font-size: 0.65rem; color: #9BA8BF; margin-top: 3px; padding: 0 0.2rem; }
.user .msg-ts { text-align: right; }

/* Bubble content formatting */
.bubble p { margin: 0 0 0.5rem 0; }
.bubble p:last-child { margin-bottom: 0; }
.bubble ul, .bubble ol { margin: 0.3rem 0; padding-left: 1.3rem; }
.bubble li { margin-bottom: 0.2rem; }
.bubble code {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8em;
    background: rgba(0,0,0,0.06);
    padding: 1px 5px;
    border-radius: 3px;
}
.bubble-user code { background: rgba(255,255,255,0.1); }
.bubble strong { font-weight: 600; }
.bubble hr { border: none; border-top: 1px solid rgba(0,0,0,0.08); margin: 0.5rem 0; }
.bubble table { border-collapse: collapse; width: 100%; font-size: 0.8em; margin: 0.4rem 0; }
.bubble th, .bubble td { border: 1px solid #dde; padding: 3px 8px; text-align: left; }
.bubble th { background: #f0f4f8; font-weight: 600; }
.bubble blockquote {
    border-left: 3px solid #447099;
    background: #EEF4FA;
    margin: 0.4rem 0;
    padding: 0.5rem 0.75rem;
    border-radius: 0 4px 4px 0;
    font-size: 0.82rem;
    color: #2D4A63;
}

/* Empty state */
.empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #9BA8BF;
    font-size: 0.82rem;
    text-align: center;
    gap: 0.5rem;
    padding: 2rem;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.25rem; }

/* Typing dots */
.typing-dots { display: flex; gap: 4px; align-items: center; padding: 0.3rem 0; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #447099; animation: pulse 1.2s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; } 40% { transform: scale(1.0); opacity: 1; } }

/* ---- Input area ---- */
.input-area {
    border-top: 1px solid #E2E6EF;
    background: #FFFFFF;
    padding: 0.85rem 1.1rem;
    flex-shrink: 0;
}
.input-row { display: flex; gap: 0.5rem; align-items: flex-end; }
.input-row textarea {
    flex: 1;
    border: 1px solid #CBD2E0;
    border-radius: 8px;
    padding: 0.55rem 0.75rem;
    font-size: 0.845rem;
    font-family: 'IBM Plex Sans', sans-serif;
    resize: none;
    line-height: 1.5;
    min-height: 42px;
    max-height: 110px;
    background: #F4F6F9;
    color: #1C2333;
    outline: none;
    transition: border-color 0.15s, background 0.15s;
}
.input-row textarea:focus { border-color: #447099; background: #FFFFFF; }
.input-row textarea::placeholder { color: #9BA8BF; }
.send-btn {
    background: #447099 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0 1.1rem !important;
    height: 42px;
    font-size: 0.845rem !important;
    font-weight: 600 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.15s;
    white-space: nowrap;
}
.send-btn:hover { background: #355880 !important; }
.send-btn:disabled { background: #9BA8BF !important; cursor: not-allowed; }
.input-hint { font-size: 0.65rem; color: #9BA8BF; margin-top: 0.4rem; }

/* ---- Right panel ---- */
.right-panel {
    background: #FFFFFF;
    border-left: 1px solid #E2E6EF;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
.panel-tabs { display: flex; border-bottom: 1px solid #E2E6EF; flex-shrink: 0; }
.tab-btn {
    flex: 1;
    padding: 0.65rem 0.5rem;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'IBM Plex Sans', sans-serif;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    border: none;
    background: transparent;
    color: #9BA8BF;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.15s;
    margin-bottom: -1px;
}
.tab-btn.active { color: #447099; border-bottom-color: #447099; }
.tab-btn:hover:not(.active) { color: #1C2333; }

.tab-content { padding: 1rem; flex: 1; overflow-y: auto; }
.tab-pane { display: none; }
.tab-pane.active { display: block; }

.panel-empty {
    color: #9BA8BF;
    font-size: 0.78rem;
    text-align: center;
    padding: 2rem 1rem;
    font-style: italic;
    line-height: 1.5;
}

/* ---- PS Summary structured layout ---- */
.summary-header {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #447099;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Follow-up indicators — prominent, top, distinct color */
.followup-block {
    background: #FFF3E0;
    border: 1px solid #FFB74D;
    border-left: 4px solid #F57C00;
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.85rem;
}
.followup-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #E65100;
    margin-bottom: 0.35rem;
}
.followup-content { font-size: 0.78rem; color: #3E2723; line-height: 1.55; }

/* Topic tags */
.tags-row { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem; }
.topic-tag {
    background: #EEF4FA;
    color: #355880;
    border: 1px solid #C5D8EC;
    border-radius: 20px;
    padding: 1px 8px;
    font-size: 0.67rem;
    font-weight: 600;
}

.summary-field { margin-bottom: 0.65rem; }
.summary-field-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #9BA8BF;
    margin-bottom: 0.2rem;
}
.summary-field-value { font-size: 0.78rem; color: #1C2333; line-height: 1.55; }
.summary-field-value.outcome-resolved { color: #2E7D32; font-weight: 600; }
.summary-field-value.outcome-partial  { color: #E65100; font-weight: 600; }
.summary-field-value.outcome-escalated { color: #C62828; font-weight: 600; }

.summary-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.65rem 0; }

/* Handoff box */
.handoff-box {
    background: #FFFDF0;
    border: 1px solid #FFD54F;
    border-radius: 6px;
    padding: 0.85rem;
    font-size: 0.78rem;
    line-height: 1.65;
    color: #3D2B00;
    white-space: pre-wrap;
}
.panel-section-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.label-handoff { color: #E65100; }

/* Copy buttons */
.copy-btn {
    background: none;
    border: 1px solid #E2E6EF;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.67rem;
    font-weight: 600;
    color: #6B7A99;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
    white-space: nowrap;
}
.copy-btn:hover { background: #F4F6F9; border-color: #CBD2E0; color: #1C2333; }
.copy-btn.copied { color: #2E7D32; border-color: #72994E; background: #E8F5E9; }

/* Email format toggle */
.email-toggle-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    margin-top: 0.25rem;
}
.email-toggle-label { font-size: 0.68rem; color: #6B7A99; }
.format-toggle-btn {
    background: none;
    border: 1px solid #E2E6EF;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.67rem;
    font-weight: 600;
    color: #6B7A99;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.15s;
}
.format-toggle-btn.active { background: #EEF4FA; border-color: #447099; color: #447099; }

/* Shiny overrides */
.shiny-input-container { margin-bottom: 0 !important; }
.form-control, .selectize-input {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.8rem !important;
    border-color: #CBD2E0 !important;
    border-radius: 6px !important;
}
.selectize-input { padding: 5px 8px !important; }
select.form-control { height: 34px !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD2E0; border-radius: 10px; }
"""

JS = """
// Enter to send
document.addEventListener('keydown', function(e) {
    if (e.target.id === 'user_input' && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('send_btn').click();
    }
});

// Auto-scroll chat
const chatObserver = new MutationObserver(() => {
    const cw = document.querySelector('.chat-window');
    if (cw) cw.scrollTop = cw.scrollHeight;
});
document.addEventListener('DOMContentLoaded', () => {
    const cw = document.querySelector('.chat-window');
    if (cw) chatObserver.observe(cw, { childList: true, subtree: true });
});

// Tab switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => {
        p.classList.remove('active');
        p.style.display = 'none';
    });
    const btn = document.querySelector('[data-tab="' + tab + '"]');
    const pane = document.getElementById('pane-' + tab);
    if (btn) btn.classList.add('active');
    if (pane) { pane.classList.add('active'); pane.style.display = 'block'; }
}

// Copy to clipboard
function copyToClipboard(elementId, btnId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById(btnId);
        if (btn) {
            const orig = btn.innerText;
            btn.innerText = '✓ Copied';
            btn.classList.add('copied');
            setTimeout(() => { btn.innerText = orig; btn.classList.remove('copied'); }, 2000);
        }
    });
}

// Thumb feedback
function sendFeedback(msgId, helpful) {
    const upBtn   = document.getElementById('up-' + msgId);
    const downBtn = document.getElementById('down-' + msgId);
    if (upBtn)   upBtn.classList.toggle('active-up',    helpful);
    if (downBtn) downBtn.classList.toggle('active-down', !helpful);
    // Send to Shiny via custom input
    if (window.Shiny) {
        Shiny.setInputValue('feedback_event', { msg_id: msgId, helpful: helpful }, { priority: 'event' });
    }
}

// Summary format toggle
function toggleSummaryFormat(format) {
    document.getElementById('summary-structured').style.display = format === 'structured' ? 'block' : 'none';
    document.getElementById('summary-email').style.display      = format === 'email'      ? 'block' : 'none';
    document.querySelectorAll('.format-toggle-btn').forEach(b => b.classList.remove('active'));
    const activeBtn = document.getElementById('fmt-' + format);
    if (activeBtn) activeBtn.classList.add('active');
}
"""

# ===========================================================================
# UI
# ===========================================================================
ROLES = [
    ("", "— Select your role —"),
    ("IT Admin / Technical Lead", "IT Admin / Technical Lead"),
    ("Project Lead / Project Manager", "Project Lead / Project Manager"),
    ("Executive Sponsor / Research Director", "Executive Sponsor / Research Director"),
    ("Researcher / End User", "Researcher / End User"),
    ("UAT Tester", "UAT Tester"),
]

app_ui = ui.page_fixed(
    ui.tags.head(
        ui.tags.style(CSS),
        ui.tags.script(JS),
    ),
    ui.div({"class": "app-shell"},

        # ---- TOP BAR ----
        ui.div({"class": "top-bar"},
            ui.div({"class": "top-bar-logo"}, "Posit"),
            ui.div({"class": "top-bar-title"}, "Cloud Implementation Assistant"),
            ui.div({"class": "top-bar-sub"}, "State University Research Computing"),
            ui.div({"class": "top-bar-badge"}, "MVP Pilot · v2"),
        ),

        # ---- LEFT SIDEBAR ----
        ui.div({"class": "left-sidebar"},
            ui.div({"class": "sidebar-label"}, "Your Name"),
            ui.input_text("customer_name", None, placeholder="Enter your name"),

            ui.div({"class": "sidebar-label"}, "Your Role"),
            ui.input_select("customer_role", None,
                choices={v: l for v, l in ROLES}, selected=""),

            ui.div({"class": "sidebar-label"}, "Session Status"),
            ui.output_ui("session_status_ui"),

            ui.div({"class": "sidebar-label"}, "Escalation"),
            ui.output_ui("escalation_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),
            ui.input_action_button("end_session", "End Session", class_="end-btn"),
            ui.tags.hr({"class": "sidebar-divider"}),

            ui.div({"class": "sidebar-label"}, "Implementation"),
            ui.div({"class": "meta-block"},
                ui.tags.div("Customer: State Univ. RC"),
                ui.tags.div("PS Lead: Meredith Callahan"),
                ui.tags.div("Phase: 1 — Setup & Pilot"),
                ui.tags.div("⚠ Overdue: SSO attribute mapping"),
                ui.tags.div("🔄 In Progress: Resource limits"),
            ),
        ),

        # ---- MAIN CHAT PANEL ----
        ui.div({"class": "chat-panel"},
            ui.div({"class": "chat-window", "id": "chat_window"},
                ui.output_ui("chat_messages_ui"),
            ),
            ui.div({"class": "input-area"},
                ui.div({"class": "input-row"},
                    ui.tags.textarea(
                        {"id": "user_input",
                         "placeholder": "Ask a question or describe what you are trying to do…",
                         "rows": "2"},
                    ),
                    ui.input_action_button("send_btn", "Send", class_="send-btn"),
                ),
                ui.div({"class": "input-hint"},
                    "Enter to send · Shift+Enter for new line · Session summaries are shared with your PS lead"
                ),
            ),
        ),

        # ---- RIGHT PANEL ----
        ui.div({"class": "right-panel"},
            ui.div({"class": "panel-tabs"},
                ui.tags.button("PS Summary",
                    {"class": "tab-btn active", "data-tab": "summary",
                     "onclick": "switchTab('summary')"}),
                ui.tags.button("Escalation",
                    {"class": "tab-btn", "data-tab": "escalation",
                     "onclick": "switchTab('escalation')"}),
            ),
            ui.div({"class": "tab-content"},
                ui.div({"id": "pane-summary", "class": "tab-pane active",
                        "style": "display:block"},
                    ui.output_ui("summary_panel_ui")),
                ui.div({"id": "pane-escalation", "class": "tab-pane",
                        "style": "display:none"},
                    ui.output_ui("escalation_panel_ui")),
            ),
        ),
    ),
)


# ===========================================================================
# SERVER
# ===========================================================================
def server(input, output, session):

    # ---- Reactive state ----
    messages        = reactive.value([])
    started         = reactive.value(False)
    ended           = reactive.value(False)
    start_ts        = reactive.value(None)
    escalated       = reactive.value(False)
    unresolved      = reactive.value(0)
    handoff_text    = reactive.value("")
    session_summary = reactive.value("")
    email_summary   = reactive.value("")
    is_thinking     = reactive.value(False)
    msg_count       = reactive.value(0)  # for unique message IDs
    feedback_log    = reactive.value([])
    unresolved_log  = reactive.value([])

    # Scope choice state — when pending, show choice prompt
    scope_pending   = reactive.value(False)

    # ---- Sidebar outputs ----
    @output
    @render.ui
    def session_status_ui():
        if not started():
            return ui.span({"class": "status-chip chip-waiting"}, "● Waiting")
        elif ended():
            return ui.span({"class": "status-chip chip-ended"}, "● Ended")
        elif escalated():
            return ui.span({"class": "status-chip chip-escalated"}, "● Escalated")
        else:
            return ui.span({"class": "status-chip chip-active"}, "● Active")

    @output
    @render.ui
    def escalation_ui():
        if not started():
            return ui.div({"style": "font-size:0.72rem; color:#9BA8BF;"}, "No active session")
        elif escalated():
            return ui.div({"class": "escalation-banner"}, "⚠ Escalated to Meredith Callahan")
        else:
            count = unresolved()
            return ui.div({"style": "font-size:0.72rem; color:#2E7D32;"},
                "✓ No escalation triggered",
                ui.tags.br(),
                ui.span({"style": "color:#9BA8BF; font-size:0.68rem;"},
                    f"Exchange count: {count}/3"),
            )

    # ---- Chat messages ----
    @output
    @render.ui
    def chat_messages_ui():
        msgs = messages()
        thinking = is_thinking()

        if not msgs and not thinking:
            return ui.div({"class": "empty-state"},
                ui.div({"class": "empty-icon"}, "💬"),
                ui.div("Select your role and send your first message to begin."),
            )

        elements = []
        for m in msgs:
            is_user = m["role"] == "user"
            row_cls = "msg-row user" if is_user else "msg-row"
            bub_cls = "bubble bubble-user" if is_user else "bubble bubble-ai"
            av_cls  = "avatar avatar-user" if is_user else "avatar avatar-ai"
            av_lbl  = "YOU" if is_user else "AI"
            msg_id  = m.get("id", "")

            html_content = format_message(m["content"])

            # Build bubble contents
            bubble_inner = [ui.HTML(html_content)]

            # Add scope choice prompt if pending on this message
            if m.get("scope_choice"):
                bubble_inner.append(
                    ui.div({"class": "scope-choice"},
                        ui.div({"style": "font-weight:600; margin-bottom:0.3rem;"},
                            "Would you like to escalate this to Meredith Callahan?"),
                        ui.div({"class": "scope-choice-btns"},
                            ui.tags.button("Yes, escalate to PS",
                                {"class": "scope-btn scope-btn-escalate",
                                 "onclick": "Shiny.setInputValue('scope_decision', 'escalate', {priority: 'event'})"}),
                            ui.tags.button("No, move on",
                                {"class": "scope-btn scope-btn-dismiss",
                                 "onclick": "Shiny.setInputValue('scope_decision', 'dismiss', {priority: 'event'})"}),
                        ),
                    )
                )

            # Source badge (non-user messages only)
            if not is_user and m.get("source_badge"):
                bubble_inner.append(
                    ui.div({"class": "source-badge"}, m["source_badge"])
                )

            # Feedback thumbs (non-user, non-system messages)
            if not is_user and msg_id and not m.get("is_system"):
                fb = feedback_log()
                existing = next((f for f in fb if f["msg_id"] == msg_id), None)
                up_cls   = "thumb-btn active-up"   if (existing and existing["helpful"])      else "thumb-btn"
                down_cls = "thumb-btn active-down" if (existing and not existing["helpful"])  else "thumb-btn"
                bubble_inner.append(
                    ui.div({"class": "feedback-row"},
                        ui.span({"class": "feedback-label"}, "Helpful?"),
                        ui.tags.button("👍",
                            {"class": up_cls, "id": f"up-{msg_id}",
                             "onclick": f"sendFeedback('{msg_id}', true)"}),
                        ui.tags.button("👎",
                            {"class": down_cls, "id": f"down-{msg_id}",
                             "onclick": f"sendFeedback('{msg_id}', false)"}),
                    )
                )

            elements.append(
                ui.div({"class": row_cls},
                    ui.div({"class": av_cls}, av_lbl),
                    ui.div(
                        ui.div({"class": bub_cls}, *bubble_inner),
                        ui.div({"class": "msg-ts"}, m.get("ts", "")),
                    ),
                )
            )

        if thinking:
            elements.append(
                ui.div({"class": "msg-row"},
                    ui.div({"class": "avatar avatar-ai"}, "AI"),
                    ui.div({"class": "bubble bubble-ai"},
                        ui.div({"class": "typing-dots"},
                            ui.div({"class": "dot"}),
                            ui.div({"class": "dot"}),
                            ui.div({"class": "dot"}),
                        )
                    ),
                )
            )

        return ui.div(*elements)

    # ---- PS Summary panel ----
    @output
    @render.ui
    def summary_panel_ui():
        s = session_summary()
        e = email_summary()

        if not s:
            return ui.div({"class": "panel-empty"},
                "Session summary will appear here when the session ends.",
                ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Click 'End Session' or say 'let's wrap up' to generate the PS-facing summary.")
            )

        # Parse the structured summary
        parsed = parse_summary(s)

        # Build structured view
        structured_children = []

        # Follow-up Indicators — FIRST, prominent, distinct color
        followup = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
        structured_children.append(
            ui.div({"class": "followup-block"},
                ui.div({"class": "followup-label"}, "⚑ Follow-up Indicators"),
                ui.div({"class": "followup-content"}, followup),
            )
        )

        # Topic tags
        tags_raw = parsed.get("TOPIC_TAGS", "")
        if tags_raw and tags_raw != "N/A":
            tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            if tag_list:
                structured_children.append(
                    ui.div({"class": "tags-row"},
                        *[ui.span({"class": "topic-tag"}, t) for t in tag_list]
                    )
                )

        structured_children.append(ui.tags.hr({"class": "summary-divider"}))

        # Standard fields
        field_order = [
            ("DATE_TIME", "Date / Time"),
            ("CUSTOMER", "Customer"),
            ("OUTCOME", "Outcome"),
            ("TOPICS_COVERED", "Topics Covered"),
            ("GUIDANCE_PROVIDED", "Guidance Provided"),
            ("ESCALATION_SUMMARY", "Escalation Summary"),
            ("UNRESOLVED_QUESTIONS", "Unresolved Questions"),
            ("RESPONSE_FEEDBACK", "Response Feedback"),
        ]

        for key, label in field_order:
            val = parsed.get(key, "—")
            if not val or val.strip() == "":
                val = "—"
            outcome_cls = ""
            if key == "OUTCOME":
                if "Resolved" in val and "Partially" not in val:
                    outcome_cls = "outcome-resolved"
                elif "Partially" in val:
                    outcome_cls = "outcome-partial"
                elif "Escalated" in val:
                    outcome_cls = "outcome-escalated"
            structured_children.append(
                ui.div({"class": "summary-field"},
                    ui.div({"class": "summary-field-label"}, label),
                    ui.div({"class": f"summary-field-value {outcome_cls}"}, val),
                )
            )

        # Build the full panel
        return ui.div(
            # Header with copy buttons
            ui.div({"class": "summary-header"},
                ui.span("PS Session Summary"),
                ui.div({"style": "display:flex; gap:0.4rem;"},
                    ui.tags.button("Copy",
                        {"class": "copy-btn", "id": "copy-summary-btn",
                         "onclick": "copyToClipboard('summary-structured', 'copy-summary-btn')"}),
                    ui.tags.button("Copy as Email",
                        {"class": "copy-btn", "id": "copy-email-btn",
                         "onclick": "copyToClipboard('summary-email', 'copy-email-btn')"}),
                ),
            ),

            # Format toggle
            ui.div({"class": "email-toggle-row"},
                ui.span({"class": "email-toggle-label"}, "View:"),
                ui.tags.button("Structured",
                    {"class": "format-toggle-btn active", "id": "fmt-structured",
                     "onclick": "toggleSummaryFormat('structured')"}),
                ui.tags.button("Email-ready",
                    {"class": "format-toggle-btn", "id": "fmt-email",
                     "onclick": "toggleSummaryFormat('email')"}),
            ),

            # Structured view
            ui.div({"id": "summary-structured", "style": "display:block"},
                *structured_children
            ),

            # Email-ready view (hidden by default)
            ui.div({"id": "summary-email", "style": "display:none; white-space:pre-wrap; font-size:0.78rem; color:#1C2333; line-height:1.6;"},
                e or build_email_summary(parsed)
            ),
        )

    # ---- Escalation panel ----
    @output
    @render.ui
    def escalation_panel_ui():
        h = handoff_text()
        if not h:
            return ui.div({"class": "panel-empty"},
                "Handoff summary appears here if escalation is triggered.",
                ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Escalation triggers after 3 unresolved exchanges "
                    "or when you ask to reach the PS team.")
            )
        return ui.div(
            ui.div({"style": "display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem;"},
                ui.div({"class": "panel-section-label label-handoff"}, "⚡ Escalation Handoff Summary"),
                ui.tags.button("Copy",
                    {"class": "copy-btn", "id": "copy-handoff-btn",
                     "onclick": "copyToClipboard('handoff-content', 'copy-handoff-btn')"}),
            ),
            ui.div({"style": "font-size:0.72rem; color:#9BA8BF; margin-bottom:0.5rem;"},
                "Share with Meredith Callahan so she can pick up without context gaps."),
            ui.div({"id": "handoff-content", "class": "handoff-box"}, h),
        )

    # ---- Handle feedback events from JS ----
    @reactive.effect
    @reactive.event(input.feedback_event)
    def handle_feedback():
        evt = input.feedback_event()
        if not evt:
            return
        msg_id  = evt.get("msg_id")
        helpful = evt.get("helpful")
        if msg_id is None:
            return
        current = feedback_log()
        # Update or append
        updated = [f for f in current if f["msg_id"] != msg_id]
        updated.append({"msg_id": msg_id, "helpful": helpful})
        feedback_log.set(updated)

    # ---- Handle scope decision from JS ----
    @reactive.effect
    @reactive.event(input.scope_decision)
    def handle_scope_decision():
        decision = input.scope_decision()
        if decision == "escalate":
            _trigger_escalation()
        elif decision == "dismiss":
            # Remove scope_choice flag from last message
            msgs = messages()
            if msgs:
                last = {**msgs[-1], "scope_choice": False}
                messages.set(msgs[:-1] + [last])
            scope_pending.set(False)
            # Add a follow-up message
            ts = datetime.now().strftime("%H:%M")
            messages.set(messages() + [{
                "role": "assistant",
                "content": "Understood — we'll set that aside. What else can I help you with?",
                "ts": ts,
                "id": f"msg_{msg_count() + 1}",
                "is_system": True,
            }])
            msg_count.set(msg_count() + 1)

    def _trigger_escalation():
        """Shared escalation logic."""
        if escalated():
            return
        escalated.set(True)
        scope_pending.set(False)

        # Remove scope_choice flag
        msgs = messages()
        if msgs:
            last = {**msgs[-1], "scope_choice": False}
            messages.set(msgs[:-1] + [last])

        api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages()]
        handoff = generate_handoff_summary(
            messages=api_msgs,
            customer_name=input.customer_name() or "Not provided",
            customer_role=input.customer_role() or "Not specified",
        )
        handoff_text.set(handoff)

        # Add handoff ONCE to chat
        ts = datetime.now().strftime("%H:%M")
        mid = msg_count() + 1
        msg_count.set(mid)
        messages.set(messages() + [{
            "role": "assistant",
            "content": (
                "Here is a summary you can share with Meredith Callahan so she can "
                "pick up right where we left off:\n\n"
                "---\n**HANDOFF SUMMARY FOR MEREDITH CALLAHAN**\n\n" + handoff
            ),
            "ts": ts,
            "id": f"msg_{mid}",
            "is_system": True,
        }])

    # ---- Send button ----
    @reactive.effect
    @reactive.event(input.send_btn)
    def handle_send():
        if ended():
            return

        user_text = input.user_input()
        if not user_text or not user_text.strip():
            return

        ui.update_text("user_input", value="")

        # Initialize session
        if not started():
            started.set(True)
            start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Detect role
        current_role = input.customer_role()
        if not current_role:
            detected = detect_role(user_text)
            if detected:
                current_role = detected

        # Check for natural language session end
        if check_session_end_intent(user_text):
            _close_session(current_role, natural_language=True)
            return

        # Update unresolved counter
        unresolved.set(update_unresolved_count(unresolved(), user_text))

        # Check escalation (non-scope)
        do_escalate = should_escalate(unresolved(), user_text, escalated())

        # Check scope question — offer choice instead of auto-escalating
        is_scope_q = check_scope_question(user_text) and not escalated()

        # Add user message
        ts = datetime.now().strftime("%H:%M")
        mid = msg_count() + 1
        msg_count.set(mid)
        messages.set(messages() + [{
            "role": "user",
            "content": user_text,
            "ts": ts,
            "id": f"msg_{mid}",
        }])

        is_thinking.set(True)

        is_first = len([m for m in messages() if m["role"] == "assistant"]) == 0

        api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages()]
        sys_prompt = build_system_prompt(
            customer_name=input.customer_name() or "",
            customer_role=current_role or "",
            is_first_message=is_first,
        )

        try:
            response_text = call_claude(messages=api_msgs, system_prompt=sys_prompt)
            is_thinking.set(False)

            # Check if model signaled session end
            if "TRIGGER_SESSION_END" in response_text:
                response_text = response_text.replace("TRIGGER_SESSION_END", "").strip()
                clean_ts = datetime.now().strftime("%H:%M")
                mid2 = msg_count() + 1
                msg_count.set(mid2)
                messages.set(messages() + [{
                    "role": "assistant",
                    "content": response_text,
                    "ts": clean_ts,
                    "id": f"msg_{mid2}",
                    "source_badge": extract_source_badge(response_text),
                }])
                _close_session(current_role, natural_language=True)
                return

            # Track unresolved questions
            if check_unresolved_response(response_text):
                ulog = unresolved_log()
                ulog = ulog + [user_text[:120]]
                unresolved_log.set(ulog)

            # Extract source badge
            source = extract_source_badge(response_text)

            # Handle standard escalation (non-scope)
            if do_escalate and not escalated() and not is_scope_q:
                escalated.set(True)
                api_msgs2 = [{"role": m["role"], "content": m["content"]} for m in messages()]
                handoff = generate_handoff_summary(
                    messages=api_msgs2,
                    customer_name=input.customer_name() or "Not provided",
                    customer_role=current_role or "Not specified",
                )
                handoff_text.set(handoff)
                response_text = (
                    response_text
                    + "\n\n---\n**HANDOFF SUMMARY FOR MEREDITH CALLAHAN**\n\n"
                    + handoff
                )

            ts_resp = datetime.now().strftime("%H:%M")
            mid3 = msg_count() + 1
            msg_count.set(mid3)

            # If scope question detected, add scope choice UI to message
            messages.set(messages() + [{
                "role": "assistant",
                "content": response_text,
                "ts": ts_resp,
                "id": f"msg_{mid3}",
                "source_badge": source,
                "scope_choice": is_scope_q and not escalated(),
            }])

            if is_scope_q:
                scope_pending.set(True)

        except Exception as e:
            is_thinking.set(False)
            messages.set(messages() + [{
                "role": "assistant",
                "content": (
                    "I encountered an error connecting to the assistant backend. "
                    "Please try again or contact your PS lead directly.\n\n"
                    f"Technical detail: {str(e)}"
                ),
                "ts": datetime.now().strftime("%H:%M"),
                "id": f"msg_{msg_count() + 1}",
                "is_system": True,
            }])
            msg_count.set(msg_count() + 1)

    # ---- End Session button ----
    @reactive.effect
    @reactive.event(input.end_session)
    def handle_end_session():
        if not started() or ended():
            return
        current_role = input.customer_role() or ""
        _close_session(current_role, natural_language=False)

    def _close_session(current_role: str, natural_language: bool = False):
        """Shared session close logic — called by button or natural language."""
        if ended():
            return
        ended.set(True)

        api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages()]
        role_str = current_role or "Not specified"

        summary = generate_session_summary(
            messages=api_msgs,
            customer_name=input.customer_name() or "Not provided",
            customer_role=role_str,
            session_start=start_ts() or "Unknown",
            escalated=escalated(),
            handoff_text=handoff_text(),
            unresolved_log=unresolved_log(),
            feedback_log=feedback_log(),
        )
        session_summary.set(summary)
        email_summary.set(build_email_summary(parse_summary(summary)))

        ts = datetime.now().strftime("%H:%M")
        mid = msg_count() + 1
        msg_count.set(mid)

        close_msg = (
            "Got it — I'll close out our session now. "
            if natural_language else ""
        )
        messages.set(messages() + [{
            "role": "assistant",
            "content": (
                close_msg +
                "**Session ended.** A summary has been generated and is visible in the "
                "PS Summary tab. Meredith Callahan will have full context of what we "
                "covered today."
            ),
            "ts": ts,
            "id": f"msg_{mid}",
            "is_system": True,
        }])


# ===========================================================================
# HELPERS
# ===========================================================================

def extract_source_badge(text: str) -> str:
    """Extract the source indicator line from a response."""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("📘 Source:") or stripped.startswith("📋 Source:") or \
           stripped.startswith("📗 Source:") or stripped.startswith("📄 Source:"):
            return stripped
    return ""


def parse_summary(raw: str) -> dict:
    """Parse the structured session summary into a dict."""
    fields = [
        "FOLLOW_UP_INDICATORS", "DATE_TIME", "CUSTOMER", "OUTCOME",
        "TOPIC_TAGS", "TOPICS_COVERED", "GUIDANCE_PROVIDED",
        "ESCALATION_SUMMARY", "UNRESOLVED_QUESTIONS", "RESPONSE_FEEDBACK",
    ]
    result = {}
    lines = raw.split("\n")
    current_key = None
    current_val = []

    for line in lines:
        matched = False
        for field in fields:
            if line.startswith(f"{field}:"):
                if current_key:
                    result[current_key] = "\n".join(current_val).strip()
                current_key = field
                current_val = [line[len(field)+1:].strip()]
                matched = True
                break
        if not matched and current_key:
            current_val.append(line)

    if current_key:
        result[current_key] = "\n".join(current_val).strip()

    return result


def build_email_summary(parsed: dict) -> str:
    """Build a plain-text email-ready summary from parsed fields."""
    lines = [
        "POSIT CLOUD IMPLEMENTATION ASSISTANT — SESSION SUMMARY",
        "=" * 55,
        "",
    ]

    followup = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
    if followup and followup != "None identified.":
        lines += [
            "FOLLOW-UP INDICATORS (Action Required)",
            "-" * 40,
            followup,
            "",
        ]

    field_map = [
        ("DATE_TIME",           "Date / Time"),
        ("CUSTOMER",            "Customer"),
        ("OUTCOME",             "Outcome"),
        ("TOPIC_TAGS",          "Topics"),
        ("TOPICS_COVERED",      "Topics Covered"),
        ("GUIDANCE_PROVIDED",   "Guidance Provided"),
        ("ESCALATION_SUMMARY",  "Escalation Summary"),
        ("UNRESOLVED_QUESTIONS","Unresolved Questions"),
        ("RESPONSE_FEEDBACK",   "Response Feedback"),
    ]

    for key, label in field_map:
        val = parsed.get(key, "—")
        if val and val.strip():
            lines += [f"{label}: {val}", ""]

    lines += [
        "-" * 55,
        "Generated by Posit Cloud Implementation Assistant",
    ]
    return "\n".join(lines)


def format_message(text: str) -> str:
    """Convert markdown-like patterns to HTML for chat bubbles."""
    # Blockquotes (transparency notice)
    def replace_blockquote(m):
        content = m.group(1).strip()
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        return f'<blockquote>{content}</blockquote>'
    text = re.sub(r'(?m)^> (.+)$', replace_blockquote, text)

    # Horizontal rules
    text = re.sub(r'\n---\n', '\n<hr>\n', text)

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Source badge lines — render as badge
    def replace_source(m):
        return f'<div class="source-badge">{m.group(0).strip()}</div>'
    text = re.sub(r'(?m)^[📘📋📗📄] Source:.*$', replace_source, text)

    # Tables
    lines = text.split('\n')
    output = []
    in_list = False
    in_table = False
    table_html = ""
    header_done = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            if re.match(r'^\|[-\s|:]+\|$', stripped):
                header_done = True
                continue
            if not in_table:
                in_table = True
                header_done = False
                table_html = '<table>'
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            if not header_done:
                row = ''.join(f'<th>{c}</th>' for c in cells)
                header_done = True
            else:
                row = ''.join(f'<td>{c}</td>' for c in cells)
            table_html += f'<tr>{row}</tr>'
            continue
        else:
            if in_table:
                output.append(table_html + '</table>')
                table_html = ''
                in_table = False
                header_done = False

        list_match = re.match(r'^(\d+\.\s+|[-*]\s+)(.*)', stripped)
        if list_match:
            if not in_list:
                output.append('<ul>')
                in_list = True
            output.append(f'<li>{list_match.group(2)}</li>')
        else:
            if in_list:
                output.append('</ul>')
                in_list = False
            output.append(line)

    if in_list:
        output.append('</ul>')
    if in_table:
        output.append(table_html + '</table>')

    text = '\n'.join(output)

    paragraphs = re.split(r'\n{2,}', text)
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        p_single = p.replace('\n', '<br>')
        if re.match(r'^<(ul|ol|table|hr|blockquote|div)', p_single):
            result.append(p_single)
        else:
            result.append(f'<p>{p_single}</p>')

    return '\n'.join(result)


# ===========================================================================
# RUN
# ===========================================================================
app = App(app_ui, server)
