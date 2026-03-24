// =========================
// Generic Fetch + Map
// =========================

async function fetchOptions(url, mapFn) {
    try {
        const res = await fetch(url, { cache: "no-store" });
        const data = await res.json();
        return mapFn(data);
    } catch (err) {
        console.error(`Error fetching ${url}:`, err);
        return [];
    }
}


// =========================
// --- helper to normalize values ---
// If value is an object, store as JSON string; else store as-is
// =========================
function normalizeValueForOption(v) {
  return (v !== null && typeof v === 'object') ? JSON.stringify(v) : String(v ?? '');
}

// =========================
// Generic Select Populator
// =========================

function populateSelect(selectEl, items, placeholder) {
    if (!selectEl) return;

    selectEl.innerHTML = "";

    // Add placeholder (enabled so it displays fully)
    if (placeholder) {
        const ph = document.createElement("option");
        ph.value = "";
        ph.textContent = placeholder;
        ph.selected = true;
        selectEl.appendChild(ph);
    }

    // Add real options
    items.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item.value;
        opt.textContent = item.label;
        selectEl.appendChild(opt);
    });
}

function createDependentDropdown(parentSelector, childSelector, config) {
    const parentSelect = document.querySelector(parentSelector);
    const childSelect  = document.querySelector(childSelector);

    if (!parentSelect || !childSelect) return;

    // Reset child
    populateSelect(childSelect, [], config.placeholder || "Select an option…");
    childSelect.disabled = true;

    parentSelect.addEventListener("change", async () => {
        const parentValue = parentSelect.value;

        if (!parentValue) {
            populateSelect(childSelect, [], config.placeholder);
            childSelect.disabled = true;
            return;
        }

        // Build API URL
        const url = config.url(parentValue);

        const items = await fetchOptions(url, (data) => {
            const arr = config.extract(data);
            
            return arr.map(obj => ({
            value: normalizeValueForOption(obj[config.valueField]),
            label: obj[config.labelField]
            }));

        });

        populateSelect(childSelect, items, config.placeholder);
        childSelect.disabled = false;
    });
}

// =========================
// Initial Loaders
// =========================

async function loadPrimaryDropdown(selector, url, extractFn, config = {}) {
    const select = document.querySelector(selector);
    if (!select) return;

    const items = await fetchOptions(url, (data) => {
        const arr = extractFn(data);
        return arr.map(obj => ({
        value: normalizeValueForOption(obj[config.valueField]),
        label: obj[config.labelField]
        }));

    });

    populateSelect(select, items, config.placeholder);
    select.disabled = false;
}

// =========================
// Next Button
// =========================


function enableButtonWhenAllSelected(buttonSelector, requiredSelectSelectors) {
    const button = document.querySelector(buttonSelector);
    const selects = requiredSelectSelectors.map(sel => document.querySelector(sel));

    function updateState() {
        const allSelected = selects.every(sel => sel && sel.value && sel.value.trim() !== "");
        button.disabled = !allSelected;
    }

    // Attach listeners
    selects.forEach(sel => {
        if (sel) sel.addEventListener("change", updateState);
    });

    // Initial check
    updateState();
}



// =========================
// Summary Button (sailor_entry only)
// =========================
document.addEventListener('DOMContentLoaded', () => {
  const summaryBtn = document.getElementById('summaryButton');
  if (!summaryBtn) return; // not on sailor_entry page

  function collectEntriesFromTable() {
    const rows = Array.from(document.querySelectorAll('#entries-table tbody tr'));
    return rows.map(tr => {
      const cells = tr.querySelectorAll('td');
      return {
        sailor: (cells[0]?.textContent || '').trim(),
        boat: (cells[1]?.textContent || '').trim(),
        sailNumber: (cells[2]?.textContent || '').trim(),
        // if you later add a 4th “Key” column, read it here:
        // key: (cells[3]?.textContent || '').trim()
      };
    }).filter(e => e.sailor && e.boat && e.sailNumber /* && e.key*/);
  }

  async function postEntries(entries) {
    const res = await fetch('/api/entries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
      body: JSON.stringify({ entries })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Server error: ${res.status}`);
    }
    return res.json();
  }

  summaryBtn.addEventListener('click', async () => {
    const entries = collectEntriesFromTable();
    if (!entries.length) {
      alert('Please add at least one entry before continuing.');
      return;
    }
    try {
      await postEntries(entries);
      window.location.href = '/summary';
    } catch (e) {
      console.error('Failed to submit entries:', e);
      alert(e.message || 'Failed to submit entries.');
    }
  });
});