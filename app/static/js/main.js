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

// =========================
// Create Dependent Dropdown
// =========================

/**
 * parentSelector:   "#clubName"
 * childSelector:    "#seriesName"
 * config = {
 *    url: (parentValue) => `/api/.../${parentValue}`,
 *    extract: (data) => data.series   // array
 *    valueField: "id",
 *    labelField: "name",
 *    placeholder: "Select a series…"
 * }
 */
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
                value: obj[config.valueField],
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
            value: obj[config.valueField],
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

