"""FastAPI app exposing the pipeline as a local web UI."""
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from cartocrisp.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES
from cartocrisp.pipeline import GenerateOptions, GenerationError, generate

app = FastAPI(title="cartocrisp")

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


class GenerateRequest(BaseModel):
    link: str
    width: int = 1600
    height: int = 1200
    fmt: str = "svg"
    lang: str = DEFAULT_LOCALE


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/generate")
def generate_map(request: GenerateRequest) -> FileResponse:
    locale = request.lang if request.lang in SUPPORTED_LOCALES else DEFAULT_LOCALE
    suffix = ".pdf" if request.fmt == "pdf" else ".svg"

    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        output_path = Path(tmp.name)

    options = GenerateOptions(
        output_path=output_path, width_px=request.width, height_px=request.height, fmt=request.fmt, locale=locale
    )

    try:
        generate(request.link, options)
    except GenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    media_type = "application/pdf" if request.fmt == "pdf" else "image/svg+xml"
    return FileResponse(output_path, media_type=media_type, filename=f"cartocrisp{suffix}")
