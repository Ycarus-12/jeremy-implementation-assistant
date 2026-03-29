# api.py v3
# Anthropic API calls, topic-aware escalation, summary generation.
# v3: topic-aware escalation tracking, rephrased handoff fields,
#     scope dismissal never sets escalation flag.

import os
import httpx
from datetime import datetime

API_URL = "https://api.anthropic.com/v1/messages"
MODEL   = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Phrase lists
# ---------------------------------------------------------------------------
ESCALATION_PHRASES = [
    "i want to escalate",
    "please escalate",
    "escalate this",
    "escalate to meredith",
    "escalate to the ps",
    "i'd like to escalate",
    "i would like to escalate",
    "can you escalate",
    "let's escalate",
    "talk to someone",
    "speak to someone",
    "speak with meredith",
    "contact meredith",
    "reach meredith",
    "call meredith",
    "get meredith involved",
    "loop in meredith",
    "need a human",
    "need a person",
    "want to speak with",
    "want to talk to",
    "can someone help me",
    "i want to talk to someone",
]

RESOLUTION_PHRASES = [
    "got it", "that works", "that helped", "makes sense",
    "i understand", "i see", "thank you", "thanks", "perfect",
    "that's what i needed", "all set", "i'm good", "solved",
    "figured it out", "i'll try that", "makes sense now",
    "move on", "let's move on", "next question", "never mind",
    "forget it", "not important",
]

SESSION_END_PHRASES = [
    "end this session",
    "end the session",
    "close this session",
    "close out the session",
    "wrap up the session",
    "wrap up this session",
    "finish the session",
    "conclude the session",
    "let's end the session",
    "let's close the session",
    "let's wrap up the session",
    "let's go ahead and end",
    "go ahead and end the session",
    "we can end the session",
    "end our session",
    "i'm ready to end",
    "done for today, end",
    "let's stop the session",
]

SCOPE_SIGNALS = [
    "can we add to scope",
    "add to the scope",
    "add to scope",
    "is that in scope",
    "is this in scope",
    "out of scope",
    "not in scope",
    "expand the scope",
    "scope change",
    "scope question",
    "what about hpc",
    "hpc integration",
    "what about hipaa",
    "hipaa compliant",
    "package mirror",
    "private mirror",
    "posit workbench",
    "posit connect",
    "data warehouse integration",
    "on-premises",
    "on-prem integration",
    "hybrid setup",
    "can we include",
    "what about adding",
]

# Signals that assistant couldn't answer — tightened to avoid false positives
# on normal source-citation language like "per your PS lead"
UNRESOLVED_SIGNALS = [
    "i don't have that information available",
    "i don't have sufficient information",
    "i can't answer that",
    "outside my knowledge boundaries",
    "not in my knowledge base",
    "i don't have enough information",
    "i'm unable to answer",
    "that's not something i can answer",
]


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")
    return key


