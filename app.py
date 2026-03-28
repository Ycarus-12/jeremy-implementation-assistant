# app.py v3 — Posit Cloud Implementation Assistant
# v3 fixes:
#   - Remove exchange count from sidebar
#   - Remove version number from top bar
#   - Sidebar shows upcoming/overdue tasks (name + due date only), Monday-ready
#   - Expandable sidebar task section
#   - Transparency notice renders as single container
#   - Topic-aware escalation (not count-based), user-prompted not auto
#   - Escalation tab renders immediately on trigger, supports multiple escalations
#   - Rephrased handoff fields: "Goal:", "What was being discussed:"
#   - Scope dismissal never sets escalation flag

from shiny import App, reactive, render, ui
from datetime import datetime, date
import re

from api import (
    call_claude,
    generate_handoff_summary,
    generate_session_summary,
    detect_role,
    check_scope_question,
    check_session_end_intent,
    check_unresolved_response,
    check_resolution_signal,
    check_explicit_escalation,
    TopicEscalationTracker,
)
from system_prompt import build_system_prompt
from knowledge_base import get_sidebar_tasks

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

.app-shell {
    display: grid;
    grid-template-columns: 230px 1fr 300px;
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
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 600;
}
.chip-waiting   { background: #EEF2FF; color: #4361EE; }
.chip-active    { background: #E8F5E9; color: #2E7D32; }
.chip-ended     { background: #FFF3E0; color: #E65100; }
.chip-escalated { background: #FFF0F0; color: #C62828; }

.escalation-banner {
    background: #FFF8E1; border: 1px solid #FFD54F;
    border-radius: 6px; padding: 0.5rem 0.6rem;
    font-size: 0.72rem; color: #5D4037; line-height: 1.4;
}

.sidebar-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.75rem 0; }

.end-btn {
    width: 100%;
    background: #FFF0F0 !important; color: #C62828 !important;
    border: 1px solid #FFCDD2 !important; border-radius: 6px !important;
    font-size: 0.75rem !important; font-weight: 600 !important;
    padding: 0.45rem !important; cursor: pointer;
    font-family: inherit !important; transition: background 0.15s;
}
.end-btn:hover { background: #FFEBEE !important; }
.end-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.meta-block { font-size: 0.72rem; color: #6B7A99; line-height: 1.7; }

/* ---- Task sections in sidebar ---- */
.task-section { margin-top: 0.25rem; }

.task-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding: 0.3rem 0;
    border-radius: 4px;
}
.task-section-header:hover { background: #F4F6F9; }

.task-section-title {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}
.task-title-overdue  { color: #C62828; }
.task-title-upcoming { color: #447099; }

.task-toggle-icon { font-size: 0.6rem; color: #9BA8BF; transition: transform 0.15s; }
.task-toggle-icon.collapsed { transform: rotate(-90deg); }

.task-list { margin-top: 0.2rem; }
.task-item {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.25rem 0.3rem;
    border-radius: 4px;
    font-size: 0.71rem;
    line-height: 1.4;
    gap: 0.4rem;
}
.task-item:hover { background: #F4F6F9; }
.task-item-name  { color: #2D3A52; flex: 1; }
.task-item-due   { font-size: 0.67rem; white-space: nowrap; flex-shrink: 0; font-weight: 500; }
.task-item-due-overdue  { color: #C62828; }
.task-item-due-upcoming { color: #447099; }

.task-empty { font-size: 0.7rem; color: #9BA8BF; font-style: italic; padding: 0.2rem 0.3rem; }

.expand-hint {
    font-size: 0.62rem;
    color: #9BA8BF;
    font-style: italic;
    margin-top: 0.15rem;
}

/* ---- Chat panel ---- */
.chat-panel {
    display: flex; flex-direction: column;
    background: #F4F6F9; overflow: hidden; min-height: 0;
}
.chat-window {
    flex: 1; overflow-y: auto;
    padding: 1.25rem;
    display: flex; flex-direction: column; gap: 1rem;
    scroll-behavior: smooth; min-height: 0;
}

/* ---- Message bubbles ---- */
.msg-row { display: flex; align-items: flex-start; gap: 0.6rem; max-width: 100%; }
.msg-row.user { flex-direction: row-reverse; }

.avatar {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 700;
    flex-shrink: 0; margin-top: 2px;
}
.avatar-ai   { background: #1C2333; color: #447099; }
.avatar-user { background: #E2E6EF; color: #6B7A99; }

.bubble {
    max-width: 76%; padding: 0.65rem 0.9rem;
    border-radius: 12px; font-size: 0.845rem; line-height: 1.6;
}
.bubble-ai {
    background: #FFFFFF; border: 1px solid #E2E6EF;
    border-top-left-radius: 3px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-user { background: #1C2333; color: #E8EDF5; border-top-right-radius: 3px; }

/* Transparency notice — SINGLE container */
.transparency-notice {
    background: #EEF4FA;
    border-left: 3px solid #447099;
    border-radius: 0 6px 6px 0;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.75rem;
    font-size: 0.8rem;
    color: #2D4A63;
    line-height: 1.55;
}

/* Scope choice prompt */
.scope-choice {
    background: #FFF8E1; border: 1px solid #FFD54F;
    border-radius: 8px; padding: 0.65rem 0.9rem; margin-top: 0.5rem;
    font-size: 0.82rem;
}
.scope-choice-btns { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.scope-btn {
    padding: 0.3rem 0.85rem; border-radius: 5px;
    font-size: 0.78rem; font-weight: 600;
    cursor: pointer; border: none; font-family: inherit; transition: background 0.15s;
}
.scope-btn-escalate { background: #447099; color: white; }
.scope-btn-escalate:hover { background: #355880; }
.scope-btn-dismiss  { background: #E2E6EF; color: #4A5568; }
.scope-btn-dismiss:hover { background: #CBD2E0; }

/* Escalation suggestion prompt */
.escalation-prompt {
    background: #FFF3E0; border: 1px solid #FFB74D;
    border-left: 3px solid #F57C00;
    border-radius: 0 8px 8px 0; padding: 0.65rem 0.9rem; margin-top: 0.5rem;
    font-size: 0.82rem; color: #3E2723; line-height: 1.5;
}
.escalation-prompt-btns { display: flex; gap: 0.5rem; margin-top: 0.5rem; }

/* Source badge */
.source-badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.68rem; color: #6B7A99; margin-top: 0.4rem;
    padding: 2px 6px; background: #F4F6F9;
    border-radius: 4px; border: 1px solid #E2E6EF;
}

/* Feedback thumbs */
.feedback-row { display: flex; align-items: center; gap: 0.4rem; margin-top: 0.4rem; }
.feedback-label { font-size: 0.68rem; color: #9BA8BF; }
.thumb-btn {
    background: none; border: 1px solid #E2E6EF;
    border-radius: 4px; padding: 1px 6px;
    font-size: 0.75rem; cursor: pointer; transition: all 0.1s; line-height: 1.4;
}
.thumb-btn:hover { background: #F4F6F9; border-color: #CBD2E0; }
.thumb-btn.active-up   { background: #E8F5E9; border-color: #72994E; }
.thumb-btn.active-down { background: #FFEBEE; border-color: #C62828; }

.msg-ts { font-size: 0.65rem; color: #9BA8BF; margin-top: 3px; padding: 0 0.2rem; }
.user .msg-ts { text-align: right; }

/* Bubble content */
.bubble p { margin: 0 0 0.5rem 0; }
.bubble p:last-child { margin-bottom: 0; }
.bubble ul, .bubble ol { margin: 0.3rem 0; padding-left: 1.3rem; }
.bubble li { margin-bottom: 0.2rem; }
.bubble code {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.8em;
    background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 3px;
}
.bubble-user code { background: rgba(255,255,255,0.1); }
.bubble strong { font-weight: 600; }
.bubble hr { border: none; border-top: 1px solid rgba(0,0,0,0.08); margin: 0.5rem 0; }
.bubble table { border-collapse: collapse; width: 100%; font-size: 0.8em; margin: 0.4rem 0; }
.bubble th, .bubble td { border: 1px solid #dde; padding: 3px 8px; text-align: left; }
.bubble th { background: #f0f4f8; font-weight: 600; }

/* Empty state */
.empty-state {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: #9BA8BF; font-size: 0.82rem; text-align: center;
    gap: 0.5rem; padding: 2rem;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.25rem; }

/* Typing dots */
.typing-dots { display: flex; gap: 4px; align-items: center; padding: 0.3rem 0; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #447099; animation: pulse 1.2s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; } 40% { transform: scale(1.0); opacity: 1; } }

/* ---- Input area ---- */
.input-area { border-top: 1px solid #E2E6EF; background: #FFFFFF; padding: 0.85rem 1.1rem; flex-shrink: 0; }
.input-row { display: flex; gap: 0.5rem; align-items: flex-end; }
.input-row textarea {
    flex: 1; border: 1px solid #CBD2E0; border-radius: 8px;
    padding: 0.55rem 0.75rem; font-size: 0.845rem;
    font-family: 'IBM Plex Sans', sans-serif; resize: none;
    line-height: 1.5; min-height: 42px; max-height: 110px;
    background: #F4F6F9; color: #1C2333; outline: none;
    transition: border-color 0.15s, background 0.15s;
}
.input-row textarea:focus { border-color: #447099; background: #FFFFFF; }
.input-row textarea::placeholder { color: #9BA8BF; }
.send-btn {
    background: #447099 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    padding: 0 1.1rem !important; height: 42px;
    font-size: 0.845rem !important; font-weight: 600 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    cursor: pointer; flex-shrink: 0; transition: background 0.15s; white-space: nowrap;
}
.send-btn:hover { background: #355880 !important; }
.send-btn:disabled { background: #9BA8BF !important; cursor: not-allowed; }
.input-hint { font-size: 0.65rem; color: #9BA8BF; margin-top: 0.4rem; }

/* ---- Right panel ---- */
.right-panel {
    background: #FFFFFF; border-left: 1px solid #E2E6EF;
    overflow-y: auto; display: flex; flex-direction: column;
}
.panel-tabs { display: flex; border-bottom: 1px solid #E2E6EF; flex-shrink: 0; }
.tab-btn {
    flex: 1; padding: 0.65rem 0.5rem;
    font-size: 0.72rem; font-weight: 600;
    font-family: 'IBM Plex Sans', sans-serif;
    letter-spacing: 0.04em; text-transform: uppercase;
    border: none; background: transparent; color: #9BA8BF;
    cursor: pointer; border-bottom: 2px solid transparent;
    transition: all 0.15s; margin-bottom: -1px;
}
.tab-btn.active { color: #447099; border-bottom-color: #447099; }
.tab-btn:hover:not(.active) { color: #1C2333; }

.tab-content { padding: 1rem; flex: 1; overflow-y: auto; }
.tab-pane { display: none !important; }
.tab-pane.active { display: block !important; }

.panel-empty {
    color: #9BA8BF; font-size: 0.78rem; text-align: center;
    padding: 2rem 1rem; font-style: italic; line-height: 1.5;
}

/* PS Summary */
.summary-header {
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: #447099; margin-bottom: 0.75rem;
    display: flex; align-items: center; justify-content: space-between;
}
.followup-block {
    background: #FFF3E0; border: 1px solid #FFB74D;
    border-left: 4px solid #F57C00; border-radius: 6px;
    padding: 0.75rem; margin-bottom: 0.85rem;
}
.followup-label {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: #E65100; margin-bottom: 0.35rem;
}
.followup-content { font-size: 0.78rem; color: #3E2723; line-height: 1.55; }

.tags-row { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem; }
.topic-tag {
    background: #EEF4FA; color: #355880;
    border: 1px solid #C5D8EC; border-radius: 20px;
    padding: 1px 8px; font-size: 0.67rem; font-weight: 600;
}

.summary-field { margin-bottom: 0.65rem; }
.summary-field-label {
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #9BA8BF; margin-bottom: 0.2rem;
}
.summary-field-value { font-size: 0.78rem; color: #1C2333; line-height: 1.55; }
.outcome-resolved { color: #2E7D32; font-weight: 600; }
.outcome-partial  { color: #E65100; font-weight: 600; }
.outcome-escalated { color: #C62828; font-weight: 600; }
.summary-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.65rem 0; }

/* Escalation tab */
.handoff-entry {
    background: #FFFDF0; border: 1px solid #FFD54F;
    border-radius: 6px; padding: 0.85rem; margin-bottom: 0.75rem;
    font-size: 0.78rem; line-height: 1.65; color: #3D2B00;
}
.handoff-entry-content {
    white-space: pre-wrap;
    font-size: 0.78rem; line-height: 1.65; color: #3D2B00;
}
.handoff-entry-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.5rem;
}
.handoff-entry-num {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #E65100;
}
.panel-section-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem; }
.label-handoff { color: #E65100; }

/* Copy buttons */
.copy-btn {
    background: none; border: 1px solid #E2E6EF; border-radius: 5px;
    padding: 2px 8px; font-size: 0.67rem; font-weight: 600; color: #6B7A99;
    cursor: pointer; font-family: inherit; transition: all 0.15s; white-space: nowrap;
}
.copy-btn:hover { background: #F4F6F9; border-color: #CBD2E0; color: #1C2333; }
.copy-btn.copied { color: #2E7D32; border-color: #72994E; background: #E8F5E9; }

/* Email format toggle */
.email-toggle-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; margin-top: 0.25rem; }
.email-toggle-label { font-size: 0.68rem; color: #6B7A99; }
.format-toggle-btn {
    background: none; border: 1px solid #E2E6EF; border-radius: 4px;
    padding: 2px 8px; font-size: 0.67rem; font-weight: 600; color: #6B7A99;
    cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.format-toggle-btn.active { background: #EEF4FA; border-color: #447099; color: #447099; }

/* ---- Info modal ---- */
.modal-overlay {
    display: none;
    position: fixed; inset: 0; z-index: 1000;
    background: rgba(28, 35, 51, 0.55);
    backdrop-filter: blur(3px);
    align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }

.modal-box {
    background: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    width: min(680px, 92vw);
    max-height: 85vh;
    display: flex; flex-direction: column;
    overflow: hidden;
}
.modal-header {
    background: #1C2333;
    color: white;
    padding: 1rem 1.25rem;
    display: flex; align-items: flex-start; justify-content: space-between;
    flex-shrink: 0;
}
.modal-header-title {
    font-size: 0.95rem; font-weight: 600; color: #E8EDF5; margin-bottom: 0.15rem;
}
.modal-header-sub { font-size: 0.72rem; color: #6B7A99; font-style: italic; }
.modal-close {
    background: none; border: none; color: #6B7A99;
    font-size: 1.2rem; cursor: pointer; padding: 0 0.25rem; line-height: 1;
    transition: color 0.15s; flex-shrink: 0; margin-left: 1rem; margin-top: 0.1rem;
}
.modal-close:hover { color: #E8EDF5; }

.modal-body {
    padding: 1.5rem 1.75rem;
    overflow-y: auto;
    flex: 1;
    font-size: 0.845rem;
    line-height: 1.65;
    color: #2D3A52;
}
.modal-body h3 {
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; color: #447099;
    margin: 1.25rem 0 0.5rem 0; border-bottom: 1px solid #E2E6EF; padding-bottom: 0.3rem;
}
.modal-body h3:first-child { margin-top: 0; }
.modal-body p { margin-bottom: 0.75rem; }
.modal-body p:last-child { margin-bottom: 0; }
.modal-body ul { padding-left: 1.3rem; margin-bottom: 0.75rem; }
.modal-body li { margin-bottom: 0.3rem; }
.modal-body strong { font-weight: 600; color: #1C2333; }

.modal-warning {
    background: #FFF3E0; border: 1px solid #FFB74D;
    border-left: 4px solid #F57C00;
    border-radius: 0 6px 6px 0;
    padding: 0.65rem 0.85rem; margin-bottom: 0.75rem;
    font-size: 0.82rem; color: #3E2723; line-height: 1.5;
}
.modal-warning strong { color: #BF360C; }

.modal-contact {
    background: #EEF4FA; border: 1px solid #C5D8EC;
    border-radius: 6px; padding: 0.65rem 0.85rem;
    font-size: 0.82rem; color: #2D4A63;
}
.modal-contact a { color: #447099; text-decoration: none; font-weight: 600; }
.modal-contact a:hover { text-decoration: underline; }

.modal-footer {
    background: #F4F6F9; border-top: 1px solid #E2E6EF;
    padding: 0.75rem 1.75rem; font-size: 0.72rem; color: #9BA8BF;
    font-style: italic; flex-shrink: 0;
}

/* ---- What am I looking at button ---- */
.info-btn {
    background: none !important; border: 1px solid rgba(68,112,153,0.4) !important;
    color: #447099 !important; border-radius: 5px !important;
    padding: 2px 10px !important; font-size: 0.68rem !important;
    font-weight: 600 !important; cursor: pointer; font-family: inherit !important;
    transition: all 0.15s; white-space: nowrap; margin-left: 0.75rem;
}
.info-btn:hover { background: rgba(68,112,153,0.1) !important; border-color: #447099 !important; }

/* ---- Demo launchers ---- */
.demo-launchers {
    display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.25rem;
}
.demo-btn {
    background: #F4F6F9 !important; border: 1px solid #E2E6EF !important;
    color: #2D3A52 !important; border-radius: 5px !important;
    font-size: 0.71rem !important; font-weight: 500 !important;
    padding: 0.35rem 0.6rem !important; cursor: pointer;
    font-family: inherit !important; text-align: left !important;
    transition: all 0.15s; line-height: 1.3;
}
.demo-btn:hover { background: #EEF4FA !important; border-color: #C5D8EC !important; color: #447099 !important; }
.demo-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.demo-btn-name { font-weight: 600; display: block; }
.demo-btn-role { font-size: 0.65rem; color: #6B7A99; display: block; }

/* ---- New session button ---- */
.new-session-btn {
    width: 100%;
    background: #EEF4FA !important; color: #447099 !important;
    border: 1px solid #C5D8EC !important; border-radius: 6px !important;
    font-size: 0.75rem !important; font-weight: 600 !important;
    padding: 0.45rem !important; cursor: pointer;
    font-family: inherit !important; transition: background 0.15s;
    margin-top: 0.4rem;
}
.new-session-btn:hover { background: #D6E8F5 !important; }

/* ---- Contact block in sidebar ---- */
.contact-block {
    background: #F4F6F9; border: 1px solid #E2E6EF;
    border-radius: 6px; padding: 0.5rem 0.6rem;
    font-size: 0.71rem; color: #4A5568; line-height: 1.6;
}
.contact-block a { color: #447099; text-decoration: none; font-weight: 600; display: block; }
.contact-block a:hover { text-decoration: underline; }
.contact-name { font-weight: 600; color: #1C2333; }

/* ---- Summary loading state ---- */
.summary-loading {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 2rem 1rem; gap: 0.75rem; color: #6B7A99;
    font-size: 0.8rem;
}
.summary-loading-dots { display: flex; gap: 5px; }
.summary-loading-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #447099;
    animation: pulse 1.2s infinite ease-in-out;
}
.summary-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.summary-loading-dot:nth-child(3) { animation-delay: 0.4s; }

/* ---- Input disabled state ---- */
.input-row textarea:disabled {
    opacity: 0.5; cursor: not-allowed; background: #E8EDF5 !important;
}

/* Name warning */
.name-warning {
    font-size: 0.68rem; color: #E65100;
    margin-top: 0.2rem; display: none;
}
.name-warning.visible { display: block; }

/* Shiny overrides */
.shiny-input-container { margin-bottom: 0 !important; }
.form-control, .selectize-input { font-family: 'IBM Plex Sans', sans-serif !important; font-size: 0.8rem !important; border-color: #CBD2E0 !important; border-radius: 6px !important; }
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
        const btn = document.getElementById('send_btn');
        if (btn && !btn.disabled) btn.click();
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

// Tab switching — CSS !important controls display, JS only manages .active class
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    const btn  = document.querySelector('[data-tab="' + tab + '"]');
    const pane = document.getElementById('pane-' + tab);
    if (btn)  btn.classList.add('active');
    if (pane) pane.classList.add('active');
}

// Collapsible task sections
function toggleTaskSection(sectionId) {
    const list = document.getElementById(sectionId);
    const icon = document.getElementById(sectionId + '-icon');
    if (!list) return;
    const collapsed = list.style.display === 'none';
    list.style.display = collapsed ? 'block' : 'none';
    if (icon) icon.classList.toggle('collapsed', !collapsed);
}

// Copy to clipboard — two modes:
// 1. copyById(elementId, btnId) — copies text from element with given ID
// 2. copyFromBtn(btn) — walks up DOM from button to find sibling content div
function copyById(elementId, btnId) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.warn('copyById: element not found:', elementId);
        return;
    }
    const text = el.innerText || el.textContent || '';
    _doCopy(text, document.getElementById(btnId));
}

function copyFromBtn(btn) {
    // Walk up to the handoff-entry container, then find the content div
    const entry = btn.closest('.handoff-entry');
    if (!entry) { console.warn('copyFromBtn: no .handoff-entry parent found'); return; }
    // The content div is the last child of the entry (after the header)
    const contentDivs = entry.querySelectorAll(':scope > div:not(.handoff-entry-header)');
    const text = Array.from(contentDivs).map(d => d.innerText || d.textContent).join('\n').trim();
    _doCopy(text, btn);
}

function _doCopy(text, btn) {
    if (!text) { console.warn('_doCopy: nothing to copy'); return; }
    navigator.clipboard.writeText(text).then(() => {
        if (btn) {
            const orig = btn.innerText;
            btn.innerText = '✓ Copied';
            btn.classList.add('copied');
            setTimeout(() => { btn.innerText = orig; btn.classList.remove('copied'); }, 2000);
        }
    }).catch(err => {
        // Fallback for browsers that block clipboard API
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand('copy');
            if (btn) {
                const orig = btn.innerText;
                btn.innerText = '✓ Copied';
                btn.classList.add('copied');
                setTimeout(() => { btn.innerText = orig; btn.classList.remove('copied'); }, 2000);
            }
        } catch(e) {
            console.warn('Copy failed:', e);
        }
        document.body.removeChild(ta);
    });
}

// Legacy alias used by summary copy buttons
function copyToClipboard(elementId, btnId) {
    copyById(elementId, btnId);
}

// Thumb feedback
function sendFeedback(msgId, helpful) {
    const upBtn   = document.getElementById('up-'   + msgId);
    const downBtn = document.getElementById('down-' + msgId);
    if (upBtn)   upBtn.classList.toggle('active-up',    helpful);
    if (downBtn) downBtn.classList.toggle('active-down', !helpful);
    if (window.Shiny) Shiny.setInputValue('feedback_event', { msg_id: msgId, helpful: helpful }, { priority: 'event' });
}

// Summary format toggle
function toggleSummaryFormat(format) {
    document.getElementById('summary-structured').style.display = format === 'structured' ? 'block' : 'none';
    document.getElementById('summary-email').style.display      = format === 'email'      ? 'block' : 'none';
    document.querySelectorAll('.format-toggle-btn').forEach(b => b.classList.remove('active'));
    const btn = document.getElementById('fmt-' + format);
    if (btn) btn.classList.add('active');
}

// Info modal
function openInfoModal() {
    const m = document.getElementById('info-modal');
    if (m) m.classList.add('open');
}
function closeInfoModal() {
    const m = document.getElementById('info-modal');
    if (m) m.classList.remove('open');
}
// Close on overlay click
document.addEventListener('click', function(e) {
    const modal = document.getElementById('info-modal');
    if (modal && e.target === modal) closeInfoModal();
});
// Close on Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeInfoModal();
});

// Demo launcher — inject message and trigger send
function launchDemo(name, role, message) {
    if (window.Shiny) {
        Shiny.setInputValue('demo_launch', { name: name, role: role, message: message }, { priority: 'event' });
    }
}
"""

# ===========================================================================
# UI
# ===========================================================================
ROLES = [
    ("", "— Select your role —"),
    ("IT Admin / Technical Lead",             "IT Admin / Technical Lead"),
    ("Project Lead / Project Manager",        "Project Lead / Project Manager"),
    ("Executive Sponsor / Research Director", "Executive Sponsor / Research Director"),
    ("Researcher / End User",                 "Researcher / End User"),
    ("UAT Tester",                            "UAT Tester"),
]

MODAL_HTML = ui.div(
    {"class": "modal-overlay", "id": "info-modal"},
    ui.div({"class": "modal-box"},
        # Header
        ui.div({"class": "modal-header"},
            ui.div(
                ui.div({"class": "modal-header-title"}, "Posit Cloud Implementation Assistant"),
                ui.div({"class": "modal-header-sub"}, "A self-service guide for your Posit Cloud implementation"),
            ),
            ui.tags.button("✕", {"class": "modal-close", "onclick": "closeInfoModal()"}),
        ),
        # Body
        ui.div({"class": "modal-body"},

            ui.tags.h3("What this is"),
            ui.tags.p(
                "This tool is your on-demand implementation resource during your Posit Cloud deployment "
                "at State University Research Computing. Instead of waiting for your PS team to be available, "
                "you can get answers to common implementation questions, check on project status, and work "
                "through tasks — right here, right now."
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("This assistant is a starting point, not a final authority."),
                " Your PS lead, Meredith Callahan, is the ultimate source of truth on all things related "
                "to your implementation. If anything this tool tells you doesn't feel right, contradicts "
                "something Meredith has told you, or leaves you uncertain — stop and reach out to her directly. "
                "Always. No exceptions."
            ),
            ui.tags.p(
                "Every conversation is summarized and shared with Meredith automatically, so she always has "
                "full context on where you are. You'll never need to repeat yourself when you connect with her directly."
            ),

            ui.tags.h3("Who it's for"),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>IT Admins</strong> — SSO configuration, account provisioning, resource limits, space setup")),
                ui.tags.li(ui.HTML("<strong>Project Managers</strong> — milestone status, task ownership, timeline questions")),
                ui.tags.li(ui.HTML("<strong>Executive Sponsors</strong> — high-level project health, upcoming decisions, go/no-go readiness")),
                ui.tags.li(ui.HTML("<strong>Researchers</strong> — getting started, creating projects, uploading data, understanding your environment")),
                ui.tags.li(ui.HTML("<strong>UAT Testers</strong> — running the UAT checklist, documenting issues, escalation paths")),
            ),

            ui.tags.h3("What it knows"),
            ui.tags.p("The assistant has access to three things — and only these three things:"),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Your project plan</strong> — milestones, task owners, due dates, and current status")),
                ui.tags.li(ui.HTML("<strong>Your Statement of Work</strong> — what's in scope, what's not, and the acceptance criteria")),
                ui.tags.li(ui.HTML("<strong>Posit Cloud task guides</strong> — step-by-step instructions for the most common implementation tasks")),
            ),
            ui.tags.p(
                "It will not speculate, guess, or make things up. If it doesn't know the answer, it will tell you "
                "— and offer to flag it for Meredith."
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("When in doubt about any answer this tool gives you,"),
                " treat it as a starting point and confirm with your PS lead before acting on it."
            ),

            ui.tags.h3("What it won't do"),
            ui.tags.ul(
                ui.tags.li("Make any changes to your systems or configuration"),
                ui.tags.li("Answer questions about pricing, contracts, or licensing"),
                ui.tags.li("Commit to scope changes or new deliverables"),
                ui.tags.li("Override guidance your PS team has already given you"),
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("If this tool ever appears to contradict something Meredith or the PS team has told you,"),
                " disregard the tool and contact Meredith immediately. The PS team's guidance always takes precedence."
            ),

            ui.tags.h3("How escalation works"),
            ui.tags.p(
                "If you get stuck, feel like you're going in circles, or simply want a human in the loop — "
                "don't hesitate. You don't need a reason to escalate. Just say \"I'd like to escalate this\" "
                "or \"Can you get Meredith involved?\" and the assistant will generate a structured handoff "
                "summary you can share with her instantly."
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("When in doubt, escalate."),
                " Meredith would rather hear from you early than have you operate on uncertain information."
            ),
            ui.div({"class": "modal-contact"},
                "Contact your PS lead directly at any time:",
                ui.tags.a(
                    "meredith.flaring453@passmail.net",
                    {"href": "mailto:meredith.flaring453@passmail.net"}
                ),
            ),

            ui.tags.h3("How to use it"),
            ui.tags.ul(
                ui.tags.li("Enter your name and select your role in the left sidebar"),
                ui.tags.li("Ask your question or describe what you're trying to do"),
                ui.tags.li(ui.HTML("When you're done, click <strong>End Session</strong> — a PS-facing summary is generated automatically")),
            ),
        ),
        # Footer
        ui.div({"class": "modal-footer"},
            "This tool is a Posit Professional Services pilot. It is intended to support — not replace — your PS team. "
            "Content is specific to the SURC implementation. Meredith Callahan remains the authoritative source "
            "on all aspects of your implementation."
        ),
    ),
)

app_ui = ui.page_fixed(
    ui.tags.head(
        ui.tags.style(CSS),
        ui.tags.script(JS),
        # Reactive style injection for input disabled state
        ui.output_ui("input_state_ui"),
        # Reactive escalation tab switch
        ui.output_ui("escalation_switch_ui"),
    ),
    # Info modal (rendered outside app-shell so it overlays everything)
    MODAL_HTML,

    ui.div({"class": "app-shell"},

        # ---- TOP BAR ----
        ui.div({"class": "top-bar"},
            ui.div({"class": "top-bar-logo"}, "Posit"),
            ui.div({"class": "top-bar-title"}, "Cloud Implementation Assistant"),
            ui.div({"class": "top-bar-sub"}, "State University Research Computing"),
            ui.tags.button("? What am I looking at",
                {"class": "info-btn", "onclick": "openInfoModal()"}),
            ui.div({"class": "top-bar-badge"}, "MVP Pilot"),
        ),

        # ---- LEFT SIDEBAR ----
        ui.div({"class": "left-sidebar"},
            ui.div({"class": "sidebar-label"}, "Your Name"),
            ui.input_text("customer_name", None, placeholder="Enter your name"),
            ui.output_ui("name_warning_ui"),

            ui.div({"class": "sidebar-label"}, "Your Role"),
            ui.input_select("customer_role", None,
                choices={v: l for v, l in ROLES}, selected=""),

            ui.div({"class": "sidebar-label"}, "Session Status"),
            ui.output_ui("session_status_ui"),

            ui.div({"class": "sidebar-label"}, "Escalation"),
            ui.output_ui("escalation_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),
            ui.input_action_button("end_session", "End Session", class_="end-btn"),
            ui.input_action_button("new_session", "↺ New Session", class_="new-session-btn"),
            ui.tags.hr({"class": "sidebar-divider"}),

            # Demo launchers
            ui.div({"class": "sidebar-label"}, "Demo Quick-Start"),
            ui.div({"class": "demo-launchers"},
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "Derek Huang"),
                    ui.span({"class": "demo-btn-role"}, "IT Admin / Technical Lead"),
                    {"class": "demo-btn", "id": "demo-derek",
                     "onclick": "launchDemo('Derek Huang','IT Admin / Technical Lead','Hi — I\\'m Derek, the IT Admin. I need help setting the default resource limits for researchers. Can you walk me through it?')"},
                ),
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "Dr. Kim Osei"),
                    ui.span({"class": "demo-btn-role"}, "Executive Sponsor"),
                    {"class": "demo-btn", "id": "demo-kim",
                     "onclick": "launchDemo('Dr. Kim Osei','Executive Sponsor / Research Director','Hi, I\\'m Dr. Osei — Research Computing Director. Can you give me a quick status update on where we stand with the implementation?')"},
                ),
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "UAT Tester"),
                    ui.span({"class": "demo-btn-role"}, "UAT Tester"),
                    {"class": "demo-btn", "id": "demo-uat",
                     "onclick": "launchDemo('UAT Tester','UAT Tester','I\\'m running UAT for the pilot group. Can you walk me through the full checklist and what I need to verify?')"},
                ),
            ),

            ui.tags.hr({"class": "sidebar-divider"}),

            # Implementation meta
            ui.div({"class": "sidebar-label"}, "Implementation"),
            ui.div({"class": "meta-block"},
                ui.tags.div("Customer: State Univ. RC"),
                ui.tags.div("PS Lead: Meredith Callahan"),
                ui.tags.div("Phase: 1 — Setup & Pilot"),
            ),

            # Task sections (collapsible, Monday-ready)
            ui.output_ui("sidebar_tasks_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),

            # Contact block
            ui.div({"class": "sidebar-label"}, "Contact PS Lead"),
            ui.div({"class": "contact-block"},
                ui.span({"class": "contact-name"}, "Meredith Callahan"),
                ui.tags.a(
                    "meredith.flaring453@passmail.net",
                    {"href": "mailto:meredith.flaring453@passmail.net"},
                ),
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
                ui.div({"id": "pane-summary", "class": "tab-pane active"},
                    ui.output_ui("summary_panel_ui")),
                ui.div({"id": "pane-escalation", "class": "tab-pane"},
                    ui.output_ui("escalation_panel_ui")),
            ),
        ),
    ),
)


# ===========================================================================
# SERVER
# ===========================================================================
def server(input, output, session):

    # ---- State ----
    messages           = reactive.value([])
    started            = reactive.value(False)
    ended              = reactive.value(False)
    start_ts           = reactive.value(None)
    escalated          = reactive.value(False)
    handoff_entries    = reactive.value([])
    session_summary    = reactive.value("")
    email_summary      = reactive.value("")
    summary_generating = reactive.value(False)
    is_thinking        = reactive.value(False)
    input_disabled     = reactive.value(False)   # drives textarea/button disabled state
    name_warned        = reactive.value(False)    # drives name warning visibility
    switch_to_esc      = reactive.value(0)        # increment to trigger tab switch
    msg_count          = reactive.value(0)
    feedback_log       = reactive.value([])
    unresolved_log     = reactive.value([])
    scope_pending      = reactive.value(False)

    tracker = TopicEscalationTracker()

    # ---- Input disabled state — driven by reactive, no JS injection ----
    @output
    @render.ui
    def input_state_ui():
        disabled = input_disabled()
        if disabled:
            return ui.tags.style("""
                #user_input { pointer-events: none; opacity: 0.5; background: #E8EDF5 !important; }
                #send_btn   { pointer-events: none; opacity: 0.5; background: #9BA8BF !important; }
            """)
        else:
            return ui.tags.style("""
                #user_input { pointer-events: auto; opacity: 1; }
                #send_btn   { pointer-events: auto; opacity: 1; }
            """)

    # ---- Name warning visibility ----
    @output
    @render.ui
    def name_warning_ui():
        if name_warned():
            return ui.div(
                {"class": "name-warning visible"},
                "Please enter your name before starting."
            )
        return ui.div({"class": "name-warning"})

    # ---- Escalation tab switch — fires once per escalation ----
    @output
    @render.ui
    def escalation_switch_ui():
        # Read the counter to make this reactive to it
        _ = switch_to_esc()
        # We only need to produce JS once when the value changes
        if switch_to_esc() > 0:
            return ui.tags.script("switchTab('escalation');")
        return ui.div()

    # ---- Sidebar task section ----
    @output
    @render.ui
    def sidebar_tasks_ui():
        tasks = get_sidebar_tasks(today=date.today())
        overdue  = tasks["overdue"]
        upcoming = tasks["upcoming"]

        children = []

        # Overdue section
        children.append(
            ui.div({"class": "task-section"},
                ui.div(
                    {"class": "task-section-header",
                     "onclick": "toggleTaskSection('task-list-overdue')"},
                    ui.span({"class": "task-section-title task-title-overdue"},
                        f"⚠ Overdue ({len(overdue)})"),
                    ui.span({"class": "task-toggle-icon", "id": "task-list-overdue-icon"}, "▾"),
                ),
                ui.div({"id": "task-list-overdue", "class": "task-list"},
                    *(
                        ui.div({"class": "task-item"},
                            ui.span({"class": "task-item-name"}, t["name"]),
                            ui.span({"class": "task-item-due task-item-due-overdue"}, t["due"]),
                        )
                        for t in overdue
                    ) if overdue else [ui.div({"class": "task-empty"}, "None")]
                ),
            )
        )

        # Upcoming section
        children.append(
            ui.div({"class": "task-section"},
                ui.div(
                    {"class": "task-section-header",
                     "onclick": "toggleTaskSection('task-list-upcoming')"},
                    ui.span({"class": "task-section-title task-title-upcoming"},
                        f"📅 Coming Up ({len(upcoming)})"),
                    ui.span({"class": "task-toggle-icon", "id": "task-list-upcoming-icon"}, "▾"),
                ),
                ui.div({"id": "task-list-upcoming", "class": "task-list"},
                    *(
                        ui.div({"class": "task-item"},
                            ui.span({"class": "task-item-name"}, t["name"]),
                            ui.span({"class": "task-item-due task-item-due-upcoming"}, t["due"]),
                        )
                        for t in upcoming
                    ) if upcoming else [ui.div({"class": "task-empty"}, "None in next 14 days")]
                ),
                ui.div({"class": "expand-hint"}, "Click heading to collapse / expand"),
            )
        )

        return ui.div(*children)

    # ---- Session status ----
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

    # ---- Escalation status (no exchange count) ----
    @output
    @render.ui
    def escalation_ui():
        if not started():
            return ui.div({"style": "font-size:0.72rem; color:#9BA8BF;"}, "No active session")
        elif escalated():
            return ui.div({"class": "escalation-banner"}, "⚠ Escalated to Meredith Callahan")
        else:
            return ui.div({"style": "font-size:0.72rem; color:#2E7D32;"},
                "✓ No escalation triggered")

    # ---- Chat messages ----
    @output
    @render.ui
    def chat_messages_ui():
        msgs    = messages()
        thinking = is_thinking()

        if not msgs and not thinking:
            return ui.div({"class": "empty-state"},
                ui.div({"class": "empty-icon"}, "💬"),
                ui.div("Select your role and send your first message to begin."),
            )

        elements = []
        for m in msgs:
            is_user  = m["role"] == "user"
            row_cls  = "msg-row user" if is_user else "msg-row"
            bub_cls  = "bubble bubble-user" if is_user else "bubble bubble-ai"
            av_cls   = "avatar avatar-user" if is_user else "avatar avatar-ai"
            av_lbl   = "YOU" if is_user else "AI"
            msg_id   = m.get("id", "")

            html_content = format_message(m["content"])
            bubble_inner = [ui.HTML(html_content)]

            # Scope choice buttons
            if m.get("scope_choice"):
                bubble_inner.append(
                    ui.div({"class": "scope-choice"},
                        ui.div({"style": "font-weight:600; margin-bottom:0.3rem;"},
                            "Would you like to escalate this to Meredith Callahan?"),
                        ui.div({"class": "scope-choice-btns"},
                            ui.tags.button("Yes, escalate",
                                {"class": "scope-btn scope-btn-escalate",
                                 "onclick": "Shiny.setInputValue('scope_decision','escalate',{priority:'event'})"}),
                            ui.tags.button("No, move on",
                                {"class": "scope-btn scope-btn-dismiss",
                                 "onclick": "Shiny.setInputValue('scope_decision','dismiss',{priority:'event'})"}),
                        ),
                    )
                )

            # Topic escalation suggestion prompt
            if m.get("suggest_escalation"):
                bubble_inner.append(
                    ui.div({"class": "escalation-prompt"},
                        "It seems like we're not making progress on this one. "
                        "Would you like me to escalate to Meredith Callahan?",
                        ui.div({"class": "escalation-prompt-btns"},
                            ui.tags.button("Yes, escalate",
                                {"class": "scope-btn scope-btn-escalate",
                                 "onclick": "Shiny.setInputValue('escalation_decision','escalate',{priority:'event'})"}),
                            ui.tags.button("No, keep going",
                                {"class": "scope-btn scope-btn-dismiss",
                                 "onclick": "Shiny.setInputValue('escalation_decision','dismiss',{priority:'event'})"}),
                        ),
                    )
                )

            # Source badge
            if not is_user and m.get("source_badge"):
                bubble_inner.append(
                    ui.div({"class": "source-badge"}, m["source_badge"])
                )

            # Feedback thumbs
            if not is_user and msg_id and not m.get("is_system"):
                fb       = feedback_log()
                existing = next((f for f in fb if f["msg_id"] == msg_id), None)
                up_cls   = "thumb-btn active-up"   if (existing and existing["helpful"])     else "thumb-btn"
                down_cls = "thumb-btn active-down" if (existing and not existing.get("helpful", True)) else "thumb-btn"
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
        generating = summary_generating()

        if generating:
            return ui.div({"class": "summary-loading"},
                ui.div({"class": "summary-loading-dots"},
                    ui.div({"class": "summary-loading-dot"}),
                    ui.div({"class": "summary-loading-dot"}),
                    ui.div({"class": "summary-loading-dot"}),
                ),
                ui.div("Generating session summary…"),
            )
        if not s:
            return ui.div({"class": "panel-empty"},
                "Session summary will appear here when the session ends.",
                ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Click 'End Session' or say 'let's wrap up' to generate the PS-facing summary.")
            )
        parsed = parse_summary(s)

        structured_children = []

        # Follow-up Indicators — FIRST, prominent
        followup = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
        structured_children.append(
            ui.div({"class": "followup-block"},
                ui.div({"class": "followup-label"}, "⚑ Follow-up Indicators"),
                ui.div({"class": "followup-content"}, followup),
            )
        )

        # Topic tags
        tags_raw = parsed.get("TOPIC_TAGS", "")
        if tags_raw and tags_raw not in ("N/A", "—"):
            tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            if tag_list:
                structured_children.append(
                    ui.div({"class": "tags-row"},
                        *[ui.span({"class": "topic-tag"}, t) for t in tag_list]
                    )
                )

        structured_children.append(ui.tags.hr({"class": "summary-divider"}))

        field_order = [
            ("DATE_TIME",             "Date / Time"),
            ("CUSTOMER",              "Customer"),
            ("OUTCOME",               "Outcome"),
            ("TOPICS_COVERED",        "Topics Covered"),
            ("GUIDANCE_PROVIDED",     "Guidance Provided"),
            ("ESCALATION_SUMMARY",    "Escalation Summary"),
            ("UNRESOLVED_QUESTIONS",  "Unresolved Questions"),
            ("RESPONSE_FEEDBACK",     "Response Feedback"),
        ]
        for key, label in field_order:
            val = parsed.get(key, "—") or "—"
            outcome_cls = ""
            if key == "OUTCOME":
                if "Escalated" in val:      outcome_cls = "outcome-escalated"
                elif "Partially" in val:    outcome_cls = "outcome-partial"
                elif "Resolved" in val:     outcome_cls = "outcome-resolved"
            structured_children.append(
                ui.div({"class": "summary-field"},
                    ui.div({"class": "summary-field-label"}, label),
                    ui.div({"class": f"summary-field-value {outcome_cls}"}, val),
                )
            )

        return ui.div(
            ui.div({"class": "summary-header"},
                ui.span("PS Session Summary"),
                ui.div({"style": "display:flex; gap:0.4rem;"},
                    ui.tags.button("Copy",
                        {"class": "copy-btn", "id": "copy-summary-btn",
                         "onclick": "copyToClipboard('summary-structured','copy-summary-btn')"}),
                    ui.tags.button("Copy as Email",
                        {"class": "copy-btn", "id": "copy-email-btn",
                         "onclick": "copyToClipboard('summary-email','copy-email-btn')"}),
                ),
            ),
            ui.div({"class": "email-toggle-row"},
                ui.span({"class": "email-toggle-label"}, "View:"),
                ui.tags.button("Structured",
                    {"class": "format-toggle-btn active", "id": "fmt-structured",
                     "onclick": "toggleSummaryFormat('structured')"}),
                ui.tags.button("Email-ready",
                    {"class": "format-toggle-btn", "id": "fmt-email",
                     "onclick": "toggleSummaryFormat('email')"}),
            ),
            ui.div({"id": "summary-structured", "style": "display:block"},
                *structured_children),
            ui.div({"id": "summary-email",
                    "style": "display:none; white-space:pre-wrap; font-size:0.78rem; color:#1C2333; line-height:1.6;"},
                e or build_email_summary(parsed)),
        )

    # ---- Escalation panel — multiple entries, immediate render ----
    @output
    @render.ui
    def escalation_panel_ui():
        entries = handoff_entries()
        if not entries:
            return ui.div({"class": "panel-empty"},
                "Handoff summary appears here if escalation is triggered.",
                ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Escalation triggers when you confirm you want to reach the PS team "
                    "or after repeated unresolved exchanges on the same topic.")
            )

        entry_elements = []
        for i, entry in enumerate(entries, 1):
            btn_id = f"copy-handoff-{entry['id']}"
            entry_elements.append(
                ui.div({"class": "handoff-entry"},
                    ui.div({"class": "handoff-entry-header"},
                        ui.span({"class": "handoff-entry-num"},
                            f"Escalation #{i} — {entry['ts']}"),
                        ui.tags.button("Copy",
                            {"class": "copy-btn", "id": btn_id,
                             "onclick": "copyFromBtn(this)"}),
                    ),
                    ui.div({"class": "handoff-entry-content"}, entry["text"]),
                )
            )

        return ui.div(
            ui.div({"class": "panel-section-label label-handoff"},
                f"⚡ Escalation Handoff {'Summary' if len(entries) == 1 else f'Summaries ({len(entries)})'}"
            ),
            ui.div({"style": "font-size:0.72rem; color:#9BA8BF; margin-bottom:0.75rem;"},
                "Share with Meredith Callahan so she can pick up without context gaps."),
            *entry_elements,
        )

    # ---- New Session button ----
    @reactive.effect
    @reactive.event(input.new_session)
    def handle_new_session():
        """Reset all state for a fresh session without page reload."""
        messages.set([])
        started.set(False)
        ended.set(False)
        start_ts.set(None)
        escalated.set(False)
        handoff_entries.set([])
        session_summary.set("")
        email_summary.set("")
        summary_generating.set(False)
        is_thinking.set(False)
        input_disabled.set(False)
        name_warned.set(False)
        switch_to_esc.set(0)
        msg_count.set(0)
        feedback_log.set([])
        unresolved_log.set([])
        scope_pending.set(False)
        tracker.reset()
        ui.update_text("user_input", value="")

    # ---- Demo launcher handler ----
    @reactive.effect
    @reactive.event(input.demo_launch)
    def handle_demo_launch():
        """Inject name, role, and opening message from a demo quick-start button."""
        evt = input.demo_launch()
        if not evt:
            return
        name    = evt.get("name", "")
        role    = evt.get("role", "")
        message = evt.get("message", "")

        # Reset if already started
        messages.set([])
        started.set(False)
        ended.set(False)
        start_ts.set(None)
        escalated.set(False)
        handoff_entries.set([])
        session_summary.set("")
        email_summary.set("")
        summary_generating.set(False)
        is_thinking.set(False)
        input_disabled.set(False)
        name_warned.set(False)
        switch_to_esc.set(0)
        msg_count.set(0)
        feedback_log.set([])
        unresolved_log.set([])
        scope_pending.set(False)
        tracker.reset()

        ui.update_text("customer_name", value=name)
        ui.update_select("customer_role", selected=role)

        if not message:
            return

        started.set(True)
        start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        is_thinking.set(True)

        ts  = datetime.now().strftime("%H:%M")
        mid = 1
        msg_count.set(mid)
        messages.set([{"role": "user", "content": message, "ts": ts, "id": f"msg_{mid}"}])

        sys_prompt = build_system_prompt(
            customer_name=name, customer_role=role, is_first_message=True)
        try:
            response_text = call_claude(
                messages=[{"role": "user", "content": message}],
                system_prompt=sys_prompt)
            is_thinking.set(False)
            source = extract_source_badge(response_text)
            ts2  = datetime.now().strftime("%H:%M")
            mid2 = 2
            msg_count.set(mid2)
            messages.set(messages() + [{
                "role": "assistant", "content": response_text,
                "ts": ts2, "id": f"msg_{mid2}", "source_badge": source,
            }])
        except Exception as e:
            is_thinking.set(False)
            mid2 = 2
            msg_count.set(mid2)
            messages.set(messages() + [{
                "role": "assistant", "content": _friendly_error(str(e)),
                "ts": datetime.now().strftime("%H:%M"),
                "id": f"msg_{mid2}", "is_system": True,
            }])

    # ---- Feedback handler ----
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
        current = [f for f in feedback_log() if f["msg_id"] != msg_id]
        current.append({"msg_id": msg_id, "helpful": helpful})
        feedback_log.set(current)

    # ---- Scope decision ----
    @reactive.effect
    @reactive.event(input.scope_decision)
    def handle_scope_decision():
        decision = input.scope_decision()
        if decision == "escalate":
            _do_escalate()
        elif decision == "dismiss":
            # Remove scope_choice flag — NOT an escalation
            msgs = messages()
            if msgs:
                messages.set(msgs[:-1] + [{**msgs[-1], "scope_choice": False}])
            scope_pending.set(False)
            ts  = datetime.now().strftime("%H:%M")
            mid = msg_count() + 1
            msg_count.set(mid)
            messages.set(messages() + [{
                "role": "assistant",
                "content": "Understood — we'll set that aside. What else can I help you with?",
                "ts": ts, "id": f"msg_{mid}", "is_system": True,
            }])

    # ---- Topic escalation decision ----
    @reactive.effect
    @reactive.event(input.escalation_decision)
    def handle_escalation_decision():
        decision = input.escalation_decision()
        if decision == "escalate":
            _do_escalate()
        elif decision == "dismiss":
            # Remove suggest_escalation flag — reset tracker
            msgs = messages()
            if msgs:
                messages.set(msgs[:-1] + [{**msgs[-1], "suggest_escalation": False}])
            tracker.reset()
            ts  = datetime.now().strftime("%H:%M")
            mid = msg_count() + 1
            msg_count.set(mid)
            messages.set(messages() + [{
                "role": "assistant",
                "content": "No problem — let's keep going. What would you like to try next?",
                "ts": ts, "id": f"msg_{mid}", "is_system": True,
            }])

    def _do_escalate():
        """Set escalation flag, generate handoff, append to entries list and chat."""
        escalated.set(True)
        scope_pending.set(False)

        # Snapshot the real conversation BEFORE cleaning flags
        # Filter out is_system messages — those are UI scaffolding, not conversation
        real_conversation = [
            {"role": m["role"], "content": m["content"]}
            for m in messages()
            if not m.get("is_system")
            and m["role"] in ("user", "assistant")
            and m.get("content", "").strip()
        ]

        # Now clean display flags from messages list
        cleaned = [{**m, "scope_choice": False, "suggest_escalation": False}
                   for m in messages()]
        messages.set(cleaned)

        handoff = generate_handoff_summary(
            messages=real_conversation,
            customer_name=input.customer_name() or "Not provided",
            customer_role=input.customer_role() or "Not specified",
        )

        ts  = datetime.now().strftime("%H:%M")
        eid = len(handoff_entries()) + 1
        is_first_escalation = eid == 1

        # Append to handoff entries (drives Escalation tab)
        handoff_entries.set(handoff_entries() + [{"id": eid, "text": handoff, "ts": ts}])

        # Auto-switch to Escalation tab on first escalation
        if is_first_escalation:
            switch_to_esc.set(switch_to_esc() + 1)

        # Add ONCE to chat
        mid = msg_count() + 1
        msg_count.set(mid)
        messages.set(messages() + [{
            "role": "assistant",
            "content": (
                "Here is a summary you can share with Meredith Callahan so she can "
                "pick up right where we left off:\n\n"
                "---\n**HANDOFF SUMMARY FOR MEREDITH CALLAHAN**\n\n" + handoff
            ),
            "ts": ts, "id": f"msg_{mid}", "is_system": True,
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

        # Name guard — soft prompt, not hard block
        customer_name = input.customer_name() or ""
        if not customer_name.strip() and not started():
            name_warned.set(True)

        ui.update_text("user_input", value="")

        if not started():
            started.set(True)
            start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        current_role = input.customer_role()
        if not current_role:
            detected = detect_role(user_text)
            if detected:
                current_role = detected

        # Natural language session end
        if check_session_end_intent(user_text):
            _close_session(current_role, natural_language=True)
            return

        # Explicit escalation request — allowed any number of times
        if check_explicit_escalation(user_text):
            _do_escalate()
            return

        # Scope question — offer choice, not auto-escalate
        is_scope_q = check_scope_question(user_text)

        # Add user message
        ts  = datetime.now().strftime("%H:%M")
        mid = msg_count() + 1
        msg_count.set(mid)
        messages.set(messages() + [{
            "role": "user", "content": user_text, "ts": ts, "id": f"msg_{mid}",
        }])

        # Disable input while thinking
        is_thinking.set(True)
        input_disabled.set(True)

        # Only send real conversation turns to Claude — exclude UI system messages
        is_first  = len([m for m in messages() if m["role"] == "assistant" and not m.get("is_system")]) == 0
        api_msgs  = [
            {"role": m["role"], "content": m["content"]}
            for m in messages()
            if not m.get("is_system")
            and m["role"] in ("user", "assistant")
            and m.get("content", "").strip()
        ]
        sys_prompt = build_system_prompt(
            customer_name=customer_name,
            customer_role=current_role or "",
            is_first_message=is_first,
        )

        try:
            response_text = call_claude(messages=api_msgs, system_prompt=sys_prompt)
            is_thinking.set(False)
            input_disabled.set(False)

            # Natural language end detection from model
            if "TRIGGER_SESSION_END" in response_text:
                response_text = response_text.replace("TRIGGER_SESSION_END", "").strip()
                ts2  = datetime.now().strftime("%H:%M")
                mid2 = msg_count() + 1
                msg_count.set(mid2)
                messages.set(messages() + [{
                    "role": "assistant", "content": response_text,
                    "ts": ts2, "id": f"msg_{mid2}",
                    "source_badge": extract_source_badge(response_text),
                }])
                _close_session(current_role, natural_language=True)
                return

            # Track unresolved questions
            if check_unresolved_response(response_text):
                ulog = unresolved_log() + [user_text[:120]]
                unresolved_log.set(ulog)

            # Topic-aware escalation suggestion (not trigger) — allowed any number of times
            suggest_esc = tracker.update(user_text, response_text)

            source = extract_source_badge(response_text)

            ts_resp = datetime.now().strftime("%H:%M")
            mid3    = msg_count() + 1
            msg_count.set(mid3)

            messages.set(messages() + [{
                "role": "assistant",
                "content": response_text,
                "ts": ts_resp,
                "id": f"msg_{mid3}",
                "source_badge": source,
                "scope_choice": is_scope_q,
                "suggest_escalation": suggest_esc,
            }])

            if is_scope_q:
                scope_pending.set(True)

        except Exception as e:
            is_thinking.set(False)
            input_disabled.set(False)
            mid_e = msg_count() + 1
            msg_count.set(mid_e)
            messages.set(messages() + [{
                "role": "assistant",
                "content": _friendly_error(str(e)),
                "ts": datetime.now().strftime("%H:%M"),
                "id": f"msg_{mid_e}", "is_system": True,
            }])

    # ---- End Session button ----
    @reactive.effect
    @reactive.event(input.end_session)
    def handle_end_session():
        if not started() or ended():
            return
        _close_session(input.customer_role() or "", natural_language=False)

    def _close_session(current_role: str, natural_language: bool = False):
        if ended():
            return
        ended.set(True)

        # Show loading state in PS Summary tab immediately
        summary_generating.set(True)

        # Add closing message to chat first
        ts  = datetime.now().strftime("%H:%M")
        mid = msg_count() + 1
        msg_count.set(mid)
        prefix = "Got it — I'll close out our session now. " if natural_language else ""
        messages.set(messages() + [{
            "role": "assistant",
            "content": (
                prefix +
                "**Session ended.** Generating your PS Summary now — "
                "it will appear in the PS Summary tab momentarily. "
                "Meredith Callahan will have full context of what we covered today."
            ),
            "ts": ts, "id": f"msg_{mid}", "is_system": True,
        }])

        # Generate summary — filter out is_system UI messages, only real conversation
        customer_name = input.customer_name() or ""
        display_name  = customer_name.strip() if customer_name.strip() else f"{current_role} — Name not provided"

        real_conversation = [
            {"role": m["role"], "content": m["content"]}
            for m in messages()
            if not m.get("is_system")
            and m["role"] in ("user", "assistant")
            and m.get("content", "").strip()
        ]

        summary = generate_session_summary(
            messages=real_conversation,
            customer_name=display_name,
            customer_role=current_role or "Not specified",
            session_start=start_ts() or "Unknown",
            escalated=escalated(),
            handoff_text="\n\n".join(e["text"] for e in handoff_entries()),
            unresolved_log=unresolved_log(),
            feedback_log=feedback_log(),
        )
        session_summary.set(summary)
        email_summary.set(build_email_summary(parse_summary(summary)))
        summary_generating.set(False)


# ===========================================================================
# HELPERS
# ===========================================================================

def extract_source_badge(text: str) -> str:
    for line in text.split("\n"):
        s = line.strip()
        if any(s.startswith(p) for p in ["📘 Source:", "📋 Source:", "📗 Source:", "📄 Source:"]):
            return s
    return ""


def _friendly_error(detail: str) -> str:
    return (
        "Something went wrong connecting to the assistant. Please try again in a moment.\n\n"
        "If this keeps happening, contact your PS lead directly:\n"
        "**Meredith Callahan** — meredith.flaring453@passmail.net\n\n"
        f"_(Technical detail: {detail[:200]})_"
    )


def parse_summary(raw: str) -> dict:
    fields = [
        "FOLLOW_UP_INDICATORS", "DATE_TIME", "CUSTOMER", "OUTCOME",
        "TOPIC_TAGS", "TOPICS_COVERED", "GUIDANCE_PROVIDED",
        "ESCALATION_SUMMARY", "UNRESOLVED_QUESTIONS", "RESPONSE_FEEDBACK",
    ]
    result      = {}
    current_key = None
    current_val = []
    for line in raw.split("\n"):
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
    lines = ["POSIT CLOUD IMPLEMENTATION ASSISTANT — SESSION SUMMARY", "=" * 55, ""]
    followup = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
    if followup and followup != "None identified.":
        lines += ["FOLLOW-UP INDICATORS (Action Required)", "-" * 40, followup, ""]
    for key, label in [
        ("DATE_TIME", "Date / Time"), ("CUSTOMER", "Customer"), ("OUTCOME", "Outcome"),
        ("TOPIC_TAGS", "Topics"), ("TOPICS_COVERED", "Topics Covered"),
        ("GUIDANCE_PROVIDED", "Guidance Provided"), ("ESCALATION_SUMMARY", "Escalation Summary"),
        ("UNRESOLVED_QUESTIONS", "Unresolved Questions"), ("RESPONSE_FEEDBACK", "Response Feedback"),
    ]:
        val = parsed.get(key, "")
        if val and val.strip():
            lines += [f"{label}: {val}", ""]
    lines += ["-" * 55, "Generated by Posit Cloud Implementation Assistant"]
    return "\n".join(lines)


def format_message(text: str) -> str:
    """
    Convert markdown to HTML for chat bubbles.
    Blockquotes rendered as a single .transparency-notice div.
    """
    # Collect blockquote lines into one block before any other processing
    def collect_blockquotes(t: str) -> str:
        lines = t.split("\n")
        out   = []
        bq    = []
        for line in lines:
            if line.strip().startswith("> "):
                bq.append(line.strip()[2:])
            else:
                if bq:
                    # Join all blockquote lines into one container
                    combined = " ".join(bq)
                    combined = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', combined)
                    combined = re.sub(r'`([^`]+)`', r'<code>\1</code>', combined)
                    out.append(f'<div class="transparency-notice">{combined}</div>')
                    bq = []
                out.append(line)
        if bq:
            combined = " ".join(bq)
            combined = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', combined)
            out.append(f'<div class="transparency-notice">{combined}</div>')
        return "\n".join(out)

    text = collect_blockquotes(text)

    # Horizontal rules
    text = re.sub(r'\n---\n', '\n<hr>\n', text)

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__',     r'<strong>\1</strong>', text)

    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Source badge lines
    text = re.sub(
        r'(?m)^[📘📋📗📄] Source:.*$',
        lambda m: f'<div class="source-badge">{m.group(0).strip()}</div>',
        text
    )

    # Tables
    lines    = text.split('\n')
    output   = []
    in_list  = False
    in_table = False
    thtml    = ""
    hdr_done = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            if re.match(r'^\|[-\s|:]+\|$', stripped):
                hdr_done = True
                continue
            if not in_table:
                in_table = True
                hdr_done = False
                thtml = '<table>'
            cells = [c.strip() for c in stripped[1:-1].split('|')]
            if not hdr_done:
                row = ''.join(f'<th>{c}</th>' for c in cells)
                hdr_done = True
            else:
                row = ''.join(f'<td>{c}</td>' for c in cells)
            thtml += f'<tr>{row}</tr>'
            continue
        else:
            if in_table:
                output.append(thtml + '</table>')
                thtml = ''; in_table = False; hdr_done = False

        lm = re.match(r'^(\d+\.\s+|[-*]\s+)(.*)', stripped)
        if lm:
            if not in_list:
                output.append('<ul>')
                in_list = True
            output.append(f'<li>{lm.group(2)}</li>')
        else:
            if in_list:
                output.append('</ul>')
                in_list = False
            output.append(line)

    if in_list:  output.append('</ul>')
    if in_table: output.append(thtml + '</table>')

    text = '\n'.join(output)

    paragraphs = re.split(r'\n{2,}', text)
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        p = p.replace('\n', '<br>')
        if re.match(r'^<(ul|ol|table|hr|div|blockquote)', p):
            result.append(p)
        else:
            result.append(f'<p>{p}</p>')

    return '\n'.join(result)


# ===========================================================================
# RUN
# ===========================================================================
app = App(app_ui, server)
