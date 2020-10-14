lexer grammar CCL_Lexer;

fragment DIGIT: [0-9];
fragment LETTER: [a-zA-Z];
fragment ALPHA: DIGIT | LETTER | '_';

NL: '\r'? '\n';
COMMENT: '#' .*? NL -> skip;
WS: [ \t\n] -> channel(HIDDEN);

NAME: 'name';
ATOM: 'atom';
BOND: 'bond';
COMMON: 'common';
PARAMETER: 'parameter';
ST: 'such that';
WHERE: 'where';
DONE: 'done';
IS: 'is';
AND: 'and';
OR: 'or';
NOT: 'not';
EQ: '=';
FOR_EACH: 'for each';
FOR: 'for';
TO: 'to';
IF: 'if';
OF: 'of';
SUM: 'sum';
CUTOFF: 'cutoff';
COVER: 'cover';
EE: 'EE';

ADD: '+';
MUL: '*';
DIV: '/';
SUB: '-';
POW: '^';

LP: '(';
RP: ')';
LB: '[';
RB: ']';
LT: '<';
GT: '>';
LEQ: '<=';
GEQ: '>=';
NEQ: '!=';
EQQ: '==';

REGRESSION_EXPR: '{}';

COLON: ':';
COMMA: ',';
NUMBER: '-'? DIGIT+ ('.' DIGIT*)?;
ID: LETTER ALPHA*;

ERROR_CHAR: .;
