
if (document.readyState !== "loading") {
    clock.call('clock');
    rendertableFunction();
    $("#entries").hide();
} else {
    document.addEventListener("DOMContentLoaded", clock('clock'));
    $("#entries").hide();
};

const start_button = $("#Start").click(() => {
    if ($("#entries tbody tr").length > 0){
        $("#Start_Time").text(`Race started at ${timeFunction()}`);
        disableButton('Start');
        $("#Elapsed_Time_Header").text("Elapsed Time");
        startelapsedtime(new Date(), 'Elapsed_Time');
        $(".control").show();
        $(".competitors").hide()
    }else{
        alert("there are no entries")
    }
})


const end_button = $("#End").click(() => {
    stopelapsedtime();
    disableButton('End');
    disableButton('Submit');}
    )

const submit = $('#Submit').click(() => {
        var myRows = [];
        var headersText = [];
        var $headers = $("th");

        // Loop through grabbing everything
        var $rows = $("tbody tr").each(function(index) {
        $cells = $(this).find("td");
        myRows[index] = {};

        $cells.each(function(cellIndex) {
            // Set the header text
            if(headersText[cellIndex] === undefined) {
            headersText[cellIndex] = $($headers[cellIndex]).text();
            }
            // Update the row object with the header/cell combo
            myRows[index][headersText[cellIndex]] = $(this).text();
        });    
        });

        sendtimes(JSON.stringify(myRows));
        disableButton('Start');
        disableButton('End');
        disableButton('Submit');

        // document.getElementById('Elapsed Time').innerHTML = "00:00:00"
        // document.getElementById('Start Time').innerHTML = ""

        }
        )

const sailor_submit_button = document.getElementById('Sailor Submit')
    sailor_submit_button.addEventListener("click",() => {
        var classes = document.getElementById('Boat');
        let classname = classes.options[classes.selectedIndex].text;
        let sailno = document.getElementById('Sail Number').value
        appendentriesFunction(classname, sailno);
        $("#entries").show()
    }
    )

function variables(vars) {
    return vars
    }



  function disableButton(disable_button) {
    let element = document.getElementById(disable_button);
    let disabled = element.getAttribute("disabled");
    if (disabled) {
          element.removeAttribute("disabled");
      } else {
          element.setAttribute("disabled", "disabled");
    }
  }

  function sendtimes(obj){
    const request = new XMLHttpRequest()
        request.open('POST', `/process_times/${obj}`)
        request.send();

  }