# api.py
# Anthropic API calls and escalation/summary generation logic.

import os
import httpx
from datetime import datetime

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Phrases that signal explicit escalation request
# ---------------------------------------------------------------------------
ESCALATION_PHRASES = [
    "talk to someone", "speak to someone", "speak with meredith",
    "contact meredith", "reach meredith", "call meredith",
    "need help from", "need a human", "need a person",
    "escalate", "ps team", "professional services",
    "can someone help me", "i want to talk to",
]

# Phrases that signal the user is unblocked / resolved
RESOLUTION_PHRASES = [
    "got it", "that works", "that helped", "makes sense",
    "i understand", "i see", "thank you", "thanks", "perfect",
    "that's what i needed", "all set", "i'm good", "solved",
    "figured it out", "i'll try that", "makes sense now",
]


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
    return key


def call_claude(messages: list, system_prompt: str, max_tokens: int = 900) -> str:
    """Send a conversation to the Claude API and return the text response."""
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
) -> str:
    """Generate a PS-facing session summary at session close."""
    try:
        transcript = "\n\n".join(
            f"{'CUSTOMER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
            for m in messages
        )
        session_end = datetime.now().strftime("%Y-%m-%d %H:%M")
        escalated_str = "Yes" if escalated else "No"

        prompt = f"""You are generating a PS-facing session summary for a Posit Cloud implementation assistant.
This summary is for the PS team (Meredith Callahan), NOT the customer.
Be factual, specific, and concise. Do not speculate about customer intent.

Customer name: {customer_name or 'Not provided'}
Customer role: {customer_role or 'Not specified'}
Session start: {session_start}
Session end: {session_end}
Escalated: {escalated_str}

CONVERSATION TRANSCRIPT:
{transcript}

Generate a session summary in EXACTLY this format:

Date/Time: [session start — session end]
Customer User: [name and role]
Topics Covered: [comma-separated list]
Guidance Provided: [2-4 sentences summarizing key guidance shared]
Outcome: [Resolved / Partially Resolved / Escalated]
Escalation Summary: [full handoff summary if escalated; otherwise N/A]
Follow-up Indicators: [specific signals PS should act on; or "None identified"]

Keep the entire summary under 300 words. No preamble or closing remarks."""

        return call_claude(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You generate factual, structured session summaries for a PS team. Be concise and specific.",
            max_tokens=600,
        )
    except Exception as e:
        return f"Session summary generation failed: {str(e)}"


# ---------------------------------------------------------------------------
# Escalation and resolution detection
# ---------------------------------------------------------------------------

def check_explicit_escalation(user_message: str) -> bool:
    msg = user_message.lower()
    return any(phrase in msg for phrase in ESCALATION_PHRASES)


def check_resolution_signal(user_message: str) -> bool:
    msg = user_message.lower()
    return any(phrase in msg for phrase in RESOLUTION_PHRASES)


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
