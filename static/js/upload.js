/**
 * upload.js — Drag-and-drop upload + in-browser recording for upload.html.
 */
(function () {
  // ── DOM refs ───────────────────────────────────────────────────────────────
  var uploadForm    = document.getElementById("upload-form");
  var fileIndicator = document.getElementById("file-indicator");
  var fileName      = document.getElementById("file-name");
  var clearFileBtn  = document.getElementById("clear-file");
  var submitBtn     = document.getElementById("submit-btn");
  var errorDisplay  = document.getElementById("error-display");

  // Tabs
  var tabBtnUpload  = document.getElementById("tab-btn-upload");
  var tabBtnRecord  = document.getElementById("tab-btn-record");
  var tabUpload     = document.getElementById("tab-upload");
  var tabRecord     = document.getElementById("tab-record");

  // Upload
  var dropZone      = document.getElementById("drop-zone");
  var fileInput     = document.getElementById("audio-file");

  // Recorder
  var recordBtn     = document.getElementById("record-btn");
  var iconMic       = document.getElementById("icon-mic");
  var iconStop      = document.getElementById("icon-stop");
  var recordStatus  = document.getElementById("record-status");
  var recordTimer   = document.getElementById("record-timer");
  var timerDisplay  = document.getElementById("timer-display");
  var recordPreview = document.getElementById("record-preview");
  var recordActions = document.getElementById("record-actions");
  var recordAgain   = document.getElementById("record-again");
  var recordUse     = document.getElementById("record-use");

  // State
  var recordedBlob   = null;
  var mediaRecorder  = null;
  var recordedChunks = [];
  var micStream      = null;
  var timerInterval  = null;
  var recSeconds     = 0;
  var isRecording    = false;

  // ── Tab switching ──────────────────────────────────────────────────────────

  tabBtnUpload.addEventListener("click", function () { switchTab("upload"); });
  tabBtnRecord.addEventListener("click", function () { switchTab("record"); });

  function switchTab(tab) {
    var toUpload = (tab === "upload");
    tabUpload.classList.toggle("hidden", !toUpload);
    tabRecord.classList.toggle("hidden", toUpload);

    var active   = toUpload ? tabBtnUpload : tabBtnRecord;
    var inactive = toUpload ? tabBtnRecord : tabBtnUpload;
    active.classList.add("border-blue-500", "text-blue-600");
    active.classList.remove("border-transparent", "text-slate-500");
    inactive.classList.remove("border-blue-500", "text-blue-600");
    inactive.classList.add("border-transparent", "text-slate-500");

    fileInput.value = "";
    recordedBlob = null;
    resetIndicator();
    hideError();
  }

  // ── Drag-and-drop / file pick ──────────────────────────────────────────────

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
    if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
  });

  dropZone.addEventListener("click", function () { fileInput.click(); });

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) setFile(fileInput.files[0]);
  });

  clearFileBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    fileInput.value = "";
    recordedBlob = null;
    resetIndicator();
    resetRecorderPreview();
    hideError();
  });

  // ── File / indicator helpers ───────────────────────────────────────────────

  function setFile(file) {
    if (!file.type.startsWith("audio/") && file.type !== "video/mp4") {
      showError("Unsupported file type. Please upload an MP3, WAV, M4A, or WebM file.");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      showError("File is too large. Maximum size is 25 MB.");
      return;
    }
    hideError();
    recordedBlob = null;
    showIndicator(file.name);
  }

  function showIndicator(name) {
    fileName.textContent = name;
    fileIndicator.classList.remove("hidden");
    submitBtn.disabled = false;
    submitBtn.classList.remove("bg-slate-300", "cursor-not-allowed");
    submitBtn.classList.add("bg-blue-600", "hover:bg-blue-700");
  }

  function resetIndicator() {
    fileIndicator.classList.add("hidden");
    fileName.textContent = "";
    submitBtn.disabled = true;
    submitBtn.classList.add("bg-slate-300", "cursor-not-allowed");
    submitBtn.classList.remove("bg-blue-600", "hover:bg-blue-700");
  }

  // ── Recorder ──────────────────────────────────────────────────────────────

  recordBtn.addEventListener("click", function () {
    if (isRecording) stopRecording();
    else startRecording();
  });

  function getMimeType() {
    var types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
    ];
    for (var i = 0; i < types.length; i++) {
      if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(types[i])) {
        return types[i];
      }
    }
    return "";
  }

  function startRecording() {
    hideError();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError("Your browser does not support audio recording. Please upload a file instead.");
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      micStream = stream;
      recordedChunks = [];

      var mimeType = getMimeType();
      var options  = mimeType ? { mimeType: mimeType } : {};
      mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorder.ondataavailable = function (e) {
        if (e.data && e.data.size > 0) recordedChunks.push(e.data);
      };
      mediaRecorder.onstop = onRecordingStop;
      mediaRecorder.start(250);
      isRecording = true;

      // UI — recording state
      recordBtn.classList.remove("bg-blue-50", "border-blue-200", "hover:bg-blue-100", "hover:border-blue-400");
      recordBtn.classList.add("bg-red-50", "border-red-300");
      iconMic.classList.add("hidden");
      iconStop.classList.remove("hidden");
      recordStatus.textContent = "Recording… tap to stop";
      recordPreview.classList.add("hidden");
      recordPreview.src = "";
      recordActions.style.display = "none";
      resetIndicator();

      // Timer
      recSeconds = 0;
      timerDisplay.textContent = "00:00";
      recordTimer.style.display = "flex";
      timerInterval = setInterval(function () {
        recSeconds++;
        var m = String(Math.floor(recSeconds / 60)).padStart(2, "0");
        var s = String(recSeconds % 60).padStart(2, "0");
        timerDisplay.textContent = m + ":" + s;
      }, 1000);

    }).catch(function () {
      showError("Microphone access denied. Please allow microphone access in your browser settings.");
    });
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    clearInterval(timerInterval);
    isRecording = false;

    // UI — idle state
    recordBtn.classList.remove("bg-red-50", "border-red-300");
    recordBtn.classList.add("bg-blue-50", "border-blue-200", "hover:bg-blue-100", "hover:border-blue-400");
    iconStop.classList.add("hidden");
    iconMic.classList.remove("hidden");
    recordTimer.style.display = "none";
  }

  function onRecordingStop() {
    if (micStream) {
      micStream.getTracks().forEach(function (t) { t.stop(); });
      micStream = null;
    }
    var mime = (mediaRecorder && mediaRecorder.mimeType) ? mediaRecorder.mimeType : "audio/webm";
    recordedBlob = new Blob(recordedChunks, { type: mime });
    recordPreview.src = URL.createObjectURL(recordedBlob);
    recordPreview.classList.remove("hidden");
    recordActions.style.display = "flex";
    recordStatus.textContent = "Preview your recording, then use it or re-record.";
  }

  function resetRecorderPreview() {
    if (isRecording) stopRecording();
    recordedBlob = null;
    recordPreview.classList.add("hidden");
    recordPreview.src = "";
    recordActions.style.display = "none";
    recordStatus.textContent = "Tap to start recording";
  }

  recordAgain.addEventListener("click", function () {
    resetRecorderPreview();
    resetIndicator();
    hideError();
  });

  recordUse.addEventListener("click", function () {
    if (!recordedBlob) return;
    var ext  = recordedBlob.type.includes("ogg") ? ".ogg" : ".webm";
    var date = new Date().toISOString().slice(0, 10);
    showIndicator("Recording " + date + ext);
    hideError();
  });

  // ── CSRF helper ────────────────────────────────────────────────────────────

  function getCookie(name) {
    var parts = (document.cookie || "").split(";");
    for (var i = 0; i < parts.length; i++) {
      var pair = parts[i].trim().split("=");
      if (pair[0] === name) return decodeURIComponent(pair[1] || "");
    }
    return null;
  }

  // ── Form submission ────────────────────────────────────────────────────────

  uploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    hideError();

    var hasFile = fileInput.files.length > 0;
    var hasBlob = !!recordedBlob;

    if (!hasFile && !hasBlob) {
      showError("Please select or record an audio file before submitting.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Uploading…";

    var formData = new FormData();
    if (hasBlob) {
      var ext = recordedBlob.type.includes("ogg") ? ".ogg" : ".webm";
      formData.append("audio_file", recordedBlob, "recording-" + Date.now() + ext);
    } else {
      formData.append("audio_file", fileInput.files[0]);
    }

    try {
      var response = await fetch("/api/encounters/", {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      });
      var data = await response.json();

      if (response.ok && data.id) {
        window.location.href = "/encounters/" + data.id + "/";
      } else {
        var msg = (data.audio_file && data.audio_file[0]) || data.detail || "Upload failed. Please try again.";
        showError(msg);
        resetBtn();
      }
    } catch (err) {
      showError("Network error. Please check your connection and try again.");
      resetBtn();
    }
  });

  function resetBtn() {
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
