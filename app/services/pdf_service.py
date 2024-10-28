import logging
import asyncio
import httpx
from openai import OpenAI
from app.core.config import Settings
from app.models.pdf_analysis import PdfAnalysisRequest, PdfAnalysisResponse

class PdfAnalysisService:
    def __init__(self):
        self.settings = Settings()
        self.system_prompt = """你是一个专业的健康报告分析助手。请生成此体检报告的健康问题总结，字数在150字以内，
                            ##要求##
                            1.不要提及人名
                            2.语言简明扼要，直接总结结论
                            3.仅输出异常项，正常项不需要输出
                            4.不输出多余解释和说明。
                            5.如果没有异常问题，直接输出"体检报告无异常"
                            6.不要遗漏健康问题和异常项

                            ##输出示例##
                            示例一：体检报告无异常。
                            示例二：存在电轴右偏、左侧小脑后下动脉血流速度增快、颈椎生理曲度变直、右肺微小结节等问题。"""

    async def analyze_pdf(self, request: PdfAnalysisRequest) -> str:
        try:
            client = OpenAI(
                api_key=self.settings.MOONSHOT_API_KEY,
                base_url=self.settings.MOONSHOT_BASE_URL,
            )

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": request.pdfUrl},
                {"role": "user", "content": "请仔细分析报告，100-150字"}
            ]

            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="moonshot-v1-32k",
                messages=messages,
                temperature=0.7,
            )

            return completion.choices[0].message.content
        except Exception as e:
            logging.error(f"PDF分析失败: {str(e)}")
            raise

    async def submit_analysis(self, request_id: str, analysis_result: str) -> None:
        try:
            result_data = PdfAnalysisResponse(
                code=0,
                msg="成功",
                data={"id": request_id, "pdfAnalysis": analysis_result}
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.PDF_ANALYSIS_SUBMIT_URL,
                    json=result_data.dict(),
                    timeout=30.0
                )
                response.raise_for_status()
                logging.info(f"成功提交PDF分析结果")
        except Exception as e:
            logging.error(f"提交PDF分析结果失败: {str(e)}")
            raise