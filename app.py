# app.py — Posit Cloud Implementation Assistant
# Shiny for Python application
# Deploy to Posit Connect Cloud via GitHub

from shiny import App, reactive, render, ui
from shiny.types import ImgData
from datetime import datetime
import re

from api import (
    call_claude, generate_handoff_summary, generate_session_summary,
    update_unresolved_count, should_escalate, detect_role,
)
from system_prompt import build_system_prompt

# ===========================================================================
# STYLES
# ===========================================================================
CSS = """
/* ---- Google Fonts ---- */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

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
    grid-template-columns: 220px 1fr 280px;
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
    border-bottom: 2px solid #2A7AFF;
    flex-shrink: 0;
}
.top-bar-logo {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2A7AFF;
}
.top-bar-title { font-size: 0.9rem; font-weight: 500; color: #E8EDF5; }
.top-bar-sub { font-size: 0.72rem; color: #6B7A99; margin-left: 0.5rem; }
.top-bar-badge {
    margin-left: auto;
    background: rgba(42,122,255,0.15);
    color: #2A7AFF;
    border: 1px solid rgba(42,122,255,0.3);
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

.sidebar-value {
    font-size: 0.78rem;
    color: #1C2333;
    font-weight: 500;
}

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

.sidebar-divider {
    border: none;
    border-top: 1px solid #E2E6EF;
    margin: 0.75rem 0;
}

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

.meta-block {
    font-size: 0.72rem;
    color: #6B7A99;
    line-height: 1.7;
}

/* ---- Main chat panel ---- */
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
.msg-row {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    max-width: 100%;
}
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 30px; height: 30px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 700;
    flex-shrink: 0; margin-top: 2px;
}
.avatar-ai   { background: #1C2333; color: #2A7AFF; }
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
    color: #1C2333;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-user {
    background: #1C2333;
    color: #E8EDF5;
    border-top-right-radius: 3px;
}
.msg-ts {
    font-size: 0.65rem;
    color: #9BA8BF;
    margin-top: 3px;
    padding: 0 0.2rem;
}
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
.bubble hr {
    border: none;
    border-top: 1px solid rgba(0,0,0,0.08);
    margin: 0.5rem 0;
}
.bubble table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.8em;
    margin: 0.4rem 0;
}
.bubble th, .bubble td {
    border: 1px solid #dde;
    padding: 3px 8px;
    text-align: left;
}
.bubble th { background: #f0f4f8; font-weight: 600; }

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
.typing-dots {
    display: flex; gap: 4px; align-items: center; padding: 0.3rem 0;
}
.dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #2A7AFF;
    animation: pulse 1.2s infinite ease-in-out;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse {
    0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
    40% { transform: scale(1.0); opacity: 1; }
}

/* ---- Input area ---- */
.input-area {
    border-top: 1px solid #E2E6EF;
    background: #FFFFFF;
    padding: 0.85rem 1.1rem;
    flex-shrink: 0;
}
.input-row {
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
}
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
.input-row textarea:focus { border-color: #2A7AFF; background: #FFFFFF; }
.input-row textarea::placeholder { color: #9BA8BF; }
.send-btn {
    background: #2A7AFF !important;
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
.send-btn:hover { background: #1A60E0 !important; }
.send-btn:disabled { background: #9BA8BF !important; cursor: not-allowed; }
.input-hint {
    font-size: 0.65rem;
    color: #9BA8BF;
    margin-top: 0.4rem;
}

/* ---- Right panel ---- */
.right-panel {
    background: #FFFFFF;
    border-left: 1px solid #E2E6EF;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.panel-tabs {
    display: flex;
    border-bottom: 1px solid #E2E6EF;
    flex-shrink: 0;
}
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
.tab-btn.active { color: #2A7AFF; border-bottom-color: #2A7AFF; }
.tab-btn:hover:not(.active) { color: #1C2333; }

.tab-content { padding: 1rem; flex: 1; }

.panel-empty {
    color: #9BA8BF;
    font-size: 0.78rem;
    text-align: center;
    padding: 2rem 1rem;
    font-style: italic;
    line-height: 1.5;
}

.summary-box {
    background: #F4F6F9;
    border: 1px solid #E2E6EF;
    border-radius: 6px;
    padding: 0.85rem;
    font-size: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.65;
    white-space: pre-wrap;
    color: #2D3A52;
}
.handoff-box {
    background: #FFFDF0;
    border: 1px solid #FFD54F;
    border-radius: 6px;
    padding: 0.85rem;
    font-size: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.65;
    white-space: pre-wrap;
    color: #3D2B00;
}
.panel-section-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.label-summary { color: #2A7AFF; }
.label-handoff { color: #E65100; }

/* Shiny default overrides */
.shiny-input-container { margin-bottom: 0 !important; }
.form-control, .selectize-input {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.8rem !important;
    border-color: #CBD2E0 !important;
    border-radius: 6px !important;
}
.selectize-input { padding: 5px 8px !important; }
select.form-control { height: 34px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD2E0; border-radius: 10px; }
"""

