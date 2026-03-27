# api.py v2
# Anthropic API calls, escalation logic, session-end detection,
# unresolved question log, summary generation.

import os
import httpx
from datetime import datetime

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Phrase lists
# ---------------------------------------------------------------------------
ESCALATION_PHRASES = [
    "talk to someone", "speak to someone", "speak with meredith",
    "contact meredith", "reach meredith", "call meredith",
    "need help from", "need a human", "need a person",
    "escalate", "ps team", "professional services",
    "can someone help me", "i want to talk to",
]

RESOLUTION_PHRASES = [
    "got it", "that works", "that helped", "makes sense",
    "i understand", "i see", "thank you", "thanks", "perfect",
    "that's what i needed", "all set", "i'm good", "solved",
    "figured it out", "i'll try that", "makes sense now",
]

# Natural language end-session signals
SESSION_END_PHRASES = [
    "end this session", "end the session", "close this session",
    "we're done", "that's all", "that's it for now", "i'm done",
    "wrap up", "wrap this up", "let's stop here", "stop here",
    "finish the session", "conclude the session", "goodbye",
    "we can end", "end our session", "let's go ahead and end",
    "go ahead and end", "done for today", "done for now",
]

# Scope-question signals — used to offer user a choice before escalating
SCOPE_SIGNALS = [
    "can we add", "can you add", "is it possible to add", "add to scope",
    "include", "also need", "what about adding", "we also want",
    "not in scope", "out of scope", "in scope", "scope question",
    "hpc", "hipaa", "package mirror", "workbench", "connect",
    "data warehouse", "on-prem", "hybrid",
]

# Signals that assistant couldn't answer (for unresolved log)
UNRESOLVED_SIGNALS = [
    "i don't have that information",
    "i don't have sufficient information",
    "your ps lead can best address",
    "meredith callahan can best address",
    "i can't answer that",
    "outside my knowledge",
    "not in my knowledge base",
    "i don't know",
    "escalate",
]


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
    return key


