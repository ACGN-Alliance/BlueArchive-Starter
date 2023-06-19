// baslParser.g4

parser grammar baslParser;

options {
  tokenVocab=baslLexer;
}

// 元素是 标识符或者值或者列表
// **************list**************
list
  : LBRACK elements? RBRACK
  ;

elements:
  SPACE element SPACE (COMMA SPACE element SPACE)*
  ;

element
    : ID
    | VALUE
    | list
    ;
// **************list**************

// 返回值是True或False的表达式
test_expression
  : NUMBER SPACE COMPARE SPACE NUMBER
  | STRING SPACE COMPARE SPACE STRING
  | VALUE SPACE SUBSET_COMPARE SPACE list
  | test_expression SPACE (EQ|NEQ) SPACE (TRUE|FALSE)
  | test_expression SPACE (AND|OR|EQ|NEQ) SPACE test_expression
  ;

string_add_expression
  : STRING SPACE? PLUS SPACE? STRING
    | string_add_expression SPACE? PLUS SPACE? STRING
  ;

expression
  : test_expression
  | atom
  | NUMBER SPACE? (NUMBER_OP SPACE? NUMBER)+
  | string_add_expression
  ;

check_stmt:
  CHECK SPACE (CHECK_HARD|CHECK_SOFT) SPACE test_expression
  ;

stay_stmt:
  STAY SPACE UNTIL SPACE test_expression
  ;

arg_stmt:
    ARG SPACE ID SPACE? ASSIGN SPACE? expression
    ;

arg_del_stmt:
    ARG SPACE DEL SPACE ID
    ;

location_stmt:
    INT SPACE? COMMA SPACE? INT SPACE? COMMA SPACE? INT SPACE? COMMA SPACE? INT
    ;

pos_stmt:
    INT SPACE? COMMA SPACE? INT
    ;

//pythonic block
universe_block
  : INDENT ((check_stmt|stay_stmt|arg_stmt|arg_del_stmt) NEWLINE)* DEDENT
  ;

// adb
adb_stmt
  : ADB (SPACE ID)+ (COLON NEWLINE universe_block)?
  ;

ocr_stmt
  : OCR SPACE location_stmt SPACE STRING (COLON NEWLINE universe_block)?
  ;

click_stmt
  : CLICK SPACE pos_stmt
  ;

sleep_stmt
  : SLEEP SPACE NUMBER
  ;

exit_stmt
  : EXIT
  ;

start:
    | adb_stmt
    | ocr_stmt
    | click_stmt
    | sleep_stmt
    | exit_stmt
    ;

atom
  : ID
  | NUMBER
  | STRING
  | TRUE
  | FALSE
  ;
