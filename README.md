
# 📘 SoftSuave AI Assistant –  RAG Chatbot

## 🚀 Overview

SoftSuave AI Assistant is a **Section-Aware Retrieval-Augmented Generation (RAG) Chatbot** designed to intelligently answer questions from structured company documents like an Employee Handbook.

Unlike basic document chatbots, this system:

- Uses **section-aware chunking**
- Validates follow-up questions
- Prevents repeated follow-ups
- Handles structured yes/no conversational flow
- Retrieves precise answers from relevant document sections only

We implemented a Section-Aware RAG pipeline where documents are chunked using regex-based section detection combined with recursive semantic splitting. Chunks are embedded using OpenAI embeddings and stored in ChromaDB. On query, we retrieve top candidates via similarity search, rerank them using a cross-encoder model, and pass the refined context to the LLM for grounded answer generation with validated follow-up control.

---

## 🧠 Architecture Overview

```
User Question
     ↓
Intent Classification
     ↓
Query Rewriting
     ↓
Vector Search (Chroma)
     ↓
Re-ranking
     ↓
LLM Answer Generation
     ↓
Follow-up Validation
     ↓
Response
```

---

## 🛠 Tech Stack

- **Backend**: FastAPI
- **Vector Database**: ChromaDB
- **Embeddings**: OpenAI Embeddings
- **LLM**: GPT (via LangChain)
- **Document Processing**: Section-based + Hybrid Chunking
- **Frontend**: HTML, CSS, JS (Chat UI)

---

## 🔥 Key Features

### ✅ 1. Section-Aware Chunking

- Splits document by headings (e.g., `1.1 OUR VALUES`)
- Combines header + content
- Applies secondary semantic splitting for large sections
- Ensures small sections (like Mission – 3 lines) are retrievable

---

### ✅ 2. Retrieval-Augmented Generation (RAG)

- Uses vector similarity search
- Re-ranks top results
- LLM answers strictly from retrieved context

---

### ✅ 3. Intelligent Follow-up System

- Generates at most one follow-up question
- Validates if section exists in metadata
- Prevents repeated follow-up questions
- Handles **YES / NO** conversational flow

---

### ✅ 4. Intent Classification Layer

Classifies messages into:

- Greeting
- Small Talk
- New Question
- Follow-up Reply

This prevents accidental follow-up triggering.

---

### ✅ 5. Repeat Follow-up Prevention

System checks conversation history and blocks previously asked follow-up questions.

---

## 📂 Project Structure

```
app/
 ├── api/
 │    └── routes/
 ├── services/
 │    ├── chat_service.py
 │    ├── reranker_service.py
 ├── vectorstore/
 │    └── chroma_db.py
 ├── core/
 │    └── llm.py
 ├── templates/
 ├── static/
 └── main.py
```

---

## ⚙️ How It Works

### 1️⃣ Document Upload

Admin uploads Employee Handbook PDF.

### 2️⃣ Section-Based Chunking

Document is split into:

- Section heading
- Section content
- Hybrid semantic chunks if large

Each chunk stores:

```
{
  "section":"1.3 OUR MISSION",
  "source":"handbook"
}
```

---

### 3️⃣ Embedding & Storage

Chunks are embedded using OpenAI embeddings and stored in ChromaDB.

---

### 4️⃣ User Interaction Flow

- User asks question
- Query rewritten for retrieval optimization
- Similarity search performed
- Top chunks re-ranked
- LLM generates answer from context only
- Optional follow-up validated
- Response returned

---

# 🔧 Technical Implementation Details

## 📌 1. Chunking Strategy

We implemented a **Hybrid Section-Aware Chunking** approach using:

- `re.split()` (Regex-based section detection)
- `RecursiveCharacterTextSplitter` from LangChain

Small sections (e.g., Mission – 3 lines) remain intact.

Large sections are semantically split into 800-token chunks with overlap.

---

## 📌 2. Embedding Model

We used:

- `OpenAIEmbeddings`
- Model: `text-embedding-3-small` (or equivalent)

Each chunk is converted into a dense vector representation and stored in ChromaDB.

---

## 📌 3. Vector Database

We used:

- `Chroma` (langchain_chroma)
- Persistent storage via `persist_directory`

Key functions:

- `add_documents()`
- `similarity_search_with_score()`

---

## 📌 4. Reranking Model

We applied cross-encoder-based reranking using:

- Sentence Transformers CrossEncoder
- Example model: `cross-encoder/ms-marco-MiniLM-L-6-v2`

This improves retrieval precision before passing context to the LLM.

---

## 📌 5. LLM

We used:

- OpenAI Chat Model (via LangChain)
- Controlled prompt engineering
- Strict context-only answering

## 🎯 Why This Project is Advanced

This is not a basic chatbot.

It includes:

- Section-aware retrieval
- Metadata validation
- Controlled follow-up logic
- Context re-retrieval for follow-up answers
- Hybrid chunking strategy
- Repeat prevention logic
- Structured conversational control

---

## 🧪 Example Flow

**User:** What awards does SoftSuave offer?

**Bot:** Long Service Award...

**Bot:** What benefits do employees receive after completing service?

**User:** Yes

**Bot:** (Retrieves benefits section and answers)

System prevents:

- Repeated follow-ups
- Invalid sections
- Hallucinated answers

---

## 📌 Setup Instructions

### 1️⃣ Clone Repository

```
git clone <repo-url>
cd project-folder
```

### 2️⃣ Install Dependencies

```
pip install-r requirements.txt
```

### 3️⃣ Add Environment Variables

Create `.env` file:

```
OPENAI_API_KEY=your_key_here
```

---

### 4️⃣ Run Backend

```
uvicorn app.main:app--reload
```

Open:

```
http://127.0.0.1:8000/chat
```

---

## 🧹 Reset Vector Database (If Chunking Changes)

If chunking logic changes:

Delete Chroma directory:

```
Remove-Item-Recurse-Forcedata\chroma
```

Then re-upload documents.
