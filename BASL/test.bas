adb shell input keyevent 4:
    check soft _RET neq "0"
    stay until _RET eq "0"
    arg test = 6
    arg del test2
log "test test test"
click 720,480
ocr 800,640,120,20 ".test.png"
sleep 1.1
exit