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
    except:
        return {
            "intent": "document_question",
            "is_yes": None,
            "is_no": None
        }


def generate_followup(answer: str) -> str:
    prompt = f"""
You are SoftSuave's AI assistant.

Based on the answer below,
generate ONE meaningful follow-up question
strictly related to SoftSuave company documents.

Answer:
{answer}

Return ONLY the question.
"""
    return llm.invoke(prompt).content.strip()


def handle_chat(
    query: str,
    history: list[str],
    followup_answer: str | None = None,
    awaiting_followup: bool = False
) -> dict:

    history = history or []

    #AUTO SUMMARY EVERY 10 USER TURNS
    user_turns = len([h for h in history if h.startswith("User:")])
    if user_turns and user_turns % SUMMARY_TRIGGER == 0:
        history = summarize_chat(history)

    # INTENT ANALYSIS
    text_to_analyze = followup_answer if awaiting_followup else query
    intent = analyze_intent(text_to_analyze, history, awaiting_followup)

    # FOLLOW-UP HANDLING
    if awaiting_followup and intent["intent"] == "followup_answer":

        if intent["is_no"]:
            reply = llm.invoke(
                "User declined the previous follow-up. Offer another related SoftSuave document topic."
            ).content.strip()

        elif intent["is_yes"]:
            reply = llm.invoke(
                "User accepted the previous follow-up. Continue the explanation in more detail using SoftSuave documents."
            ).content.strip()

        else:
            reply = llm.invoke(
                "Clarify the user's response politely within SoftSuave document context."
            ).content.strip()

        followup = generate_followup(reply)

        return {
            "reply": f"{reply}\n\n{followup}",
            "awaiting_followup": True
        }

    # GREETING / SMALL TALK
    if intent["intent"] in {"greeting", "small_talk"}:

        reply = llm.invoke(
            f"You are SoftSuave's AI assistant. Respond politely:\n{text_to_analyze}"
        ).content.strip()

        followup = generate_followup(reply)

        return {
            "reply": f"{reply}\n\n {followup}",
            "awaiting_followup": True
        }

    #  QUERY NORMALIZATION
    rewritten_query = rewrite_query(query, history)

    # RAG
    answer = rag_answer(rewritten_query, history)

    if not answer or len(answer.strip()) < 30:

        reply = llm.invoke(
            "Politely state that the requested information is not available in SoftSuave company documents."
        ).content.strip()

        followup = generate_followup(reply)

        return {
            "reply": f"{reply}\n\n {followup}",
            "awaiting_followup": True
        }

    #FINAL DOCUMENT RESPONSE
    final_answer = llm.invoke(
        f"""
You are SoftSuave's official AI assistant.

Answer ONLY using the document content below.
Do NOT add external knowledge.

Document content:
{answer}
"""
    ).content.strip()

    followup = generate_followup(final_answer)

    return {
        "reply": f"{final_answer}\n\n {followup}",
        "awaiting_followup": True
    }
