.. _Types:

=====
Types
=====

CCL is a strongly-typed language. When new variable is created, its type is inferred from the context and cannot be changed later.

Simple types
============

There are two numeric types, namely ``Int`` and ``Float``, ``String`` and ``Bool``. Assignment of ``Int`` expression to ``Float`` variable
is possible, but not the other way around. ``String`` can only be a constant used as arguments in functions. ``Bool`` type
is used internally by CCL when evaluating :ref:`Constraints`.

Object types
============

Two object types are available, i.e., ``Atom`` and ``Bond``.

.. _Complex types:

Complex (Array) types
=====================

CCL supports up to two-dimensional arrays.
Each element of the array has to have the same numeric type, either ``Int`` or ``Float``.
Compared to general-purporse programming languages, the size of the array in CCL (in each dimension) must match the number
of atoms or bonds in the molecule.

For example, vector of charges ``q`` for each atom in the molecule (defined implicitly in each CCL method) has a type
``float[Atom]``, connectivity matrix of the molecular graph would be a 2D array with type ``int[Atom, Atom]``.