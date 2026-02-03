const form = document.getElementById("cv-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const downloadEl = document.getElementById("download");
const previewBtn = document.getElementById("preview-btn");
const previewEl = document.getElementById("preview");
const previewTextEl = document.getElementById("preview-text");
const jobUrlInput = document.getElementById("job_url");

const setStatus = (message) => {
  statusEl.textContent = message;
};

const setPreviewVisible = (visible) => {
  previewEl.hidden = !visible;
};

const setDownloadEnabled = (enabled) => {
  if (enabled) {
    downloadEl.removeAttribute("aria-disabled");
    downloadEl.classList.remove("is-disabled");
  } else {
    downloadEl.setAttribute("aria-disabled", "true");
    downloadEl.classList.add("is-disabled");
    downloadEl.removeAttribute("href");
    downloadEl.removeAttribute("download");
  }
};

const fetchPreview = async () => {
  const jobUrl = jobUrlInput.value.trim();
  if (!jobUrl) {
    setStatus("Please enter a job offer URL to preview.");
    setPreviewVisible(false);
    return;
  }

  setStatus("Fetching job offer preview...");
  setPreviewVisible(false);

  const formData = new FormData();
  formData.append("job_url", jobUrl);

  const response = await fetch("/api/preview", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = "Failed to fetch preview.";
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = typeof payload.detail === "string"
          ? payload.detail
          : JSON.stringify(payload.detail);
      }
    } catch (parseError) {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }

  const data = await response.json();
  previewTextEl.textContent = data.job_text || "No content extracted.";
  setPreviewVisible(true);
  setStatus("Preview updated.");
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultEl.hidden = true;
  setDownloadEnabled(false);
  setStatus("Generating your CV. This can take a moment...");

  const formData = new FormData(form);

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let detail = "Failed to generate CV";
      try {
        const errorPayload = await response.json();
        if (errorPayload?.detail) {
          detail = typeof errorPayload.detail === "string"
            ? errorPayload.detail
            : JSON.stringify(errorPayload.detail);
        }
      } catch (parseError) {
        // ignore JSON parse errors
      }
      throw new Error(detail);
    }

    const data = await response.json();
    const downloadCheck = await fetch(data.download_url, { method: "HEAD" });
    if (!downloadCheck.ok) {
      throw new Error("PDF not available");
    }
    downloadEl.href = data.download_url;
    downloadEl.download = data.pdf_filename;
    setDownloadEnabled(true);
    resultEl.hidden = false;
    setStatus(`Ready: ${data.job_title}`);
  } catch (error) {
    const message = error?.message
      ? `CV generation failed: ${error.message}`
      : "CV generation failed. Please check the URL and skills file.";
    setStatus(message);
    setDownloadEnabled(false);
  }
});

previewBtn.addEventListener("click", async () => {
  try {
    await fetchPreview();
  } catch (error) {
    const message = error?.message
      ? `Preview failed: ${error.message}`
      : "Preview failed. Please check the job URL.";
    setStatus(message);
    setPreviewVisible(false);
  }
});

const startLiveReload = () => {
  if (!["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    return;
  }

  let lastHash = "";
  const poll = async () => {
    try {
      const response = await fetch("/api/dev-assets-hash", { cache: "no-store" });
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      if (lastHash && data.hash && data.hash !== lastHash) {
        window.location.reload();
      }
      lastHash = data.hash || lastHash;
    } catch (error) {
      // ignore reload failures
    }
  };

  poll();
  setInterval(poll, 1200);
};

startLiveReload();
