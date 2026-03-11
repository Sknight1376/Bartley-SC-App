// renders.js

function isFinished($row) {
  return $row.attr("data-finished") === "1";
}

function lockRow($row) {
  $row.attr("data-finished", "1");
  $row.addClass("finished");
  $row.find(".lap_btn, .finish_btn").prop("disabled", true);
}

function appendentriesFunction(boatName, sailNo, boatId) {
  const safeSail = String(sailNo).replace(/\W+/g, "_");
  const rowId = `entry_${boatId}_${safeSail}`;

  if (document.getElementById(rowId)) return;

  $("#entries tbody").append(`
    <tr id="${rowId}" data-boat-id="${boatId}" data-sail="${sailNo}" data-lap="0">
      <td class="control"><button type="button" class="control_button lap_btn">Lap</button></td>
      <td class="control"><button type="button" class="control_button finish_btn">Finish</button></td>
      <td>${boatName}</td>
      <td>${sailNo}</td>
    </tr>
  `);

  const $row = $(`#${rowId}`);
  $row.find(".lap_btn").on("click", () => recordLapOrFinish($row, "Lap"));
  $row.find(".finish_btn").on("click", () => recordLapOrFinish($row, "Finish"));
}

function ensureHeaders(label) {
  const exists = $("#headers th").filter(function () {
    return $(this).text() === label;
  }).length > 0;

  if (exists) return;

  $("#headers").append(`<th>${label}</th>`);
  $("#headers").append(`<th>${label} Corrected</th>`);
}

function recordLapOrFinish($row, eventType) {
  if (isFinished($row)) return;

  const boatId = Number($row.data("boat-id"));
  const sail = String($row.data("sail"));

  const elapsed = $("#Elapsed_Time").text();
  if (!elapsed || elapsed.trim() === "") {
    alert("Race has not started yet.");
    return;
  }

  const clubName = sessionStorage.getItem("clubName") || "";
  const seriesName = sessionStorage.getItem("seriesName") || "";
  const raceNo = sessionStorage.getItem("raceNo") || "";

  if (!clubName || !seriesName || !raceNo) {
    alert("Missing setup data. Reset and set up race again.");
    return;
  }

  // lap numbering per boat row
  let label = "Final";
  if (eventType === "Lap") {
    const currentLap = Number($row.attr("data-lap") || 0) + 1;
    $row.attr("data-lap", currentLap);
    label = `Lap ${currentLap}`;
  }

  ensureHeaders(label);

  $.post("/times", {
    boat_id: boatId,
    sail: sail,
    elapsed: elapsed,
    split: timeFunction(),
    club_name: clubName,
    series_name: seriesName,
    race: Number(raceNo),
    event_type: eventType
  })
  .done((data) => {
    $row.append(`<td>${elapsed}</td>`);
    $row.append(`<td>${data.corrected_time}</td>`);

    if (eventType === "Finish") {
      lockRow($row);
    }
  })
  .fail((xhr) => {
    console.error("POST /times failed:", xhr.responseText);
    alert("Failed to calculate/save time.");
  });
}
