from fastapi import APIRouter, BackgroundTasks
from app.models.pdf_analysis import PdfAnalysisRequest, BasicResponse
from app.services.pdf_service import PdfAnalysisService
import logging

router = APIRouter()
pdf_service = PdfAnalysisService()

@router.post("/analyze_pdf", response_model=BasicResponse)  # 修改这里的路径
async def analyze_pdf(
    request: PdfAnalysisRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_pdf_analysis, request)
    return BasicResponse(code=0, msg="成功", data="")

async def process_pdf_analysis(request: PdfAnalysisRequest):
    try:
        # 分析PDF
        analysis_result = await pdf_service.analyze_pdf(request)
        logging.info(f"准备提交数据：{analysis_result}")
        # 提交结果
        await pdf_service.submit_analysis(request.id, analysis_result)
    except Exception as e:
        logging.error(f"处理PDF分析任务失败: {str(e)}")