def call_claude(messages: list, system_prompt: str, max_tokens: int = 1000) -> str:
    """Send a conversation to Claude and return the text response."""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": get_api_key(),
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }
    try:
        response = httpx.post(API_URL, headers=headers, json=body, timeout=60.0)
        response.raise_for_status()
        data = response.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        if not text_blocks:
            raise ValueError("No text content returned by API.")
        return "\n".join(text_blocks)
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            detail = str(e)
        raise RuntimeError(f"Anthropic API error: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"API request failed: {str(e)}") from e


def generate_handoff_summary(messages: list, customer_name: str, customer_role: str) -> str:
    """Generate a PS-facing escalation handoff summary."""
    try:
        transcript = "\n\n".join(
            f"{'CUSTOMER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
            for m in messages
        )
        prompt = f"""Generate a concise escalation handoff summary based on this conversation.
Customer: {customer_name or 'Not provided'} ({customer_role or 'Role not specified'})

CONVERSATION:
{transcript}

Format the output in EXACTLY this structure — no preamble, no closing remarks:

Customer was trying to: [one sentence]
What was discussed: [2-3 sentences max]
Where they got stuck: [specific blocker or unanswered question]
Relevant project context: [milestone, due date, or task reference if applicable]"""

        return call_claude(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You generate concise, factual escalation handoff summaries for a PS team.",
            max_tokens=400,
        )
    except Exception as e:
        return f"Handoff summary generation failed: {str(e)}"


def generate_session_summary(
    messages: list,
    customer_name: str,
    customer_role: str,
    session_start: str,
    escalated: bool,
    handoff_text: str = "",
    unresolved_log: list = None,
    feedback_log: list = None,
) -> str:
    """Generate a structured PS-facing session summary at session close."""
    try:
        transcript = "\n\n".join(
            f"{'CUSTOMER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
            for m in messages
        )
        session_end = datetime.now().strftime("%Y-%m-%d %H:%M")
        escalated_str = "Yes" if escalated else "No"

        unresolved_str = ""
        if unresolved_log:
            unresolved_str = "\n\nUNRESOLVED QUESTIONS THIS SESSION:\n" + "\n".join(
                f"- {q}" for q in unresolved_log
            )

        feedback_str = ""
        if feedback_log:
            helpful = sum(1 for f in feedback_log if f["helpful"])
            not_helpful = sum(1 for f in feedback_log if not f["helpful"])
            feedback_str = f"\n\nRESPONSE FEEDBACK: {helpful} helpful, {not_helpful} not helpful"

        from knowledge_base import TOPIC_TAGS
        tags_list = ", ".join(TOPIC_TAGS)

        prompt = f"""You are generating a PS-facing session summary for a Posit Cloud implementation assistant.
This summary is for the PS team (Meredith Callahan), NOT the customer.
Be factual, specific, and concise. Do not speculate about customer intent.

Customer name: {customer_name or 'Not provided'}
Customer role: {customer_role or 'Not specified'}
Session start: {session_start}
Session end: {session_end}
Escalated: {escalated_str}
{feedback_str}
{unresolved_str}

CONVERSATION TRANSCRIPT:
{transcript}

Generate a session summary in EXACTLY this format. Every field is required.

FOLLOW_UP_INDICATORS: [List any specific signals PS should act on proactively — questions about out-of-scope items, repeated confusion, expressed frustration, overdue tasks mentioned, scope misunderstandings. Be specific. If none, write "None identified."]

DATE_TIME: {session_start} — {session_end}
CUSTOMER: {customer_name or 'Not provided'} | {customer_role or 'Not specified'}
OUTCOME: [Resolved / Partially Resolved / Escalated]
TOPIC_TAGS: [Select all that apply from: {tags_list}]
TOPICS_COVERED: [Comma-separated list of topics discussed]
GUIDANCE_PROVIDED: [2-4 sentences summarizing key guidance and steps shared]
ESCALATION_SUMMARY: [Full handoff summary if escalated; otherwise N/A]
UNRESOLVED_QUESTIONS: [List questions the assistant could not answer; otherwise None]
RESPONSE_FEEDBACK: [Summary of helpful/not-helpful feedback if any; otherwise None]

Keep the entire summary under 400 words. No preamble or closing remarks."""

        return call_claude(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You generate factual, structured session summaries for a PS team. Be concise and specific.",
            max_tokens=700,
        )
    except Exception as e:
        return f"Session summary generation failed: {str(e)}"


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def check_explicit_escalation(user_message: str) -> bool:
    msg = user_message.lower()
    return any(phrase in msg for phrase in ESCALATION_PHRASES)


def check_resolution_signal(user_message: str) -> bool:
    msg = user_message.lower()
    return any(phrase in msg for phrase in RESOLUTION_PHRASES)


def check_session_end_intent(user_message: str) -> bool:
    """Detect if the user wants to end the session via natural language."""
    msg = user_message.lower()
    return any(phrase in msg for phrase in SESSION_END_PHRASES)


def check_scope_question(user_message: str) -> bool:
    """Detect if a message is likely touching on out-of-scope topics."""
    msg = user_message.lower()
    return any(phrase in msg for phrase in SCOPE_SIGNALS)


def check_unresolved_response(assistant_message: str) -> bool:
    """Detect if an assistant response signals it couldn't answer."""
    msg = assistant_message.lower()
    return any(phrase in msg for phrase in UNRESOLVED_SIGNALS)


def update_unresolved_count(current_count: int, user_message: str) -> int:
    if check_resolution_signal(user_message):
        return 0
    return current_count + 1


def should_escalate(unresolved_count: int, user_message: str, escalated_already: bool) -> bool:
    if escalated_already:
        return False
    if check_explicit_escalation(user_message):
        return True
    if unresolved_count >= 3:
        return True
    return False


# ---------------------------------------------------------------------------
# Role detection from free-text
# ---------------------------------------------------------------------------

def detect_role(user_message: str) -> str | None:
    msg = user_message.lower()
    it_signals = ["it admin", "sysadmin", "system admin", "technical lead", "tech lead",
                  "derek", "infrastructure", "shibboleth", "sso config", "network admin"]
    if any(s in msg for s in it_signals):
        return "IT Admin / Technical Lead"
    pm_signals = ["project manager", "pm ", " pm", "project lead", "project coordinator",
                  "implementation lead", "program manager"]
    if any(s in msg for s in pm_signals):
        return "Project Lead / Project Manager"
    exec_signals = ["executive", "director", "vp ", "dean", "chief", "sponsor",
                    "leadership", "dr. kim", "kim osei", "research director"]
    if any(s in msg for s in exec_signals):
        return "Executive Sponsor / Research Director"
    uat_signals = ["uat", "user acceptance", "tester", "testing team", "qa "]
    if any(s in msg for s in uat_signals):
        return "UAT Tester"
    researcher_signals = ["researcher", "faculty", "professor", "grad student", "graduate student",
                          "postdoc", "analyst", "scientist", "end user", "i use r", "i run analyses"]
    if any(s in msg for s in researcher_signals):
        return "Researcher / End User"
    return None
