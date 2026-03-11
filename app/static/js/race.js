// main.js (Race page only)

document.addEventListener("DOMContentLoaded", () => {
  clock("clock"); // from time_functions.js [4](https://nhbc2-my.sharepoint.com/personal/sjknight_nhbc_co_uk/Documents/Microsoft%20Copilot%20Chat%20Files/summary.html)

  // Hide controls until the race starts
  $(".control").hide();
  $("#entries").hide();

  // Pull setup data from sessionStorage
  const clubName = sessionStorage.getItem("clubName") || "";
  const seriesName = sessionStorage.getItem("seriesName") || "";
  const raceNo = sessionStorage.getItem("raceNo") || "";
  const entriesRaw = sessionStorage.getItem("entries") || "[]";

  let entries = [];
  try {
    entries = JSON.parse(entriesRaw);
  } catch (e) {
    console.error("Bad entries JSON in sessionStorage:", entriesRaw);
  }

  // If anything missing, send them back to setup
  if (!clubName || !seriesName || !raceNo || entries.length === 0) {
    alert("Missing setup data (club/series/race/entries). Returning to setup.");
    window.location.href = "/";
    return;
  }

  // Populate race table
  entries.forEach(e => {
    appendentriesFunction(e.boatName, e.sailNo, e.boatId); // from renders.js [3](blob:https://outlook.office.com/d2eac566-20df-4e06-a83a-5b573ba14d79)
  });

  $("#entries").show();

  // Start race
  $("#Start").on("click", () => {
    const startIso = new Date().toISOString();
    sessionStorage.setItem("raceStartIso", startIso);

    $("#Start_Time").text(`Race started at ${timeFunction()}`); // time_functions.js [4](https://nhbc2-my.sharepoint.com/personal/sjknight_nhbc_co_uk/Documents/Microsoft%20Copilot%20Chat%20Files/summary.html)
    $("#Elapsed_Time_Header").text("Elapsed Time");
    startelapsedtime(new Date(), "Elapsed_Time"); // time_functions.js [4](https://nhbc2-my.sharepoint.com/personal/sjknight_nhbc_co_uk/Documents/Microsoft%20Copilot%20Chat%20Files/summary.html)

    $(".control").show();
  });

  // End race -> summary
  $("#End").on("click", () => {
    stopelapsedtime(); // time_functions.js [4](https://nhbc2-my.sharepoint.com/personal/sjknight_nhbc_co_uk/Documents/Microsoft%20Copilot%20Chat%20Files/summary.html)

    const startIso = sessionStorage.getItem("raceStartIso") || "";
    const endIso = new Date().toISOString();

    const qs = new URLSearchParams({
      start: startIso,
      end: endIso,
      club_name: clubName,
      series_name: seriesName,
      race: raceNo
    });

    window.location.href = `/summary?${qs.toString()}`;
  });

  // Reset -> clear state and go back to setup
  $("#Reset").on("click", () => {
    stopelapsedtime();
    sessionStorage.clear();
    window.location.href = "/";
  });
});