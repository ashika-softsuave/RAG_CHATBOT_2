import json
from app.core.llm import llm
from app.vectorstore.chroma_db import get_vectorstore
from app.services.reranker_service import rerank_documents

# LLM CALL 1 → CLASSIFICATION

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

DEFINITIONS:

greeting:
Simple hello/hi messages.

small_talk:
Casual conversation not related to SoftSuave documents.

new_question:
Any independent factual question.
Even if it is about the same topic,
if the user is asking a new question, classify as new_question.

followup_reply:
ONLY if the user is directly responding to the last follow-up question.
Examples:
- yes
- no
- proceed
- continue
- okay
- or providing clarification that was requested.

CRITICAL RULE:

If the message contains a new question,
it MUST be classified as new_question,
even if awaiting_followup is TRUE.

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

# LLM CALL 2 → QUERY REWRITE (NATURAL LANGUAGE FIX)
def rewrite_query_naturally(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_followup_question: str | None = None
) -> str:

    prompt = f"""
You are an advanced query rewriting engine for a RAG chatbot
that answers ONLY about the company SoftSuave.

Your job:
Rewrite the user's message into a clear, standalone,
retrieval-optimized question.

STRICT RULES:

1. Replace pronouns like:
   - "you"
   - "your"
   - "your company"
   - "it"
   with: "SoftSuave"

2. If the user message is short or vague (e.g. "About company",
   "Tell me more", "Details please"):
   → Expand it into a complete factual question.

3. If awaiting_followup is TRUE and the user confirms
   (e.g. "yes", "ok", "proceed", "continue"):
   → Return the last_followup_question exactly.
   → Do NOT rewrite.

4. If user asks something unrelated to SoftSuave company,
   still rewrite it clearly but DO NOT answer.

5. Do NOT answer the question.
6. Do NOT add explanations.
7. Return ONLY the rewritten standalone question.
8. No JSON. No formatting. Only the question text.

Conversation history:
{history}

Awaiting follow-up:
{awaiting_followup}

Last follow-up question:
"{last_followup_question}"

User message:
"{query}"
"""

    rewritten = llm.invoke(prompt).content.strip()

    # Safety fallback (LLM protection)
    if not rewritten or len(rewritten) < 5:
        return query

    return rewritten

# LLM CALL 3 → RAG + FOLLOWUP
def rag_with_followup(question: str, context: str):

    prompt = f"""
You are SoftSuave's official AI assistant.

STRICT RULES:
- Answer ONLY using provided document context.
- Do NOT use external knowledge.
- If answer not in context, respond EXACTLY:
  "The requested information is not available in SoftSuave documents."
  and DO NOT generate follow-up.

After every valid answer:
- Generate ONE follow-up question.
- Must come from SAME context.
- Must be answerable from SAME context.
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

# MAIN HANDLE_CHAT
def handle_chat(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_context: str | None = None,
    last_followup_question: str | None = None
):

    vectordb = get_vectorstore()

    # CLASSIFY
    message_type = classify_message(
        query,
        awaiting_followup,
        last_followup_question
    )
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

    # Rewrite naturally
    rewritten_query = rewrite_query_naturally(query, history)

    # Retrieve
    results = vectordb.similarity_search_with_score(rewritten_query, k=6)

    # Filter by threshold
    filtered_docs = [doc for doc, score in results if score < 0.5]

    #Rerank
    docs = rerank_documents(rewritten_query, filtered_docs, top_k=4)

    if not docs:
        return {
            "reply": "The requested information is not available in SoftSuave documents.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    context = "\n\n".join(d.page_content for d in docs)

    #Generate answer
    answer, followup = rag_with_followup(
        rewritten_query,
        context
    )

    return {
        "reply": f"{answer}\n\n{followup}" if followup else answer,
        "awaiting_followup": True if followup else False,
        "last_context": context,
        "last_followup_question": followup
    }
