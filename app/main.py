import os
import sys
import uvicorn

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import application

if __name__ == "__main__":
    uvicorn.run(
        "app.main:application",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=60,
    )
