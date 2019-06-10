#include <vector>
#include <cmath>
#include <Eigen/Dense>
{sys_includes}

#include "structures/molecule.h"
#include "parameters.h"
#include "ccl_method.h"
#include "geometry.h"

{defs}

std::vector<double> {method_name}::calculate_charges(const Molecule &molecule) const {{
    auto n = static_cast<int>(molecule.atoms().size());
    auto m = static_cast<int>(molecule.bonds().size());
{var_definitions}

{code}

    return std::vector<double> (_q.data(), _q.data() + _q.size());
}}
