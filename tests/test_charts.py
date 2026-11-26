import io

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from test_documents import POSTMORTEM

from rca_investigator.documents import (
    Document,
    document_from_text,
    investigate_documents,
    load_document,
)
from rca_investigator.vision import ChartImage, VisionClient, VisionError, local_vision
from rca_investigator.web import create_app


def chart_png() -> Image.Image:
    img = Image.new("RGB", (600, 300), "white")
    d = ImageDraw.Draw(img)
    d.line([(40, 250), (300, 245), (310, 80), (560, 90)], fill="blue", width=4)
    d.line([(40, 260), (560, 260)], fill="black", width=2)
    return img


class FakeVision:
    where, host, model = "local", "localhost", "fake-vl"

    def __init__(self, fail=False):
        self.fail, self.calls = fail, 0

    def describe(self, png, caption=None):
        self.calls += 1
        if self.fail:
            raise VisionError("model not reachable")
        return "Checkout errors were flat, then jumped sharply at 09:00 and stayed high."


def test_chart_picture_in_pdf_is_found():
    buffer = io.BytesIO()
    chart_png().save(buffer, format="PDF")
    doc = load_document("charts.pdf", buffer.getvalue())
    assert len(doc.charts) == 1 and doc.charts[0].page == 1
    assert doc.charts[0].png.startswith(b"\x89PNG") and not doc.chunks


def with_chart() -> Document:
    doc = document_from_text("review.pdf", POSTMORTEM)
    buffer = io.BytesIO()
    chart_png().save(buffer, format="PNG")
    doc.charts = [ChartImage(2, buffer.getvalue(), "Figure 1: Checkout errors on sale day")]
    return doc


def test_chart_labels_are_used_without_a_vision_model():
    report = investigate_documents("What went wrong?", [with_chart()], None)
    assert any(e.summary == 'Chart: "Figure 1: Checkout errors on sale day"'
               for e in report.evidence)
    assert report.guardrails.charts_found == 1 and report.guardrails.charts_read == 0


def test_vision_model_reads_the_chart():
    vision = FakeVision()
    report = investigate_documents("What went wrong?", [with_chart()], None, vision=vision)
    seen = [e.summary for e in report.evidence if e.summary.startswith("Chart (read from")]
    assert seen and "jumped sharply" in seen[0]
    assert report.guardrails.charts_read == 1 and vision.calls == 1


def test_vision_failure_falls_back_to_labels():
    steps = []
    report = investigate_documents("What went wrong?", [with_chart()], None,
                                   on_step=lambda s, m: steps.append(m), vision=FakeVision(True))
    assert any("couldn't look at the chart" in m for m in steps)
    assert report.guardrails.charts_read == 0 and report.contributing_factors


def test_no_local_vision_when_ollama_is_unreachable():
    assert local_vision("http://127.0.0.1:9") is None


def test_server_lists_vision_options_and_cloud_is_off_by_default():
    client = TestClient(create_app(client_factory=lambda llm: None, memory_dir=None,
                                   vision={"local": VisionClient("http://x/v1", "fake-vl")}))
    assert client.get("/api/info").json()["vision"] == {"local": "fake-vl", "cloud": None}
