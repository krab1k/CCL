#pragma once

#include <vector>
#include <boost/config.hpp>

#include "structures/molecule.h"
#include "method.h"

class {method_name} : public Method {{
    {common_parameters_enum}
    {atom_parameters_enum}
    {bond_parameters_enum}
    {prototypes}
public:
    explicit {method_name}() : Method("{method_name}", {{{common_parameters}}}, {{{atom_parameters}}}, {{{bond_parameters}}}, {{}}) {{}};

    virtual ~{method_name}() = default;

    std::vector<double> calculate_charges(const Molecule &molecule) const override;
}};

extern "C" BOOST_SYMBOL_EXPORT {method_name} method;
{method_name} method;
