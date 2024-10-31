import logging
import asyncio
import httpx
import tempfile
from openai import OpenAI
from app.core.config import Settings
from app.models.pdf_analysis import PdfAnalysisRequest, PdfAnalysisResponse
import os
from pathlib import Path

class PdfAnalysisService:
    """pdf解析服务，分钟并发3次，建议增加api轮换"""
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
        self.client = OpenAI(
            api_key=self.settings.MOONSHOT_API_KEY,
            base_url=self.settings.MOONSHOT_BASE_URL,
        )

    async def download_pdf(self, url: str) -> bytes:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logging.error(f"下载PDF失败: {str(e)}")
            raise

    async def upload_to_moonshot(self, pdf_content: bytes) -> str:
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(pdf_content)
                temp_file.flush()
                
                file_object = await asyncio.to_thread(
                    self.client.files.create,
                    file=Path(temp_file_path),
                    purpose="file-extract"
                )
                
                file_content = await asyncio.to_thread(
                    self.client.files.content,
                    file_id=file_object.id
                )
                return file_content.text
        except Exception as e:
            logging.error(f"上传PDF到Moonshot失败: {str(e)}")
            raise
        finally:
            # 确保在所有情况下都清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logging.error(f"清理临时文件失败: {str(e)}")

    async def analyze_pdf(self, request: PdfAnalysisRequest) -> str:
        try:
            # 下载PDF
            pdf_content = await self.download_pdf(request.pdfUrl)
            
            # 上传到Moonshot并获取内容
            file_content = await self.upload_to_moonshot(pdf_content)

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": file_content},
                {"role": "user", "content": "请仔细分析报告，100-150字"}
            ]

            completion = await asyncio.to_thread(
                self.client.chat.completions.create,
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