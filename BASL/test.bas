adb shell input keyevent 4:
    check soft _RET neq "0"
    # 完整的stay语法: stay [interval]? until [condition]?
    # interval单位为秒，condition为条件表达式，支持变量和运算符,interval省略时默认1.0s,condition省略时默认_RET (_RET == True)
    stay 0.7 until _RET eq "0"
    arg test = 6
    arg del test2
log "test test test"
click 720,480
ocr 800,640,120,20 ".test.png"
    stay until
sleep 1.1
exit