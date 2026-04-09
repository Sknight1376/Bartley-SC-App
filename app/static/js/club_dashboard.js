(function () {
  const views = ["sailors", "calendar", "duties", "review", "handicap", "exports", "imports"];
  const manualEntries = [];
  let dutyMembers = [];
  let dutyAssignableRaces = [];
  let dutyRosterRows = [];
  let pendingDutyAssignment = null;

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

  function normalizeRoleCode(value) {
    const v = String(value || "").trim().toLowerCase();
    return v || "race_officer";
  }

  function roleLabel(value) {
    const code = normalizeRoleCode(value);
    const labels = {
      race_officer: "Race Officer",
      assistant_race_officer: "Assistant Race Officer",
      timekeeper: "Timekeeper",
      safety_officer: "Safety Officer",
      mark_layer: "Mark Layer",
    };
    return labels[code] || code.replaceAll("_", " ");
  }

  function isMobileEligible(roleCode, status) {
    return normalizeRoleCode(roleCode) === "race_officer" && String(status || "").toLowerCase() === "assigned";
  }

  function mobileChip(roleCode, status) {
    if (isMobileEligible(roleCode, status)) {
      return '<span class="duty-chip duty-chip-mobile-ok">Mobile Enabled</span>';
    }
    return '<span class="duty-chip duty-chip-mobile-warn">Not Mobile Enabled</span>';
  }

  function statusChip(status) {
    const s = String(status || "assigned").toLowerCase();
    const cls = s === "confirmed" ? "duty-chip-confirmed" : s === "completed" ? "duty-chip-completed" : "duty-chip-assigned";
    return `<span class="duty-chip ${cls}">${esc(s)}</span>`;
  }

  function raceTimingHint(startedAt) {
    if (!startedAt) return "No scheduled start";
    const start = new Date(startedAt);
    if (Number.isNaN(start.getTime())) return "";
    const now = new Date();
    const diffMs = start.getTime() - now.getTime();
    const absMin = Math.round(Math.abs(diffMs) / 60000);
    const hours = Math.floor(absMin / 60);
    const minutes = absMin % 60;
    const part = hours ? `${hours}h ${minutes}m` : `${minutes}m`;
    if (diffMs > 0) return `Starts in ${part}`;
    if (diffMs < 0) return `Started ${part} ago`;
    return "Starting now";
  }

  function setDutyStatus(message, level = "info") {
    const node = document.getElementById("dutyStatusMessage");
    if (!node) return;
    node.textContent = message || "";
    node.style.color = level === "error" ? "#991b1b" : level === "success" ? "#166534" : "#6b7280";
  }

  function openDutyConflictModal() {
    const modal = document.getElementById("dutyConflictModal");
    if (modal) modal.classList.add("open");
  }

  function closeDutyConflictModal() {
    const modal = document.getElementById("dutyConflictModal");
    if (modal) modal.classList.remove("open");
    pendingDutyAssignment = null;
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
      </tr>
    `).join("") || `<tr><td colspan="5" class="muted">No races in range</td></tr>`;
  }

  function renderDutyCoverageSnapshot() {
    const tbody = document.getElementById("dutyUnassignedRows");
    if (!tbody) return;

    const filterCoverage = (document.getElementById("dutyFilterCoverage")?.value || "all").trim();
    const coveredRaceIds = new Set(
      dutyRosterRows
        .filter((d) => normalizeRoleCode(d.role_code || d.duty_type) === "race_officer" && ["assigned", "confirmed"].includes(String(d.status || "").toLowerCase()))
        .map((d) => String(d.race_id))
    );

    const rows = dutyAssignableRaces
      .map((r) => {
        const covered = coveredRaceIds.has(String(r.race_id));
        return { ...r, covered };
      })
      .filter((r) => filterCoverage === "all" || (filterCoverage === "covered" ? r.covered : !r.covered));

    tbody.innerHTML = rows.map((r) => `
      <tr>
        <td>#${esc(r.race_no)}</td>
        <td>${esc(r.series_name)}</td>
        <td>${fmtDateTime(r.started_at)}<div class="duty-inline-note">${esc(raceTimingHint(r.started_at))}</div></td>
        <td>${r.covered ? '<span class="duty-chip duty-chip-confirmed">Covered</span>' : '<span class="duty-chip duty-chip-mobile-warn">Needs Race Officer</span>'}</td>
        <td>
          ${r.covered ? "" : `<button class="dash-nav-btn" style="padding:4px 8px;" data-quick-assign-date="${esc(r.started_at ? r.started_at.substring(0, 10) : '')}">Assign Race Officer</button>`}
        </td>
      </tr>
    `).join("") || `<tr><td colspan="5" class="muted">No races in this coverage view.</td></tr>`;

    tbody.querySelectorAll("button[data-quick-assign-date]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const raceDate = btn.getAttribute("data-quick-assign-date");
        const dateInput = document.getElementById("dutyDate");
        const roleSelect = document.getElementById("dutyRoleCode");
        const statusSelect = document.getElementById("dutyStatus");
        if (dateInput) dateInput.value = raceDate;
        if (roleSelect) roleSelect.value = "race_officer";
        if (statusSelect) statusSelect.value = "assigned";
        applyMobileModeForSelects("dutyRoleCode", "dutyStatus", "dutyMobileFirst", "dutyEligibilityHint");
        setDutyStatus("Date selected. Choose a member and click Assign Member.");
      });
    });
  }

  function renderDutyRows() {
    const rowsNode = document.getElementById("dutyRows");
    if (!rowsNode) return;

    const filterStatus = (document.getElementById("dutyFilterStatus")?.value || "all").trim();
    const filterRole = normalizeRoleCode(document.getElementById("dutyFilterRole")?.value || "all");
    const filterSearch = (document.getElementById("dutyFilterSearch")?.value || "").trim().toLowerCase();

    const filtered = dutyRosterRows.filter((d) => {
      const statusOk = filterStatus === "all" || String(d.status || "").toLowerCase() === filterStatus;
      const roleOk = filterRole === "all" || normalizeRoleCode(d.role_code || d.duty_type) === filterRole;
      const haystack = `${d.sailor_name || ""} ${d.series_name || ""} ${d.race_no || ""} ${d.duty_type || d.role_code || ""}`.toLowerCase();
      const searchOk = !filterSearch || haystack.includes(filterSearch);
      return statusOk && roleOk && searchOk;
    });

    rowsNode.innerHTML = filtered.map((d) => {
      const roleCode = normalizeRoleCode(d.role_code || d.duty_type);
      return `
        <tr>
          <td>#${esc(d.race_no)}</td>
          <td>${esc(d.series_name)}</td>
          <td>${fmtDateTime(d.started_at)}<div class="duty-inline-note">${esc(raceTimingHint(d.started_at))}</div></td>
          <td>${esc(d.sailor_name)}</td>
          <td>${esc(roleLabel(roleCode))}</td>
          <td>${statusChip(d.status)}</td>
          <td>${mobileChip(roleCode, d.status)}</td>
          <td>
            <button class="dash-nav-btn" style="padding:4px 8px;" data-copy-duty="${esc(d.duty_id)}" data-race-no="${esc(d.race_no)}" data-series-name="${esc(d.series_name)}" data-sailor-name="${esc(d.sailor_name)}">Copy Mobile Steps</button>
            <button class="dash-nav-btn" style="padding:4px 8px; margin-left:6px;" data-delete-duty="${esc(d.duty_id)}" data-delete-race="${esc(d.race_id)}">Remove</button>
          </td>
        </tr>
      `;
    }).join("") || `<tr><td colspan="8" class="muted">No duty assignments match the current filters.</td></tr>`;

    rowsNode.querySelectorAll("button[data-delete-duty]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const dutyId = btn.getAttribute("data-delete-duty");
        const raceId = btn.getAttribute("data-delete-race");
        try {
          await deleteJson(`/api/races/${encodeURIComponent(raceId)}/duties/${encodeURIComponent(dutyId)}`);
          setDutyStatus("Duty assignment removed.", "success");
          await Promise.all([loadDuties(), loadDutyControls()]);
        } catch (e) {
          setDutyStatus(e.message || "Failed to remove duty assignment.", "error");
        }
      });
    });

    rowsNode.querySelectorAll("button[data-copy-duty]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const text = [
          `Race duty assigned: ${btn.getAttribute("data-series-name")} race #${btn.getAttribute("data-race-no")}`,
          `Member: ${btn.getAttribute("data-sailor-name")}`,
          "In the Sailor app, open Race Control > Upcoming Races to access your assigned duty race.",
        ].join("\n");
        try {
          if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(text);
            setDutyStatus("Mobile handoff steps copied to clipboard.", "success");
          } else {
            setDutyStatus(text, "info");
          }
        } catch (e) {
          setDutyStatus("Unable to copy. " + text, "info");
        }
      });
    });

    renderDutyCoverageSnapshot();
  }

  async function loadDuties() {
    const data = await getJson("/api/dashboard/duty-roster");
    dutyRosterRows = data.duties || [];
    renderDutyRows();
  }

  function populateDutyControls() {
    const dateInput = document.getElementById("dutyDate");
    const sailorSelect = document.getElementById("dutySailorId");
    if (!sailorSelect) return;

    if (dateInput && !dateInput.value) {
      const today = new Date();
      dateInput.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    }

    const sailorOptions = dutyMembers.map((m) => `<option value="${esc(m.id)}">${esc(m.full_name)}</option>`).join("");
    sailorSelect.innerHTML = `<option value="">Select member...</option>${sailorOptions}`;

    renderDutyCoverageSnapshot();
  }

  async function loadDutyControls() {
    const today = new Date();
    const fromDate = new Date(today);
    fromDate.setDate(fromDate.getDate() - 14);
    const toDate = new Date(today);
    toDate.setDate(toDate.getDate() + 120);
    const toIso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    const qs = new URLSearchParams({ from_date: toIso(fromDate), to_date: toIso(toDate) });

    const [calendarData, membersData] = await Promise.all([
      getJson(`/api/dashboard/race-calendar?${qs.toString()}`),
      getJson("/api/members"),
    ]);

    dutyAssignableRaces = (calendarData.races || []).map((r) => ({
      race_id: r.race_id,
      race_no: r.race_no,
      series_name: r.series_name,
      started_at: r.started_at,
    }));
    dutyMembers = (membersData.members || []).slice().sort((a, b) => String(a.full_name || "").localeCompare(String(b.full_name || "")));
    populateDutyControls();
    renderDutyCoverageSnapshot();
  }

  function updateDutyEligibilityHint() {
    const node = document.getElementById("dutyEligibilityHint");
    if (!node) return;
    const roleCode = (document.getElementById("dutyRoleCode")?.value || "race_officer").trim();
    const status = (document.getElementById("dutyStatus")?.value || "assigned").trim();
    if (isMobileEligible(roleCode, status)) {
      node.innerHTML = 'This assignment will <strong>enable mobile race control access</strong> for the selected member.';
      node.style.color = "#166534";
    } else {
      node.innerHTML = 'Mobile control access requires <strong>Race Officer</strong> role with <strong>Assigned</strong> status.';
      node.style.color = "#92400e";
    }
  }

  function applyMobileModeForSelects(roleSelectId, statusSelectId, modeToggleId, hintId) {
    const roleSelect = document.getElementById(roleSelectId);
    const statusSelect = document.getElementById(statusSelectId);
    const modeToggle = document.getElementById(modeToggleId);
    const hintNode = hintId ? document.getElementById(hintId) : null;
    if (!roleSelect || !statusSelect || !modeToggle) return;

    const mobileMode = !!modeToggle.checked;

    Array.from(roleSelect.options).forEach((opt) => {
      opt.disabled = mobileMode && String(opt.value) !== "race_officer";
    });
    Array.from(statusSelect.options).forEach((opt) => {
      opt.disabled = mobileMode && String(opt.value) !== "assigned";
    });

    if (mobileMode) {
      roleSelect.value = "race_officer";
      statusSelect.value = "assigned";
      if (hintNode) {
        hintNode.innerHTML = 'Mobile-enabled mode is ON. Role/status are locked to <strong>Race Officer</strong> and <strong>Assigned</strong>.';
        hintNode.style.color = "#166534";
      }
    } else if (hintNode) {
      const roleCode = (roleSelect.value || "").trim();
      const statusValue = (statusSelect.value || "").trim();
      if (isMobileEligible(roleCode, statusValue)) {
        hintNode.innerHTML = 'This assignment will <strong>enable mobile race control access</strong> for the selected member.';
        hintNode.style.color = "#166534";
      } else {
        hintNode.innerHTML = 'Mobile control access requires <strong>Race Officer</strong> role with <strong>Assigned</strong> status.';
        hintNode.style.color = "#92400e";
      }
    }
  }

  function getDutyConflicts(date, sailorId) {
    const conflicts = [];
    dutyRosterRows
      .filter((d) => String(d.sailor) === String(sailorId) && d.started_at && d.started_at.substring(0, 10) === date)
      .forEach((d) => {
        conflicts.push({
          type: "Same-day assignment",
          race_no: d.race_no,
          series_name: d.series_name,
          started_at: d.started_at,
          status: d.status,
          duty: roleLabel(d.role_code || d.duty_type),
        });
      });
    return conflicts;
  }

  function showDutyConflicts(conflicts, date, sailorId) {
    const tbody = document.getElementById("dutyConflictRows");
    const intro = document.getElementById("dutyConflictIntro");
    const sailor = dutyMembers.find((m) => String(m.id) === String(sailorId));
    if (!tbody || !intro) return;

    intro.textContent = `Review ${conflicts.length} potential conflict(s) before assigning ${sailor?.full_name || "this member"} to all races on ${date}.`;
    tbody.innerHTML = conflicts.map((c) => `
      <tr>
        <td>${esc(c.type)}</td>
        <td>#${esc(c.race_no || "-")}</td>
        <td>${esc(c.series_name || "-")}</td>
        <td>${fmtDateTime(c.started_at)}</td>
        <td>${statusChip(c.status)}</td>
        <td>${esc(c.duty || "-")}</td>
      </tr>
    `).join("");

    openDutyConflictModal();
  }

  async function submitDutyAssignment(payload) {
    await postJson(`/api/races/duties/by-date`, {
      sailor_id: Number(payload.sailorId),
      role_code: payload.roleCode,
      duty_type: payload.roleCode,
      status: payload.statusValue,
      date: payload.date,
    });

    setDutyStatus(
      isMobileEligible(payload.roleCode, payload.statusValue)
        ? `Duty assignment saved for all races on ${payload.date} and mobile control access is enabled.`
        : `Duty assignment saved for all races on ${payload.date}. This role/status will not unlock mobile race control.`,
      "success"
    );

    await Promise.all([loadDuties(), loadDutyControls()]);
  }

  async function assignDuty() {
    const date = (document.getElementById("dutyDate")?.value || "").trim();
    const sailorId = (document.getElementById("dutySailorId")?.value || "").trim();
    const roleCode = (document.getElementById("dutyRoleCode")?.value || "race_officer").trim();
    const statusValue = (document.getElementById("dutyStatus")?.value || "assigned").trim();
    if (!date || !sailorId) {
      setDutyStatus("Select a date and member before assigning duty.", "error");
      return;
    }

    const conflicts = getDutyConflicts(date, sailorId);
    if (conflicts.length) {
      pendingDutyAssignment = { date, sailorId, roleCode, statusValue };
      showDutyConflicts(conflicts, date, sailorId);
      setDutyStatus("Potential conflicts found. Review and confirm to continue.", "error");
      return;
    }

    try {
      await submitDutyAssignment({ date, sailorId, roleCode, statusValue });
    } catch (e) {
      setDutyStatus(e.message || "Failed to assign duty.", "error");
    }
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
        setWorkflowRaceId(raceId);
        previewRetrospective();
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
    const retrospectiveSeries = document.getElementById("retrospectiveSeries");
    if (!select) return;
    const data = await getJson("/api/series/manage");
    const options = (data.series || []).map((s) => `<option value="${esc(s.key || s.id)}">${esc(s.name)}${s.year ? ` (${esc(s.year)})` : ""}</option>`).join("");
    select.innerHTML = `<option value="">Select series...</option>${options}`;
    if (retrospectiveSeries) {
      retrospectiveSeries.innerHTML = `<option value="">All series</option>${options}`;
    }
  }

  function setWorkflowRaceId(raceId) {
    const rid = raceId ? String(raceId) : "";
    const workflow = document.getElementById("workflowRaceId");
    const manual = document.getElementById("manualRaceId");
    const importRace = document.getElementById("importRaceId");
    if (workflow) workflow.value = rid;
    if (manual) manual.value = rid;
    if (importRace) importRace.value = rid;
  }

  async function loadRetrospectiveRaces() {
    const status = document.getElementById("retrospectiveStatus");
    const rows = document.getElementById("retrospectiveRows");
    const from = document.getElementById("retrospectiveFrom")?.value || "";
    const to = document.getElementById("retrospectiveTo")?.value || "";
    const seriesId = document.getElementById("retrospectiveSeries")?.value || "";

    const qs = new URLSearchParams();
    if (from) qs.set("from_date", from);
    if (to) qs.set("to_date", to);
    if (seriesId) qs.set("series_id", seriesId);

    try {
      const data = await getJson(`/api/races/retrospective?${qs.toString()}`);
      rows.innerHTML = (data.races || []).map((r) => `
        <tr>
          <td>${esc(r.key)}</td>
          <td>${esc(r.series_name || r.series || "")}</td>
          <td>#${esc(r.race_no)}</td>
          <td>${fmtDateTime(r.started_at)}</td>
          <td>${esc(r.status)}</td>
          <td>${esc(r.results_status || "draft")}</td>
          <td>${esc(r.source_mode || "retrospective")}</td>
          <td>
            <button class="dash-nav-btn" style="padding:4px 8px;" data-select-race="${esc(r.key)}">Select</button>
            <a href="/race_summary?race_id=${encodeURIComponent(r.key)}" style="margin-left:6px;">Summary</a>
            <a href="/api/races/${encodeURIComponent(r.key)}/audit" style="margin-left:6px;">Audit</a>
            <a href="/api/races/${encodeURIComponent(r.key)}/revisions" style="margin-left:6px;">Revisions</a>
          </td>
        </tr>
      `).join("") || `<tr><td colspan="8" class="muted">No retrospective races found for this filter.</td></tr>`;

      rows.querySelectorAll("button[data-select-race]").forEach((btn) => {
        btn.addEventListener("click", () => {
          setWorkflowRaceId(btn.getAttribute("data-select-race"));
          status.textContent = `Selected race ${btn.getAttribute("data-select-race")}.`;
        });
      });

      status.textContent = `Loaded ${(data.races || []).length} retrospective race(s).`;
    } catch (e) {
      rows.innerHTML = `<tr><td colspan="8" class="muted">Failed to load races.</td></tr>`;
      status.textContent = e.message || "Failed to load retrospective races.";
    }
  }

  async function previewRetrospective() {
    const raceId = (document.getElementById("workflowRaceId")?.value || "").trim();
    const status = document.getElementById("retrospectiveStatus");
    const rows = document.getElementById("retrospectivePreviewRows");

    if (!raceId) {
      status.textContent = "Select a race first.";
      return;
    }

    try {
      const data = await getJson(`/api/races/${encodeURIComponent(raceId)}/retrospective/preview`);
      rows.innerHTML = (data.results || []).map((e) => `
        <tr>
          <td>${esc(e.sailor)}</td>
          <td>${esc(e.boat)}</td>
          <td>${esc(e.sail_number)}</td>
          <td class="mono">${esc(e.elapsed_time || "")}</td>
          <td class="mono">${esc(e.corrected_time || "")}</td>
          <td>${esc(e.position || "")}</td>
          <td>${e.dnf ? "YES" : ""}</td>
        </tr>
      `).join("") || `<tr><td colspan="7" class="muted">No results in draft for this race.</td></tr>`;
      status.textContent = `Preview loaded for race ${raceId}. Results status: ${data.race?.results_status || "draft"}.`;
    } catch (e) {
      rows.innerHTML = `<tr><td colspan="7" class="muted">Preview failed.</td></tr>`;
      status.textContent = e.message || "Failed to preview retrospective results.";
    }
  }

  async function publishRetrospective() {
    const raceId = (document.getElementById("workflowRaceId")?.value || "").trim();
    const status = document.getElementById("retrospectiveStatus");
    if (!raceId) {
      status.textContent = "Select a race first.";
      return;
    }

    try {
      await postJson(`/api/races/${encodeURIComponent(raceId)}/results/publish`, {
        reason: "Approved and published from Club Dashboard retrospective workflow",
      });
      status.textContent = `Race ${raceId} published successfully.`;
      await loadRetrospectiveRaces();
      await previewRetrospective();
    } catch (e) {
      status.textContent = e.message || "Failed to publish results.";
    }
  }

  function renderManualEntries() {
    const rows = document.getElementById("manualEntryRows");
    if (!rows) return;
    rows.innerHTML = manualEntries.map((e) => `
      <tr>
        <td>${esc(e.sailor)}</td>
        <td>${esc(e.boat)}</td>
        <td>${esc(e.sailNumber)}</td>
        <td>${esc(e.handicap || "")}</td>
        <td class="mono">${esc(e.elapsed_time || "")}</td>
        <td class="mono">${esc(e.corrected_time || "")}</td>
        <td>${esc(e.position || "")}</td>
        <td>${e.dnf ? "YES" : ""}</td>
      </tr>
    `).join("") || `<tr><td colspan="8" class="muted">No manual rows added yet</td></tr>`;
  }

  function addManualEntry() {
    const sailor = (document.getElementById("manualSailor").value || "").trim();
    const boat = (document.getElementById("manualBoat").value || "").trim();
    const sailNumber = (document.getElementById("manualSailNumber").value || "").trim();
    const handicap = (document.getElementById("manualHandicap").value || "").trim();
    const elapsed = (document.getElementById("manualElapsed").value || "").trim();
    const corrected = (document.getElementById("manualCorrected").value || "").trim();
    const position = (document.getElementById("manualPosition").value || "").trim();
    const dnf = document.getElementById("manualDnf").checked;
    const status = document.getElementById("manualImportStatus");

    if (!sailor || !boat || !sailNumber) {
      status.textContent = "Sailor, boat, and sail number are required.";
      return;
    }

    manualEntries.push({
      sailor,
      boat,
      sailNumber,
      handicap: handicap ? Number(handicap) : undefined,
      elapsed_time: elapsed || undefined,
      corrected_time: corrected || undefined,
      position: position ? Number(position) : undefined,
      dnf,
    });

    ["manualSailor", "manualBoat", "manualSailNumber", "manualHandicap", "manualElapsed", "manualCorrected", "manualPosition"].forEach((id) => {
      document.getElementById(id).value = "";
    });
    document.getElementById("manualDnf").checked = false;
    status.textContent = `${manualEntries.length} manual row(s) ready.`;
    renderManualEntries();
  }

  async function saveManualRace() {
    const status = document.getElementById("manualImportStatus");
    if (!manualEntries.length) {
      status.textContent = "Add at least one row first.";
      return;
    }

    const existingRaceId = (document.getElementById("manualRaceId").value || "").trim();
    let raceId = existingRaceId;

    try {
      if (!raceId) {
        const seriesId = (document.getElementById("manualSeriesId").value || "").trim();
        const raceNo = (document.getElementById("manualRaceNo").value || "").trim();
        const startedAt = (document.getElementById("manualStartedAt").value || "").trim();
        const endedAt = (document.getElementById("manualEndedAt").value || "").trim();

        if (!seriesId || !startedAt) {
          status.textContent = "Select a series and start time, or provide an existing race ID.";
          return;
        }

        const createPayload = {
          series_id: Number(seriesId),
          race_no: raceNo ? Number(raceNo) : undefined,
          started_at: startedAt,
          ended_at: endedAt || startedAt,
          reason: "Manual hand-captured race entry",
        };

        const created = await postJson("/api/races/retrospective", createPayload);
        raceId = created.race_id;
      }

      await postJson(`/api/races/${encodeURIComponent(raceId)}/retrospective/draft`, {
        entries: manualEntries,
        replace_existing: true,
        reason: "Manual hand-captured race entry",
      });

      status.textContent = `Saved ${manualEntries.length} row(s) to race ${raceId}.`;
      setWorkflowRaceId(raceId);
      await loadRetrospectiveRaces();
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
  }

  document.querySelectorAll(".dash-nav-btn[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => setActiveView(btn.getAttribute("data-view")));
  });

  document.getElementById("reloadCalendar").addEventListener("click", loadCalendar);
  document.getElementById("exportResultsBtn").addEventListener("click", exportResults);
  document.getElementById("previewImportBtn").addEventListener("click", previewImport);
  document.getElementById("applyImportBtn").addEventListener("click", applyImport);
  document.getElementById("addManualEntryBtn")?.addEventListener("click", addManualEntry);
  document.getElementById("saveManualRaceBtn")?.addEventListener("click", saveManualRace);
  document.getElementById("reloadRetrospectiveBtn")?.addEventListener("click", loadRetrospectiveRaces);
  document.getElementById("previewRetrospectiveBtn")?.addEventListener("click", previewRetrospective);
  document.getElementById("publishRetrospectiveBtn")?.addEventListener("click", publishRetrospective);
  document.getElementById("assignDutyBtn")?.addEventListener("click", assignDuty);
  document.getElementById("dutyRoleCode")?.addEventListener("change", updateDutyEligibilityHint);
  document.getElementById("dutyStatus")?.addEventListener("change", updateDutyEligibilityHint);
  document.getElementById("dutyMobileFirst")?.addEventListener("change", () => {
    applyMobileModeForSelects("dutyRoleCode", "dutyStatus", "dutyMobileFirst", "dutyEligibilityHint");
    updateDutyEligibilityHint();
  });
  document.getElementById("dutyConflictCloseBtn")?.addEventListener("click", closeDutyConflictModal);
  document.getElementById("dutyConflictCancelBtn")?.addEventListener("click", closeDutyConflictModal);
  document.getElementById("dutyConflictConfirmBtn")?.addEventListener("click", async () => {
    if (!pendingDutyAssignment) return;
    try {
      await submitDutyAssignment(pendingDutyAssignment);
      closeDutyConflictModal();
    } catch (e) {
      setDutyStatus(e.message || "Failed to assign duty.", "error");
    }
  });
  document.getElementById("dutyFilterStatus")?.addEventListener("change", renderDutyRows);
  document.getElementById("dutyFilterRole")?.addEventListener("change", renderDutyRows);
  document.getElementById("dutyFilterCoverage")?.addEventListener("change", renderDutyRows);
  document.getElementById("dutyFilterSearch")?.addEventListener("input", renderDutyRows);
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
      { run: loadDuties, fallback: () => setTableFallback("dutyRows", 8, "Unable to load duty roster right now.") },
      { run: loadDutyControls },
      { run: loadReviewQueue, fallback: () => setTableFallback("reviewRows", 7, "Unable to load review queue right now.") },
      { run: loadHandicapRecommendations, fallback: () => setTableFallback("handicapRows", 6, "Unable to load handicap recommendations right now.") },
      { run: loadSeriesOptions },
      { run: loadRetrospectiveRaces, fallback: () => setTableFallback("retrospectiveRows", 8, "Unable to load retrospective races right now.") },
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
    applyMobileModeForSelects("dutyRoleCode", "dutyStatus", "dutyMobileFirst", "dutyEligibilityHint");
    updateDutyEligibilityHint();
  })();
})();
