// ===== State =====
let currentJobId = null;

// ===== DOM Helpers =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function showStatus(elId, message, type = "info") {
  const el = $(`#${elId}`);
  el.className = `status ${type}`;
  el.innerHTML = message;
  el.classList.remove("hidden");
}

function hideStatus(elId) {
  $(`#${elId}`).classList.add("hidden");
}

// ===== Tabs =====
$$(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    $$(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
    $$(".tab-content").forEach(c => {
      c.classList.toggle("hidden", c.dataset.tab !== target);
    });
    // Clear the other input so the API gets exactly one input type
    if (target === "jd") {
      const skillsInput = document.querySelector('input[name="skills_input"]');
      if (skillsInput) skillsInput.value = "";
    } else {
      const descInput = document.querySelector('textarea[name="description"]');
      if (descInput) descInput.value = "";
    }
  });
});

// ===== File Upload =====
const dropZone = $("#drop-zone");
const fileInput = $("#file-input");
const fileInputFiles = $("#file-input-files");

["dragenter", "dragover"].forEach(evt => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
});
["dragleave", "drop"].forEach(evt => {
  dropZone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  const files = Array.from(e.dataTransfer.files).filter(f => {
    const ext = f.name.split(".").pop().toLowerCase();
    return ["pdf", "doc", "docx", "txt"].includes(ext);
  });
  if (files.length > 0) uploadFiles(files);
});

fileInput.addEventListener("change", (e) => {
  uploadFiles(Array.from(e.target.files));
});
fileInputFiles.addEventListener("change", (e) => {
  uploadFiles(Array.from(e.target.files));
});

async function uploadFiles(files) {
  if (!files.length) return;
  showStatus("upload-status",
    `<span class="spinner"></span>Uploading and parsing ${files.length} resume(s)... (this may take 10-30 seconds)`,
    "info");

  const formData = new FormData();
  files.forEach(f => formData.append("files", f));

  try {
    const res = await fetch("/api/resumes/upload", {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderUploadResults(data);
    loadCandidates();
  } catch (err) {
    showStatus("upload-status", `❌ Upload failed: ${err.message}`, "error");
  }
}

function renderUploadResults(data) {
  const parts = [];
  if (data.parsed.length) parts.push(`✅ Parsed ${data.parsed.length}`);
  if (data.duplicates.length) parts.push(`🔁 Skipped ${data.duplicates.length} duplicate(s)`);
  if (data.skipped.length) parts.push(`⚠️ Skipped ${data.skipped.length}`);
  if (data.errors.length) parts.push(`❌ ${data.errors.length} error(s)`);

  const type = data.errors.length > 0 ? "error" : "success";
  showStatus("upload-status", parts.join(" · "), type);

  // Show error details if any
  if (data.errors.length || data.skipped.length) {
    const details = [...data.errors, ...data.skipped].map(e =>
      `<li>${e.filename}: ${e.reason}</li>`
    ).join("");
    $("#upload-results").innerHTML = `<ul style="margin-top:8px;padding-left:24px;font-size:13px;color:#742a2a;">${details}</ul>`;
    $("#upload-results").classList.remove("hidden");
  } else {
    $("#upload-results").classList.add("hidden");
  }
}

// ===== Candidates List =====
async function loadCandidates() {
  try {
    const res = await fetch("/api/candidates");
    const data = await res.json();
    renderCandidates(data.candidates);
  } catch (err) {
    console.error(err);
  }
}

function renderCandidates(candidates) {
  const container = $("#candidate-list");
  if (!candidates.length) {
    container.innerHTML = `<p class="muted">No resumes uploaded yet.</p>`;
    return;
  }
  container.innerHTML = `
    <h3 style="margin: 16px 0 12px; font-size: 15px;">Parsed Candidates (${candidates.length})</h3>
    ${candidates.map(c => `
      <div class="candidate-card">
        <h3>${c.name || "Unknown"} <span class="filename">— ${c.filename}</span></h3>
        <div class="info-grid">
          <div><strong>Email:</strong> ${c.email || "—"}</div>
          <div><strong>Phone:</strong> ${c.phone || "—"}</div>
          <div><strong>Experience:</strong> ${c.total_experience_years ?? "—"} yrs</div>
          <div><strong>Location:</strong> ${c.location || "—"}</div>
          <div><strong>Notice:</strong> ${c.notice_period || "—"}</div>
          <div><strong>Company:</strong> ${c.current_company || "—"}</div>
          <div><strong>Domain:</strong> ${c.domain || "—"}</div>
          <div><strong>Education:</strong> ${(c.education || []).join("; ") || "—"}</div>
        </div>
        ${c.skills && c.skills.length ? `
          <div class="skills-list">
            ${c.skills.map(s => `<span class="skill-tag">${s}</span>`).join("")}
          </div>` : ""}
      </div>
    `).join("")}
  `;
}

async function clearCandidates() {
  if (!confirm("Delete all uploaded resumes and parsed profiles?")) return;
  await fetch("/api/candidates", { method: "DELETE" });
  loadCandidates();
  showStatus("upload-status", "Cleared all candidates.", "info");
  $("#step-results").classList.add("hidden");
}

async function exportCandidatesExcel() {
  const res = await fetch("/api/candidates/export/excel");
  if (!res.ok) {
    alert("No candidates to export.");
    return;
  }
  const blob = await res.blob();
  downloadBlob(blob, "candidates.xlsx");
}

// ===== Job Submission =====
$("#job-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);

  // Validate at least one of description/skills_input is filled
  if (!formData.get("description") && !formData.get("skills_input")) {
    showStatus("job-status", "❌ Please paste a job description OR enter required skills.", "error");
    return;
  }

  showStatus("job-status", `<span class="spinner"></span>Creating job and matching candidates...`, "info");

  try {
    // Create job
    const jobRes = await fetch("/api/jobs", { method: "POST", body: formData });
    if (!jobRes.ok) {
      const err = await jobRes.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${jobRes.status}`);
    }
    const job = await jobRes.json();
    currentJobId = job.job_id;

    // Run matching
    const matchRes = await fetch(`/api/match/${job.job_id}`, { method: "POST" });
    if (!matchRes.ok) {
      const err = await matchRes.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${matchRes.status}`);
    }
    const result = await matchRes.json();

    showStatus("job-status", `✅ Matched ${result.ranked.length} candidate(s) against "${job.title || 'job'}".`, "success");
    renderResults(result);
  } catch (err) {
    showStatus("job-status", `❌ ${err.message}`, "error");
  }
});

