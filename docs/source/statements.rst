==========
Statements
==========

There are three types of statements in CCL. Assignment and two types of loops.

.. _Assignment:

Assignment
==========

Assignment is the simplest statement in CCL. The general syntax is:

.. code-block:: none

    <NAME> = <EXPR>

where ``<EXPR>`` must be of a numeric type. If ``<NAME>`` is not defined yet, it will be defined with the type of
the ``<EXPR>``. If ``<NAME>`` is already defined, it must have same type as ``<EXPR>``.

For
===

For loop general syntax is:

.. code-block:: none

    for <NAME> = <FROM> to <TO>:
        <BODY>
    done

The ``<NAME>`` must not be defined before. ``<FROM>`` and ``<TO>`` must have a ``Int`` type. ``<NAME>`` is also
defined with ``Int`` type and this it is local to the for loop where it was defined
(i.e., can be reused after the ``done`` keyword).

Before each iteration condition ``<NAME> <= <TO>`` is evaluated. If the result is ``True``, ``<BODY>`` is executed,
otherwise, the execution continues after the ``done`` keyword. After each iteration ``<NAME>`` is increased by one and
the whole process repeats.

.. _For each:

For Each
========

To iterate over a set of objects (either atoms or bonds), CCL contains a For each loop:

.. code-block:: none

    for each <OBJECT> <NAME> such that <CONSTRAINT>:
        <BODY>
    done

``<OBJECT>`` specifies the type of the ``<NAME>``. There are two valid options: ``atom`` or ``bond`` for types ``Atom``
and ``Bond``, respectively. Again, the ``<NAME>`` must not be defined before. ``such that`` keyword with
the ``<CONSTRAINT>`` is the optional part.
``<CONSTRAINT>`` specifies restrictions on the objects in question, see :ref:`Constraints <Constraints>`.