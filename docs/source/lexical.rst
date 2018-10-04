=======
Lexical
=======

Lexical elements are described using regular expressions in the `standard form <https://github.com/antlr/antlr4/blob/master/doc/lexer-rules.md>`_ used by ANTLR.

Keywords
--------

CCL defines following keywords: ``to``, ``such that``, ``each``, ``for``, ``property``, ``where``, ``done``, ``is``,
``parameter``, ``if``, ``and``, ``or``, ``sum``, ``atom``, ``bond``, ``common``.


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