function renderResults(result) {
  $("#step-results").classList.remove("hidden");
  $("#step-results").scrollIntoView({ behavior: "smooth" });

  const job = result.job;
  $("#results-meta").innerHTML = `
    <strong>${job.title || "Untitled Job"}</strong> ·
    ${job.required_skills.length} required skills ·
    ${result.ranked.length} candidates ranked
  `;

  const list = $("#results-list");
  list.innerHTML = result.ranked.map(r => {
    const tier = r.overall_score >= 75 ? "top" : r.overall_score >= 50 ? "good" : "low";
    const c = r.candidate;
    const b = r.breakdown;
    return `
      <div class="ranked-card ${tier}">
        <div class="rank-header">
          <div>
            <span class="rank-badge">#${r.rank}</span>
            <div class="rank-title" style="margin-top:6px;">
              ${c.name || "Unknown"} <span class="filename" style="color:#718096;font-size:12px;font-weight:normal;">— ${c.filename}</span>
            </div>
            <div style="font-size:13px;color:#718096;margin-top:2px;">
              ${c.total_experience_years ?? "?"} yrs · ${c.location || "Location N/A"} · Notice: ${c.notice_period || "N/A"}
            </div>
          </div>
          <div class="score-display">
            <div class="score">${r.overall_score}</div>
            <div class="label">Overall Match</div>
          </div>
        </div>

        <div class="score-bars">
          ${bar("Skills (40%)", b.skills)}
          ${bar("Experience (20%)", b.experience)}
          ${bar("Education (10%)", b.education)}
          ${bar("Domain (10%)", b.domain)}
          ${bar("Certifications (10%)", b.certifications)}
          ${bar("Location/Notice (10%)", b.location_notice)}
        </div>

        ${r.matched_skills.length ? `
          <div style="margin-top:10px;">
            <strong style="font-size:13px;">✅ Matched skills:</strong>
            <div class="skills-list">
              ${r.matched_skills.map(s => `<span class="skill-tag matched">${s}</span>`).join("")}
            </div>
          </div>` : ""}

        ${r.missing_skills.length ? `
          <div style="margin-top:8px;">
            <strong style="font-size:13px;">⚠️ Missing skills:</strong>
            <div class="skills-list">
              ${r.missing_skills.map(s => `<span class="skill-tag missing">${s}</span>`).join("")}
            </div>
          </div>` : ""}

        ${r.recommendation ? `<div class="recommendation">💡 ${r.recommendation}</div>` : ""}
      </div>
    `;
  }).join("");
}

function bar(label, value) {
  const pct = Math.max(0, Math.min(100, value));
  return `
    <div class="score-bar">
      <div class="bar-label"><span>${label}</span><span>${Math.round(pct)}</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;"></div></div>
    </div>
  `;
}

// ===== Export Ranked =====
$("#export-ranked-btn").addEventListener("click", async () => {
  if (!currentJobId) {
    alert("Run matching first.");
    return;
  }
  const res = await fetch(`/api/match/${currentJobId}/export`, { method: "POST" });
  if (!res.ok) {
    alert("Export failed.");
    return;
  }
  const blob = await res.blob();
  downloadBlob(blob, `ranked_candidates_${currentJobId}.xlsx`);
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ===== Initial Load =====
loadCandidates();
