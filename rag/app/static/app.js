const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const uploadBtn = document.getElementById("uploadBtn");
const urlBtn = document.getElementById("urlBtn");
const urlInput = document.getElementById("urlInput");
const csvMode = document.getElementById("csvMode");
const includeImages = document.getElementById("includeImages");
const visionModel = document.getElementById("visionModel");
const results = document.getElementById("results");
const clearBtn = document.getElementById("clearBtn");
const healthStatus = document.getElementById("healthStatus");
const resultTemplate = document.getElementById("resultTemplate");

let selectedFiles = [];

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderFileList() {
  fileList.innerHTML = "";
  selectedFiles.forEach((file, index) => {
    const item = document.createElement("li");
    item.className = "file-item";
    item.innerHTML = `
      <div class="file-meta">
        <span class="file-name">${file.name}</span>
        <span class="file-size">${formatBytes(file.size)}</span>
      </div>
      <button class="remove-btn" aria-label="Remove ${file.name}">×</button>
    `;
    item.querySelector(".remove-btn").addEventListener("click", () => {
      selectedFiles.splice(index, 1);
      renderFileList();
    });
    fileList.appendChild(item);
  });

  uploadBtn.disabled = selectedFiles.length === 0;
}

function addFiles(files) {
  const incoming = Array.from(files);
  selectedFiles = [...selectedFiles, ...incoming];
  renderFileList();
}

function setLoading(message) {
  results.className = "results";
  results.innerHTML = `<p class="loading">${message}</p>`;
  clearBtn.hidden = true;
}

function renderStats(container, pipelines, contentTypes) {
  container.innerHTML = "";
  Object.entries(pipelines || {}).forEach(([key, value]) => {
    const chip = document.createElement("span");
    chip.className = "stat-chip";
    chip.textContent = `${key}: ${value}`;
    container.appendChild(chip);
  });
  Object.entries(contentTypes || {}).forEach(([key, value]) => {
    const chip = document.createElement("span");
    chip.className = "stat-chip";
    chip.textContent = `${key}: ${value}`;
    container.appendChild(chip);
  });
}

function renderPreviewList(container, previews) {
  container.innerHTML = "";
  (previews || []).forEach((preview) => {
    const block = document.createElement("div");
    block.className = "preview";
    block.innerHTML = `
      <div class="preview-meta">
        <span>${preview.pipeline}</span>
        <span>${preview.content_type}</span>
        <span>page ${preview.page ?? 0}</span>
        ${preview.skip_chunking ? "<span>skip chunking</span>" : ""}
      </div>
      <p class="preview-text">${preview.preview}</p>
    `;
    container.appendChild(block);
  });
}

function renderResultCard(result) {
  const node = resultTemplate.content.cloneNode(true);
  node.querySelector(".result-title").textContent = result.source;
  node.querySelector(".badge").textContent = `${result.total_documents} docs`;
  renderStats(node.querySelector(".stats"), result.pipelines, result.content_types);
  renderPreviewList(node.querySelector(".previews"), result.previews);
  return node;
}

function renderErrorCard(filename, error) {
  const card = document.createElement("article");
  card.className = "error-card";
  card.innerHTML = `
    <h3>${filename}</h3>
    <p class="muted">${error}</p>
  `;
  return card;
}

function renderUploadResponse(data) {
  results.className = "results";
  results.innerHTML = "";
  clearBtn.hidden = false;

  data.results.forEach((result) => {
    results.appendChild(renderResultCard(result));
  });

  data.errors.forEach((item) => {
    results.appendChild(renderErrorCard(item.filename, item.error));
  });

  if (!data.results.length && !data.errors.length) {
    results.innerHTML = "<p class='muted'>No results returned.</p>";
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("Server unavailable");
    healthStatus.textContent = "Server online";
    healthStatus.className = "status-pill ok";
  } catch {
    healthStatus.textContent = "Server offline";
    healthStatus.className = "status-pill error";
  }
}

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => addFiles(event.target.files));

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  addFiles(event.dataTransfer.files);
});

uploadBtn.addEventListener("click", async () => {
  if (!selectedFiles.length) return;

  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append("files", file));
  formData.append("csv_mode", csvMode.value);
  formData.append("include_images", includeImages.checked ? "true" : "false");
  formData.append("vision_model", visionModel.value.trim() || "llava");

  uploadBtn.disabled = true;
  setLoading("Running ingestion pipeline...");

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      const detail = data.detail;
      const message =
        typeof detail === "string"
          ? detail
          : detail?.message || "Upload failed";
      const errors = detail?.errors || [];
      results.innerHTML = `<p class="error-card">${message}</p>`;
      errors.forEach((item) => {
        results.appendChild(renderErrorCard(item.filename, item.error));
      });
      clearBtn.hidden = false;
      return;
    }

    renderUploadResponse(data);
    selectedFiles = [];
    fileInput.value = "";
    renderFileList();
  } catch (error) {
    results.innerHTML = `<p class="error-card">${error.message}</p>`;
    clearBtn.hidden = false;
  } finally {
    uploadBtn.disabled = selectedFiles.length === 0;
  }
});

urlBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) return;

  urlBtn.disabled = true;
  setLoading("Fetching and ingesting URL...");

  try {
    const response = await fetch("/api/ingest-url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        include_images: includeImages.checked,
        vision_model: visionModel.value.trim() || "llava",
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      const message = typeof data.detail === "string" ? data.detail : "URL ingestion failed";
      results.innerHTML = `<p class="error-card">${message}</p>`;
      clearBtn.hidden = false;
      return;
    }

    results.className = "results";
    results.innerHTML = "";
    results.appendChild(renderResultCard(data));
    clearBtn.hidden = false;
  } catch (error) {
    results.innerHTML = `<p class="error-card">${error.message}</p>`;
    clearBtn.hidden = false;
  } finally {
    urlBtn.disabled = false;
  }
});

clearBtn.addEventListener("click", () => {
  results.className = "results empty-state";
  results.innerHTML = `
    <p>No ingestion run yet.</p>
    <p class="muted">Upload files or ingest a URL to see pipeline output here.</p>
  `;
  clearBtn.hidden = true;
});

checkHealth();
