import base64
# import cv2
import numpy as np
from PIL import Image
import io
import logging

class FileToBase64Converter:
    # @staticmethod
    # def convert_image(image_path: str) -> str:
    #     """
    #     将图片转换为base64编码
    #     支持: PNG, JPG, JPEG
    #     """
    #     try:
    #         # 读取图片
    #         img = cv2.imread(image_path)
    #
    #         # 图片预处理
    #         # 1. 调整大小（如果需要）
    #         max_size = 1024
    #         height, width = img.shape[:2]
    #         if height > max_size or width > max_size:
    #             ratio = min(max_size/width, max_size/height)
    #             new_size = (int(width * ratio), int(height * ratio))
    #             img = cv2.resize(img, new_size)
    #
    #         # 2. 优化图片质量
    #         encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    #         _, buffer = cv2.imencode('.jpg', img, encode_param)
    #
    #         # 转base64
    #         base64_str = base64.b64encode(buffer).decode('utf-8')
    #         return base64_str
    #
    #     except Exception as e:
    #         logging.error(f"图片转换失败: {str(e)}")
    #         raise

    @staticmethod
    def convert_pdf(pdf_path: str) -> str:
        """
        将PDF转换为base64编码
        """
        try:
            with open(pdf_path, "rb") as file:
                base64_str = base64.b64encode(file.read()).decode('utf-8')
            return base64_str
        except Exception as e:
            logging.error(f"PDF转换失败: {str(e)}")
            raise

    @staticmethod
    def convert_docx(docx_path: str) -> str:
        """
        将DOCX转换为base64编码
        """
        try:
            with open(docx_path, "rb") as file:
                base64_str = base64.b64encode(file.read()).decode('utf-8')
            return base64_str
        except Exception as e:
            logging.error(f"DOCX转换失败: {str(e)}")
            raise
