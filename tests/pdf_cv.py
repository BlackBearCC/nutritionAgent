import requests
from pathlib import Path

# 使用 Path 对象处理路径
current_dir = Path(__file__).parent
pdf_path = current_dir / 'pdf' / '2024-01-08健康体检报告.pdf'

# 确保路径存在
if not pdf_path.exists():
    raise FileNotFoundError(f"找不到文件: {pdf_path}")

# 使用 with 语句确保文件正确关闭
with open(pdf_path, 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/parse_health_report', files=files)
    
    # 打印完整响应信息
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Response Text:", response.text)
    
    # 尝试解析 JSON
    try:
        print("JSON Response:", response.json())
    except requests.exceptions.JSONDecodeError as e:
        print("JSON Decode Error:", str(e))
