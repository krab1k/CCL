parser grammar CCL;

options { tokenVocab=CCL_Lexer; }

method: NAME method_name=ID NL+ body+=statement+ (WHERE NL+ annotations+=annotation+)? EOF;
statement: assign | for_loop | for_each;
assign: lhs=var EQ rhs=expr NL+;
for_loop: FOR identifier=ID EQ value_from=number TO value_to=number COLON NL+ body+=statement+ DONE NL+;
for_each: FOR_EACH abtype=objtype identifier=ID (bond_decomp)? (ST constraint)? COLON NL+ body+=statement+ DONE NL+;

objtype: ATOM | BOND;
bond_decomp: EQ LB indices+=ID COMMA indices+=ID RB;

expr: <assoc=right> left=expr op=POW right=expr                 #BinOp
    | op=(ADD | SUB) expr                                       #UnaryOp
    | left=expr op=(MUL | DIV) right=expr                       #BinOp
    | left=expr op=(ADD | SUB) right=expr                       #BinOp
    | LP expr RP                                                #ParenOp
    | SUM LB identifier=ID RB LP expr RP                        #SumOp
    | EE LB idx_row=ID COMMA idx_col=ID RB
      LP diag=expr COMMA off=expr COMMA rhs=expr
      (COMMA ee_type=(CUTOFF | COVER) radius=number)? RP        #EEExpr
    | fn=ID LP fn_arg=expr RP                                   #FnExpr
    | var                                                       #VarExpr
    | number                                                    #NumberExpr
    ;

var: basename | subscript;
basename: name=ID;
subscript: name=ID LB indices+=ID (COMMA indices+=ID)? RB;

annotation: var EQ expr (IF constraint)? NL+                                  #ExprAnnotation
          | name=ID IS ptype=(ATOM | BOND | COMMON) PARAMETER NL+             #ParameterAnnotation
          | name=ID (bond_decomp)? IS abtype=objtype (ST constraint)? NL+     #ObjectAnnotation
          | name=ID IS ptype+=names+ OF element=ID NL+                        #ConstantAnnotation
          | name=ID IS ptype+=names+ NL+                                      #PropertyAnnotation
          ;

constraint: left=constraint op=(AND | OR) right=constraint                  #AndOrConstraint
           | NOT constraint                                                 #NotConstraint
           | LP constraint RP                                               #ParenConstraint
           | left=expr op=(LT| GT | NEQ | EQQ | LEQ | GEQ ) right=expr      #CompareConstraint
           | pred=ID LP args+=arg (COMMA args+=arg )* RP                    #PredicateConstraint
           ;

arg: basename | number;

names: ID | ATOM | BOND;

number: NUMBER;
