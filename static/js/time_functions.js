var keepgoing = true

function timeFunction() {
    var currentdate = new Date(); 
    var time = currentdate.getHours() + ":"  
                + checkTime(currentdate.getMinutes()) + ":" 
                + checkTime(currentdate.getSeconds())
    return time;
    }

function timeelapsedFunction(time, element) {
        var new_time = new Date(); 
        if (keepgoing) {
          var diff = new_time - time
        }else{
          var diff = new_time - time - 1000
        }
        var msec = diff;
        var hh = Math.floor(msec / 1000 / 60 / 60);
        msec -= hh * 1000 * 60 * 60;
        var mm = Math.floor(msec / 1000 / 60);
        msec -= mm * 1000 * 60;
        var ss = Math.floor(msec / 1000);
        msec -= ss * 1000;
        elapsedtime = addprecedingzeroFunction(hh) 
        + ":" + 
        addprecedingzeroFunction(mm) 
        + ":" + 
        addprecedingzeroFunction(ss)
        document.getElementById(element).innerHTML = elapsedtime;

        if (keepgoing) {
          setTimeout(timeelapsedFunction, 1000, time, element)
        }
      }

function startelapsedtime(time, element) {
        keepgoing = true;
        timeelapsedFunction(time, element)
    }

function stopelapsedtime() {
        keepgoing = false;
    }
      

function clock(element) {
    document.getElementById(element).innerHTML = timeFunction()
      setTimeout(clock, 1000, element)
  }


function checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
    }

function addprecedingzeroFunction(num) {
  num = num.toString();
    while (num.length < 2) num = "0" + num;
    return num;
}

