
if (document.readyState !== "loading") {
    clock.call();
} else {
    document.addEventListener("DOMContentLoaded", clock());
};

//   function disableButton(disable_button) {
//     let element = document.getElementById(disable_button);
//     let disabled = element.getAttribute("disabled");
//     if (disabled) {
//           element.removeAttribute("disabled");
//       } else {
//           element.setAttribute("disabled", "disabled");
//     }
//   }

//   function sendtimes(){
//     var currentdate = new Date(); 
//     let time = timeFunction()
//     console.log(time)
//     const request = new XMLHttpRequest()
//         request.open('POST', `/process_times/${JSON.stringify({'start_time':time})}`)
//         request.send();

//   }