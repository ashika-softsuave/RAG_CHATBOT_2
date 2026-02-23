import json
from app.core.llm import llm
from app.vectorstore.chroma_db import get_vectorstore
from app.services.reranker_service import rerank_documents

# INTENT CLASSIFICATION
def classify_message(
    query: str,
    awaiting_followup: bool,
    last_followup_question: str | None
) -> str:

    prompt = f"""
You are a strict intent classification engine for a RAG chatbot.

User message:
"{query}"

System awaiting_followup:
{awaiting_followup}

Last follow-up question:
"{last_followup_question}"

Classify the message into EXACTLY ONE of:

- greeting
- small_talk
- new_question
- followup_reply

Rules:
- If awaiting_followup is TRUE and the user clearly says yes/continue/proceed,
  classify as followup_reply.
- If awaiting_followup is TRUE and the user says no/skip/not interested,
  classify as new_question.
- Be conservative.

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



# QUERY REWRITE
def rewrite_query_naturally(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_followup_question: str | None = None
) -> str:

    normalized_query = query.strip().lower()

    if awaiting_followup and last_followup_question:
        if normalized_query in ["yes", "ok", "okay", "proceed", "continue", "go ahead"]:
            return last_followup_question

    prompt = f"""
Rewrite the user's message into a clear standalone factual question
about SoftSuave.

Do NOT answer.

Conversation history:
{history}

User message:
"{query}"
"""

    try:
        rewritten = llm.invoke(prompt).content.strip()
        return rewritten if rewritten else query
    except:
        return query

# RAG ANSWER + FOLLOWUP
def rag_with_followup(
        question: str,
        context: str,
        history: list[str] | None = None
):

    short_history = ""
    if history:
        short_history = "\n".join(history[-6:])

    prompt = f"""
You are SoftSuave's official AI assistant.

STRICT RULES:
- Answer ONLY using the provided Context.
- If answer not in Context, respond EXACTLY:
  "The requested information is not available."

FOLLOW-UP RULES:
- Generate at most ONE follow-up question.
- The follow-up must relate to another section of the document.
- If no suitable follow-up exists, return FOLLOWUP: None.

Recent Conversation:
{short_history}

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

    try:
        response = llm.invoke(prompt).content.strip()
    except:
        return "The requested information is not available.", None

    answer = None
    followup = None

    if "ANSWER:" in response and "FOLLOWUP:" in response:
        try:
            answer = response.split("ANSWER:")[1].split("FOLLOWUP:")[0].strip()
            followup = response.split("FOLLOWUP:")[1].strip()
            if followup.lower() in ["none", "null", ""]:
                followup = None
        except:
            answer = response.strip()
    else:
        answer = response.strip()

    return answer, followup

#SECTION VALIDATION

def section_exists(vectordb, followup_text):
    all_data = vectordb.get(include=["metadatas"])
    sections = set()

    for meta in all_data["metadatas"]:
        section = meta.get("section")
        if section:
            sections.add(section.lower())

    followup_text = followup_text.lower()

    for section in sections:
        if any(word in section for word in followup_text.split()):
            return True

    return False

def is_repeated_followup(followup_text, history):
    if not followup_text:
        return False

    followup_text = followup_text.strip().lower()

    for msg in history:
        if followup_text in msg.lower():
            return True

    return False

# MAIN HANDLE_CHAT
def handle_chat(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_context: str | None = None,
    last_followup_question: str | None = None
):

    vectordb = get_vectorstore()

    message_type = classify_message(
        query,
        awaiting_followup,
        last_followup_question
    )

    # GREETING
    if message_type == "greeting":
        return {
            "reply": "Hello 👋 How can I assist you regarding SoftSuave today?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    #SMALL TALK
    if message_type == "small_talk":
        return {
            "reply": "I'm here to assist you with information about SoftSuave. What would you like to know?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    # FOLLOW-UP FLOW
    if awaiting_followup:

        if message_type == "followup_reply":

            followup_query = last_followup_question

            results = vectordb.similarity_search_with_score(followup_query, k=6)
            retrieved_docs = [doc for doc, score in results]

            if not retrieved_docs:
                return {
                    "reply": "The requested information is not available.",
                    "awaiting_followup": False,
                    "last_context": None,
                    "last_followup_question": None
                }

            retrieved_docs = list({doc.page_content: doc for doc in retrieved_docs}.values())
            docs = rerank_documents(followup_query, retrieved_docs, top_k=3)

            if not docs:
                return {
                    "reply": "The requested information is not available.",
                    "awaiting_followup": False,
                    "last_context": None,
                    "last_followup_question": None
                }

            context = "\n\n".join(d.page_content for d in docs)

            answer, followup = rag_with_followup(
                followup_query,
                context,
                history
            )

        else:
            return {
                "reply": "Alright 👍 Would you like to explore another section of the Employee Handbook?",
                "awaiting_followup": False,
                "last_context": None,
                "last_followup_question": None
            }


    # NEW QUESTION FLOW
    else:
        rewritten_query = rewrite_query_naturally(query, history)

        results = vectordb.similarity_search_with_score(rewritten_query, k=8)

        if not results:
            return {
                "reply": "The requested information is not available.",
                "awaiting_followup": False,
                "last_context": None,
                "last_followup_question": None
            }

        retrieved_docs = [doc for doc, score in results]
        retrieved_docs = list({doc.page_content: doc for doc in retrieved_docs}.values())
        docs = rerank_documents(rewritten_query, retrieved_docs, top_k=3)

        if not docs:
            return {
                "reply": "The requested information is not available.",
                "awaiting_followup": False,
                "last_context": None,
                "last_followup_question": None
            }

        context = "\n\n".join(d.page_content for d in docs)

        answer, followup = rag_with_followup(
            rewritten_query,
            context,
            history
        )

    # FOLLOW-UP VALIDATION LAYER
    validated_followup = None

    if followup:
        followup = followup.strip()

        # Section must exist
        if section_exists(vectordb, followup):

            # Must NOT be repeated
            if not is_repeated_followup(followup, history):
                validated_followup = followup

    reply_text = answer.strip()

    if validated_followup:
        reply_text += f"\n\n{validated_followup}"

    return {
        "reply": reply_text,
        "awaiting_followup": bool(validated_followup),
        "last_context": context if validated_followup else None,
        "last_followup_question": validated_followup
    }
