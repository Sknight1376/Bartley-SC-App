(function () {
  const views = ["sailors", "calendar", "duties", "review", "handicap", "exports", "imports"];

  function esc(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fmtDateTime(raw) {
    if (!raw) return "";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return esc(raw);
    return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
  }

  function setActiveView(view) {
    views.forEach((v) => {
      const section = document.getElementById(`view-${v}`);
      if (section) section.classList.toggle("hidden", v !== view);
    });
    document.querySelectorAll(".dash-nav-btn[data-view]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-view") === view);
    });
  }

  async function getJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `Request failed: ${url}`);
    return data;
  }

  async function loadSailorsBoats() {
    const data = await getJson("/api/dashboard/sailors-boats");
    const sailorsRows = document.getElementById("sailorsRows");
    const boatClassRows = document.getElementById("boatClassRows");

    sailorsRows.innerHTML = (data.sailors || []).map((s) => `
      <tr>
        <td>${esc(s.name)}</td>
        <td><span class="dash-chip">${(s.boats || []).length}</span></td>
      </tr>
    `).join("") || `<tr><td colspan="2" class="muted">No sailors found</td></tr>`;

    boatClassRows.innerHTML = (data.boat_classes || []).map((b) => `
      <tr>
        <td>${esc(b.boat_class)}</td>
        <td>${esc(b.handicap)}</td>
        <td><span class="dash-chip">${esc(b.assigned_count)}</span></td>
      </tr>
    `).join("") || `<tr><td colspan="3" class="muted">No boat classes found</td></tr>`;
  }

  async function loadCalendar() {
    const from = document.getElementById("calendarFrom").value;
    const to = document.getElementById("calendarTo").value;
    const qs = new URLSearchParams();
    if (from) qs.set("from_date", from);
    if (to) qs.set("to_date", to);

    const data = await getJson(`/api/dashboard/race-calendar?${qs.toString()}`);
    const rows = document.getElementById("calendarRows");
    rows.innerHTML = (data.races || []).map((r) => `
      <tr>
        <td>${esc(r.series_name)}</td>
        <td>#${esc(r.race_no)}</td>
        <td>${fmtDateTime(r.started_at)}</td>
        <td>${esc(r.status)}</td>
        <td>${esc(r.results_status || "draft")}</td>
        <td>${esc(r.source_mode || "live")}</td>
      </tr>
    `).join("") || `<tr><td colspan="6" class="muted">No races in range</td></tr>`;
  }

  async function loadDuties() {
    const data = await getJson("/api/dashboard/duty-roster");
    const rows = document.getElementById("dutyRows");
    rows.innerHTML = (data.duties || []).map((d) => `
      <tr>
        <td>#${esc(d.race_no)}</td>
        <td>${esc(d.series_name)}</td>
        <td>${esc(d.sailor_name)}</td>
        <td>${esc(d.duty_type || d.role_code)}</td>
        <td>${esc(d.status)}</td>
        <td>${esc(d.notes || "")}</td>
      </tr>
    `).join("") || `<tr><td colspan="6" class="muted">No duty assignments found</td></tr>`;
  }

  async function loadReviewQueue() {
    const data = await getJson("/api/dashboard/results-review-queue");
    const rows = document.getElementById("reviewRows");
    rows.innerHTML = (data.queue || []).map((r) => `
      <tr>
        <td>#${esc(r.race_no)}</td>
        <td>${esc(r.series_name)}</td>
        <td>${esc(r.status)}</td>
        <td>${esc(r.results_status || "draft")}</td>
        <td>${esc(r.entry_count)}</td>
        <td>${esc(r.finish_count)}</td>
        <td><a href="/race_summary?race_id=${encodeURIComponent(r.race_id)}">Open</a></td>
      </tr>
    `).join("") || `<tr><td colspan="7" class="muted">Queue is empty</td></tr>`;
  }

  async function loadHandicapRecommendations() {
    const data = await getJson("/api/dashboard/handicap-recommendations");
    const rows = document.getElementById("handicapRows");
    rows.innerHTML = (data.recommendations || []).map((r) => `
      <tr>
        <td>${fmtDateTime(r.created_at)}</td>
        <td>#${esc(r.race_no)}</td>
        <td>${esc(r.series_name)}</td>
        <td>${esc(r.recommendation_id)}</td>
        <td>${esc(r.decision)}</td>
        <td>${esc(r.reason || "")}</td>
      </tr>
    `).join("") || `<tr><td colspan="6" class="muted">No recommendations recorded yet</td></tr>`;
  }

  async function exportResults() {
    const status = document.getElementById("exportStatus");
    const raceId = (document.getElementById("exportRaceId").value || "").trim();
    if (!raceId) {
      status.textContent = "Enter a race ID first.";
      return;
    }

    status.textContent = `Downloading race_${raceId}_results.csv...`;
    window.location.href = `/api/dashboard/exports/results.csv?race_id=${encodeURIComponent(raceId)}`;
  }

  async function previewImport() {
    const file = document.getElementById("importFile").files[0];
    const status = document.getElementById("importStatus");
    const rows = document.getElementById("importRows");
    if (!file) {
      status.textContent = "Choose a CSV file first.";
      return;
    }

    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/dashboard/imports/paper-csv/preview", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      status.textContent = data.error || "Preview failed";
      return;
    }

    status.textContent = `Preview loaded: ${data.count} rows`;
    rows.innerHTML = (data.entries || []).map((e) => `
      <tr>
        <td>${esc(e.sailor)}</td>
        <td>${esc(e.boat)}</td>
        <td>${esc(e.sailNumber)}</td>
        <td class="mono">${esc(e.elapsed_time || "")}</td>
        <td class="mono">${esc(e.corrected_time || "")}</td>
        <td>${esc(e.position || "")}</td>
        <td>${e.dnf ? "YES" : ""}</td>
      </tr>
    `).join("");
  }

  async function applyImport() {
    const file = document.getElementById("importFile").files[0];
    const raceId = (document.getElementById("importRaceId").value || "").trim();
    const status = document.getElementById("importStatus");

    if (!file || !raceId) {
      status.textContent = "Choose a CSV and race ID first.";
      return;
    }

    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`/api/dashboard/imports/paper-csv/apply/${encodeURIComponent(raceId)}`, {
      method: "POST",
      body: form,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      status.textContent = data.error || "Apply failed";
      return;
    }

    status.textContent = `Applied import to race ${raceId}. Entries: ${data.saved_entries || data.count || 0}.`;
  }

  document.querySelectorAll(".dash-nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => setActiveView(btn.getAttribute("data-view")));
  });

  document.getElementById("reloadCalendar").addEventListener("click", loadCalendar);
  document.getElementById("exportResultsBtn").addEventListener("click", exportResults);
  document.getElementById("previewImportBtn").addEventListener("click", previewImport);
  document.getElementById("applyImportBtn").addEventListener("click", applyImport);

  (async function init() {
    try {
      await Promise.all([
        loadSailorsBoats(),
        loadCalendar(),
        loadDuties(),
        loadReviewQueue(),
        loadHandicapRecommendations(),
      ]);
    } catch (e) {
      alert(e.message || "Failed to load dashboard");
    }
  })();
})();
