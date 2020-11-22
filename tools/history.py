import sys
import matplotlib.pyplot as plt


def main():
    gens = []
    rmsd_med = []
    rmsd_min = []
    r2_med = []
    r2_max = []
    fig = plt.figure()
    ax1 = fig.add_subplot('211')
    ax2 = fig.add_subplot('212')

    with open(sys.argv[1]) as f:
        file_iter = iter(f)
        line = next(file_iter)
        # Skip all lines before the actual stats
        while True:
            if line.strip() == '*** Statistics over generations ***':
                next(file_iter)
                next(file_iter)
                next(file_iter)
                break
            line = next(file_iter)

        for line in file_iter:
            if not line.strip():
                break
            data = line.split()
            gens.append(int(data[0]))
            rmsd_med.append(float(data[3]))
            rmsd_min.append(float(data[2]))
            r2_med.append(float(data[6]))
            r2_max.append(float(data[7]))
    plt.xlabel('Generations')
    ax1.plot(gens, rmsd_med, label='Median', alpha=0.8)
    ax1.plot(gens, rmsd_min, label='Min', c='red', alpha=0.8)
    ax1.title.set_text('RMSD')
    ax2.plot(gens, r2_med, label='Median', alpha=0.8)
    ax2.plot(gens, r2_max, label='Max', c='red', alpha=0.8)
    ax2.title.set_text('R2')
    ax1.legend()

    ax2.legend()
    plt.show()


if __name__ == '__main__':
    main()
