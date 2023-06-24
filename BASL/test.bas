adb shell input keyevent 4:
    check soft _RET neq "0"
    # 完整的stay语法: stay [interval]? until [condition]?
    # interval单位为秒，condition为条件表达式，支持变量和运算符,interval省略时默认1.0s,condition省略时默认_RET (_RET == True)
    stay 0.7 until _RET eq "0"
    var test = 6
    var del test2
log "test test test"
var test3 = "test"
var del test3

var loop = 3
adb shell input keyevent 4:
    stay until loop eq 0
    var loop = loop - 1

click 720,480:
    stay until _RET eq "0"
    var test = 6
    var del test2
ocr 800,640,120,20,0.9 ".test.png"
    stay until
sleep 1.1
exit

# 注:只有adb ocr click 这三个会解析子句，其他的都不会
# 注:adb ocr 会产生返回值并默认存放到本地变量_RET中，但click不会产生返回值(_RET永远为None)

