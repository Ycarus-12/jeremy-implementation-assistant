# app.py — Posit Cloud Implementation Assistant (Shiny for Python)

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
    check_explicit_escalation,
    TopicEscalationTracker,
)
from system_prompt import build_system_prompt
from knowledge_base import get_sidebar_tasks

# ===========================================================================
# CSS
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

/* Top bar */
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
    background: rgba(68,112,153,0.2); color: #447099;
    border: 1px solid rgba(68,112,153,0.35);
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.65rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
}
.info-btn {
    background: none !important; border: 1px solid rgba(68,112,153,0.4) !important;
    color: #447099 !important; border-radius: 5px !important;
    padding: 2px 10px !important; font-size: 0.68rem !important;
    font-weight: 600 !important; cursor: pointer; font-family: inherit !important;
    transition: all 0.15s; white-space: nowrap; margin-left: 0.5rem;
}
.info-btn:hover { background: rgba(68,112,153,0.1) !important; }

/* Left sidebar */
.left-sidebar {
    background: #FFFFFF; border-right: 1px solid #E2E6EF;
    padding: 1.1rem; overflow-y: auto;
    display: flex; flex-direction: column; gap: 0.1rem;
}
.sidebar-label {
    font-size: 0.6rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #9BA8BF; margin-top: 1rem; margin-bottom: 0.35rem;
}
.sidebar-label:first-child { margin-top: 0; }
.sidebar-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.75rem 0; }
.meta-block { font-size: 0.72rem; color: #6B7A99; line-height: 1.7; }

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

.end-btn {
    width: 100%; background: #FFF0F0 !important; color: #C62828 !important;
    border: 1px solid #FFCDD2 !important; border-radius: 6px !important;
    font-size: 0.75rem !important; font-weight: 600 !important;
    padding: 0.45rem !important; cursor: pointer;
    font-family: inherit !important; transition: background 0.15s;
}
.end-btn:hover { background: #FFEBEE !important; }

.new-session-btn {
    width: 100%; background: #EEF4FA !important; color: #447099 !important;
    border: 1px solid #C5D8EC !important; border-radius: 6px !important;
    font-size: 0.75rem !important; font-weight: 600 !important;
    padding: 0.45rem !important; cursor: pointer;
    font-family: inherit !important; transition: background 0.15s; margin-top: 0.4rem;
}
.new-session-btn:hover { background: #D6E8F5 !important; }

/* Demo launchers */
.demo-launchers { display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.25rem; }
.demo-btn {
    background: #F4F6F9 !important; border: 1px solid #E2E6EF !important;
    color: #2D3A52 !important; border-radius: 5px !important;
    font-size: 0.71rem !important; font-weight: 500 !important;
    padding: 0.35rem 0.6rem !important; cursor: pointer;
    font-family: inherit !important; text-align: left !important;
    transition: all 0.15s; line-height: 1.3; width: 100%;
}
.demo-btn:hover { background: #EEF4FA !important; border-color: #C5D8EC !important; color: #447099 !important; }
.demo-btn-name { font-weight: 600; display: block; }
.demo-btn-role { font-size: 0.65rem; color: #6B7A99; display: block; }

/* Contact block */
.contact-block {
    background: #F4F6F9; border: 1px solid #E2E6EF;
    border-radius: 6px; padding: 0.5rem 0.6rem;
    font-size: 0.71rem; color: #4A5568; line-height: 1.6;
}
.contact-block a { color: #447099; text-decoration: none; font-weight: 600; display: block; }
.contact-block a:hover { text-decoration: underline; }
.contact-name { font-weight: 600; color: #1C2333; }

/* Task sections */
.task-section { margin-top: 0.25rem; }
.task-section-header {
    display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; user-select: none; padding: 0.3rem 0; border-radius: 4px;
}
.task-section-header:hover { background: #F4F6F9; }
.task-section-title { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; }
.task-title-overdue  { color: #C62828; }
.task-title-upcoming { color: #447099; }
.task-toggle-icon { font-size: 0.6rem; color: #9BA8BF; transition: transform 0.15s; }
.task-toggle-icon.collapsed { transform: rotate(-90deg); }
.task-list { margin-top: 0.2rem; }
.task-item {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: 0.25rem 0.3rem; border-radius: 4px;
    font-size: 0.71rem; line-height: 1.4; gap: 0.4rem;
}
.task-item:hover { background: #F4F6F9; }
.task-item-name { color: #2D3A52; flex: 1; }
.task-item-due { font-size: 0.67rem; white-space: nowrap; flex-shrink: 0; font-weight: 500; }
.task-item-due-overdue  { color: #C62828; }
.task-item-due-upcoming { color: #447099; }
.task-empty { font-size: 0.7rem; color: #9BA8BF; font-style: italic; padding: 0.2rem 0.3rem; }
.expand-hint { font-size: 0.62rem; color: #9BA8BF; font-style: italic; margin-top: 0.15rem; }

.name-warning { font-size: 0.68rem; color: #E65100; margin-top: 0.2rem; }

/* Chat panel */
.chat-panel {
    display: flex; flex-direction: column;
    background: #F4F6F9; overflow: hidden; min-height: 0;
}
.chat-window {
    flex: 1; overflow-y: auto; padding: 1.25rem;
    display: flex; flex-direction: column; gap: 1rem;
    scroll-behavior: smooth; min-height: 0;
}

/* Message bubbles */
.msg-row { display: flex; align-items: flex-start; gap: 0.6rem; max-width: 100%; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;
}
.avatar-ai   { background: #1C2333; color: #447099; }
.avatar-user { background: #E2E6EF; color: #6B7A99; }
.bubble {
    max-width: 76%; padding: 0.65rem 0.9rem;
    border-radius: 12px; font-size: 0.845rem; line-height: 1.6;
}
.bubble-ai {
    background: #FFFFFF; border: 1px solid #E2E6EF;
    border-top-left-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.bubble-user { background: #1C2333; color: #E8EDF5; border-top-right-radius: 3px; }

.transparency-notice {
    background: #EEF4FA; border-left: 3px solid #447099;
    border-radius: 0 6px 6px 0; padding: 0.6rem 0.85rem;
    margin-bottom: 0.75rem; font-size: 0.8rem; color: #2D4A63; line-height: 1.55;
}

.scope-choice {
    background: #FFF8E1; border: 1px solid #FFD54F;
    border-radius: 8px; padding: 0.65rem 0.9rem; margin-top: 0.5rem; font-size: 0.82rem;
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

.escalation-prompt {
    background: #FFF3E0; border: 1px solid #FFB74D;
    border-left: 3px solid #F57C00; border-radius: 0 8px 8px 0;
    padding: 0.65rem 0.9rem; margin-top: 0.5rem;
    font-size: 0.82rem; color: #3E2723; line-height: 1.5;
}
.escalation-prompt-btns { display: flex; gap: 0.5rem; margin-top: 0.5rem; }

.source-badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.68rem; color: #6B7A99; margin-top: 0.4rem;
    padding: 2px 6px; background: #F4F6F9;
    border-radius: 4px; border: 1px solid #E2E6EF;
}

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

.empty-state {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: #9BA8BF; font-size: 0.82rem; text-align: center;
    gap: 0.5rem; padding: 2rem;
}
.empty-icon { font-size: 2rem; margin-bottom: 0.25rem; }

.typing-dots { display: flex; gap: 4px; align-items: center; padding: 0.3rem 0; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #447099; animation: pulse 1.2s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; } 40% { transform: scale(1.0); opacity: 1; } }

/* Input area */
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
.input-hint { font-size: 0.65rem; color: #9BA8BF; margin-top: 0.4rem; }

/* Right panel */
.right-panel {
    background: #FFFFFF; border-left: 1px solid #E2E6EF;
    overflow: hidden; display: flex; flex-direction: column;
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

/* Tab panes — hidden by default, shown when .active */
.tab-content { flex: 1; overflow: hidden; position: relative; }
.tab-pane {
    position: absolute; inset: 0;
    overflow-y: auto; padding: 1rem;
    opacity: 0; pointer-events: none; transition: opacity 0.15s;
}
.tab-pane.active { opacity: 1; pointer-events: auto; }

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
.outcome-resolved  { color: #2E7D32; font-weight: 600; }
.outcome-partial   { color: #E65100; font-weight: 600; }
.outcome-escalated { color: #C62828; font-weight: 600; }
.summary-divider { border: none; border-top: 1px solid #E2E6EF; margin: 0.65rem 0; }

/* Escalation tab */
.handoff-entry {
    background: #FFFDF0; border: 1px solid #FFD54F;
    border-radius: 6px; padding: 0.85rem; margin-bottom: 0.75rem;
}
.handoff-entry-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.5rem;
}
.handoff-entry-num {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #E65100;
}
.handoff-entry-content {
    font-size: 0.78rem; line-height: 1.65; color: #3D2B00; white-space: pre-wrap;
}
.panel-section-label {
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; margin-bottom: 0.5rem;
}
.label-handoff { color: #E65100; }

/* Copy + format buttons */
.copy-btn {
    background: none; border: 1px solid #E2E6EF; border-radius: 5px;
    padding: 2px 8px; font-size: 0.67rem; font-weight: 600; color: #6B7A99;
    cursor: pointer; font-family: inherit; transition: all 0.15s; white-space: nowrap;
}
.copy-btn:hover { background: #F4F6F9; border-color: #CBD2E0; color: #1C2333; }
.copy-btn.copied { color: #2E7D32; border-color: #72994E; background: #E8F5E9; }
.email-toggle-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; margin-top: 0.25rem; }
.email-toggle-label { font-size: 0.68rem; color: #6B7A99; }
.format-toggle-btn {
    background: none; border: 1px solid #E2E6EF; border-radius: 4px;
    padding: 2px 8px; font-size: 0.67rem; font-weight: 600; color: #6B7A99;
    cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.format-toggle-btn.active { background: #EEF4FA; border-color: #447099; color: #447099; }

/* Summary loading */
.summary-loading {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 2rem 1rem; gap: 0.75rem;
    color: #6B7A99; font-size: 0.8rem;
}
.summary-loading-dots { display: flex; gap: 5px; }
.summary-loading-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #447099;
    animation: pulse 1.2s infinite ease-in-out;
}
.summary-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.summary-loading-dot:nth-child(3) { animation-delay: 0.4s; }

/* Info modal */
.modal-overlay {
    display: none; position: fixed; inset: 0; z-index: 1000;
    background: rgba(28,35,51,0.55); backdrop-filter: blur(3px);
    align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal-box {
    background: #FFFFFF; border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    width: min(680px, 92vw); max-height: 85vh;
    display: flex; flex-direction: column; overflow: hidden;
}
.modal-header {
    background: #1C2333; color: white; padding: 1rem 1.25rem;
    display: flex; align-items: flex-start; justify-content: space-between; flex-shrink: 0;
}
.modal-header-title { font-size: 0.95rem; font-weight: 600; color: #E8EDF5; margin-bottom: 0.15rem; }
.modal-header-sub { font-size: 0.72rem; color: #6B7A99; font-style: italic; }
.modal-close {
    background: none; border: none; color: #6B7A99;
    font-size: 1.2rem; cursor: pointer; padding: 0 0.25rem; line-height: 1;
    transition: color 0.15s; flex-shrink: 0; margin-left: 1rem; margin-top: 0.1rem;
}
.modal-close:hover { color: #E8EDF5; }
.modal-body {
    padding: 1.5rem 1.75rem; overflow-y: auto; flex: 1;
    font-size: 0.845rem; line-height: 1.65; color: #2D3A52;
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
    border-left: 4px solid #F57C00; border-radius: 0 6px 6px 0;
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

/* Shiny overrides */
.shiny-input-container { margin-bottom: 0 !important; }
.form-control, .selectize-input {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.8rem !important; border-color: #CBD2E0 !important; border-radius: 6px !important;
}
.selectize-input { padding: 5px 8px !important; }
select.form-control { height: 34px !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD2E0; border-radius: 10px; }
"""

# ===========================================================================
# JS — minimal, no DOM mutation, no insert_ui
# ===========================================================================
JS = """
// Enter to send
document.addEventListener('keydown', function(e) {
    if (e.target.id === 'user_input' && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('send_btn').click();
    }
});

// Auto-scroll chat window
const chatObs = new MutationObserver(function() {
    var cw = document.querySelector('.chat-window');
    if (cw) cw.scrollTop = cw.scrollHeight;
});
document.addEventListener('DOMContentLoaded', function() {
    var cw = document.querySelector('.chat-window');
    if (cw) chatObs.observe(cw, { childList: true, subtree: true });
});

// Tab switching — pure class toggle, no style manipulation
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-pane').forEach(function(p) { p.classList.remove('active'); });
    var btn  = document.querySelector('[data-tab="' + tab + '"]');
    var pane = document.getElementById('pane-' + tab);
    if (btn)  btn.classList.add('active');
    if (pane) pane.classList.add('active');
}

// Collapsible sidebar task sections
function toggleTaskSection(id) {
    var list = document.getElementById(id);
    var icon = document.getElementById(id + '-icon');
    if (!list) return;
    var isHidden = list.style.display === 'none';
    list.style.display = isHidden ? 'block' : 'none';
    if (icon) icon.classList.toggle('collapsed', !isHidden);
}

// Copy — walks up DOM from button to find content, no element ID required
function copyFromBtn(btn) {
    var entry = btn.closest('.handoff-entry');
    if (!entry) return;
    var content = entry.querySelector('.handoff-entry-content');
    if (!content) return;
    var text = content.innerText || content.textContent || '';
    doCopy(text, btn);
}

// Copy by element ID (used by summary panel)
function copyById(id, btnId) {
    var el  = document.getElementById(id);
    var btn = document.getElementById(btnId);
    if (!el) return;
    doCopy(el.innerText || el.textContent || '', btn);
}

function doCopy(text, btn) {
    if (!text.trim()) return;
    var doConfirm = function() {
        if (!btn) return;
        var orig = btn.innerText;
        btn.innerText = '✓ Copied';
        btn.classList.add('copied');
        setTimeout(function() { btn.innerText = orig; btn.classList.remove('copied'); }, 2000);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(doConfirm).catch(function() { fallbackCopy(text, doConfirm); });
    } else {
        fallbackCopy(text, doConfirm);
    }
}

function fallbackCopy(text, cb) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); if (cb) cb(); } catch(e) {}
    document.body.removeChild(ta);
}

// Summary view toggle
function toggleSummaryFormat(fmt) {
    document.getElementById('summary-structured').style.display = fmt === 'structured' ? 'block' : 'none';
    document.getElementById('summary-email').style.display      = fmt === 'email'      ? 'block' : 'none';
    document.querySelectorAll('.format-toggle-btn').forEach(function(b) { b.classList.remove('active'); });
    var btn = document.getElementById('fmt-' + fmt);
    if (btn) btn.classList.add('active');
}

// Feedback thumbs
function sendFeedback(msgId, helpful) {
    var up   = document.getElementById('up-'   + msgId);
    var down = document.getElementById('down-' + msgId);
    if (up)   up.classList.toggle('active-up',    helpful);
    if (down) down.classList.toggle('active-down', !helpful);
    if (window.Shiny) Shiny.setInputValue('feedback_event', {msg_id: msgId, helpful: helpful}, {priority: 'event'});
}

// Info modal
function openInfoModal()  { var m = document.getElementById('info-modal'); if (m) m.classList.add('open'); }
function closeInfoModal() { var m = document.getElementById('info-modal'); if (m) m.classList.remove('open'); }
document.addEventListener('click', function(e) {
    var m = document.getElementById('info-modal');
    if (m && e.target === m) closeInfoModal();
});
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeInfoModal(); });

// Demo launcher
function launchDemo(name, role, msg) {
    if (window.Shiny) Shiny.setInputValue('demo_launch', {name: name, role: role, message: msg}, {priority: 'event'});
}
"""

# ===========================================================================
# MODAL
# ===========================================================================
MODAL_HTML = ui.div(
    {"class": "modal-overlay", "id": "info-modal"},
    ui.div({"class": "modal-box"},
        ui.div({"class": "modal-header"},
            ui.div(
                ui.div({"class": "modal-header-title"}, "Posit Cloud Implementation Assistant"),
                ui.div({"class": "modal-header-sub"}, "A proof-of-concept built to start a conversation"),
            ),
            ui.tags.button("✕", {"class": "modal-close", "onclick": "closeInfoModal()"}),
        ),
        ui.div({"class": "modal-body"},

            ui.tags.h3("Hey Posit — this one's for you"),
            ui.tags.p(
                "If you're reading this, you're probably on the hiring team, and I built this specifically "
                "to get your attention. (Is it working? I genuinely have no idea, but here we are.) "
                "This is a working proof-of-concept of an AI-powered implementation assistant — "
                "the kind of tool your Professional Services team could be using with customers right now."
            ),
            ui.tags.p(
                "It's not a mockup. It's not a slide deck. It actually connects to Claude via the Anthropic API, "
                "it's actually trained on real Posit Cloud documentation, and it's actually operating under a "
                "fictional-but-realistic customer project plan modeled on what I imagine a university research "
                "computing implementation looks like at Posit. The knowledge base was researched and validated "
                "against docs.posit.co. The project plan, SOW, task guides, and persona logic are all custom-built "
                "for this demo. It's doing real work."
            ),

            ui.tags.h3("What this demonstrates"),
            ui.tags.p(
                "The PS team at any professional services organization spends a significant portion of its time "
                "answering questions that are routine, repeatable, and well-documented — but that still require "
                "a human to field them. This tool offloads that work."
            ),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Role-aware guidance</strong> — the assistant adjusts depth and framing based on whether you're an IT admin, a project manager, an executive sponsor, or a researcher")),
                ui.tags.li(ui.HTML("<strong>Project plan awareness</strong> — it knows what's overdue, what's coming up, and who owns what, and surfaces that context proactively")),
                ui.tags.li(ui.HTML("<strong>Source citation</strong> — every answer cites the exact document, section, and task it's drawing from")),
                ui.tags.li(ui.HTML("<strong>Escalation workflow</strong> — when the customer needs a human, the assistant generates a structured handoff summary so the PS lead can pick up without friction")),
                ui.tags.li(ui.HTML("<strong>PS-facing session summaries</strong> — every session produces a structured summary for the PS team, including follow-up indicators and unresolved questions")),
                ui.tags.li(ui.HTML("<strong>Hard guardrails</strong> — it won't speculate, commit to scope changes, discuss pricing, or contradict prior PS guidance")),
            ),

            ui.tags.h3("The value for Posit specifically"),
            ui.tags.p(
                "Posit's PS team works with customers who are implementing complex data science infrastructure — "
                "often with multiple stakeholders, long timelines, and a mix of technical and non-technical users. "
                "That's exactly the environment where a tool like this creates the most leverage:"
            ),
            ui.tags.ul(
                ui.tags.li("Customers get answers instantly instead of waiting for PS availability"),
                ui.tags.li("PS consultants stay informed without being in every conversation"),
                ui.tags.li("Implementation quality improves because guidance is consistent and grounded in actual documentation"),
                ui.tags.li("The PS team gets a structured record of every customer interaction — what was asked, what was answered, where people got stuck"),
                ui.tags.li("Patterns across sessions reveal where customers struggle most, which feeds directly into better documentation and process design"),
            ),
            ui.tags.p(
                "This is a force multiplier, not a replacement. The PS lead — in this demo, Meredith Callahan — "
                "remains the authority on everything. The assistant is explicit about that, constantly."
            ),

            ui.tags.h3("What's actually working in this POC"),
            ui.tags.p(
                "To be clear about what 'proof of concept' means here: most of it is working. The AI connection "
                "is live. The knowledge base is real. The project plan logic is functional. The escalation and "
                "summary flows produce actual output. What's stubbed out for Phase 2:"
            ),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Monday.com integration</strong> — the project plan is hardcoded; in production it would pull live from a Monday board via API")),
                ui.tags.li(ui.HTML("<strong>Automated delivery</strong> — session summaries and escalation handoffs are displayed in-app; in production they'd be emailed, posted to Slack, and added to the Monday project automatically")),
                ui.tags.li(ui.HTML("<strong>Customer-uploaded project plans</strong> — right now the plan is baked in; in production each customer deployment would inject their own SOW and project plan")),
            ),

            ui.tags.h3("On AI and implementation culture"),
            ui.tags.p(
                "There's a broader point here beyond the tool itself. Embedding AI into implementation workflows "
                "isn't just about efficiency — it's about changing what's possible. A PS team that has AI handling "
                "the first line of customer questions can focus its human capacity on the work that actually requires "
                "human judgment: complex configuration, relationship management, navigating ambiguity. "
                "The teams that figure out how to do this well are going to look very different from the ones that don't."
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("[ Your culture answer will be woven in here once you share it. ]"),
                " This section will reflect your specific framing on how AI tools should be adopted into "
                "PS team culture — not just deployed, but genuinely integrated into how the team works."
            ),

            ui.tags.h3("How to explore this"),
            ui.tags.ul(
                ui.tags.li("Use the Demo Quick-Start buttons on the left to launch a pre-loaded persona"),
                ui.tags.li("Try asking about overdue tasks, SSO configuration, resource limits, or UAT"),
                ui.tags.li("Say 'I'd like to escalate this' to see the escalation workflow"),
                ui.tags.li("Click End Session to generate a PS-facing summary"),
                ui.tags.li("Try the different roles — the assistant adjusts its framing for each one"),
            ),
        ),
        ui.div({"class": "modal-footer"},
            "Built as a demonstration for Posit's hiring process. "
            "All Posit Cloud knowledge is sourced from docs.posit.co. "
            "The customer scenario (State University Research Computing) is fictional. "
            "Powered by Claude via the Anthropic API."
        ),
    ),
)

# ===========================================================================
# UI
# ===========================================================================
ROLES = [
    ("",                                      "— Select your role —"),
    ("IT Admin / Technical Lead",             "IT Admin / Technical Lead"),
    ("Project Lead / Project Manager",        "Project Lead / Project Manager"),
    ("Executive Sponsor / Research Director", "Executive Sponsor / Research Director"),
    ("Researcher / End User",                 "Researcher / End User"),
    ("UAT Tester",                            "UAT Tester"),
]

app_ui = ui.page_fixed(
    ui.tags.head(
        ui.tags.style(CSS),
        ui.tags.script(JS),
    ),
    MODAL_HTML,
    ui.div({"class": "app-shell"},

        # TOP BAR
        ui.div({"class": "top-bar"},
            ui.div({"class": "top-bar-logo"}, "Posit"),
            ui.div({"class": "top-bar-title"}, "Cloud Implementation Assistant"),
            ui.div({"class": "top-bar-sub"}, "State University Research Computing"),
            ui.tags.button("? What am I looking at", {"class": "info-btn", "onclick": "openInfoModal()"}),
            ui.div({"class": "top-bar-badge"}, "Proof of Concept"),
        ),

        # LEFT SIDEBAR
        ui.div({"class": "left-sidebar"},
            ui.div({"class": "sidebar-label"}, "Your Name"),
            ui.input_text("customer_name", None, placeholder="Enter your name"),
            ui.output_ui("name_warning_ui"),

            ui.div({"class": "sidebar-label"}, "Your Role"),
            ui.input_select("customer_role", None, choices={v: l for v, l in ROLES}, selected=""),

            ui.div({"class": "sidebar-label"}, "Session Status"),
            ui.output_ui("session_status_ui"),

            ui.div({"class": "sidebar-label"}, "Escalation"),
            ui.output_ui("escalation_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),
            ui.input_action_button("end_session", "End Session", class_="end-btn"),
            ui.input_action_button("new_session", "↺ New Session", class_="new-session-btn"),
            ui.tags.hr({"class": "sidebar-divider"}),

            ui.div({"class": "sidebar-label"}, "Demo Quick-Start"),
            ui.div({"class": "demo-launchers"},
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "Derek Huang"),
                    ui.span({"class": "demo-btn-role"}, "IT Admin / Technical Lead"),
                    {"class": "demo-btn",
                     "onclick": "launchDemo('Derek Huang','IT Admin / Technical Lead','Hi — I am Derek, the IT Admin. I need help setting the default resource limits for researchers. Can you walk me through it?')"},
                ),
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "Dr. Kim Osei"),
                    ui.span({"class": "demo-btn-role"}, "Executive Sponsor"),
                    {"class": "demo-btn",
                     "onclick": "launchDemo('Dr. Kim Osei','Executive Sponsor / Research Director','Hi, I am Dr. Osei, Research Computing Director. Can you give me a quick status update on where we stand with the implementation?')"},
                ),
                ui.tags.button(
                    ui.span({"class": "demo-btn-name"}, "UAT Tester"),
                    ui.span({"class": "demo-btn-role"}, "UAT Tester"),
                    {"class": "demo-btn",
                     "onclick": "launchDemo('UAT Tester','UAT Tester','I am running UAT for the pilot group. Can you walk me through the full checklist and what I need to verify?')"},
                ),
            ),

            ui.tags.hr({"class": "sidebar-divider"}),
            ui.div({"class": "sidebar-label"}, "Implementation"),
            ui.div({"class": "meta-block"},
                ui.tags.div("Customer: State Univ. RC"),
                ui.tags.div("PS Lead: Meredith Callahan"),
                ui.tags.div("Phase: 1 — Setup & Pilot"),
            ),
            ui.output_ui("sidebar_tasks_ui"),

            ui.tags.hr({"class": "sidebar-divider"}),
            ui.div({"class": "sidebar-label"}, "Contact PS Lead"),
            ui.div({"class": "contact-block"},
                ui.span({"class": "contact-name"}, "Meredith Callahan"),
                ui.tags.a("meredith.flaring453@passmail.net",
                          {"href": "mailto:meredith.flaring453@passmail.net"}),
            ),
        ),

        # CHAT PANEL
        ui.div({"class": "chat-panel"},
            ui.div({"class": "chat-window", "id": "chat_window"},
                ui.output_ui("chat_messages_ui"),
            ),
            ui.div({"class": "input-area"},
                ui.div({"class": "input-row"},
                    ui.tags.textarea({"id": "user_input",
                                      "placeholder": "Ask a question or describe what you are trying to do…",
                                      "rows": "2"}),
                    ui.input_action_button("send_btn", "Send", class_="send-btn"),
                ),
                ui.div({"class": "input-hint"},
                    "Enter to send · Shift+Enter for new line · Session summaries are shared with your PS lead"),
            ),
        ),

        # RIGHT PANEL
        ui.div({"class": "right-panel"},
            ui.div({"class": "panel-tabs"},
                ui.tags.button("PS Summary",  {"class": "tab-btn active", "data-tab": "summary",   "onclick": "switchTab('summary')"}),
                ui.tags.button("Escalation",  {"class": "tab-btn",        "data-tab": "escalation", "onclick": "switchTab('escalation')"}),
            ),
            ui.div({"class": "tab-content"},
                ui.div({"id": "pane-summary",    "class": "tab-pane active"}, ui.output_ui("summary_panel_ui")),
                ui.div({"id": "pane-escalation", "class": "tab-pane"},        ui.output_ui("escalation_panel_ui")),
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
    name_warned        = reactive.value(False)
    msg_count          = reactive.value(0)
    feedback_log       = reactive.value([])
    unresolved_log     = reactive.value([])
    tracker            = TopicEscalationTracker()

    # ---- Helpers ----
    def real_msgs():
        """Return only real conversation turns, excluding UI system messages."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages()
            if not m.get("is_system")
            and m["role"] in ("user", "assistant")
            and m.get("content", "").strip()
        ]

    def reset_state():
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
        name_warned.set(False)
        msg_count.set(0)
        feedback_log.set([])
        unresolved_log.set([])
        tracker.reset()

    def next_mid():
        mid = msg_count() + 1
        msg_count.set(mid)
        return mid

    def add_msg(role, content, is_system=False, **kwargs):
        mid = next_mid()
        entry = {"role": role, "content": content,
                 "ts": datetime.now().strftime("%H:%M"),
                 "id": f"msg_{mid}", "is_system": is_system}
        entry.update(kwargs)
        messages.set(messages() + [entry])
        return mid

    # ---- Sidebar outputs ----
    @output
    @render.ui
    def name_warning_ui():
        if name_warned():
            return ui.div({"class": "name-warning"}, "Please enter your name before starting.")
        return ui.div()

    @output
    @render.ui
    def session_status_ui():
        if not started():   return ui.span({"class": "status-chip chip-waiting"},   "● Waiting")
        elif ended():       return ui.span({"class": "status-chip chip-ended"},     "● Ended")
        elif escalated():   return ui.span({"class": "status-chip chip-escalated"}, "● Escalated")
        else:               return ui.span({"class": "status-chip chip-active"},    "● Active")

    @output
    @render.ui
    def escalation_ui():
        if not started():
            return ui.div({"style": "font-size:0.72rem; color:#9BA8BF;"}, "No active session")
        elif escalated():
            return ui.div({"class": "escalation-banner"}, "⚠ Escalated to Meredith Callahan")
        else:
            return ui.div({"style": "font-size:0.72rem; color:#2E7D32;"}, "✓ No escalation triggered")

    @output
    @render.ui
    def sidebar_tasks_ui():
        tasks    = get_sidebar_tasks(today=date.today())
        overdue  = tasks["overdue"]
        upcoming = tasks["upcoming"]

        def task_row(t, cls):
            return ui.div({"class": "task-item"},
                ui.span({"class": "task-item-name"}, t["name"]),
                ui.span({"class": f"task-item-due {cls}"}, t["due"]),
            )

        return ui.div(
            ui.div({"class": "task-section"},
                ui.div({"class": "task-section-header",
                        "onclick": "toggleTaskSection('task-list-overdue')"},
                    ui.span({"class": "task-section-title task-title-overdue"}, f"⚠ Overdue ({len(overdue)})"),
                    ui.span({"class": "task-toggle-icon", "id": "task-list-overdue-icon"}, "▾"),
                ),
                ui.div({"id": "task-list-overdue", "class": "task-list"},
                    *(task_row(t, "task-item-due-overdue") for t in overdue)
                    if overdue else [ui.div({"class": "task-empty"}, "None")]
                ),
            ),
            ui.div({"class": "task-section"},
                ui.div({"class": "task-section-header",
                        "onclick": "toggleTaskSection('task-list-upcoming')"},
                    ui.span({"class": "task-section-title task-title-upcoming"}, f"📅 Coming Up ({len(upcoming)})"),
                    ui.span({"class": "task-toggle-icon", "id": "task-list-upcoming-icon"}, "▾"),
                ),
                ui.div({"id": "task-list-upcoming", "class": "task-list"},
                    *(task_row(t, "task-item-due-upcoming") for t in upcoming)
                    if upcoming else [ui.div({"class": "task-empty"}, "None in next 14 days")]
                ),
                ui.div({"class": "expand-hint"}, "Click heading to collapse / expand"),
            ),
        )

    # ---- Chat messages ----
    @output
    @render.ui
    def chat_messages_ui():
        msgs     = messages()
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
            msg_id   = m.get("id", "")

            inner = [ui.HTML(format_message(m["content"]))]

            if m.get("scope_choice"):
                inner.append(ui.div({"class": "scope-choice"},
                    ui.div({"style": "font-weight:600; margin-bottom:0.3rem;"}, "Would you like to escalate this to Meredith Callahan?"),
                    ui.div({"class": "scope-choice-btns"},
                        ui.tags.button("Yes, escalate", {"class": "scope-btn scope-btn-escalate",
                            "onclick": "Shiny.setInputValue('scope_decision','escalate',{priority:'event'})"}),
                        ui.tags.button("No, move on",   {"class": "scope-btn scope-btn-dismiss",
                            "onclick": "Shiny.setInputValue('scope_decision','dismiss',{priority:'event'})"}),
                    ),
                ))

            if m.get("suggest_escalation"):
                inner.append(ui.div({"class": "escalation-prompt"},
                    "It seems like we are not making progress on this one. Would you like me to escalate to Meredith Callahan?",
                    ui.div({"class": "escalation-prompt-btns"},
                        ui.tags.button("Yes, escalate", {"class": "scope-btn scope-btn-escalate",
                            "onclick": "Shiny.setInputValue('escalation_decision','escalate',{priority:'event'})"}),
                        ui.tags.button("No, keep going", {"class": "scope-btn scope-btn-dismiss",
                            "onclick": "Shiny.setInputValue('escalation_decision','dismiss',{priority:'event'})"}),
                    ),
                ))

            if not is_user and m.get("source_badge"):
                inner.append(ui.div({"class": "source-badge"}, m["source_badge"]))

            if not is_user and msg_id and not m.get("is_system"):
                fb  = feedback_log()
                ex  = next((f for f in fb if f["msg_id"] == msg_id), None)
                up_cls   = "thumb-btn active-up"   if (ex and ex["helpful"])              else "thumb-btn"
                down_cls = "thumb-btn active-down" if (ex and not ex.get("helpful",True)) else "thumb-btn"
                inner.append(ui.div({"class": "feedback-row"},
                    ui.span({"class": "feedback-label"}, "Helpful?"),
                    ui.tags.button("👍", {"class": up_cls,   "id": f"up-{msg_id}",
                                         "onclick": f"sendFeedback('{msg_id}',true)"}),
                    ui.tags.button("👎", {"class": down_cls, "id": f"down-{msg_id}",
                                         "onclick": f"sendFeedback('{msg_id}',false)"}),
                ))

            elements.append(ui.div({"class": row_cls},
                ui.div({"class": av_cls}, "YOU" if is_user else "AI"),
                ui.div(
                    ui.div({"class": bub_cls}, *inner),
                    ui.div({"class": "msg-ts"}, m.get("ts", "")),
                ),
            ))

        if thinking:
            elements.append(ui.div({"class": "msg-row"},
                ui.div({"class": "avatar avatar-ai"}, "AI"),
                ui.div({"class": "bubble bubble-ai"},
                    ui.div({"class": "typing-dots"},
                        ui.div({"class": "dot"}), ui.div({"class": "dot"}), ui.div({"class": "dot"}),
                    )
                ),
            ))

        return ui.div(*elements)

    # ---- PS Summary ----
    @output
    @render.ui
    def summary_panel_ui():
        if summary_generating():
            return ui.div({"class": "summary-loading"},
                ui.div({"class": "summary-loading-dots"},
                    ui.div({"class": "summary-loading-dot"}),
                    ui.div({"class": "summary-loading-dot"}),
                    ui.div({"class": "summary-loading-dot"}),
                ),
                ui.div("Generating session summary…"),
            )
        s = session_summary()
        e = email_summary()
        if not s:
            return ui.div({"class": "panel-empty"},
                "Session summary will appear here when the session ends.", ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"}, "Click 'End Session' or say 'let's wrap up' to generate.")
            )

        parsed = parse_summary(s)
        children = []

        # Phase 2 auto-delivery notice
        children.append(ui.div(
            {"style": "background:#EEF4FA; border:1px solid #C5D8EC; border-left:3px solid #447099; "
                      "border-radius:0 6px 6px 0; padding:0.6rem 0.85rem; margin-bottom:0.85rem; "
                      "font-size:0.75rem; color:#2D4A63; line-height:1.5;"},
            ui.HTML("<strong>📬 Coming in v2:</strong> This summary will be automatically emailed to your PS lead, "
                    "posted to the team Slack channel, and added to the Monday project board for discussion — "
                    "no copy-paste required."),
        ))

        followup = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
        children.append(ui.div({"class": "followup-block"},
            ui.div({"class": "followup-label"}, "⚑ Follow-up Indicators"),
            ui.div({"class": "followup-content"}, followup),
        ))

        tags_raw = parsed.get("TOPIC_TAGS", "")
        if tags_raw and tags_raw not in ("N/A", "—"):
            tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
            if tag_list:
                children.append(ui.div({"class": "tags-row"},
                    *[ui.span({"class": "topic-tag"}, t) for t in tag_list]
                ))

        children.append(ui.tags.hr({"class": "summary-divider"}))

        for key, label in [
            ("DATE_TIME", "Date / Time"), ("CUSTOMER", "Customer"), ("OUTCOME", "Outcome"),
            ("TOPICS_COVERED", "Topics Covered"), ("GUIDANCE_PROVIDED", "Guidance Provided"),
            ("ESCALATION_SUMMARY", "Escalation Summary"),
            ("UNRESOLVED_QUESTIONS", "Unresolved Questions"), ("RESPONSE_FEEDBACK", "Response Feedback"),
        ]:
            val = parsed.get(key, "—") or "—"
            ocls = ""
            if key == "OUTCOME":
                if "Escalated" in val:  ocls = "outcome-escalated"
                elif "Partially" in val: ocls = "outcome-partial"
                elif "Resolved" in val:  ocls = "outcome-resolved"
            children.append(ui.div({"class": "summary-field"},
                ui.div({"class": "summary-field-label"}, label),
                ui.div({"class": f"summary-field-value {ocls}"}, val),
            ))

        email_text = e or build_email_summary(parsed)
        return ui.div(
            ui.div({"class": "summary-header"},
                ui.span("PS Session Summary"),
                ui.div({"style": "display:flex;gap:0.4rem;"},
                    ui.tags.button("Copy",          {"class": "copy-btn", "id": "copy-summary-btn",
                                                     "onclick": "copyById('summary-structured','copy-summary-btn')"}),
                    ui.tags.button("Copy as Email", {"class": "copy-btn", "id": "copy-email-btn",
                                                     "onclick": "copyById('summary-email','copy-email-btn')"}),
                ),
            ),
            ui.div({"class": "email-toggle-row"},
                ui.span({"class": "email-toggle-label"}, "View:"),
                ui.tags.button("Structured",  {"class": "format-toggle-btn active", "id": "fmt-structured",
                                               "onclick": "toggleSummaryFormat('structured')"}),
                ui.tags.button("Email-ready", {"class": "format-toggle-btn",        "id": "fmt-email",
                                               "onclick": "toggleSummaryFormat('email')"}),
            ),
            ui.div({"id": "summary-structured", "style": "display:block"}, *children),
            ui.div({"id": "summary-email",
                    "style": "display:none;white-space:pre-wrap;font-size:0.78rem;color:#1C2333;line-height:1.6;"},
                   email_text),
        )

    # ---- Escalation panel ----
    @output
    @render.ui
    def escalation_panel_ui():
        entries = handoff_entries()
        if not entries:
            return ui.div({"class": "panel-empty"},
                "Handoff summary appears here if escalation is triggered.", ui.tags.br(), ui.tags.br(),
                ui.span({"style": "font-size:0.68rem;"},
                    "Say 'I'd like to escalate this' or 'Can you get Meredith involved?' to trigger.")
            )
        items = []
        # Phase 2 auto-delivery notice
        items.append(ui.div(
            {"style": "background:#FFF8E1; border:1px solid #FFD54F; border-left:3px solid #F57C00; "
                      "border-radius:0 6px 6px 0; padding:0.6rem 0.85rem; margin-bottom:0.85rem; "
                      "font-size:0.75rem; color:#5D4037; line-height:1.5;"},
            ui.HTML("<strong>📬 Coming in v2:</strong> This escalation summary will be automatically emailed "
                    "to your PS lead, posted to Slack, and added to the Monday project board as a flagged item — "
                    "the moment escalation is triggered."),
        ))
        for i, entry in enumerate(entries, 1):
            bid = f"copy-handoff-{entry['id']}"
            items.append(ui.div({"class": "handoff-entry"},
                ui.div({"class": "handoff-entry-header"},
                    ui.span({"class": "handoff-entry-num"}, f"Escalation #{i} — {entry['ts']}"),
                    ui.tags.button("Copy", {"class": "copy-btn", "id": bid, "onclick": "copyFromBtn(this)"}),
                ),
                ui.div({"class": "handoff-entry-content"}, entry["text"]),
            ))
        return ui.div(
            ui.div({"class": "panel-section-label label-handoff"},
                f"⚡ Escalation Handoff {'Summary' if len(entries)==1 else f'Summaries ({len(entries)})'}"),
            ui.div({"style": "font-size:0.72rem;color:#9BA8BF;margin-bottom:0.75rem;"},
                "Share with Meredith Callahan so she can pick up without context gaps."),
            *items,
        )

    # ---- New Session ----
    @reactive.effect
    @reactive.event(input.new_session)
    def handle_new_session():
        reset_state()
        ui.update_text("user_input", value="")

    # ---- Demo launcher ----
    @reactive.effect
    @reactive.event(input.demo_launch)
    def handle_demo_launch():
        evt = input.demo_launch()
        if not evt: return
        name    = evt.get("name", "")
        role    = evt.get("role", "")
        message = evt.get("message", "")
        reset_state()
        ui.update_text("customer_name", value=name)
        ui.update_select("customer_role", selected=role)
        if not message: return
        started.set(True)
        start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        is_thinking.set(True)
        mid = next_mid()
        messages.set([{"role": "user", "content": message,
                       "ts": datetime.now().strftime("%H:%M"), "id": f"msg_{mid}"}])
        sys_prompt = build_system_prompt(customer_name=name, customer_role=role, is_first_message=True)
        try:
            resp = call_claude(messages=[{"role": "user", "content": message}], system_prompt=sys_prompt)
            is_thinking.set(False)
            add_msg("assistant", resp, source_badge=extract_source_badge(resp))
        except Exception as ex:
            is_thinking.set(False)
            add_msg("assistant", _friendly_error(str(ex)), is_system=True)

    # ---- Feedback ----
    @reactive.effect
    @reactive.event(input.feedback_event)
    def handle_feedback():
        evt = input.feedback_event()
        if not evt: return
        mid = evt.get("msg_id")
        if mid is None: return
        fl = [f for f in feedback_log() if f["msg_id"] != mid]
        fl.append({"msg_id": mid, "helpful": evt.get("helpful")})
        feedback_log.set(fl)

    # ---- Scope decision ----
    @reactive.effect
    @reactive.event(input.scope_decision)
    def handle_scope_decision():
        if input.scope_decision() == "escalate":
            _do_escalate()
        else:
            msgs = messages()
            if msgs:
                messages.set(msgs[:-1] + [{**msgs[-1], "scope_choice": False}])
            add_msg("assistant", "Understood — we'll set that aside. What else can I help you with?", is_system=True)

    # ---- Topic escalation decision ----
    @reactive.effect
    @reactive.event(input.escalation_decision)
    def handle_escalation_decision():
        if input.escalation_decision() == "escalate":
            _do_escalate()
        else:
            msgs = messages()
            if msgs:
                messages.set(msgs[:-1] + [{**msgs[-1], "suggest_escalation": False}])
            tracker.reset()
            add_msg("assistant", "No problem — let's keep going. What would you like to try next?", is_system=True)

    def _do_escalate():
        escalated.set(True)
        # Clean flags from all messages
        messages.set([{**m, "scope_choice": False, "suggest_escalation": False} for m in messages()])
        handoff = generate_handoff_summary(
            messages=real_msgs(),
            customer_name=input.customer_name() or "Not provided",
            customer_role=input.customer_role() or "Not specified",
        )
        ts  = datetime.now().strftime("%H:%M")
        eid = len(handoff_entries()) + 1
        handoff_entries.set(handoff_entries() + [{"id": eid, "text": handoff, "ts": ts}])
        # Switch to escalation tab via JS in chat message (safe — it's content, not DOM mutation)
        add_msg("assistant",
            "Here is a summary you can share with Meredith Callahan so she can pick up right where we left off:\n\n"
            "---\n**HANDOFF SUMMARY FOR MEREDITH CALLAHAN**\n\n" + handoff
            + "\n\n_The Escalation tab on the right has been updated with this summary._",
            is_system=True)
        # Trigger tab switch via a Shiny session JS call — one-time, no accumulation
        ui.notification_show("Escalation summary added — see the Escalation tab →", type="message", duration=5)

    # ---- Send ----
    @reactive.effect
    @reactive.event(input.send_btn)
    def handle_send():
        if ended() or is_thinking(): return
        user_text = input.user_input()
        if not user_text or not user_text.strip(): return

        customer_name = input.customer_name() or ""
        if not customer_name.strip() and not started():
            name_warned.set(True)

        ui.update_text("user_input", value="")

        if not started():
            started.set(True)
            start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        current_role = input.customer_role() or detect_role(user_text) or ""

        if check_session_end_intent(user_text):
            _close_session(current_role, natural_language=True)
            return

        if check_explicit_escalation(user_text):
            _do_escalate()
            return

        is_scope_q = check_scope_question(user_text)

        mid = next_mid()
        messages.set(messages() + [{"role": "user", "content": user_text,
                                     "ts": datetime.now().strftime("%H:%M"), "id": f"msg_{mid}"}])
        is_thinking.set(True)

        is_first = not any(m["role"] == "assistant" and not m.get("is_system") for m in messages())
        sys_prompt = build_system_prompt(customer_name=customer_name, customer_role=current_role, is_first_message=is_first)

        try:
            resp = call_claude(messages=real_msgs(), system_prompt=sys_prompt)
            is_thinking.set(False)

            if "TRIGGER_SESSION_END" in resp:
                resp = resp.replace("TRIGGER_SESSION_END", "").strip()
                add_msg("assistant", resp, source_badge=extract_source_badge(resp))
                _close_session(current_role, natural_language=True)
                return

            if check_unresolved_response(resp):
                unresolved_log.set(unresolved_log() + [user_text[:120]])

            suggest_esc = tracker.update(user_text, resp)
            source      = extract_source_badge(resp)

            mid2 = next_mid()
            messages.set(messages() + [{
                "role": "assistant", "content": resp,
                "ts": datetime.now().strftime("%H:%M"), "id": f"msg_{mid2}",
                "source_badge": source, "scope_choice": is_scope_q, "suggest_escalation": suggest_esc,
            }])

        except Exception as ex:
            is_thinking.set(False)
            add_msg("assistant", _friendly_error(str(ex)), is_system=True)

    # ---- End Session ----
    @reactive.effect
    @reactive.event(input.end_session)
    def handle_end_session():
        if not started() or ended():
            return
        _close_session(input.customer_role() or "", natural_language=False)

    def _close_session(current_role, natural_language=False):
        if ended(): return
        ended.set(True)
        summary_generating.set(True)
        prefix = "Got it — I'll close out our session now. " if natural_language else ""
        add_msg("assistant",
            prefix + "**Session ended.** Generating your PS Summary now — it will appear in the PS Summary tab momentarily. "
            "Meredith Callahan will have full context of what we covered today.",
            is_system=True)
        customer_name = input.customer_name() or ""
        display_name  = customer_name.strip() or f"{current_role} — Name not provided"
        summary = generate_session_summary(
            messages=real_msgs(),
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

def extract_source_badge(text):
    for line in text.split("\n"):
        s = line.strip()
        if any(s.startswith(p) for p in ["📘 Source:", "📋 Source:", "📗 Source:", "📄 Source:"]):
            return s
    return ""


def _friendly_error(detail):
    return (
        "Something went wrong connecting to the assistant. Please try again in a moment.\n\n"
        "If this keeps happening, contact your PS lead directly:\n"
        "**Meredith Callahan** — meredith.flaring453@passmail.net\n\n"
        f"_(Technical detail: {detail[:200]})_"
    )


def parse_summary(raw):
    fields = ["FOLLOW_UP_INDICATORS","DATE_TIME","CUSTOMER","OUTCOME","TOPIC_TAGS",
              "TOPICS_COVERED","GUIDANCE_PROVIDED","ESCALATION_SUMMARY",
              "UNRESOLVED_QUESTIONS","RESPONSE_FEEDBACK"]
    result, cur_key, cur_val = {}, None, []
    for line in raw.split("\n"):
        matched = False
        for f in fields:
            if line.startswith(f"{f}:"):
                if cur_key: result[cur_key] = "\n".join(cur_val).strip()
                cur_key, cur_val = f, [line[len(f)+1:].strip()]
                matched = True; break
        if not matched and cur_key:
            cur_val.append(line)
    if cur_key: result[cur_key] = "\n".join(cur_val).strip()
    return result


def build_email_summary(parsed):
    lines = ["POSIT CLOUD IMPLEMENTATION ASSISTANT — SESSION SUMMARY", "="*55, ""]
    fu = parsed.get("FOLLOW_UP_INDICATORS", "None identified.")
    if fu and fu != "None identified.":
        lines += ["FOLLOW-UP INDICATORS (Action Required)", "-"*40, fu, ""]
    for key, label in [
        ("DATE_TIME","Date / Time"),("CUSTOMER","Customer"),("OUTCOME","Outcome"),
        ("TOPIC_TAGS","Topics"),("TOPICS_COVERED","Topics Covered"),
        ("GUIDANCE_PROVIDED","Guidance Provided"),("ESCALATION_SUMMARY","Escalation Summary"),
        ("UNRESOLVED_QUESTIONS","Unresolved Questions"),("RESPONSE_FEEDBACK","Response Feedback"),
    ]:
        val = parsed.get(key, "")
        if val and val.strip(): lines += [f"{label}: {val}", ""]
    lines += ["-"*55, "Generated by Posit Cloud Implementation Assistant"]
    return "\n".join(lines)


def format_message(text):
    def collect_blockquotes(t):
        lines, out, bq = t.split("\n"), [], []
        for line in lines:
            if line.strip().startswith("> "):
                bq.append(line.strip()[2:])
            else:
                if bq:
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
    text = re.sub(r'\n---\n', '\n<hr>\n', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'(?m)^[📘📋📗📄] Source:.*$',
                  lambda m: f'<div class="source-badge">{m.group(0).strip()}</div>', text)

    lines, output = text.split('\n'), []
    in_list = in_table = False
    thtml = ""; hdr_done = False
    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            if re.match(r'^\|[-\s|:]+\|$', s): hdr_done = True; continue
            if not in_table: in_table = True; hdr_done = False; thtml = '<table>'
            cells = [c.strip() for c in s[1:-1].split('|')]
            tag = 'th' if not hdr_done else 'td'
            if not hdr_done: hdr_done = True
            thtml += '<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>'
            continue
        else:
            if in_table: output.append(thtml + '</table>'); thtml = ''; in_table = False; hdr_done = False
        lm = re.match(r'^(\d+\.\s+|[-*]\s+)(.*)', s)
        if lm:
            if not in_list: output.append('<ul>'); in_list = True
            output.append(f'<li>{lm.group(2)}</li>')
        else:
            if in_list: output.append('</ul>'); in_list = False
            output.append(line)
    if in_list:  output.append('</ul>')
    if in_table: output.append(thtml + '</table>')

    result = []
    for p in re.split(r'\n{2,}', '\n'.join(output)):
        p = p.strip()
        if not p: continue
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
