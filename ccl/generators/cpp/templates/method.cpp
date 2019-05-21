#include <vector>
#include <cmath>
{sys_includes}

{user_includes}
#include "structures/molecule.h"
#include "parameters.h"
#include "ccl_method.h"

{defs}

std::vector<double> {method_name}::calculate_charges(const Molecule &molecule) const {{
    auto n = static_cast<int>(molecule.atoms().size());
    std::vector<double> q(n, 0);
{code}
    return q;
}}
