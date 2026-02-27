/**
 * upload.js — Handles the drag-and-drop upload form on upload.html.
 * On successful upload, redirects to the result/polling page.
 */

(function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("audio-file");
  const fileIndicator = document.getElementById("file-indicator");
  const fileName = document.getElementById("file-name");
  const clearFileBtn = document.getElementById("clear-file");
  const submitBtn = document.getElementById("submit-btn");
  const errorDisplay = document.getElementById("error-display");
  const uploadForm = document.getElementById("upload-form");

  // ── Drag-and-drop ─────────────────────────────────────────────────────────

  dropZone.addEventListener("dragover", function (e) {
    e.preventDefault();
    dropZone.classList.add("border-blue-400", "bg-blue-50");
  });

  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("border-blue-400", "bg-blue-50");
  });

  dropZone.addEventListener("drop", function (e) {
    e.preventDefault();
    dropZone.classList.remove("border-blue-400", "bg-blue-50");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      setFile(files[0]);
    }
  });

  dropZone.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
      setFile(fileInput.files[0]);
    }
  });

  clearFileBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    clearFile();
  });

  // ── File helpers ──────────────────────────────────────────────────────────

  function setFile(file) {
    // Validate on client side too (double-checked server side)
    const allowedTypes = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
                          "audio/mp4", "audio/x-m4a", "audio/m4a", "audio/ogg"];
    if (allowedTypes.length && !file.type.startsWith("audio/") && file.type !== "video/mp4") {
      showError("Unsupported file type. Please upload an MP3, WAV, or M4A file.");
      return;
    }
    const maxMB = 25;
    if (file.size > maxMB * 1024 * 1024) {
      showError(`File is too large. Maximum size is ${maxMB} MB.`);
      return;
    }

    hideError();
    fileName.textContent = file.name;
    fileIndicator.classList.remove("hidden");
    submitBtn.disabled = false;
    submitBtn.classList.remove("bg-slate-300", "cursor-not-allowed");
    submitBtn.classList.add("bg-blue-600", "hover:bg-blue-700");
  }

  function clearFile() {
    fileInput.value = "";
    fileIndicator.classList.add("hidden");
    submitBtn.disabled = true;
    submitBtn.classList.add("bg-slate-300", "cursor-not-allowed");
    submitBtn.classList.remove("bg-blue-600", "hover:bg-blue-700");
    hideError();
  }

  // ── CSRF cookie helper ─────────────────────────────────────────────────────

  function getCookie(name) {
    const cookieStr = document.cookie || "";
    for (const part of cookieStr.split(";")) {
      const [key, val] = part.trim().split("=");
      if (key === name) return decodeURIComponent(val);
    }
    return null;
  }

  // ── Form submission ───────────────────────────────────────────────────────

  uploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    if (!fileInput.files.length) {
      showError("Please select an audio file before submitting.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Uploading…";
    hideError();

    const formData = new FormData();
    formData.append("audio_file", fileInput.files[0]);

    try {
      const response = await fetch("/api/encounters/", {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const data = await response.json();

      if (response.ok && data.id) {
        window.location.href = "/encounters/" + data.id + "/";
      } else {
        const msg =
          (data.audio_file && data.audio_file[0]) ||
          data.detail ||
          "Upload failed. Please try again.";
        showError(msg);
        resetButton();
      }
    } catch (err) {
      showError("Network error. Please check your connection and try again.");
      resetButton();
    }
  });

  function resetButton() {
    submitBtn.disabled = false;
    submitBtn.textContent = "Process Consultation";
  }

  function showError(msg) {
    errorDisplay.textContent = msg;
    errorDisplay.classList.remove("hidden");
  }

  function hideError() {
    errorDisplay.classList.add("hidden");
    errorDisplay.textContent = "";
  }
})();
