import uvicorn
from api.routes_4 import app

if __name__ == "__main__":
    uvicorn.run("api.routes_4:app", host="0.0.0.0", port=8004, reload=True)