JS = """
// Enter to send (Shift+Enter for newline)
document.addEventListener('keydown', function(e) {
    if (e.target.id === 'user_input' && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('send_btn').click();
    }
});

// Auto-scroll chat to bottom
const observer = new MutationObserver(() => {
    const cw = document.querySelector('.chat-window');
    if (cw) cw.scrollTop = cw.scrollHeight;
});
document.addEventListener('DOMContentLoaded', () => {
    const cw = document.querySelector('.chat-window');
    if (cw) observer.observe(cw, { childList: true, subtree: true });
});

// Tab switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
    document.querySelector('[data-tab="' + tab + '"]').classList.add('active');
    document.getElementById('pane-' + tab).style.display = 'block';
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
            ui.div({"class": "top-bar-badge"}, "MVP Pilot"),
        ),

        # ---- LEFT SIDEBAR ----
        ui.div({"class": "left-sidebar"},

            ui.div({"class": "sidebar-label"}, "Your Name"),
            ui.input_text("customer_name", None, placeholder="Enter your name"),

            ui.div({"class": "sidebar-label"}, "Your Role"),
            ui.input_select("customer_role", None,
                choices={v: l for v, l in ROLES},
                selected="",
            ),

            ui.div({"class": "sidebar-label"}, "Session Status"),
            ui.output_ui("session_status_ui"),

            ui.div({"class": "sidebar-label"}, "Escalation"),
            ui.output_ui("escalation_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),

            ui.input_action_button("end_session", "End Session",
                class_="end-btn"),

            ui.tags.hr({"class": "sidebar-divider"}),

            ui.div({"class": "sidebar-label"}, "Implementation"),
            ui.div({"class": "meta-block"},
                ui.tags.div("Customer: State Univ. RC"),
                ui.tags.div("PS Lead: Meredith Callahan"),
                ui.tags.div("Phase: 1 — Setup & Pilot"),
                ui.tags.div("Next due: Resource limits (Mar 27)"),
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
                    "Enter to send · Shift+Enter for new line · "
                    "Session summaries are shared with your PS lead"
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
                ui.div({"id": "pane-summary", "class": "tab-pane"},
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

    # ---- Session state ----
    messages       = reactive.value([])   # list of {"role": ..., "content": ..., "ts": ...}
    started        = reactive.value(False)
    ended          = reactive.value(False)
    start_ts       = reactive.value(None)
    escalated      = reactive.value(False)
    unresolved     = reactive.value(0)
    handoff_text   = reactive.value("")
    session_summary= reactive.value("")
    is_thinking    = reactive.value(False)

    # ---- Status pill ----
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

    # ---- Escalation indicator ----
    @output
    @render.ui
    def escalation_ui():
        if not started():
            return ui.div({"style": "font-size:0.72rem; color:#9BA8BF;"}, "No active session")
        elif escalated():
            return ui.div({"class": "escalation-banner"},
                "⚠ Escalated to Meredith Callahan")
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

            html_content = format_message(m["content"])

            elements.append(
                ui.div({"class": row_cls},
                    ui.div({"class": av_cls}, av_lbl),
                    ui.div(
                        ui.div({"class": bub_cls}, ui.HTML(html_content)),
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
        if not s:
            return ui.div({"class": "panel-empty"},
                "Session summary will appear here when the session ends.",
                ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Click 'End Session' to generate the PS-facing summary.")
            )
        return ui.div(
            ui.div({"class": "panel-section-label label-summary"}, "PS Session Summary"),
            ui.div({"class": "summary-box"}, s),
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
                    "or when the customer asks to reach the PS team.")
            )
        return ui.div(
            ui.div({"class": "panel-section-label label-handoff"}, "Escalation Handoff Summary"),
            ui.div({"style": "font-size:0.72rem; color:#9BA8BF; margin-bottom:0.5rem;"},
                "Share with Meredith Callahan so she can pick up without context gaps."),
            ui.div({"class": "handoff-box"}, h),
        )

    # ---- Send button ----
    @reactive.effect
    @reactive.event(input.send_btn)
    def handle_send():
        if ended():
            return

        # Read user input via JS value (Shiny for Python textarea workaround)
        user_text = input.user_input()
        if not user_text or not user_text.strip():
            return

        # Clear input
        ui.update_text("user_input", value="")

        # Start session on first message
        if not started():
            started.set(True)
            start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Detect role from text if dropdown not set
        current_role = input.customer_role()
        if not current_role:
            detected = detect_role(user_text)
            if detected:
                current_role = detected

        # Update unresolved counter
        unresolved.set(update_unresolved_count(unresolved(), user_text))

        # Check escalation
        do_escalate = should_escalate(unresolved(), user_text, escalated())

        # Add user message
        ts = datetime.now().strftime("%H:%M")
        current_msgs = messages()
        new_msgs = current_msgs + [{"role": "user", "content": user_text, "ts": ts}]
        messages.set(new_msgs)

        # Show typing indicator
        is_thinking.set(True)

        # Build API messages (no ts field)
        api_msgs = [{"role": m["role"], "content": m["content"]} for m in new_msgs]

        # Build system prompt
        sys_prompt = build_system_prompt(
            customer_name=input.customer_name() or "",
            customer_role=current_role or "",
        )

        # Call API
        try:
            response_text = call_claude(messages=api_msgs, system_prompt=sys_prompt)
            is_thinking.set(False)

            # Handle escalation
            if do_escalate and not escalated():
                escalated.set(True)
                handoff = generate_handoff_summary(
                    messages=api_msgs,
                    customer_name=input.customer_name() or "Not provided",
                    customer_role=current_role or "Not specified",
                )
                handoff_text.set(handoff)
                response_text = (
                    response_text
                    + "\n\n---\n**HANDOFF SUMMARY FOR YOUR PS LEAD (Meredith Callahan)**\n\n"
                    + handoff
                )

            ts_resp = datetime.now().strftime("%H:%M")
            messages.set(messages() + [{"role": "assistant", "content": response_text, "ts": ts_resp}])

        except Exception as e:
            is_thinking.set(False)
            error_msg = (
                "I encountered an error connecting to the assistant backend. "
                "Please try again or contact your PS lead directly.\n\n"
                f"Technical detail: {str(e)}"
            )
            messages.set(messages() + [{"role": "assistant", "content": error_msg,
                                         "ts": datetime.now().strftime("%H:%M")}])

    # ---- End Session ----
    @reactive.effect
    @reactive.event(input.end_session)
    def handle_end_session():
        if not started() or ended():
            return

        ended.set(True)

        api_msgs = [{"role": m["role"], "content": m["content"]} for m in messages()]
        current_role = input.customer_role() or "Not specified"

        summary = generate_session_summary(
            messages=api_msgs,
            customer_name=input.customer_name() or "Not provided",
            customer_role=current_role,
            session_start=start_ts() or "Unknown",
            escalated=escalated(),
            handoff_text=handoff_text(),
        )
        session_summary.set(summary)

        ts = datetime.now().strftime("%H:%M")
        messages.set(messages() + [{
            "role": "assistant",
            "content": (
                "**Session ended.** A summary has been generated and is visible in the "
                "PS Summary tab. Thank you — Meredith Callahan will have full context "
                "of what we covered today."
            ),
            "ts": ts,
        }])


# ===========================================================================
# MARKDOWN-LIKE FORMATTER
# ===========================================================================
def format_message(text: str) -> str:
    """Convert basic markdown patterns to HTML for message bubbles."""
    # Horizontal rules
    text = re.sub(r'\n---\n', '\n<hr>\n', text)

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Process line by line for lists and tables
    lines = text.split('\n')
    output = []
    in_list = False
    in_table = False
    table_html = ""

    for line in lines:
        stripped = line.strip()

        # Table detection
        if stripped.startswith('|') and stripped.endswith('|'):
            if re.match(r'^\|[-\s|:]+\|$', stripped):
                continue  # separator row
            if not in_table:
                in_table = True
                table_html = '<table>'
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            row = ''.join(f'<td>{c}</td>' for c in cells)
            table_html += f'<tr>{row}</tr>'
            continue
        else:
            if in_table:
                output.append(table_html + '</table>')
                table_html = ''
                in_table = False

        # Lists
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

    # Paragraphs: split on double newlines
    paragraphs = re.split(r'\n{2,}', text)
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        p = p.replace('\n', '<br>')
        if re.match(r'^<(ul|ol|table|hr)', p):
            result.append(p)
        else:
            result.append(f'<p>{p}</p>')

    return '\n'.join(result)


# ===========================================================================
# RUN
# ===========================================================================
app = App(app_ui, server)
