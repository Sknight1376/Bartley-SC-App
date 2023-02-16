
if (document.readyState !== "loading") {
    clock.call('txt');
    rendertableFunction();
} else {
    document.addEventListener("DOMContentLoaded", clock('txt'));
};

const start_button = document.getElementById('Start')
start_button.addEventListener("click",() => {
    document.getElementById('Start Time').innerHTML = timeFunction();
    disableButton('Start');
    startelapsedtime(new Date(), 'Elapsed Time');}
    )


const end_button = document.getElementById('End')
    end_button.addEventListener("click",() => {
    stopelapsedtime();
    disableButton('End');
    disableButton('Submit');}
    )

const submit = document.getElementById('Submit')
    submit.addEventListener("click",() => {
        let start_time = document.getElementById('Start Time').innerHTML;
        let end_time = document.getElementById('Elapsed Time').innerHTML;

        sendtimes(JSON.stringify({'Start_time': start_time,'Elapsed_time': end_time}));
        disableButton('Start');
        disableButton('End');
        disableButton('Submit');

        document.getElementById('Elapsed Time').innerHTML = "00:00:00"
        document.getElementById('Start Time').innerHTML = ""

        }
        )

const sailor_submit_button = document.getElementById('Sailor Submit')
    sailor_submit_button.addEventListener("click",() => {
        var classes = document.getElementById('Boat');
        let classname = classes.options[classes.selectedIndex].text;
        let sailno = document.getElementById('Sail Number').value
        appendentriesFunction(classname, sailno);
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