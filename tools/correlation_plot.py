import matplotlib.pyplot as plt
import numpy as np
import sys


def read_charges(filename: str) -> list:
    charges = []
    with open(filename) as f:
        while True:
            try:
                next(f).strip()
                charges.extend(float(x) for x in next(f).strip().split())
            except StopIteration:
                break

    return charges


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Incorrect number of arguments.', file=sys.stderr)
        sys.exit(1)

    ref_charges = read_charges(sys.argv[1])
    new_charges = read_charges(sys.argv[2])

    d = np.array(ref_charges) - np.array(new_charges)
    rmsd = np.sqrt(np.sum(d ** 2) / len(ref_charges))
    print(f'RMSD = {rmsd:.3f}')
    R2 = np.corrcoef(ref_charges, new_charges)[0, 1] ** 2
    print(f'R2 = {R2:.3f}')

    fig, ax = plt.subplots()
    ax.scatter(ref_charges, new_charges, s=10)

    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),
        np.max([ax.get_xlim(), ax.get_ylim()]),
    ]

    ax.plot(lims, lims, 'k-', alpha=0.75, zorder=0)
    ax.set_aspect('equal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    plt.savefig(sys.argv[3])
