

function appendentriesFunction(Boat, Sail) {
    $("#entries tbody").append(`<tr id = ${Boat}_${Sail}_row>
    <td class = control><button type="button" id = "${Boat}_${Sail}_lap" value = 0 class = control_button>Lap</button></td>
    <td class = control><button type="button" id = "${Boat}_${Sail}_finish" class = control_button>Finish</button></td>
    <td>${Boat}</td>
    <td>${Sail}</td>
    </tr>`)

    $(".control").hide()


    laprecorder($(`#${Boat}_${Sail}_lap`), `#${Boat}_${Sail}_row`, Boat, Sail, "Lap")
    laprecorder($(`#${Boat}_${Sail}_finish`), `#${Boat}_${Sail}_row`, Boat, Sail, "Finish")

}


function laprecorder(button, row, Boat, Sail, record_type) {

    button.on("click", () => {

        button.val(+button.val() + +1 )

        if  (record_type == "Lap") {
            var headername = `Lap ${button.val()}`
            var classname = `lap_${button.val()}`
        }else{
            var headername = "Final"
            var classname = "Final"
            $(`#${Boat}_${Sail}_lap`).hide()
            $(`#${Boat}_${Sail}_finish`).hide()
        }
        
        
        if ($("#entries tbody tr").length == $(".control_button:hidden").length/2){
            $(".control").hide()}

        let Elapsed_Time =  $("#Elapsed_Time").text()
        $(`${row} td:last`).after(`<td>${Elapsed_Time}</td>`)

        if ($(`#headers th:last`).text() !== `${headername} Position`) {

            $(`#headers th:last`).after(`<th>${headername}</th>`)
            $(`#headers th:last`).after(`<th>${headername} Corrected</th>`)
            $(`#headers th:last`).after(`<th>${headername} Position</th>`)
        }
        

        $.post('/times',
        {Elapsed: Elapsed_Time,
            boat: Boat}, function(data) {
            console.log(data)
            $(`${row} td:last`).after(
                `<td class = ${classname} value = ${data['seconds']}>${data['corrected_time']}</td>
                <td class = ${classname}_rank></td>`)

                $(`.${classname}`)
                .map(function() {return $(this).attr('value')})
                .get()
                .sort(function(a,b){return a - b }).reverse()
                .reduce(function(a, b) {if (b != a[0]) a.unshift(b);return a}, [])
                .forEach((v,i)=>{
                    $(`.${classname}`).filter(function() {return $(this).attr('value') == v;}).next().text(i + 1);
                });    
        })
    })
}

