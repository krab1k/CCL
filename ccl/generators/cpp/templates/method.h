#pragma once

#include <vector>
#include <Eigen/Core>

#include "structures/molecule.h"
#include "method.h"

class {method_name} : public {method_type} {{
    {common_parameters_enum}
    {atom_parameters_enum}
    {bond_parameters_enum}
    {prototypes}
public:
    explicit {method_name}() : {method_type}("{method_name}", {{{common_parameters}}}, {{{atom_parameters}}}, {{{bond_parameters}}}, {{}}) {{}};

    virtual ~{method_name}() = default;

    [[nodiscard]] std::vector<double> calculate_charges(const Molecule &molecule) const override;

    [[nodiscard]] std::vector<RequiredFeatures> get_requirements() const override {{
        return {{{required_features}}};
    }}

}};
