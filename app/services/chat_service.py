import json
from app.core.llm import llm
from app.vectorstore.chroma_db import get_vectorstore


def unified_reasoning(query: str, history: list[str], awaiting_followup: bool):
    
    # RULE-BASED OVERRIDE for Follow-up
    if awaiting_followup:
        normalized = query.lower().strip().strip(".,!?")
        yes_variants = {"yes", "sure", "ok", "okay", "proceed", "go ahead", "continue", "tell me more", "please", "yes please", "yep", "yeah"}
        no_variants = {"no", "no thanks", "stop", "cancel", "nope", "nah"}
        
        if normalized in yes_variants:
            return {
                "intent": "followup_answer",
                "is_yes": True,
                "is_no": False,
                "rewritten_query": None
            }
        
        if normalized in no_variants:
            return {
                "intent": "followup_answer",
                "is_yes": False,
                "is_no": True,
                "rewritten_query": None
            }

    prompt = f"""
You are SoftSuave's reasoning engine.

Tasks:
1. ANALYSIS PRIORITY:
   - Check 'Awaiting Followup' state FIRST.
   - If True:
     - User input "Yes", "Yes, please", "Sure", "Proceed", "Okay", "Tell me more", "Please" -> intent: "followup_answer", is_yes: true
     - User input "No", "No thanks", "Stop", "Cancel" -> intent: "followup_answer", is_no: true
     - Only if input is clearly a NEW topic -> intent: "document_question"
   
2. If 'Awaiting Followup' is False:
   - "Hi", "Hello" -> intent: "greeting"
   - Question about company -> intent: "document_question"

3. Rewrite query:
   - If intent is "document_question", rewrite to be self-contained.
   - Otherwise, return null.

Return STRICT JSON only:
{{
  "intent": "greeting" | "small_talk" | "document_question" | "followup_answer",
  "is_yes": true | false | null,
  "is_no": true | false | null,
  "rewritten_query": "string" | null
}}

Conversation:
{history}

Current State:
Awaiting Followup: {awaiting_followup}

User message:
"{query}"
"""

    try:
        response = llm.invoke(prompt).content.strip()
        # Clean up JSON if it contains markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
            
        return json.loads(response)
    except Exception as e:
        print(f"JSON Parsing Error: {e}, Response: {response if 'response' in locals() else 'None'}")
        return {
            "intent": "document_question",
            "is_yes": None,
            "is_no": None,
            "rewritten_query": query
        }

def rag_with_followup(query: str, context: str):

    prompt = f"""
You are SoftSuave's official AI assistant.

Rules:
- Answer ONLY using the provided context.
- After answering, choose ONE sentence from the SAME context.
- Convert THAT sentence into a follow-up question.
- The follow-up MUST be answerable using the SAME context.
- Do NOT introduce new topics.
- Do NOT move to another document section.
- If answer is not found, say:
  "The requested information is not available in SoftSuave documents."
  and DO NOT generate follow-up.

Context:
{context}

Question:
{query}

Return EXACT format:

ANSWER:
<answer>

FOLLOWUP:
<question derived directly from a sentence in context>
"""
    return llm.invoke(prompt).content.strip()



def handle_chat(
    query: str,
    history: list[str],
    followup_answer: str | None = None,
    awaiting_followup: bool = False,
    last_context: str | None = None,
    last_followup_question: str | None = None
) -> dict:

    history = history or []

    if awaiting_followup and not followup_answer:
        followup_answer = query

    reasoning = unified_reasoning(
        followup_answer if awaiting_followup else query,
        history,
        awaiting_followup
    )

    intent = reasoning["intent"]

    # ---------------- GREETING ----------------
    if intent in {"greeting", "small_talk"}:
        return {
            "reply": "Hello! How can I assist you regarding SoftSuave documents today?",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    # ---------------- FOLLOW-UP YES / NO ----------------
    if intent == "followup_answer" and awaiting_followup:

        # YES → reuse SAME question + SAME context
        if reasoning["is_yes"] and last_context and last_followup_question:
            prompt = f"""
        You are SoftSuave's official AI assistant.

        Continue answering the following question
        STRICTLY using the SAME context.

        Do NOT retrieve new topics.
        Do NOT switch document sections.

        Context:
        {last_context}

        Question:
        {last_followup_question}

        Return format:

        ANSWER:
        <expanded answer>

        FOLLOWUP:
        <next question within same topic>
        """

            rag_output = llm.invoke(prompt).content.strip()
            
            try:
                answer = rag_output.split("FOLLOWUP:")[0].replace("ANSWER:", "").strip()
                followup = rag_output.split("FOLLOWUP:")[1].strip()
            except:
                answer = rag_output
                followup = None

            return {
                "reply": f"{answer}\n\n{followup}" if followup else answer,
                "awaiting_followup": True if followup else False,
                "last_context": last_context,
                "last_followup_question": followup
            }

        # NO → exit followup mode
        if reasoning["is_no"]:
            return {
                "reply": "Alright 👍 What would you like to explore about SoftSuave?",
                "awaiting_followup": False,
                "last_context": None,
                "last_followup_question": None
            }

    # ---------------- NEW DOCUMENT QUESTION ----------------

    rewritten_query = reasoning["rewritten_query"]

    vectordb = get_vectorstore()
    docs = vectordb.similarity_search(rewritten_query, k=3)

    if not docs:
        return {
            "reply": "The requested information is not available in SoftSuave documents.",
            "awaiting_followup": False,
            "last_context": None,
            "last_followup_question": None
        }

    context = "\n\n".join(d.page_content for d in docs)

    rag_output = rag_with_followup(rewritten_query, context)

    try:
        answer = rag_output.split("FOLLOWUP:")[0].replace("ANSWER:", "").strip()
        followup = rag_output.split("FOLLOWUP:")[1].strip()
    except:
        answer = rag_output
        followup = None

    return {
        "reply": f"{answer}\n\n{followup}" if followup else answer,
        "awaiting_followup": True if followup else False,
        "last_context": context,
        "last_followup_question": followup
    }
