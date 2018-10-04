======
Method
======

Method in CCL describes a procedure to calculate partial atomic charges for a given single molecule.
Each method in CCL consists of sequence of statements (main part) and a list of annotations.
There must be at least one statement, annotations are optional (but necessary in all but very simple cases).
Statements are separated from annotations by ``where`` keyword.

When CCL code is being processed, annotations are read first to define meaning for the symbols, then the statements are analyzed.