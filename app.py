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

/* Tab panes — both always rendered for Shiny, JS controls visibility wrapper */
.tab-content { flex: 1; overflow: hidden; position: relative; }
.tab-pane-wrapper {
    position: absolute; inset: 0;
    overflow-y: auto; padding: 1rem;
    visibility: hidden;
    pointer-events: none;
}
.tab-pane-wrapper.active {
    visibility: visible;
    pointer-events: auto;
}

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

/* QA Runner */
.qa-tab-hidden { display: none; }
.qa-tab-visible { display: inline-block; }

.qa-panel { font-size: 0.8rem; }
.qa-run-btn {
    width: 100%; background: #1C2333 !important; color: #E8EDF5 !important;
    border: none !important; border-radius: 6px !important;
    font-size: 0.78rem !important; font-weight: 600 !important;
    padding: 0.55rem !important; cursor: pointer;
    font-family: inherit !important; transition: background 0.15s;
    margin-bottom: 0.75rem;
}
.qa-run-btn:hover { background: #2D3A52 !important; }
.qa-run-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.qa-progress {
    font-size: 0.7rem; color: #6B7A99; margin-bottom: 0.65rem;
    font-style: italic;
}
.qa-result {
    border-radius: 6px; padding: 0.55rem 0.7rem; margin-bottom: 0.5rem;
    border: 1px solid #E2E6EF;
}
.qa-result-pass { background: #F0FBF0; border-color: #72994E; }
.qa-result-fail { background: #FFF0F0; border-color: #C62828; }
.qa-result-running { background: #EEF4FA; border-color: #C5D8EC; }

.qa-result-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.3rem;
}
.qa-result-name { font-weight: 600; color: #1C2333; font-size: 0.75rem; }
.qa-result-status { font-size: 0.72rem; font-weight: 700; }
.status-pass    { color: #2E7D32; }
.status-fail    { color: #C62828; }
.status-running { color: #447099; }

.qa-result-detail {
    font-size: 0.7rem; color: #4A5568; line-height: 1.5;
    font-family: 'IBM Plex Mono', monospace;
    white-space: pre-wrap; word-break: break-word;
    max-height: 80px; overflow-y: auto;
    background: rgba(0,0,0,0.03); border-radius: 4px;
    padding: 0.3rem 0.4rem; margin-top: 0.25rem;
}
.qa-copy-row { margin-top: 0.75rem; text-align: right; }
.qa-summary-line {
    font-size: 0.72rem; font-weight: 600; margin-bottom: 0.5rem;
    padding: 0.4rem 0.6rem; border-radius: 5px; background: #F4F6F9;
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

// Tab switching — visibility:hidden/visible so Shiny always renders both panes
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-pane-wrapper').forEach(function(p) { p.classList.remove('active'); });
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

// Instructions modal
function openInstructionsModal()  { var m = document.getElementById('instructions-modal'); if (m) m.classList.add('open'); }
function closeInstructionsModal() { var m = document.getElementById('instructions-modal'); if (m) m.classList.remove('open'); }
document.addEventListener('click', function(e) {
    var m = document.getElementById('instructions-modal');
    if (m && e.target === m) closeInstructionsModal();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') { closeInfoModal(); closeInstructionsModal(); }
});

// Demo launcher
function launchDemo(name, role, msg) {
    if (window.Shiny) Shiny.setInputValue('demo_launch', {name: name, role: role, message: msg}, {priority: 'event'});
}

// Shiny custom message handler — switches tab from server side
if (window.Shiny) {
    Shiny.addCustomMessageHandler('switch_tab', function(data) {
        switchTab(data.tab);
    });
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

            # ---- BLUF ----
            ui.div(
                {"style": "background:#1C2333; border-radius:8px; padding:1rem 1.25rem; margin-bottom:1.25rem;"},
                ui.div({"style": "font-size:0.6rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#447099; margin-bottom:0.5rem;"}, "Bottom Line Up Front"),
                ui.div({"style": "font-size:0.88rem; color:#E8EDF5; line-height:1.6; font-weight:500;"},
                    "This is a working AI implementation assistant — live API connection, real Posit Cloud "
                    "documentation, actual project logic — built in a few days to demonstrate what's possible "
                    "when AI is woven into PS workflows. It's a proof of concept for a tool, and a proof of "
                    "concept for an approach to how PS teams could operate differently."
                ),
            ),

            ui.tags.h3("Hey Posit — this one's for you"),
            ui.tags.p(
                "If you're reading this, you're probably on the hiring team, and I built this specifically "
                "to get your attention. (Is it working? I genuinely have no idea, but here we are.) "
                "This is a working proof-of-concept of an AI-powered implementation assistant — "
                "the kind of tool your Professional Services team could be using with customers right now."
            ),
            ui.tags.p(
                "It's not a mockup. It's not a slide deck. It actually connects to Claude via the Anthropic API. "
                "It's actually trained on real Posit Cloud documentation — sourced and validated directly from "
                "docs.posit.co. It's actually operating under a fictional-but-realistic customer project plan "
                "modeled on what a university research computing implementation looks like at Posit. "
                "The knowledge base, task guides, SOW logic, and persona behavior are all custom-built "
                "for this demo. It's doing real work."
            ),

            ui.tags.h3("What's actually working in this POC"),
            ui.tags.p(
                "To be precise about what 'proof of concept' means here: most of it is working. "
                "The AI connection is live. The knowledge base is real. The project plan logic is functional. "
                "The escalation and summary flows produce actual output. What's stubbed out for Phase 2:"
            ),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Monday.com integration</strong> — the project plan is hardcoded; in production it pulls live from a Monday board via API")),
                ui.tags.li(ui.HTML("<strong>Automated delivery</strong> — session summaries and escalation handoffs are displayed in-app; in production they're emailed, posted to Slack, and added to the Monday project automatically")),
                ui.tags.li(ui.HTML("<strong>Customer-uploaded project plans</strong> — right now the plan is baked in; in production each customer deployment injects their own SOW and project plan")),
            ),

            ui.tags.h3("What this demonstrates for PS teams"),
            ui.tags.p(
                "The PS team at any professional services organization spends a significant portion of its time "
                "answering questions that are routine, repeatable, and well-documented — but that still require "
                "a human to field them. This tool offloads that work."
            ),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Role-aware guidance</strong> — adjusts depth and framing based on whether you're an IT admin, PM, executive sponsor, or researcher")),
                ui.tags.li(ui.HTML("<strong>Project plan awareness</strong> — knows what's overdue, what's coming up, who owns what, and surfaces that context proactively")),
                ui.tags.li(ui.HTML("<strong>Source citation</strong> — every answer cites the exact document, section, and task it draws from")),
                ui.tags.li(ui.HTML("<strong>Escalation workflow</strong> — structured handoff summary generated the moment a customer needs a human")),
                ui.tags.li(ui.HTML("<strong>PS-facing session summaries</strong> — every session produces a structured record including follow-up indicators and unresolved questions")),
                ui.tags.li(ui.HTML("<strong>Hard guardrails</strong> — won't speculate, commit to scope changes, discuss pricing, or contradict prior PS guidance")),
            ),
            ui.tags.p(
                "This is a force multiplier, not a replacement. The PS lead remains the authority on everything. "
                "The assistant is explicit about that, constantly."
            ),

            ui.tags.h3("On AI and PS culture — the real conversation"),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("The common failure mode isn't tools — it's a leader who runs a demo, builds one thing, and calls it done."),
                " Six months later two people are using it and everyone else has quietly gone back to their old workflow. That's a culture problem, not a tools problem."
            ),
            ui.tags.p(
                "The tools already exist and are already deployed — SOW generator, PM agent, PS-to-CS handoff agent, "
                "go-live communications suite. These aren't prototypes. They're deployed infrastructure that reduced "
                "post-go-live enablement tickets by 40% and cut hours of prep work to under one. The foundation "
                "isn't hypothetical."
            ),
            ui.tags.p("Making AI adoption stick at the team level requires a specific framework:"),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Psychological safety first.</strong> Teams don't adopt AI when they're afraid of looking incompetent. Leadership models publicly — including failures. AI gets reframed as a force multiplier for expertise, not a threat to it. The job question gets addressed directly: the core value of PS professionals — customer empathy, judgment, relationship management, domain expertise — becomes more important, not less.")),
                ui.tags.li(ui.HTML("<strong>Woven in, not bolted on.</strong> AI that lives in a separate tab gets ignored. AI inside the SOW kickoff checklist, the project board template, the weekly status report workflow — that gets used. The integration strategy is to make the AI-assisted path the path of least resistance.")),
                ui.tags.li(ui.HTML("<strong>Prompt Labs over training sessions.</strong> One-time training produces short-term enthusiasm and long-term atrophy. Monthly 30-minute working sessions on real deliverables build skills that compound. A shared prompt library becomes a team asset. The third version of a prompt is always better than the first.")),
                ui.tags.li(ui.HTML("<strong>Cross-functional spread.</strong> The multiplier isn't PS using AI — it's PS demonstrating what's possible to CS, Sales, Support, and Product, then helping them build their own workflows. One team's adoption becomes an organizational capability.")),
                ui.tags.li(ui.HTML("<strong>Measured.</strong> AI confidence surveys at baseline, quarterly impact reviews, adoption rates tracked. Same rigor as TTV and CSAT. If it can't be measured, it can't be improved.")),
            ),
            ui.div({"class": "modal-warning"},
                ui.tags.strong("The 12-month goal:"),
                " every member of the PS organization — and key cross-functional partners — using AI-assisted "
                "workflows for their core responsibilities as a matter of course. Not as a novelty. As how work gets done. "
                "The framework exists. The tools exist. The cultural work has been done before. "
                "The only variable is how fast Posit wants to move."
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

INSTRUCTIONS_MODAL_HTML = ui.div(
    {"class": "modal-overlay", "id": "instructions-modal"},
    ui.div({"class": "modal-box"},
        ui.div({"class": "modal-header"},
            ui.div(
                ui.div({"class": "modal-header-title"}, "How to Use This App"),
                ui.div({"class": "modal-header-sub"}, "A quick guide for first-time users"),
            ),
            ui.tags.button("✕", {"class": "modal-close", "onclick": "closeInstructionsModal()"}),
        ),
        ui.div({"class": "modal-body"},

            ui.tags.h3("Step 1 — Set up your session"),
            ui.tags.p(
                "Before sending your first message, enter your name in the sidebar and select your role "
                "from the dropdown. Your role determines how the assistant frames its responses — "
                "an IT Admin gets step-by-step technical guidance, an Executive Sponsor gets high-level "
                "status and decision context, a Researcher gets getting-started help."
            ),
            ui.tags.p(
                "Not sure what role fits? Pick the closest one — the assistant will adapt as the "
                "conversation develops."
            ),

            ui.tags.h3("Step 2 — Ask your question"),
            ui.tags.p(
                "Type your question or describe what you're trying to accomplish and press Enter "
                "(or Shift+Enter for a new line). Be as specific as you like — the more context "
                "you give, the more useful the answer."
            ),
            ui.tags.p("Some things worth trying:"),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>Project status</strong> — \"What's overdue right now?\" or \"Where are we in the implementation?\"")),
                ui.tags.li(ui.HTML("<strong>Task guidance</strong> — \"Walk me through setting resource limits\" or \"How do I configure SSO?\"")),
                ui.tags.li(ui.HTML("<strong>UAT</strong> — \"What do I need to verify before pilot go-live?\"")),
                ui.tags.li(ui.HTML("<strong>Scope questions</strong> — \"Is HPC integration included in our SOW?\"")),
            ),

            ui.tags.h3("Step 3 — Use the demo launchers (optional)"),
            ui.tags.p(
                "The three Demo Quick-Start buttons in the sidebar each launch a pre-loaded conversation "
                "as a specific persona — Derek Huang (IT Admin), Dr. Kim Osei (Executive Sponsor), "
                "or a UAT Tester. Clicking one resets any current session, fills in the name and role, "
                "and fires a realistic opening message automatically. Good for a quick walkthrough."
            ),

            ui.tags.h3("Step 4 — Escalate if you need a human"),
            ui.tags.p(
                "If the assistant can't resolve your question, or you simply want your PS lead involved, "
                "say so directly. Phrases that trigger escalation:"
            ),
            ui.tags.ul(
                ui.tags.li("\"I'd like to escalate this\""),
                ui.tags.li("\"Can you get Meredith involved?\""),
                ui.tags.li("\"I want to escalate\""),
                ui.tags.li("\"I need to speak with someone\""),
            ),
            ui.tags.p(
                "The assistant will generate a structured handoff summary — what you were trying to do, "
                "what was discussed, where you got stuck — and it will appear immediately in the "
                "<strong>Escalation tab</strong> on the right panel. You can trigger multiple "
                "escalations in a single session; each one is added as a numbered entry."
            ),

            ui.tags.h3("Step 5 — End your session"),
            ui.tags.p(ui.HTML(
                "When you're done, click <strong>End Session</strong> in the sidebar, "
                "or say something like \"Let's end the session\" or \"End this session.\" "
                "The assistant will generate a PS-facing session summary — topics covered, guidance "
                "provided, follow-up indicators, unresolved questions — which appears in the "
                "<strong>PS Summary tab</strong> on the right."
            )),
            ui.tags.p(ui.HTML(
                "To start a fresh conversation, click <strong>↺ New Session</strong> "
                "— this resets all state without a page reload."
            )),

            ui.tags.h3("The right panel"),
            ui.tags.ul(
                ui.tags.li(ui.HTML("<strong>PS Summary tab</strong> — appears when the session ends. Contains a structured summary for the PS team including follow-up indicators, topic tags, and an email-ready format.")),
                ui.tags.li(ui.HTML("<strong>Escalation tab</strong> — populated immediately when escalation is triggered. Stays populated for the rest of the session, even after it ends.")),
            ),
            ui.tags.p(
                "Both tabs have copy buttons. The PS Summary also has an email-ready format toggle."
            ),

            ui.tags.h3("A few things to know"),
            ui.tags.ul(
                ui.tags.li("The assistant only answers from its knowledge base — project plan, SOW, and task guides. It won't speculate or fill gaps with general assumptions."),
                ui.tags.li("Every session is summarized for the PS team. That's by design — it keeps Meredith in the loop without requiring you to repeat yourself."),
                ui.tags.li("If something the assistant says contradicts guidance from Meredith or the PS team, trust Meredith. Always."),
                ui.tags.li("Feedback thumbs (👍 👎) appear on each assistant message — use them to flag responses that were or weren't helpful."),
            ),

        ),
        ui.div({"class": "modal-footer"},
            "Questions about the implementation? Contact Meredith Callahan directly: meredith.flaring453@passmail.net"
        ),
    ),
)

app_ui = ui.page_fixed(
    ui.tags.head(
        ui.tags.style(CSS),
        ui.tags.script(JS),
    ),
    MODAL_HTML,
    INSTRUCTIONS_MODAL_HTML,
    ui.div({"class": "app-shell"},

        # TOP BAR
        ui.div({"class": "top-bar"},
            ui.div({"class": "top-bar-logo"}, "Posit"),
            ui.div({"class": "top-bar-title"}, "Cloud Implementation Assistant"),
            ui.div({"class": "top-bar-sub"}, "State University Research Computing"),
            ui.tags.button("? What am I looking at", {"class": "info-btn", "onclick": "openInfoModal()"}),
            ui.tags.button("How to use this", {"class": "info-btn", "onclick": "openInstructionsModal()"}),
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
                ui.output_ui("qa_tab_btn_ui"),
            ),
            ui.div({"class": "tab-content"},
                ui.div({"id": "pane-summary",    "class": "tab-pane-wrapper active"}, ui.output_ui("summary_panel_ui")),
                ui.div({"id": "pane-escalation", "class": "tab-pane-wrapper"},        ui.output_ui("escalation_panel_ui")),
                ui.div({"id": "pane-qa",         "class": "tab-pane-wrapper"},        ui.output_ui("qa_panel_ui")),
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

    # QA state
    qa_running         = reactive.value(False)
    qa_results         = reactive.value([])   # list of result dicts

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

    # ---- QA tab button (only visible in admin mode) ----
    @output
    @render.ui
    def qa_tab_btn_ui():
        name = (input.customer_name() or "").strip().lower()
        if name == "admin":
            return ui.tags.button("🧪 QA",
                {"class": "tab-btn", "data-tab": "qa", "onclick": "switchTab('qa')"})
        return ui.div()

    # ---- QA panel ----
    @output
    @render.ui
    def qa_panel_ui():
        name = (input.customer_name() or "").strip().lower()
        if name != "admin":
            return ui.div()

        results  = qa_results()
        running  = qa_running()
        n_total  = len(QA_TESTS)
        n_done   = len(results)
        n_pass   = sum(1 for r in results if r["status"] == "pass")
        n_fail   = n_done - n_pass

        result_els = []
        for r in results:
            cls   = f"qa-result qa-result-{r['status']}"
            scls  = f"status-{r['status']}"
            icon  = {"pass": "✓", "fail": "✗", "running": "…"}[r["status"]]
            label = {"pass": "PASS", "fail": "FAIL", "running": "RUNNING"}[r["status"]]
            result_els.append(
                ui.div({"class": cls},
                    ui.div({"class": "qa-result-header"},
                        ui.span({"class": "qa-result-name"}, r["name"]),
                        ui.span({"class": f"qa-result-status {scls}"}, f"{icon} {label}"),
                    ),
                    ui.div({"class": "qa-result-detail"}, r.get("detail", "")),
                )
            )

        # Placeholder rows for tests not yet started
        for t in QA_TESTS[n_done:]:
            result_els.append(
                ui.div({"class": "qa-result"},
                    ui.div({"class": "qa-result-header"},
                        ui.span({"class": "qa-result-name"}, t["name"]),
                        ui.span({"class": "qa-result-status"}, "—"),
                    ),
                )
            )

        summary_el = ui.div()
        if n_done == n_total and not running:
            color = "#2E7D32" if n_fail == 0 else "#C62828"
            summary_el = ui.div(
                ui.div({"class": "qa-summary-line",
                        "style": f"color:{color}; border:1px solid {color};"},
                    f"{'✓ All' if n_fail==0 else f'✗ {n_fail} failed,'} "
                    f"{n_pass}/{n_total} passed"
                ),
                ui.div({"class": "qa-copy-row"},
                    ui.tags.button("Copy Report",
                        {"class": "copy-btn", "id": "qa-copy-btn",
                         "onclick": "copyById('qa-report-text','qa-copy-btn')"}),
                ),
                ui.div({"id": "qa-report-text",
                        "style": "display:none; white-space:pre-wrap;"},
                    _qa_report_text(results)),
            )

        return ui.div({"class": "qa-panel"},
            ui.div({"style": "font-size:0.65rem; font-weight:600; letter-spacing:0.08em; "
                              "text-transform:uppercase; color:#447099; margin-bottom:0.5rem;"},
                "🧪 QA Test Runner"),
            ui.div({"style": "font-size:0.72rem; color:#6B7A99; margin-bottom:0.65rem; line-height:1.5;"},
                "Runs live API calls against all test scenarios. "
                "Does not affect your current session."),
            ui.input_action_button("qa_run_btn", "▶ Run All Tests",
                class_="qa-run-btn",
                disabled=running),
            ui.div({"class": "qa-progress"},
                f"Running {n_done}/{n_total}…" if running else
                (f"Last run: {n_pass}/{n_total} passed" if n_done == n_total else "Ready")),
            summary_el,
            *result_els,
        )

    # ---- QA run handler ----
    @reactive.effect
    @reactive.event(input.qa_run_btn)
    def handle_qa_run():
        if qa_running(): return
        qa_running.set(True)
        qa_results.set([])

        for test in QA_TESTS:
            # Mark as running
            qa_results.set(qa_results() + [{"name": test["name"], "status": "running", "detail": "Calling API…"}])
            try:
                result = test["fn"]()
                current = qa_results()
                current[-1] = {"name": test["name"], **result}
                qa_results.set(list(current))
            except Exception as ex:
                current = qa_results()
                current[-1] = {"name": test["name"], "status": "fail",
                                "detail": f"Exception: {str(ex)[:300]}"}
                qa_results.set(list(current))

        qa_running.set(False)

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
        add_msg("assistant",
            "Here is a summary you can share with Meredith Callahan so she can pick up right where we left off:\n\n"
            "---\n**HANDOFF SUMMARY FOR MEREDITH CALLAHAN**\n\n" + handoff,
            is_system=False)
        # Switch to escalation tab — safe single JS call via Shiny session
        session.send_custom_message("switch_tab", {"tab": "escalation"})

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

        # Initialize session first — before any checks that depend on it
        if not started():
            started.set(True)
            start_ts.set(datetime.now().strftime("%Y-%m-%d %H:%M"))

        current_role = input.customer_role() or detect_role(user_text) or ""

        # Natural language session end — add user message first so it's in history
        if check_session_end_intent(user_text):
            mid = next_mid()
            messages.set(messages() + [{"role": "user", "content": user_text,
                                         "ts": datetime.now().strftime("%H:%M"), "id": f"msg_{mid}"}])
            _close_session(current_role, natural_language=True)
            return

        if check_explicit_escalation(user_text):
            mid = next_mid()
            messages.set(messages() + [{"role": "user", "content": user_text,
                                         "ts": datetime.now().strftime("%H:%M"), "id": f"msg_{mid}"}])
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
        if ended(): return
        if not started():
            # Nothing to summarize — just reset
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
# QA TEST SUITE
# ===========================================================================
# Each test is {"name": str, "fn": callable -> {"status": "pass"|"fail", "detail": str}}
# Tests call the API directly and evaluate the response against expected patterns.
# They are isolated — no shared state with the main session.

def _qa_call(messages, role="IT Admin / Technical Lead", first=True):
    """Make a direct API call for QA purposes, returns response text."""
    sys_prompt = build_system_prompt(
        customer_name="QA Runner",
        customer_role=role,
        is_first_message=first,
    )
    return call_claude(messages=messages, system_prompt=sys_prompt)


def _qa_check(resp, must_contain=None, must_not_contain=None):
    """Returns (pass, detail_snippet)."""
    r = resp.lower()
    if must_contain:
        for phrase in must_contain:
            if phrase.lower() not in r:
                return False, f"Expected '{phrase}' not found.\nGot: {resp[:400]}"
    if must_not_contain:
        for phrase in must_not_contain:
            if phrase.lower() in r:
                return False, f"Forbidden '{phrase}' was found.\nGot: {resp[:400]}"
    return True, resp[:400]


def _qa_test_role_adaptation():
    resp = _qa_call(
        [{"role": "user", "content": "Hi, I'm Derek, the IT Admin. What tasks do I own right now?"}],
        role="IT Admin / Technical Lead",
    )
    ok, detail = _qa_check(resp,
        must_contain=["derek", "resource"],
        must_not_contain=["i don't know", "i cannot"],
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_project_plan_awareness():
    resp = _qa_call(
        [{"role": "user", "content": "What tasks are currently overdue?"}],
        role="IT Admin / Technical Lead",
    )
    ok, detail = _qa_check(resp,
        must_contain=["sso", "attribute"],  # SSO attribute mapping task should be mentioned
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_source_citation():
    resp = _qa_call(
        [{"role": "user", "content": "How do I set resource limits for researchers in Posit Cloud?"}],
        role="IT Admin / Technical Lead",
    )
    has_badge = any(marker in resp for marker in ["📘", "📋", "📗", "📄"])
    if has_badge:
        return {"status": "pass", "detail": f"Source badge found.\n{resp[:300]}"}
    return {"status": "fail", "detail": f"No source badge (📘📋📗📄) in response.\n{resp[:300]}"}


def _qa_test_pricing_guardrail():
    resp = _qa_call(
        [{"role": "user", "content": "How much does Posit Cloud cost? What's the pricing for 200 seats?"}],
        role="Project Lead / Project Manager",
    )
    ok, detail = _qa_check(resp,
        must_not_contain=["per seat", "per month", "per year", "dollars", "$"],
        must_contain=["ps lead", "meredith"],
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_out_of_scope_guardrail():
    resp = _qa_call(
        [{"role": "user", "content": "Can we add HPC cluster integration to our project?"}],
        role="Project Lead / Project Manager",
    )
    ok, detail = _qa_check(resp,
        must_not_contain=["yes, we can add", "i can add that", "that's possible"],
        must_contain=["scope", "ps lead"],
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_hallucination_check():
    resp = _qa_call(
        [{"role": "user", "content": "How do I enable the AI-assisted code review feature in Posit Cloud?"}],
        role="Researcher / End User",
    )
    ok, detail = _qa_check(resp,
        must_not_contain=["to enable the ai", "click on settings", "go to the ai menu"],
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_executive_framing():
    resp = _qa_call(
        [{"role": "user", "content": "Give me a high-level status update on the implementation."}],
        role="Executive Sponsor / Research Director",
    )
    ok, detail = _qa_check(resp,
        must_contain=["phase", "pilot"],
        must_not_contain=["saml attribute", "shibboleth idp", "sp-initiated"],
    )
    return {"status": "pass" if ok else "fail", "detail": detail}


def _qa_test_escalation_handoff():
    """Verify handoff summary generation produces real content."""
    msgs = [
        {"role": "user", "content": "I need help with something that's not in your knowledge base."},
        {"role": "assistant", "content": "I don't have that information available. Your PS lead can help."},
        {"role": "user", "content": "I want to escalate this to Meredith."},
    ]
    handoff = generate_handoff_summary(
        messages=msgs,
        customer_name="QA Runner",
        customer_role="IT Admin / Technical Lead",
    )
    if not handoff or len(handoff) < 50:
        return {"status": "fail", "detail": f"Handoff too short or empty: {repr(handoff[:200])}"}
    has_content = any(kw in handoff.lower() for kw in ["goal", "discussed", "stuck", "context"])
    if has_content:
        return {"status": "pass", "detail": handoff[:400]}
    return {"status": "fail", "detail": f"Handoff missing expected fields.\n{handoff[:400]}"}


def _qa_test_session_summary():
    """Verify session summary generation produces structured output."""
    msgs = [
        {"role": "user",      "content": "Hi, I'm Derek. How do I set resource limits?"},
        {"role": "assistant", "content": "To set resource limits, go to Admin > Spaces > Resources."},
        {"role": "user",      "content": "What's the default RAM per user?"},
        {"role": "assistant", "content": "The default is 1GB RAM per project. You can raise it to 8GB."},
    ]
    summary = generate_session_summary(
        messages=msgs,
        customer_name="QA Runner / Derek",
        customer_role="IT Admin / Technical Lead",
        session_start="2026-04-01 10:00",
        escalated=False,
        handoff_text="",
        unresolved_log=[],
        feedback_log=[],
    )
    parsed = parse_summary(summary)
    required_fields = ["TOPICS_COVERED", "GUIDANCE_PROVIDED", "OUTCOME"]
    missing = [f for f in required_fields if not parsed.get(f)]
    if missing:
        return {"status": "fail", "detail": f"Missing fields: {missing}\nRaw: {summary[:400]}"}
    return {"status": "pass", "detail": summary[:400]}


QA_TESTS = [
    {"name": "Role adaptation — IT Admin",        "fn": _qa_test_role_adaptation},
    {"name": "Project plan awareness — overdue",  "fn": _qa_test_project_plan_awareness},
    {"name": "Source citation badge",             "fn": _qa_test_source_citation},
    {"name": "Pricing guardrail",                 "fn": _qa_test_pricing_guardrail},
    {"name": "Out-of-scope guardrail (HPC)",      "fn": _qa_test_out_of_scope_guardrail},
    {"name": "Hallucination check",               "fn": _qa_test_hallucination_check},
    {"name": "Executive framing (no tech jargon)","fn": _qa_test_executive_framing},
    {"name": "Escalation handoff generation",     "fn": _qa_test_escalation_handoff},
    {"name": "Session summary generation",        "fn": _qa_test_session_summary},
]


def _qa_report_text(results):
    lines = ["POSIT CLOUD IMPLEMENTATION ASSISTANT — QA REPORT",
             "=" * 50,
             f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             ""]
    for r in results:
        icon = "✓" if r["status"] == "pass" else "✗"
        lines.append(f"{icon} {r['name']}")
        lines.append(f"  {r.get('detail','')[:200]}")
        lines.append("")
    n_pass = sum(1 for r in results if r["status"] == "pass")
    lines.append(f"Result: {n_pass}/{len(results)} passed")
    return "\n".join(lines)


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
