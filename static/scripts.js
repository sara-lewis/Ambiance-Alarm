//Will eventually have javascript functions that can be factored out

function elapsedTime(load_time) {
    var today = new Date();
    if((today.getMinutes() - load_time) == 5){
        window.location.replace("/");
    }
    setTimeout(function() {
        elapsedTime(load_time);
        }, 5000);
}

function PlaySound(soundObj) {
    var sound = document.getElementById(soundObj);
     sound.Play;
}

function alarm(){
    startTime();
    PlaySound('sound1');
}

function alarmCancel(){
    window.location.replace("/cancel");
}

function alarmSnooze(){
    window.location.replace("/snooze");
}

function checkAlarm(alarm_hours, alarm_minutes, am_pm){
    var today = new Date();
    if(am_pm == "PM" && alarm_hours != 0){
        alarm_hours += 12;
    }

    console.log("Current hours: " + today.getHours());
    console.log("Current minutes: " + today.getMinutes());
    console.log("Wake up hours: " + alarm_hours);
    console.log("Wake up minutes: " + alarm_minutes);
    if(today.getHours() == alarm_hours && today.getMinutes() == alarm_minutes){
        window.location.replace("/alarm");
    }
    setTimeout(function() {
        checkAlarm(alarm_hours, alarm_minutes, am_pm);
        }, 60000);
}