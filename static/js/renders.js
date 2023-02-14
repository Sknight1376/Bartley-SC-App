

function appendentriesFunction(Boat, Sail) {
    let table = document.getElementById("entries");

    let row = table.insertRow(-1);

    let cellone = row.insertCell(0);
    let celltwo = row.insertCell(1);
    let cellthree = row.insertCell(2);

    cellone.innerText = Boat
    celltwo.innerText = Sail
    cellthree.innerHTML = `<button type="button" id = "${Sail}lap">Lap</button>`


}