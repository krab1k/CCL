import matplotlib.pyplot as plt
import numpy as np
import sys
from typing import Tuple, List


def read_charges(filename: str) -> List[float]:
    charges = []
    with open(filename) as f:
        while True:
            try:
                next(f).strip()
                charges.extend(float(x) for x in next(f).strip().split())
            except StopIteration:
                break

    return charges


def correlation_plot(ref_charges: str, new_charges: str, output: str) -> Tuple[float, float]:
    ref_charges = read_charges(ref_charges)
    new_charges = read_charges(new_charges)

    d = np.array(ref_charges) - np.array(new_charges)
    rmsd = np.sqrt(np.sum(d ** 2) / len(ref_charges))
    r2 = np.corrcoef(ref_charges, new_charges)[0, 1] ** 2

    fig, ax = plt.subplots()
    ax.scatter(ref_charges, new_charges, s=10)

    limits = [
        np.min([ax.get_xlim(), ax.get_ylim()]),
        np.max([ax.get_xlim(), ax.get_ylim()]),
    ]

    ax.plot(limits, limits, 'k-', alpha=0.75, zorder=0)
    ax.set_aspect('equal')
    ax.set_xlim(limits)
    ax.set_ylim(limits)

    plt.savefig(output)
    return rmsd, r2


def main():
    if len(sys.argv) != 4:
        print('Incorrect number of arguments.', file=sys.stderr)
        sys.exit(1)

    rmsd, r2 = correlation_plot(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f'RMSD = {rmsd:.3f}')
    print(f'R2 = {r2:.3f}')


if __name__ == '__main__':
    main()
