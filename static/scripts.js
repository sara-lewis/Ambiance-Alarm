// Name: elaspedTime
// Parameters: load_time (i.e. when the python function redirected to the html page)
// Purpose: Redirect to home page after 5 minutes (because that's where lightbulb is changed)
function elapsedTime(load_time) {
    var today = new Date();
    if((today.getMinutes() - load_time) == 5){
        window.location.replace("/");
    }
    setTimeout(function() {
        elapsedTime(load_time);
        }, 5000);
}

// Name: PlaySound
// Parameters: soundObj (i.e. the sound file that plays when the alarm goes off)
// Purpose: Play alarm noise when alarm goes off
function PlaySound(soundObj) {
    var sound = document.getElementById(soundObj);
    sound.Play;
}

// Name: alarm
// Parameters: none
// Purpose: play the alarm sound when the alarm goes off
function alarm(){
    startTime();
    PlaySound('sound1');
}

// Name: alarmCancel
// Parameters: none
// Purpose: redirect to cancel page (from alarm sounding page)
function alarmCancel(){
    window.location.replace("/cancel");
}

// Name: alarmSnooze
// Parameters: none
// Purpose: redirect to snooze page (from alarm sounding page)
function alarmSnooze(){
    window.location.replace("/snooze");
}

// Name: checkAlarm
// Parameters: alarm_hours, alarm_minutes (user values from Python)
// Purpose: Redirect to alarm when it's the right time to do so
function checkAlarm(alarm_hours, alarm_minutes){
    var today = new Date();
    if(today.getHours() == alarm_hours && today.getMinutes() == alarm_minutes){
        window.location.replace("/alarm");
    }
}

// Name: redirectColors
// Parameters: color (i.e. the redirection for that specific color)
// Purpose: redirect once button is pushed so the corresponding color appears on lightbulb
function redirectColors(color){
  window.location.replace(color);
}

// Name: checkLightToSleep
// Parameters: tosleep_hours, tosleep_minutes (user values from Python)
// Purpose: redirect to change light colors for the sleep cycle at the correct times
function checkLightToSleep(tosleep_hours, tosleep_minutes){
    var today = new Date();
    console.log(today.getHours() + "==" + tosleep_hours);
    console.log((today.getMinutes()+11) + ">=" +tosleep_minutes);
    console.log(today.getMinutes() + "<=" + tosleep_minutes);

    if(today.getHours() == tosleep_hours && (today.getMinutes() + 11) >= tosleep_minutes && today.getMinutes() <= tosleep_minutes){
        window.location.replace("/tosleep");
    }
}

// Name: checkLightToAwake
// Parameters: alarm_hours, alarm_minutes (user values from Python)
// Purpose: redirect to change light colors for the wake up cycle at the correct times
function checkLightToAwake(alarm_hours, alarm_minutes){
    var today = new Date();
    console.log(today.getHours() + "==" + alarm_hours);
    console.log((today.getMinutes()+11) + ">=" + alarm_minutes);
    console.log(today.getMinutes() + "<=" + alarm_minutes);

    if(today.getHours() == alarm_hours && (today.getMinutes() + 11) >= alarm_minutes && today.getMinutes() <= alarm_minutes){
        window.location.replace("/toawake");
    }
}

// Name: onLoadHome
// Parameters: tosleep_hours, tosleep_minutes, alarm_hours, alarm_minutes (user values from Python)
// Purpose: run checkLightToAwake and checkLightToSleep at the correct times
function onLoadHome(tosleep_hours, tosleep_minutes, alarm_hours, alarm_minutes){
  setTimeout(function() {
    checkLightToSleep(tosleep_hours, tosleep_minutes);
    checkLightToAwake(alarm_hours, alarm_minutes);
    checkAlarm(alarm_hours, alarm_minutes);
    }, 60000);
    setTimeout(function() {
      onLoadHome(tosleep_hours, tosleep_minutes, alarm_hours, alarm_minutes)
    }, 120000);
}
