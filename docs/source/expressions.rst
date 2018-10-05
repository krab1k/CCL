===========
Expressions
===========

Expressions are the fundamental part of almost every computer language. There are two simple (atomic) expressions --
names representing variables and numerical constants. Using :ref:`arithmetic operators <Arithmetic operators>` and
brackets ``()`` complex expressions can be build.

Sum
===

Sometimes is useful to use summation inside an expression. For this purpose, Sum expressions can be used. The general
form is:

.. code-block:: none

    sum[<NAME>](<EXPR>)

The ``<NAME>`` must be defined via :ref:`Object annotation <Object annotation>`. ``<EXPR>`` can be an arbitrary expression.

To illustrate on an example:

.. code-block:: ccl

    x = sum[i](q[i])
    where
    i is atom such that element(i, "hydrogen")

is equivalent to the following code using :ref:`For each <For each>` loop:

.. code-block:: ccl

    x = 0
    for each atom i such that element(i, "hydrogen")
        x = x + q[i]
    done

For another example, see :ref:`PEOE method <PEOE example>`.


Operator priority
=================

Sorted from highest to lowest:

+----+-------------------------+
| ^  | exponentiation          |
+----+-------------------------+
| +- | unary plus/minus        |
+----+-------------------------+
| \*/| multiplication/division |
+----+-------------------------+
| +- | addition/subtraction    |
+----+-------------------------+

Expression types
================

Each expression in CCL has a certain :ref:`type <Types>`. Note that only numerical types (simple or array-like) can be
used at the right-hand side of the :ref:`assignment <Assignment>`.

Simple expressions
------------------

Numerical constants have type ``Int`` or ``Float`` depending on whether they contain ``.`` character.

.. code-block:: ccl

    x = 4.3 # Float
    y = 4.  # Float
    z = 4   # Int

Type of the variable is set when expression is assigned to it.

Similar rules apply also to :ref:`array types <Complex types>` as long as usual math conditions on array dimensions
are satisfied.

Binary operations
-----------------

If both of the operands are of type ``Int``, the result has type ``Int`` too. Otherwise, result has type ``Float``.

Sum expression
--------------

The type of ``sum[IDX](EXPR)`` is the type of the ``EXPR``.

Complex expressions
-------------------

The type of the complex expression is based on the types of its subexpressions.
