from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from generate_pdf import generate_pdf  # Tu importes ta fonction ici
from io import BytesIO

router = APIRouter()

@router.post("/creer-pdf")
async def creer_pdf(request: Request):
    data = await request.json()
    pdf_stream: BytesIO = generate_pdf(data)

    return StreamingResponse(pdf_stream, media_type="application/pdf", headers={
        "Content-Disposition": "inline; filename=soumission_finale.pdf"
    })