def call_claude(messages: list, system_prompt: str, max_tokens: int = 1000) -> str:
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
        resp = httpx.post(API_URL, headers=headers, json=body, timeout=60.0)
        resp.raise_for_status()
        data = resp.json()
        blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        if not blocks:
            raise ValueError("No text content returned by API.")
        return "\n".join(blocks)
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("error", {}).get("message", str(e))
        except Exception:
            detail = str(e)
        raise RuntimeError(f"Anthropic API error: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"API request failed: {str(e)}") from e


# ---------------------------------------------------------------------------
# Handoff summary — rephrased fields
# "Customer was trying to:" → "Goal:"
# "What was discussed:" → "What was being discussed:"
# ---------------------------------------------------------------------------
def generate_handoff_summary(messages: list, customer_name: str, customer_role: str) -> str:
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

Goal: [one sentence describing what the customer was trying to accomplish]
What was being discussed: [2-3 sentences max]
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
    try:
        transcript = "\n\n".join(
            f"{'CUSTOMER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
            for m in messages
        )
        session_end    = datetime.now().strftime("%Y-%m-%d %H:%M")
        escalated_str  = "Yes" if escalated else "No"

        unresolved_str = ""
        if unresolved_log:
            unresolved_str = "\n\nUNRESOLVED QUESTIONS THIS SESSION:\n" + "\n".join(
                f"- {q}" for q in unresolved_log
            )

        feedback_str = ""
        if feedback_log:
            helpful     = sum(1 for f in feedback_log if f["helpful"])
            not_helpful = sum(1 for f in feedback_log if not f["helpful"])
            feedback_str = f"\n\nRESPONSE FEEDBACK: {helpful} helpful, {not_helpful} not helpful"

        from knowledge_base import TOPIC_TAGS
        tags_list = ", ".join(TOPIC_TAGS)

        prompt = f"""You are generating a PS-facing session summary for a Posit Cloud implementation assistant.
This summary is for Meredith Callahan (PS Lead), NOT the customer.
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

FOLLOW_UP_INDICATORS: [Specific signals PS should act on proactively. Be specific. If none, write "None identified."]
DATE_TIME: {session_start} — {session_end}
CUSTOMER: {customer_name or 'Not provided'} | {customer_role or 'Not specified'}
OUTCOME: [Resolved / Partially Resolved / Escalated]
TOPIC_TAGS: [Select all that apply from: {tags_list}]
TOPICS_COVERED: [Comma-separated list]
GUIDANCE_PROVIDED: [2-4 sentences summarizing key guidance shared]
ESCALATION_SUMMARY: [Full handoff summary if escalated; otherwise N/A]
UNRESOLVED_QUESTIONS: [List questions the assistant could not answer; otherwise None]
RESPONSE_FEEDBACK: [Summary of helpful/not-helpful feedback if any; otherwise None]

Keep under 400 words. No preamble or closing remarks."""

        return call_claude(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You generate factual, structured session summaries for a PS team.",
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
    msg = user_message.lower()
    return any(phrase in msg for phrase in SESSION_END_PHRASES)


def check_scope_question(user_message: str) -> bool:
    msg = user_message.lower()
    return any(phrase in msg for phrase in SCOPE_SIGNALS)


def check_unresolved_response(assistant_message: str) -> bool:
    msg = assistant_message.lower()
    return any(phrase in msg for phrase in UNRESOLVED_SIGNALS)


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


# ---------------------------------------------------------------------------
# Topic-aware escalation tracker
#
# Tracks consecutive unresolved exchanges PER TOPIC (derived from the last
# user question). Resets when the user signals resolution or changes topic.
# Never fires on scope dismissal — that is handled separately in app.py.
# ---------------------------------------------------------------------------

class TopicEscalationTracker:
    """
    Tracks how many consecutive exchanges on the same topic have not resolved.
    Escalation is SUGGESTED (not triggered) when count reaches 3 AND the assistant
    signals it couldn't help. The app prompts the user; only user confirmation
    sets escalated=True.

    Deliberately conservative:
    - Topic similarity threshold is high (60% word overlap) to avoid false matches
    - Count must reach 3 full exchanges, not 2
    - Assistant must explicitly signal it can't help (not just cite a PS contact)
    """

    def __init__(self):
        self.current_topic: str = ""
        self.count: int = 0

    def update(self, user_message: str, assistant_response: str) -> bool:
        msg = user_message.lower().strip()

        # Resolution signal resets
        if check_resolution_signal(user_message):
            self.count = 0
            self.current_topic = ""
            return False

        topic_key = msg[:80]

        if self._same_topic(topic_key):
            self.count += 1
        else:
            # New topic — reset to 1
            self.current_topic = topic_key
            self.count = 1

        # Only suggest escalation after 3+ exchanges on same topic
        # AND assistant explicitly couldn't help (not just routine PS referral)
        if self.count >= 3 and check_unresolved_response(assistant_response):
            return True

        return False

    def _same_topic(self, topic_key: str) -> bool:
        """Returns True only if there is strong word overlap with current topic."""
        if not self.current_topic:
            return False
        a = set(self.current_topic.split())
        b = set(topic_key.split())
        if not a or not b:
            return False
        # Raised from 0.35 to 0.6 to avoid false topic matches
        overlap = len(a & b) / max(len(a), len(b))
        return overlap >= 0.60

    def reset(self):
        self.current_topic = ""
        self.count = 0
