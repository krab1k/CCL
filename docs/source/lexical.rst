=======
Lexical
=======

Lexical elements are described using regular expressions in the `standard form <https://github.com/antlr/antlr4/blob/master/doc/lexer-rules.md>`_ used by ANTLR.

Comments
--------

Comments starts with the ``#`` character and spans the line until the line break.

Keywords
--------

CCL defines following keywords: ``to``, ``such that``, ``each``, ``for``, ``property``, ``where``, ``done``, ``is``,
``parameter``, ``if``, ``sum``, ``atom``, ``bond``, ``common``.


Logical operators
-----------------

``and|or|not``

.. _Arithmetic operators:

Arithmetic operators
--------------------

``+-*/^``

.. _Relational operators:

Relational operators
--------------------
``>|>=|==|!=|<=|<``

Names
-----

``[a-zA-Z]+``

Numbers
-------

``'-'? DIGIT+ ('.' DIGIT*)?``

where ``DIGIT`` is defined as ``[0-9]``.


String constants
----------------

``"[a-zA-Z]+"``

