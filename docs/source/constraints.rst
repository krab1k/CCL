.. _Constraints:

===========
Constraints
===========

Constraints are used to restrict atoms or bonds of the molecule to some subset. They follow the ``such that`` keyword.

Simple constraint might be a :ref:`predicate <Predicates>` or a :ref:`comparison <Comparison>` of two expressions. Complex constraints are composed of the simple ones
using ``and``, ``or``, ``not`` keywords and brackets ``()`` with their usual mathematical meaning.


.. _Predicates:

Predicates
==========

Predicates are builtin functions used in :ref:`constraints <Constraints>`.
Each of them evaluates either to ``True`` or ``False``.

CCL defines the following predicates:

bonded
------

``bonded(i: Atom, j: Atom) -> Bool``

Satisfied when atoms ``i`` and ``j`` are connected via a bond.

element
-------

``element(i: Atom, element: String) -> Bool``

Satisfied when atom ``i`` is of element ``<element>``. There are two options of specifying the ``<element>``,
lowercase name or element symbol. E.g., ``"hydrogen"`` or ``"H"``.

near
----
``near(i: Object, j: Object, distance: Float) -> Bool``

Satisfied when object ``i`` is at most ``distance`` from object ``j``.

.. _Comparison:

Comparison
==========

Second type of constraint is the comparison of two expressions.
Common :ref:`relational operators <Relational operators>` can be used.

Following example from :ref:`PEOE method <PEOE example>` shows both constraint types:

.. code-block:: ccl

    j is atom such that bonded(i, j) and chi[j] > chi[i]
