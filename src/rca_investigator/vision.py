"""Charts inside PDFs: find them, read their labels, and (optionally) look at the picture.

Local first, cloud optional:
1. **Always, on this computer, instantly:** pages with a chart are found (a large picture,
   or a captioned drawing), and the chart's caption is read from the page text.
2. **Optional, local:** a vision model in Ollama looks at just those chart pictures
   (e.g. `ollama pull qwen2.5vl:3b`). Private, but slower on a laptop.
3. **Optional, cloud:** any OpenAI-compatible vision service, e.g. your own GPU server or a
   hosted provider. Fast, but the chart pictures (only those) leave this computer, so it is
   used only when the server is configured for it AND the user switches it on.
   Configure with RCA_CLOUD_VISION_URL, RCA_CLOUD_VISION_MODEL and RCA_CLOUD_VISION_KEY.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

MAX_CHARTS = 6  # charts found per document
READ_CHARTS = 4  # charts looked at by a vision model per investigation
MIN_AREA = 0.08  # a picture covering at least 8% of the page may be a chart
VISION_FAMILIES = ("qwen2.5vl", "qwen2-vl", "llava", "llama3.2-vision", "moondream",
                   "minicpm-v", "granite3.2-vision", "gemma3", "bakllava")
CAPTION = re.compile(r"^\s*((figure|fig\.|chart|graph|plot|exhibit|diagram)\s*\d*\s*[:.\-–]?.*)$",
                     re.IGNORECASE | re.MULTILINE)
CHART_PROMPT = """You are helping investigate an incident. Describe this chart briefly:
what it measures, the time range, the main trend, and any sudden change (when, from what
level to what level). Mention anything unusual. Use only what is visible; if a value is
unclear, say so. At most 5 sentences.{hint}"""


@dataclass
class ChartImage:
    page: int
    png: bytes
    caption: str | None


def _caption(text: str) -> str | None:
    m = CAPTION.search(text or "")
    return m.group(1).strip()[:200] if m else None


def find_charts(data: bytes, page_texts: list[str]) -> list[ChartImage]:
    """Pictures of charts in a PDF: large images, or captioned pages full of drawing."""
    try:
        import pypdfium2 as pdfium
        from pypdfium2 import raw
    except ImportError:
        return []
    charts: list[ChartImage] = []
    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError:
        return []
    for index in range(len(pdf)):
        if len(charts) >= MAX_CHARTS:
            break
        page = pdf[index]
        width, height = page.get_size()
        text = page_texts[index] if index < len(page_texts) else ""
        caption = _caption(text)
        boxes, paths = [], 0
        for obj in page.get_objects(max_depth=3):
            if obj.type == raw.FPDF_PAGEOBJ_IMAGE:
                left, bottom, right, top = obj.get_bounds()
                if (right - left) * (top - bottom) >= MIN_AREA * width * height:
                    boxes.append((left, bottom, right, top))
            elif obj.type == raw.FPDF_PAGEOBJ_PATH:
                paths += 1
                if paths > 2000:
                    break
        if not boxes and not (caption and paths >= 25):
            continue
        scale = min(2.0, 1100 / max(width, height))
        image = page.render(scale=scale).to_pil()
        for left, bottom, right, top in boxes[:2] or [(0, 0, width, height)]:
            crop = image.crop((int(left * scale), int((height - top) * scale),
                               int(right * scale), int((height - bottom) * scale)))
            buffer = io.BytesIO()
            crop.convert("RGB").save(buffer, format="PNG", optimize=True)
            charts.append(ChartImage(index + 1, buffer.getvalue(), caption))
    return charts


class VisionClient:
    """Any OpenAI-compatible chat endpoint that accepts images (Ollama included)."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None,
                 timeout: float = 240, where: str = "local"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.where = where  # "local" or "cloud"

    @property
    def host(self) -> str:
        return urlparse(self.base_url).hostname or self.base_url

    def describe(self, png: bytes, caption: str | None = None) -> str:
        hint = f"\nThe chart's caption says: {caption}" if caption else ""
        image = "data:image/png;base64," + base64.b64encode(png).decode()
        body = {"model": self.model, "temperature": 0.1, "max_tokens": 300, "messages": [{
            "role": "user", "content": [
                {"type": "text", "text": CHART_PROMPT.format(hint=hint)},
                {"type": "image_url", "image_url": {"url": image}}]}]}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(f"{self.base_url}/chat/completions",
                                         data=json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                reply = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise VisionError(f"couldn't read the chart ({exc})") from exc
        return reply["choices"][0]["message"]["content"].strip()


class VisionError(RuntimeError):
    pass


def local_vision(ollama_host: str | None = None) -> VisionClient | None:
    """A vision model already installed in Ollama, if there is one."""
    from .llm import OllamaClient

    host = ollama_host or os.environ.get("RCA_OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("RCA_VISION_MODEL")
    if not model:
        try:
            installed = OllamaClient(host=host, timeout=3).installed_models()
        except Exception:  # noqa: BLE001 (Ollama not running: no local vision)
            return None
        model = next((m for m in installed if any(f in m for f in VISION_FAMILIES)), None)
    return VisionClient(f"{host.rstrip('/')}/v1", model, where="local") if model else None


def cloud_vision() -> VisionClient | None:
    """A cloud vision service, only if the person running CuteBot configured one."""
    url, model = os.environ.get("RCA_CLOUD_VISION_URL"), os.environ.get("RCA_CLOUD_VISION_MODEL")
    if not (url and model):
        return None
    return VisionClient(url, model, os.environ.get("RCA_CLOUD_VISION_KEY"), timeout=60,
                        where="cloud")
