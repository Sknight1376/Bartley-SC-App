function timeFunction() {
    var currentdate = new Date(); 
    var time = currentdate.getHours() + ":"  
                + checkTime(currentdate.getMinutes()) + ":" 
                + checkTime(currentdate.getSeconds())
    return time;
    }

    function clock() {
      document.getElementById('Start Time').innerHTML = timeFunction()
        setTimeout(clock, 1000)
    }


function checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
    }

