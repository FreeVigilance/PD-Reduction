from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.routes import profiles, upload, status, results, download

app = FastAPI(
    title="FreeVigilanceReduction API",
    description="Сервис для анонимизации персональных данных в документах",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h1>Free Vigilance Reduction API</h1>
    <p>Документацию можно найти кликнув на <a href="/docs">/docs</a>.</p>
    """

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(upload.router)
app.include_router(status.router)
app.include_router(results.router)
app.include_router(download.router)
