(function () {
  const views = ["sailors", "calendar", "imports", "handicap", "exports"];
  const manualEntries = [];
  let showingApprovedQueue = false;
  let sailorDirectory = [];

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

  function parseHmsToSeconds(raw) {
    const parts = String(raw || "").trim().split(":").map((p) => Number(p));
    if (parts.length !== 3 || parts.some((p) => Number.isNaN(p))) return null;
    return (parts[0] * 3600) + (parts[1] * 60) + parts[2];
  }

  function secsToHms(totalSeconds) {
    if (totalSeconds == null || Number.isNaN(totalSeconds)) return "";
    const s = Math.round(Number(totalSeconds));
    const hh = String(Math.floor(s / 3600)).padStart(2, "0");
    const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  }

  function calcCorrectedTime(elapsedTime, handicap) {
    const elapsedSec = parseHmsToSeconds(elapsedTime);
    const hc = Number(handicap);
    if (elapsedSec == null || !hc) return "";
    return secsToHms(Math.round((elapsedSec * 1000) / hc));
  }

  function calcProjectedTime(timeValue, lapCount = 1, targetLapCount = 1) {
    const baseSeconds = typeof timeValue === "number" ? timeValue : parseHmsToSeconds(timeValue);
    const laps = Math.max(Number(lapCount) || 1, 1);
    const targetLaps = Math.max(Number(targetLapCount) || laps, laps);
    if (baseSeconds == null || Number.isNaN(baseSeconds)) return "";
    return secsToHms(Math.round((baseSeconds * targetLaps) / laps));
  }

  function getManualTargetLaps(extraLapCount = 1) {
    const lapValues = [
      Number(extraLapCount) || 1,
      ...manualEntries.map((entry) => Math.max(Number(entry.lap_number) || 1, 1)),
    ].filter((value) => value > 0);
    return Math.max(1, ...lapValues);
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

  function setDashboardStatus(message) {
    const node = document.getElementById("dashboardStatus");
    if (!node) return;
    node.textContent = message || "";
  }

  function setTableFallback(tbodyId, colspan, message) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="${colspan}" class="muted">${esc(message)}</td></tr>`;
  }

  async function getJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `Request failed: ${url}`);
    return data;
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `Request failed: ${url}`);
    return data;
  }

  async function deleteJson(url) {
    const res = await fetch(url, { method: "DELETE" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `Request failed: ${url}`);
    return data;
  }

  function isPast(dateStr) {
    if (!dateStr) return false;
    const d = new Date(dateStr);
    return !Number.isNaN(d.getTime()) && d < new Date();
  }

  function openRaceEditWorkflow(raceId, raceNo) {
    const panel = document.getElementById("raceEditWorkflow");
    const hint = document.getElementById("raceWorkflowHint");
    const title = document.getElementById("raceEditWorkflowTitle");
    const meta = document.getElementById("raceEditWorkflowMeta");
    const previousRaceId = document.getElementById("manualRaceId")?.value || "";

    if (previousRaceId !== String(raceId)) {
      manualEntries.length = 0;
      renderManualEntries();
      const importRows = document.getElementById("importRows");
      if (importRows) importRows.innerHTML = "";
      const fileInput = document.getElementById("importFile");
      if (fileInput) fileInput.value = "";
      const importStatus = document.getElementById("importStatus");
      const manualStatus = document.getElementById("manualImportStatus");
      if (importStatus) importStatus.textContent = "";
      if (manualStatus) manualStatus.textContent = "";
      const sailorSelect = document.getElementById("manualSailor");
      const sailNumberInput = document.getElementById("manualSailNumber");
      const lapsInput = document.getElementById("manualLaps");
      const elapsedInput = document.getElementById("manualElapsed");
      if (sailorSelect) sailorSelect.value = "";
      if (sailNumberInput) sailNumberInput.value = "";
      if (lapsInput) lapsInput.value = "1";
      if (elapsedInput) elapsedInput.value = "";
      populateManualBoatOptions();
    }

    setWorkflowRaceId(raceId);
    if (title) title.textContent = `Race Edit Workflow — Race #${raceNo || raceId}`;
    if (meta) meta.textContent = `Race ID ${raceId}`;
    if (hint) hint.classList.add("hidden");
    if (panel) panel.classList.remove("hidden");
    panel?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function closeRaceEditWorkflow() {
    const panel = document.getElementById("raceEditWorkflow");
    const hint = document.getElementById("raceWorkflowHint");
    if (panel) panel.classList.add("hidden");
    if (hint) hint.classList.remove("hidden");
  }

  function renderRaceQueueRows(races, showApproved) {
    const rows = document.getElementById("raceQueueRows");
    if (!rows) return;
    rows.innerHTML = races.map((r) => {
      const selectCell = showApproved
        ? '<span class="muted">—</span>'
        : `<input type="checkbox" name="raceSelect" value="${esc(r.race_id)}">`;

      const editAction = showApproved
        ? ""
        : `<button class="dash-nav-btn" type="button" style="padding:3px 8px;" data-edit-race="${esc(r.race_id)}" data-edit-race-no="${esc(r.race_no)}">Edit</button>`;

      return `
      <tr>
        <td>${selectCell}</td>
        <td>#${esc(r.race_no)}</td>
        <td>${esc(r.series_name)}</td>
        <td>${fmtDateTime(r.started_at)}</td>
        <td>${esc(r.results_status || "draft")}</td>
        <td>${esc(r.entry_count ?? "")}</td>
        <td>${esc(r.finish_count ?? "")}</td>
        <td style="white-space:nowrap;">
          <a href="/race_summary?race_id=${encodeURIComponent(r.race_id)}" style="margin-right:6px;">View</a>
          ${editAction}
        </td>
      </tr>
    `;
    }).join("") || `<tr><td colspan="8" class="muted">No races found for this filter.</td></tr>`;

    rows.querySelectorAll("button[data-edit-race]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const raceId = btn.getAttribute("data-edit-race");
        const raceNo = btn.getAttribute("data-edit-race-no") || raceId;
        setActiveView("imports");
        openRaceEditWorkflow(raceId, raceNo);
      });
    });
  }

  async function loadRaceQueue(showApproved = false) {
    showingApprovedQueue = showApproved;
    const statusEl = document.getElementById("raceQueueStatus");
    const rows = document.getElementById("raceQueueRows");
    if (!statusEl || !rows) return;
    statusEl.textContent = "Loading race queue...";

    try {
      if (!showApproved) {
        const data = await getJson("/api/dashboard/results-review-queue");
        const races = (data.queue || []).filter((r) => isPast(r.started_at));
        renderRaceQueueRows(races, false);
        statusEl.textContent = races.length ? `Showing ${races.length} unapproved past race(s).` : "No past races are awaiting approval.";
      } else {
        const data = await getJson("/api/dashboard/race-calendar?from_date=2000-01-01&to_date=2100-01-01&limit=500");
        const races = (data.races || []).filter((r) => isPast(r.started_at) && String(r.results_status || "").toLowerCase() === "locked");
        renderRaceQueueRows(races, true);
        statusEl.textContent = races.length ? `Showing ${races.length} approved past race(s).` : "No approved races found in this range.";
      }
    } catch (e) {
      rows.innerHTML = `<tr><td colspan="8" class="muted">Failed to load races.</td></tr>`;
      statusEl.textContent = e.message || "Failed to load race queue.";
    }
  }

  async function approveSelectedRaces(e) {
    e.preventDefault();
    const form = document.getElementById("raceApprovalForm");
    const statusEl = document.getElementById("raceQueueStatus");
    if (!form || !statusEl) return;

    const selected = Array.from(form.querySelectorAll("input[name='raceSelect']:checked")).map((cb) => cb.value);
    if (!selected.length) {
      statusEl.textContent = "Select at least one race to approve.";
      return;
    }

    statusEl.textContent = `Approving ${selected.length} race(s)...`;
    let success = 0;
    let fail = 0;

    for (const raceId of selected) {
      try {
        await postJson(`/api/races/${encodeURIComponent(raceId)}/results/lock`, {});
        success += 1;
      } catch (err) {
        fail += 1;
      }
    }

    statusEl.textContent = `Approved ${success} race(s)${fail ? `, ${fail} failed` : ""}.`;
    await loadRaceQueue(false);
  }

  function populateManualSailorOptions() {
    const sailorSelect = document.getElementById("manualSailor");
    if (!sailorSelect) return;
    sailorSelect.innerHTML = '<option value="">Select sailor...</option>' + sailorDirectory.map((s) =>
      `<option value="${esc(s.sailor_id)}">${esc(s.name)}</option>`
    ).join("");
  }

  function populateManualBoatOptions() {
    const sailorSelect = document.getElementById("manualSailor");
    const boatSelect = document.getElementById("manualBoat");
    const sailNumberInput = document.getElementById("manualSailNumber");
    if (!boatSelect) return;

    const sailorId = sailorSelect?.value || "";
    const sailor = sailorDirectory.find((s) => String(s.sailor_id) === String(sailorId));
    const boats = sailor?.boats || [];

    boatSelect.innerHTML = '<option value="">Select boat...</option>' + boats.map((b) =>
      `<option value="${esc(b.boatkey || "")}" data-boat-class="${esc(b.boat_class || "")}" data-sail-number="${esc(b.sail_number || "")}" data-handicap="${esc(b.handicap || "")}">${esc(b.boat_class || "Boat")} · ${esc(b.sail_number || "No sail #")}</option>`
    ).join("");
    boatSelect.disabled = !boats.length;
    if (sailNumberInput) sailNumberInput.value = "";
  }

  async function loadSailorsBoats() {
    const data = await getJson("/api/dashboard/sailors-boats");
    const sailorsRows = document.getElementById("sailorsRows");
    const boatClassRows = document.getElementById("boatClassRows");
    sailorDirectory = data.sailors || [];
    populateManualSailorOptions();
    populateManualBoatOptions();

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
      </tr>
    `).join("") || `<tr><td colspan="5" class="muted">No races in range</td></tr>`;
  }

  async function loadReviewQueue() {
    const data = await getJson("/api/dashboard/results-review-queue");
    const rows = document.getElementById("reviewRows");
    const statusEl = document.getElementById("dashboardStatus");
    rows.innerHTML = (data.queue || []).map((r) => `
      <tr data-race-id="${esc(r.race_id)}">
        <td>#${esc(r.race_no)}</td>
        <td>${esc(r.series_name)}</td>
        <td>${fmtDateTime(r.started_at)}</td>
        <td>${esc(r.results_status || "draft")}</td>
        <td>${esc(r.entry_count)}</td>
        <td>${esc(r.finish_count)}</td>
        <td style="white-space:nowrap;">
          <a href="/race_summary?race_id=${encodeURIComponent(r.race_id)}" style="margin-right:6px;">View</a>
          <button class="dash-nav-btn" style="padding:3px 8px; margin-right:6px;" data-confirm-race="${esc(r.race_id)}">Confirm Results</button>
          <button class="dash-nav-btn" style="padding:3px 8px;" data-edit-race="${esc(r.race_id)}">Edit</button>
        </td>
      </tr>
    `).join("") || `<tr><td colspan="7" class="muted">No finished races pending review</td></tr>`;

    rows.querySelectorAll("button[data-confirm-race]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const raceId = btn.getAttribute("data-confirm-race");
        btn.disabled = true;
        btn.textContent = "Confirming\u2026";
        try {
          const res = await fetch(`/api/races/${encodeURIComponent(raceId)}/results/lock`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
          });
          const d = await res.json().catch(() => ({}));
          if (!res.ok || !d.ok) throw new Error(d.error || "Failed to confirm results");
          if (statusEl) statusEl.textContent = `Race ${raceId} results confirmed.`;
          await loadReviewQueue();
        } catch (e) {
          btn.disabled = false;
          btn.textContent = "Confirm Results";
          if (statusEl) statusEl.textContent = e.message || "Failed to confirm results.";
        }
      });
    });

    rows.querySelectorAll("button[data-edit-race]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const raceId = btn.getAttribute("data-edit-race");
        setActiveView("imports");
        openRaceEditWorkflow(raceId, raceId);
      });
    });
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

  async function loadSeriesOptions() {
    const select = document.getElementById("manualSeriesId");
    if (!select) return;
    const data = await getJson("/api/series/manage");
    const options = (data.series || []).map((s) => `<option value="${esc(s.key || s.id)}">${esc(s.name)}${s.year ? ` (${esc(s.year)})` : ""}</option>`).join("");
    select.innerHTML = `<option value="">Select series...</option>${options}`;
  }

  function setWorkflowRaceId(raceId) {
    const rid = raceId ? String(raceId) : "";
    const manual = document.getElementById("manualRaceId");
    const importRace = document.getElementById("importRaceId");
    if (manual) manual.value = rid;
    if (importRace) importRace.value = rid;
  }

  function renderManualEntries() {
    const rows = document.getElementById("manualEntryRows");
    if (!rows) return;
    const targetLaps = getManualTargetLaps();
    rows.innerHTML = manualEntries.map((e) => {
      const actualCorrected = e.corrected_time || calcCorrectedTime(e.elapsed_time, e.handicap);
      const projectedCorrected = calcProjectedTime(actualCorrected, e.lap_number || 1, targetLaps);
      return `
      <tr>
        <td>${esc(e.sailor)}</td>
        <td>${esc(e.boat)}</td>
        <td>${esc(e.sailNumber)}</td>
        <td>${esc(e.lap_number || 1)}</td>
        <td class="mono">${esc(e.elapsed_time || "")}</td>
        <td class="mono">${esc(projectedCorrected || actualCorrected || "")}</td>
      </tr>
    `;
    }).join("") || `<tr><td colspan="6" class="muted">No manual rows added yet</td></tr>`;
  }

  function addManualEntry() {
    const sailorSelect = document.getElementById("manualSailor");
    const boatSelect = document.getElementById("manualBoat");
    const sailor = sailorSelect?.options[sailorSelect.selectedIndex]?.text || "";
    const boat = boatSelect?.options[boatSelect.selectedIndex]?.dataset?.boatClass || "";
    const boatkey = boatSelect?.value || "";
    const handicapRaw = boatSelect?.options[boatSelect.selectedIndex]?.dataset?.handicap || "";
    const sailNumber = (document.getElementById("manualSailNumber").value || "").trim();
    const lapsRaw = (document.getElementById("manualLaps").value || "1").trim();
    const elapsed = (document.getElementById("manualElapsed").value || "").trim();
    const status = document.getElementById("manualImportStatus");
    const lapNumber = Number(lapsRaw || 1);

    if (!sailorSelect?.value || !boatSelect?.value || !sailNumber || !elapsed) {
      status.textContent = "Choose sailor and boat, then enter sail number, laps, and elapsed time.";
      return;
    }
    if (!Number.isInteger(lapNumber) || lapNumber < 1) {
      status.textContent = "Laps must be a whole number of 1 or more.";
      return;
    }

    const handicap = handicapRaw ? Number(handicapRaw) : undefined;
    const correctedTime = calcCorrectedTime(elapsed, handicap);

    manualEntries.push({
      sailor,
      boat,
      sailNumber,
      boatkey: boatkey ? Number(boatkey) : undefined,
      handicap,
      lap_number: lapNumber,
      elapsed_time: elapsed,
      corrected_time: correctedTime || undefined,
      dnf: false,
    });

    if (boatSelect) boatSelect.value = "";
    const sailInput = document.getElementById("manualSailNumber");
    const lapsInput = document.getElementById("manualLaps");
    const elapsedInput = document.getElementById("manualElapsed");
    if (sailInput) sailInput.value = "";
    if (lapsInput) lapsInput.value = "1";
    if (elapsedInput) elapsedInput.value = "";
    status.textContent = `${manualEntries.length} manual row(s) ready.`;
    renderManualEntries();
  }

  async function saveManualRace() {
    const status = document.getElementById("manualImportStatus");
    if (!manualEntries.length) {
      status.textContent = "Add at least one row first.";
      return;
    }

    const raceId = (document.getElementById("manualRaceId")?.value || "").trim();
    if (!raceId) {
      status.textContent = "Open a pending race with Edit first.";
      return;
    }

    try {
      await postJson(`/api/races/${encodeURIComponent(raceId)}/retrospective/draft`, {
        entries: manualEntries,
        replace_existing: true,
        reason: "Manual hand-captured race entry",
      });

      status.textContent = `Saved ${manualEntries.length} row(s) to race ${raceId}.`;
      setWorkflowRaceId(raceId);
      await loadRaceQueue(showingApprovedQueue);
    } catch (e) {
      status.textContent = e.message || "Failed to save manual race.";
    }
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
    await loadRaceQueue(showingApprovedQueue);
  }


  // --- Navigation and event wiring ---
  document.querySelectorAll(".dash-nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => setActiveView(btn.getAttribute("data-view")));
  });

  // Race Queue controls
  document.getElementById("manualSailor")?.addEventListener("change", () => {
    populateManualBoatOptions();
  });
  document.getElementById("manualBoat")?.addEventListener("change", (e) => {
    const sailNumber = e.target?.options?.[e.target.selectedIndex]?.dataset?.sailNumber || "";
    const sailInput = document.getElementById("manualSailNumber");
    if (sailInput && sailNumber) sailInput.value = sailNumber;
  });

  document.getElementById("showUnapprovedRacesBtn")?.addEventListener("click", () => {
    closeRaceEditWorkflow();
    loadRaceQueue(false);
  });
  document.getElementById("showApprovedRacesBtn")?.addEventListener("click", () => {
    closeRaceEditWorkflow();
    loadRaceQueue(true);
  });
  document.getElementById("closeRaceEditBtn")?.addEventListener("click", closeRaceEditWorkflow);
  document.getElementById("raceApprovalForm")?.addEventListener("submit", approveSelectedRaces);

  // ...existing event wiring...
  document.getElementById("reloadCalendar")?.addEventListener("click", loadCalendar);
  document.getElementById("exportResultsBtn")?.addEventListener("click", exportResults);
  document.getElementById("previewImportBtn")?.addEventListener("click", previewImport);
  document.getElementById("applyImportBtn")?.addEventListener("click", applyImport);
  document.getElementById("addManualEntryBtn")?.addEventListener("click", addManualEntry);
  document.getElementById("saveManualRaceBtn")?.addEventListener("click", saveManualRace);
  document.getElementById("clearManualEntriesBtn")?.addEventListener("click", () => {
    manualEntries.length = 0;
    document.getElementById("manualImportStatus").textContent = "Manual rows cleared.";
    renderManualEntries();
  });

  (async function init() {
    const errors = [];

    const tasks = [
      { run: loadSailorsBoats, fallback: () => {
          setTableFallback("sailorsRows", 2, "Unable to load sailors right now.");
          setTableFallback("boatClassRows", 3, "Unable to load boat classes right now.");
        }
      },
      { run: loadCalendar, fallback: () => setTableFallback("calendarRows", 5, "Unable to load race calendar right now.") },
      { run: loadRaceQueue, fallback: () => setTableFallback("raceQueueRows", 8, "Unable to load race queue right now.") },
      { run: loadHandicapRecommendations, fallback: () => setTableFallback("handicapRows", 6, "Unable to load handicap recommendations right now.") },
      { run: loadSeriesOptions },
    ];

    for (const task of tasks) {
      try {
        await task.run();
      } catch (e) {
        errors.push(e?.message || "Request failed");
        if (task.fallback) task.fallback();
      }
    }

    if (errors.length) {
      setDashboardStatus("Some dashboard data is temporarily unavailable. You can keep working and retry specific sections.");
    } else {
      setDashboardStatus("");
    }

    renderManualEntries();
    if (typeof applyMobileModeForSelects === "function") {
      applyMobileModeForSelects("dutyRoleCode", "dutyStatus", "dutyMobileFirst", "dutyEligibilityHint");
    }
    if (typeof updateDutyEligibilityHint === "function") {
      updateDutyEligibilityHint();
    }
  })();
})();
