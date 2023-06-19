lexer grammar baslLexer;

INDENT
 : [ \t]+ -> skip
 ;

DEDENT
 : ( [\r\n] | EOF ) {this.popMode(); this.skip();}
 ;

ID
: ID_START ID_CONTINUE*;
INT
: [0-9]+;
FLOAT
: [0-9]+ '.' [0-9]*;
STRING
 : ( [rR] | [uU] | [fF] | ( [fF] [rR] ) | ( [rR] [fF] ) )? ( SHORT_STRING | LONG_STRING )
 ;
TRUE
    : 'True'
    ;
FALSE
    : 'False'
    ;
NONE
    : 'None'
    ;
RETURN_SYMBOL
    : '_RET'
    ;
NUMBER:
    INT | FLOAT
    ;

VALUE
 : NUMBER
 | STRING
 | TRUE
 | FALSE
 | NONE
 | RETURN_SYMBOL
 ;

// 运算
PLUS: '+';
MINUS: '-';
MUL: '*';
DIV: '/';
MOD: '%';
POW: '**';
FLOORDIV: '//';
AND: 'and';
OR: 'or';
NOT: 'not';
XOR: '^';

NUMBER_OP
 : PLUS
 | MINUS
 | MUL
 | DIV
 | MOD
 | POW
 | FLOORDIV
 ;


LOGIC_OP
:AND
| OR
| NOT
| XOR
;


//逻辑运算

// 比较运算
EQ: 'eq';
NEQ: 'neq';
LT: 'lt';
LE: 'le';
GT: 'gt';
GE: 'ge';
IN : 'in';
NOT_IN : 'nin';

COMPARE
 : EQ
 | NEQ
 | LT
 | LE
 | GT
 | GE
 ;

SUBSET_COMPARE
 : IN
 | NOT_IN
 ;

// 赋值
ASSIGN : '=';

//

//关键字
ADB: 'adb';
OCR: 'ocr';
CLICK: 'click';
SLEEP: 'sleep';
EXIT: 'exit';
CHECK: 'check';

STAY: 'stay';
UNTIL: 'until';

ARG: 'arg';
DEL : 'del';

CHECK_HARD:'hard';
CHECK_SOFT:'soft';

//分隔符
LPAREN: '(';
RPAREN: ')';
LBRACK: '[';
RBRACK: ']';
COMMA: ',';
COLON: ':';

SPACE :' '+ -> skip;

// string part begin ************************************************************

 fragment SHORT_STRING
 : '\'' ( STRING_ESCAPE_SEQ | ~[\\\r\n\f'] )* '\''
 | '"' ( STRING_ESCAPE_SEQ | ~[\\\r\n\f"] )* '"'
 ;
/// longstring      ::=  "'''" longstringitem* "'''" | '"""' longstringitem* '"""'
fragment LONG_STRING
 : '\'\'\'' LONG_STRING_ITEM*? '\'\'\''
 | '"""' LONG_STRING_ITEM*? '"""'
 ;
 /// longstringitem  ::=  longstringchar | stringescapeseq
fragment LONG_STRING_ITEM
 : LONG_STRING_CHAR
 | STRING_ESCAPE_SEQ
 ;
 fragment STRING_ESCAPE_SEQ
 : '\\' .
 | '\\' NEWLINE
 ;

 NEWLINE
 : ( {this.atStartOfInput()}?   SPACES
   | ( '\r'? '\n' | '\r' | '\f' ) SPACES?
   )
   {this.onNewLine();}
 ;

 fragment SPACES
 : [ \t]+
 ;

/// longstringchar  ::=  <any source character except "\">
fragment LONG_STRING_CHAR
 : ~'\\'
 ;

// string part end ************************************************************

// id part begin ************************************************************

fragment UNICODE_OIDS
 : '\u1885'..'\u1886'
 | '\u2118'
 | '\u212e'
 | '\u309b'..'\u309c'
 ;
 fragment UNICODE_OIDC
 : '\u00b7'
 | '\u0387'
 | '\u1369'..'\u1371'
 | '\u19da'
 ;

fragment ID_START
 : '_'
 | [\p{L}]
 | [\p{Nl}]
 //| [\p{Other_ID_Start}]
 | UNICODE_OIDS
 ;

 fragment ID_CONTINUE
 : ID_START
 | [\p{Mn}]
 | [\p{Mc}]
 | [\p{Nd}]
 | [\p{Pc}]
 //| [\p{Other_ID_Continue}]
 | UNICODE_OIDC
 ;
// id part end ************************************************************