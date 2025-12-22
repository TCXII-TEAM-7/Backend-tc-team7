from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/kb", tags=["kb"])

PDF_DIR = Path("uploads/kb")  # dossier où sont déjà les PDF

@router.get("/documents")
def list_pdfs():
    files = []
    for path in PDF_DIR.glob("*.pdf"):
        files.append({
            "name": path.name,
            "url": f"/kb/documents/{path.name}/pdf"
        })
    return files