from fastapi import APIRouter, UploadFile, Depends, HTTPException
import shutil, os

from app.auth.jwt_auth import get_current_user
from app.vectorstore.chroma_db import get_vectorstore
from app.utils.loaders import load_document
from app.core.config import UPLOAD_DIR, ADMIN_EMAIL

router = APIRouter(
    prefix="/admin/upload",
    tags=["Admin Upload"]
)

@router.post("/")
def upload_document(
    file: UploadFile,
    current_user: str = Depends(get_current_user)
):
    # ✅ ADMIN CHECK
    if current_user != ADMIN_EMAIL:
        raise HTTPException(
            status_code=403,
            detail="Only admin can upload documents"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = f"{UPLOAD_DIR}/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    docs = load_document(path)
    vectordb = get_vectorstore()
    vectordb.add_documents(docs)

    return {"status": "Document uploaded & indexed"}
