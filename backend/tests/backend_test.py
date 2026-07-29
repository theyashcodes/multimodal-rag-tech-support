"""End-to-end backend tests for Multi-modal RAG Technical Support app."""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if "REACT_APP_BACKEND_URL" in os.environ else "https://support-ai-mentor.preview.emergentagent.com"

FIXTURES = "/app/test_fixtures"
PDF_PATH = f"{FIXTURES}/sample_manual.pdf"
IMG_PATH = f"{FIXTURES}/product.jpg"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    return s


# ---------- Health / status ----------
class TestStatus:
    def test_api_root(self, api):
        r = api.get(f"{BASE_URL}/api/")
        assert r.status_code == 200
        assert "message" in r.json()

    def test_status_returns_has_index_boolean(self, api):
        r = api.get(f"{BASE_URL}/api/status")
        assert r.status_code == 200
        data = r.json()
        assert "has_index" in data
        assert isinstance(data["has_index"], bool)


# ---------- Reset ----------
class TestReset:
    def test_reset_clears_index(self, api):
        r = api.post(f"{BASE_URL}/api/reset")
        assert r.status_code == 200
        assert r.json().get("ok") is True
        # verify index cleared
        s = api.get(f"{BASE_URL}/api/status").json()
        assert s["has_index"] is False


# ---------- PDF upload / index build ----------
class TestPdfUpload:
    def test_upload_pdf_success(self, api):
        # ensure clean
        api.post(f"{BASE_URL}/api/reset")
        with open(PDF_PATH, "rb") as f:
            r = api.post(
                f"{BASE_URL}/api/upload-pdf",
                files={"file": ("sample_manual.pdf", f, "application/pdf")},
                timeout=120,
            )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["filename"] == "sample_manual.pdf"
        assert isinstance(data["chunks"], int)
        assert data["chunks"] >= 1

        # index should now exist
        s = api.get(f"{BASE_URL}/api/status").json()
        assert s["has_index"] is True

    def test_upload_pdf_rejects_non_pdf(self, api):
        r = api.post(
            f"{BASE_URL}/api/upload-pdf",
            files={"file": ("foo.txt", b"hello", "text/plain")},
        )
        assert r.status_code == 400


# ---------- Image upload ----------
class TestImageUpload:
    def test_upload_image_success(self, api):
        with open(IMG_PATH, "rb") as f:
            r = api.post(
                f"{BASE_URL}/api/upload-image",
                files={"file": ("product.jpg", f, "image/jpeg")},
                timeout=60,
            )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "path" in data and data["path"]
        assert data["original"] == "product.jpg"
        # stash path for other tests
        pytest.image_path = data["path"]

    def test_upload_image_rejects_bad_ext(self, api):
        r = api.post(
            f"{BASE_URL}/api/upload-image",
            files={"file": ("evil.svg", b"<svg/>", "image/svg+xml")},
        )
        assert r.status_code == 400


# ---------- Ask (RAG) ----------
class TestAsk:
    def test_ask_text_only(self, api):
        # ensure index present
        s = api.get(f"{BASE_URL}/api/status").json()
        if not s["has_index"]:
            with open(PDF_PATH, "rb") as f:
                api.post(
                    f"{BASE_URL}/api/upload-pdf",
                    files={"file": ("sample_manual.pdf", f, "application/pdf")},
                    timeout=120,
                )
        r = api.post(
            f"{BASE_URL}/api/ask",
            data={"question": "My device won't power on. What should I do?", "image_paths": ""},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 30, "Gemini answer too short"
        # Should reference something from the manual (power/cable/reset/battery)
        low = data["answer"].lower()
        assert any(k in low for k in ["power", "cable", "reset", "battery", "charger", "outlet"]), \
            f"Answer does not reference manual: {data['answer'][:200]}"
        # context chunks
        assert isinstance(data["context"], list)
        assert len(data["context"]) >= 1
        for c in data["context"]:
            assert "text" in c and "score" in c
            assert isinstance(c["score"], float)

    def test_ask_with_image_multimodal(self, api):
        # upload image
        with open(IMG_PATH, "rb") as f:
            up = api.post(
                f"{BASE_URL}/api/upload-image",
                files={"file": ("product.jpg", f, "image/jpeg")},
                timeout=60,
            ).json()
        image_path = up["path"]

        r = api.post(
            f"{BASE_URL}/api/ask",
            data={
                "question": "The screen shows an error. What does the image show and how do I fix it?",
                "image_paths": image_path,
            },
            timeout=180,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 50
        # Vision should describe what's in image (screen/error/device/red/led/button etc)
        low = data["answer"].lower()
        assert any(k in low for k in [
            "screen", "display", "device", "error", "e01", "overheat",
            "red", "led", "button", "indicator", "image"
        ]), f"Vision answer doesn't describe image: {data['answer'][:300]}"

    def test_ask_empty_question_rejected(self, api):
        r = api.post(
            f"{BASE_URL}/api/ask",
            data={"question": "   ", "image_paths": ""},
        )
        assert r.status_code == 400
