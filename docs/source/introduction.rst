============
Introduction
============

CCL (Charge Calculation Language) is a domain specific language for describing empirical methods for computing partial atomic charges in molecules.
The purpose is of CCL is to provide a simple formalism which can describe and cover all major empirical methods in a way natural to the users and developers of these methods.

The code in CCL resembles the notation used in many scientific papers, i.e., main idea represented as an equation along with the annotation of the symbol meaning. Let's ilustrate this on an example.

Example
=======

One of the most famous empirical methods is Partial Equalization of Orbital Electronegativity (PEOE) by Gasteiger and Marsili.
It's an iterative approach in which the charge is shifted between bonded atoms. The amount of charge transferred between two atoms is proportional to the difference of their electronegativities. Here PEOE is written in CCL:

.. literalinclude:: ../../examples/peoe.ccl
    :language: ccl


Python/C++ output
-----------------

CCL provides a high-level abstraction for charge calculation methods. However, without any means of translating the code into some general purpose language, it's use would be rather limited.
Therefore, CCL reference implementation includes a translator to Python/C++ so that each method migh work as a module in ChargeFW.


Latex output
------------

CCL reference implementation also features a Latex output format to provide user with a nice-looking representation of each method. The translation of PEOE follows:

.. math::
    :nowrap:

    \leavevmode\\\noindent $\text{for } 0 \leq \alpha \leq 6:
    \\\hspace*{4mm} \forall \text{ atom } i: \chi_{i} = C_{i}  {q_{i}} ^ {2} + B_{i}  q_{i} + A_{i}\\
    \hspace*{4mm} \forall \text{ atom } i: q_{i} = q_{i} + \left(\sum_{j}\left(\frac{\chi_{j} - \chi_{i}}{d_{i}}\right) + \sum_{k}\left(\frac{\chi_{k} - \chi_{i}}{d_{k}}\right)\right)  {0.5} ^ {\alpha}$
    \vspace*{5mm}

    \noindent where
    \noindent $d_{i} =
    \begin{cases}
    20.02 & \text{if }i\text{ is \text{hydrogen}}\\
    A_{i} + B_{i} + C_{i} & \text{otherwise}\\
    \end{cases}$

    \noindent and
    $q$ is a vector of charges, $A$, $B$, $C$ are atom parameters, $j$ is an atom such that $i$\text{ is bonded to }$j$ and $\chi_{j} > \chi_{i}$, $k$ is an atom such that $i$\text{ is bonded to }$k$ and $\chi_{k} < \chi_{i}$.

