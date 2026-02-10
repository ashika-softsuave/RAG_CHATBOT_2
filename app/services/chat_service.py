import json
from app.core.llm import llm
from app.services.rag_service import rag_answer
from app.services.summarizer import summarize_chat
from app.services.query_rewrite import rewrite_query

SUMMARY_TRIGGER = 10


def analyze_intent(text: str, history: list[str], awaiting_followup: bool) -> dict:
    prompt = f"""
You are an intent classification engine.

Return ONLY valid JSON.

Conversation history:
{history}

User message:
"{text}"

Is the system awaiting a follow-up answer?
{awaiting_followup}

Return JSON ONLY:
{{
  "intent": "greeting | document_question | followup_answer | small_talk",
  "is_yes": true | false | null,
  "is_no": true | false | null
}}
"""
    response = llm.invoke(prompt).content.strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "intent": "document_question",
            "is_yes": None,
            "is_no": None
        }


def generate_followup(answer: str) -> str:
    prompt = f"""
You are SoftSuave's AI assistant.

Based on the answer below, ask ONE relevant follow-up question
strictly related to SoftSuave company documents.

Answer:
{answer}

Return ONLY the follow-up question.
"""
    return llm.invoke(prompt).content.strip()


def handle_chat(
    query: str,
    history: list[str],
    followup_answer: str | None = None,
    awaiting_followup: bool = False
) -> dict:

    history = history or []

    # ---------- 1. INTENT ANALYSIS ----------
    text_to_analyze = followup_answer if awaiting_followup else query
    intent = analyze_intent(text_to_analyze, history, awaiting_followup)

    # ---------- 2. GREETING / SMALL TALK ----------
    if intent["intent"] in {"greeting", "small_talk"}:
        reply = llm.invoke(
            f"You are SoftSuave's AI assistant. Respond politely to:\n{text_to_analyze}"
        ).content.strip()

        followup = generate_followup(reply)

        return {
            "reply": reply,
            "awaiting_followup": True,
            "followup_question": followup
        }

    # ---------- 3. FOLLOW-UP YES / NO ----------
    if intent["intent"] == "followup_answer":
        if intent["is_no"]:
            reply = llm.invoke(
                "User said no. Politely offer another SoftSuave document-related topic."
            ).content.strip()

            followup = generate_followup(reply)

            return {
                "reply": reply,
                "awaiting_followup": True,
                "followup_question": followup
            }

        if intent["is_yes"]:
            query = rewrite_query(query, history)

    # ---------- 4. SUMMARIZATION ----------
    if len(history) >= SUMMARY_TRIGGER * 2:
        summary = summarize_chat(history)
        history = summary

    # ---------- 5. QUERY NORMALIZATION ----------
    rewritten_query = rewrite_query(query, history)

    # ---------- 6. RAG ----------
    answer = rag_answer(rewritten_query, history)

    if not answer or len(answer.strip()) < 30:
        reply = llm.invoke(
            "Politely state the information is not available in SoftSuave documents."
        ).content.strip()

        followup = generate_followup(reply)

        return {
            "reply": reply,
            "awaiting_followup": True,
            "followup_question": followup
        }

    # ---------- 7. FINAL DOCUMENT ANSWER ----------
    final_answer = llm.invoke(
        f"""
You are SoftSuave's official AI assistant.
Answer ONLY using the document content below.

Document content:
{answer}
"""
    ).content.strip()

    followup = generate_followup(final_answer)

    return {
        "reply": final_answer,
        "awaiting_followup": True,
        "followup_question": followup
    }
