from pydantic import BaseModel

class PdfAnalysisRequest(BaseModel):
    id: str
    pdfUrl: str

class PdfAnalysisData(BaseModel):
    id: str
    pdfAnalysis: str

class PdfAnalysisResponse(BaseModel):
    code: int
    msg: str
    data: PdfAnalysisData

class BasicResponse(BaseModel):
    code: int
    msg: str
    data: str
