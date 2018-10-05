===========
Annotations
===========

Annotations provide a meaning for the symbols used in the method description.

Parameters
==========

There are three types of parameters: ``atom``, ``bond`` and ``common``. When used in code, former two requires an index of a particular type, e.g., ``Atom`` or ``Bond``.
Example of annotations for all three kinds is listed here:

.. code-block:: ccl

    A is atom parameter
    B is bond parameter
    C is common parameter

.. _Object annotation:

Object annotations
==================

When using ``Sum`` one has to define an index to iterate over. Object annotations defines a variable of the objects types, i.e.,
``Atom`` or ``Bond``. The syntax is following:

.. code-block:: ccl

    i is atom
    j is bond

Restrictions on the objects
---------------------------

In some cases, we might want to work with only a subset of atoms or bonds. CCL offers a ``such that`` keyword that extends
object annotation with some additional :ref:`constraints <Constraints>`. As an example, consider all atoms of the molecule bonded to a particular atom ``i``. In CCL:

.. code-block:: ccl

    j is atom such that bonded(i, j)

where ``bonded`` is a predicate which is satisfied when its arguments are two atoms connected by a bond.

Note that ``i`` of type ``Atom`` must be defined in the context where ``j`` is referenced.

Properties
==========

CCL supports following properties:

:electronegativity:
    electronegativity of an atom

:covradius:
    covalent radius of an atom

:vdwradius:
    van der Waals radius of an atom

Substitute expressions
======================
