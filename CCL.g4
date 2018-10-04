grammar CCL;

method: body+=statement+ ('where' annotations+=annotation+)? EOF;
statement: assign | for_loop | for_each;
assign: lhs=var '=' rhs=expr;
for_loop: 'for' identifier=NAME '=' value_from=number 'to' value_to=number ':' body+=statement+ 'done';
for_each: 'for each' abtype=('atom' | 'bond') identifier=NAME ('such that' constraint)? ':' body+=statement+ 'done';

expr: <assoc=right> left=expr op='^' right=expr #BinOp
    | op=('+' | '-') expr                       #UnaryOp
    | left=expr op=('*' | '/') right=expr       #BinOp
    | left=expr op=('+' | '-') right=expr       #BinOp
    | '(' expr ')'                              #ParenOp
    | 'sum' '[' identifier=NAME ']' '(' expr ')'#SumOp
    | var                                       #VarExpr
    | number                                    #NumberExpr
    ;

var: basename | subscript;
basename: name=NAME;
subscript: name=NAME '[' indices+=NAME (',' indices+=NAME)? ']';

annotation: var '=' expr ('if' constraint)?                                     #ExprAnnotation
          | name=NAME 'is' ptype=('atom' | 'bond' | 'common') 'parameter'       #ParameterAnnotation
          | name=NAME 'is' abtype=('atom' | 'bond') ('such that' constraint)?   #ABAnnotation
          | name=NAME 'is property' prop=NAME                                   #PropertyAnnotation
          ;
constraint: left=constraint op=('and' | 'or') right=constraint                #AndOrConstraint
           | 'not' constraint                                                 #NotConstraint
           | '(' constraint ')'                                               #ParenConstraint
           | left=expr op=('<' | '>' | '!=' | '==' | '<=' | '>=' ) right=expr #CompareConstraint
           | pred=NAME '(' args+=arg (',' args+=arg )* ')'                    #PredicateConstraint
           ;

arg: basename | number | string;
number: NUMBER;
string: STRING;

fragment NL: '\r'? '\n';
fragment DIGIT: [0-9];
fragment LETTER: [a-zA-Z];
STRING: '"' (DIGIT | LETTER)+ '"';

COMMENT: '#' .*? NL -> skip;
WS: [ \t\n] -> channel(HIDDEN);

NUMBER: '-'? DIGIT+ ('.' DIGIT*)?;
NAME: LETTER+;

ERROR_CHAR: .;
