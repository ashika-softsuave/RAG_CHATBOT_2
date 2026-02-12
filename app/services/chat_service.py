import json
from app.core.llm import llm
from app.vectorstore.chroma_db import get_vectorstore

# LLM CALL 1 → ROUTER (ONLY CLASSIFICATION)

def classify_message(query: str, awaiting_followup: bool) -> str:
    prompt = f"""
You are a classification engine.

User message:
"{query}"

System awaiting follow-up:
{awaiting_followup}

Classify this message into ONE of:

- greeting
- small_talk
- new_question
- followup_reply

Rules:
- greeting → simple hello/hi
- small_talk → casual conversation not about documents
- followup_reply → response to previous follow-up when system is awaiting one
- new_question → asking new information about SoftSuave

Return STRICT JSON:

{{
  "type": "greeting | small_talk | new_question | followup_reply"
}}
"""

    try:
        response = llm.invoke(prompt).content.strip()
        return json.loads(response)["type"]
    except:
        return "new_question"

# LLM CALL 2 → RAG + FOLLOWUP
def rag_with_followup(question: str, context: str):

    prompt = f"""
You are SoftSuave's official AI assistant.

STRICT RULES:
- Answer ONLY using the provided document context.
- Do NOT use external knowledge.
- Do NOT guess.
- If answer is not explicitly in context, respond EXACTLY:
  "The requested information is not available in SoftSuave documents."
  and DO NOT generate follow-up.

After every valid answer:
- Generate ONE follow-up question.
- It must come strictly from the SAME context.
- It must be answerable from the SAME context.
- Do NOT introduce new topics.

Context:
{context}

Question:
{question}

Return EXACT format:

ANSWER:
<answer>

FOLLOWUP:
<question or None>
"""

    response = llm.invoke(prompt).content.strip()

    answer = None
    followup = None

    if "ANSWER:" in response:
        part = response.split("ANSWER:")[1]
        if "FOLLOWUP:" in part:
            answer = part.split("FOLLOWUP:")[0].strip()
            followup = part.split("FOLLOWUP:")[1].strip()
            if followup.lower() in ["none", "null", ""]:
                followup = None
        else:
            answer = part.strip()
    else:
        answer = response

    return answer, followup

# MAIN HANDLE_CHAT (STABLE)
def handle_chat(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_context: str | None = None,
    last_followup_question: str | None = None
):

    vectordb = get_vectorstore()

    # ROUTER
    message_type = classify_message(query, awaiting_followup)

    # GREETING
    if message_type == "greeting":
        return {
            "reply": "Hello 👋 How can I assist you regarding SoftSuave documents today?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    # SMALL TALK
    if message_type == "small_talk":
        return {
            "reply": "I'm here to assist you with information about SoftSuave documents. What would you like to know?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    # FOLLOW-UP REPLY
    if message_type == "followup_reply" and awaiting_followup:

        if not last_context or not last_followup_question:
            return {
                "reply": "The requested information is not available in SoftSuave documents.",
                "awaiting_followup": False,
                "last_context": None,
                "last_followup_question": None
            }

        answer, followup = rag_with_followup(
            last_followup_question,
            last_context
        )

        return {
            "reply": f"{answer}\n\n{followup}" if followup else answer,
            "awaiting_followup": True if followup else False,
            "last_context": last_context,
            "last_followup_question": followup
        }

    # NEW QUESTION
    docs = vectordb.similarity_search(query, k=3)

    if not docs:
        return {
            "reply": "The requested information is not available in SoftSuave documents.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    context = "\n\n".join(d.page_content for d in docs)

    answer, followup = rag_with_followup(query, context)
    print("DEBUG:", awaiting_followup, last_followup_question is not None)

    return {
        "reply": f"{answer}\n\n{followup}" if followup else answer,
        "awaiting_followup": True if followup else False,
        "last_context": context,
        "last_followup_question": followup
    }



