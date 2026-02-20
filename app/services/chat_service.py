import json
from app.core.llm import llm
from app.vectorstore.chroma_db import get_vectorstore
from app.services.reranker_service import rerank_documents

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

Your job is to determine the user's intent.

Classify the message into EXACTLY ONE of:

- greeting
- small_talk
- new_question
- followup_reply

INTENT DEFINITIONS:

greeting:
Simple hello/hi messages.

small_talk:
Casual conversation not related to SoftSuave documents.

new_question:
Any independent factual question.
Also classify as new_question if:
- The user rejects or declines the previous follow-up question.
- The user stops the follow-up flow.
- The user changes topic.
- The user does not clearly continue the follow-up.

followup_reply:
ONLY if:
- The system is awaiting a follow-up AND
- The user is clearly continuing or confirming the previous follow-up question OR
- The user provides clarification requested in the previous follow-up.

CRITICAL RULES:

- If the user declines the previous follow-up question,
  DO NOT classify as followup_reply.
- If the user clearly stops the follow-up flow,
  classify as new_question.
- Only classify as followup_reply when the user is actively continuing the same follow-up branch.
- Be conservative when choosing followup_reply.

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
def rewrite_query_naturally(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_followup_question: str | None = None
) -> str:

    normalized_query = query.strip().lower()

    # Follow-up confirmation
    if awaiting_followup and last_followup_question:
        if normalized_query in ["yes", "ok", "okay", "proceed", "continue", "go ahead"]:
            return last_followup_question

    prompt = f"""
You are an advanced query rewriting engine for a RAG chatbot
that answers ONLY about SoftSuave using internal documents.

Your job:
Rewrite the user's message into a clear, standalone,
retrieval-optimized factual question.

IMPORTANT BEHAVIOR:

- If the user asks what documents, information, or data are available,
  rewrite it as:
  "Provide a comprehensive overview of SoftSuave based on the available documents."

- If the user message is vague or incomplete,
  intelligently expand it into a meaningful factual question.

- Replace pronouns like "you", "your", "it" with "SoftSuave".

- Do NOT answer.
- Return ONLY the rewritten question text.

Conversation history:
{history}

User message:
"{query}"
"""

    rewritten = llm.invoke(prompt).content.strip()

    if not rewritten or len(rewritten) < 5:
        return query

    return rewritten

# LLM CALL 3 → RAG + FOLLOWUP
def rag_with_followup(
        question: str,
        context: str,
        history: list[str] | None = None
):
    # Only keep last few turns (memory control)
    short_history = ""
    if history:
        short_history = "\n".join(history[-6:])  # last 3 user+assistant turns

    prompt = f"""
    You are SoftSuave's official AI assistant.

    STRICT RULES:
    - Answer ONLY using the provided Context.
    - Do NOT use external knowledge.
    - If the answer can be reasonably inferred from the Context,
      provide a concise and accurate answer strictly based on it.
    - Only respond EXACTLY:
      "The requested information is not available ."
      if the Context truly does not contain relevant information.

    FOLLOW-UP RULES:
    - Follow-up question is OPTIONAL.
    - Generate at most ONE follow-up question.
    -The follow-up must be answerable from the broader document,
  even if not fully contained in the current Context..
    - Do NOT generate a follow-up if the Context does not clearly support it.
    - Do NOT generate speculative or broad follow-up questions.
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
    except Exception as e:
        print("LLM Error:", e)
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
            answer = response
    else:
        answer = response

    return answer, followup

#MAIN HANDLE_CHAT
def handle_chat(
    query: str,
    history: list[str],
    awaiting_followup: bool = False,
    last_context: str | None = None,
    last_followup_question: str | None = None
):
    docs = []
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
            "reply": "Hello 👋 How can I assist you regarding SoftSuave today?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }
    # SMALL TALK
    if message_type == "small_talk":
        return {
            "reply": "I'm here to assist you with information about SoftSuave. What would you like to know?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    # FOLLOW-UP REPLY
    if message_type == "followup_reply" and awaiting_followup:

        if not last_context or not last_followup_question:
            return {
                "reply": "The requested information is not available",
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

    if not results:
        return {
            "reply": "No documents found in the knowledge base. Please upload documents.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    filtered_docs = [doc for doc, score in results]

    if not filtered_docs:
        return {
            "reply": "No relevant information found.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    docs = rerank_documents(rewritten_query, filtered_docs, top_k=3)

    if not docs:
        return {
            "reply": "The requested information is not available.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    print("Number of results retrieved:", len(results))

    for i, (doc, score) in enumerate(results):
        print(f"Result {i} length:", len(doc.page_content))
    # Filter by threshold
    filtered_docs = list({doc.page_content: doc for doc in filtered_docs}.values())

    context = "\n\n".join(d.page_content for d in docs)

    #Generate answer
    answer, followup = rag_with_followup(
        rewritten_query,
        context,
        history
    )

    print(rewritten_query)
    # Clean followup safely
    if followup:
        cleaned_followup = followup.strip()

        # Remove accidental "None" text
        if cleaned_followup.lower() in ["none", "null", ""]:
            cleaned_followup = None
    else:
        cleaned_followup = None

    # Build reply safely
    reply_text = answer.strip()

    if cleaned_followup:
        reply_text = f"{reply_text}\n\n{cleaned_followup}"

    return {
        "reply": reply_text,
        "awaiting_followup": bool(cleaned_followup),
        "last_context": context if cleaned_followup else None,
        "last_followup_question": cleaned_followup
    }