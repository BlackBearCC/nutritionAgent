import uvicorn
import sys
from pathlib import Path


project_root = Path(__file__).parent
sys.path.append(str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=8
    )