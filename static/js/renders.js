

function appendentriesFunction(Boat, Sail) {
    let table = document.querySelector("table#entries>tbody");

    let row = table.insertRow(-1);

    let cellone = row.insertCell(0);
    let celltwo = row.insertCell(1);
    let cellthree = row.insertCell(2);
    let cellfour = row.insertCell(3);

    row.id = `${Boat} ${Sail} row`
    cellone.innerText = Boat
    celltwo.innerText = Sail
    cellthree.innerHTML = `<button type="button" id = "${Sail} lap" value = "${Boat} ${Sail}">Lap</button>`
    cellfour.innerHTML = `<button type="button" id = "${Sail} finish" value = "${Boat} ${Sail}">Finish</button>`

    laprecorder(Boat, Sail)

    function laprecorder (Boat, Sail) {
        const lapbutton = document.getElementById(`${Sail} lap`)
        lapbutton.addEventListener("click",() => {
            let row = document.getElementById(`${Boat} ${Sail} row`);
            let time = document.getElementById("Elapsed Time").innerHTML;
            let cell = row.insertCell(4);
            cell.innerHTML = time
        })

    }


}