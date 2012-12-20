from sys import argv

import numpy as np
import matplotlib.pyplot as plt


def get_data():
    """Grab crc data from file."""
    fname = 'crc-data'
    f = open(fname)
    f.seek(0)
    d = f.readlines()

    # specify substances and the line index at which they occur
    substances = [('Glycerol', 4), ('NaCl', 14), ('MKP', 24)]
    fields = ['wt.', 'density', 'n', 'viscosity']

    data = {}
    for substance, o in substances:
        data[substance] = {}
        for i, f in enumerate(fields):
            # work out the line number
            l = 2 * (i + 1) + o
            # get the line
            line = d[l].split('\n')[0].split(',')
            # fill in the field
            data[substance][f] = np.array([float(v) for v in line])

    return data


def calc_coefficients(data, substance, x, y):
    """Assuming a straight line fit, calculate (m,c) for specific
    values of x, y (density, n, etc.) for a specific substance.
    """
    m, c = np.polyfit(data[substance][x], data[substance][y], 1)
    return m, c


def n_sensitivity(substance, n, volume=None, dn=0.0001):
    """A prototype experimental n-matching procedure is to mix the
    Glycerol phase to the required density and then measure the
    refractive index, n_gly. The mkp phase is then mixed such that
    n_mkp == n_gly and the density recorded.

    What we want to know is how accurately we can set n_mkp; i.e. for
    the total volume of the lock, what is the quantity of mkp that
    corresponds to dn = 0.0001? If we can't set n to within dn, we are
    a bit stuck.

    Essentially, we can *measure* n to within dn but if we can't
    *control* it to the same precision then this method won't work.

    This function calculates the required mass precision for a given
    substance at a given n and volume, with dn=0.0001 by default.

    Returns: dm, the mass precision.
    """
    # volume for the substance specified
    volumes = {'Glycerol': 0.2 * 0.25 * 5.5, 'MKP': 0.2 * 0.25 * 0.25}
    if not volume:
        volume = volumes[substance]

    d = get_data()
    # calc density at the given n
    m_rn, c_rn = calc_coefficients(d, substance, 'n', 'density')
    rho = m_rn * n + c_rn
    # total mass
    M = volume * rho * 1000
    # variation of n with % wt.
    m, c = calc_coefficients(d, substance, 'wt.', 'n')
    dwt = dn / m
    dm = M * dwt / 100

    print rho
    print volume
    print M
    print dwt
    print dm

    return dm


def cost(ratio):
    """Takes desired density difference or ratio as input and
    calculates the cost of a run based on unit costs of glycerol
    and mkp.
    Outputs: cost of run, quantities of gly/mkp, required n.
    """
    # determine coefficients
    d = get_data()
    C_g = calc_coefficients(d, 'Glycerol', 'n', 'density')
    C_k = calc_coefficients(d, 'MKP', 'n', 'density')

    # if specified difference
    if ratio < 1:
        diff = ratio
        # calculate n
        n = (diff - (C_k[1] - C_g[1])) / (C_k[0] - C_g[0])
    # if specified ratio
    elif ratio >= 1:
        n = - (C_k[1] - ratio * C_g[1]) / (C_k[0] - ratio * C_g[0])

    # calculate densities of fluids
    r_k = C_k[0] * n + C_k[1]
    r_g = C_g[0] * n + C_g[1]

    # volumes of fluid
    v_lock = 0.25 * 0.25 * 0.2
    v_flume = 5 * 0.25 * 0.2

    # calculate wt. % from n
    M_g = calc_coefficients(d, 'Glycerol', 'n', 'wt.')
    M_k = calc_coefficients(d, 'MKP', 'n', 'wt.')

    # % wt.
    mwt_g = M_g[0] * n + M_g[1]
    mwt_k = M_k[0] * n + M_k[1]

    m_g = round(v_flume * r_g * 1000 * mwt_g / 100, 3)
    m_k = round(v_lock * r_k * 1000 * mwt_k / 100, 3)
    # unit costs (gbp/kg)
    ucost_g = 1.1
    ucost_k = 25

    # total costs
    tcost_g = round(ucost_g * m_g, 2)
    tcost_k = round(ucost_k * m_k, 2)
    total = round(tcost_k + tcost_g, 2)

    # solution volume specfic mass (mass of solute per litre solution)
    # mv_g = r_g * mwt_g / 100
    # mv_k = r_k * mwt_k / 100

    # density of water (g/cm^3)
    r_w = 0.9982
    # water volume specific mass (mass of solute per litre water)
    mvw_g = mwt_g / (100 - mwt_g) * r_w
    mvw_k = mwt_k / (100 - mwt_k) * r_w

    print("Density ratio/diff of %s" % ratio)
    print("Requires n = %s" % round(n, 4))
    print("MKP: density = %.4f, total mass = %skg @ %.2f%%mass (%.3fg / 250ml water) " % (r_k, m_k, mwt_k, mvw_k * 1000 / 4))
    print("cost = %sgbp @ %sgbp/kg" % (tcost_k, ucost_k))
    print("Gly: density = %.4f, total mass = %skg @ %.2f%%mass (%.3fg / 250ml water) " % (r_g, m_g, mwt_g, mvw_g * 1000 / 4))
    print("cost = %sgbp @ %sgbp/kg" % (tcost_g, ucost_g))
    print("Total cost is %sgbp" % total)

    return total


def plot_cost():
    r = np.linspace(1, 1.10)
    c = map(cost, r)
    plt.plot(r, c)
    plt.xlabel(r'ratio of densities, $\rho_c / \rho_0$')
    plt.ylabel(u'Cost (\u00A3)')
    plt.xlim(1, 1.11)
    plt.savefig('cost_vs_density.png')


def plot():
    d = get_data()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # gly_n = d['Glycerol']['n']
    # nacl_n = d['NaCl']['n']
    # mkp_n = d['MKP']['n']
    # gly_r = d['Glycerol']['density']
    # nacl_r = d['NaCl']['density']
    # mkp_r = d['MKP']['density']

    # nacl_eta = d['NaCl']['viscosity']
    # sub_gly = d['Glycerol']['viscosity'][:len(nacl_eta)]
    # deta_gly_nacl = ( sub_gly / nacl_eta )

    # gly_c = np.polyfit(gly_n, gly_r, 1)
    # nacl_c = np.polyfit(nacl_n, nacl_r, 1)
    # mkp_c = np.polyfit(mkp_n, mkp_r, 1)
    gly_c = calc_coefficients(d, 'Glycerol', 'n', 'density')
    nacl_c = calc_coefficients(d, 'NaCl', 'n', 'density')
    mkp_c = calc_coefficients(d, 'MKP', 'n', 'density')

    n = np.linspace(1.333, 1.35)
    gly_R = n * gly_c[0] + gly_c[1]
    nacl_R = n * nacl_c[0] + nacl_c[1]
    mkp_R = n * mkp_c[0] + mkp_c[1]

    ax.plot(n, mkp_R - gly_R, label=r'$\Delta\rho_{mkp-gly}$')
    ax.plot(n, nacl_R - gly_R, label=r'$\Delta\rho_{nacl-gly}$')
    # ax.plot(gly_n, gly_r, label='Gly')
    # ax.plot(nacl_n, nacl_r, label='NaCl')
    # ax.plot(mkp_n, mkp_r, label='MKP')
    ax.set_xlim(1.333, 1.35)
    ax.set_ylim(0, 0.1)
    ax.set_xlabel('Refractive index, n')
    ax.set_ylabel(r'Density difference, $g/cm^3$')
    ax.grid()
    ax.legend(loc=0)

    # ax2 = ax.twinx()
    # ax2.plot(nacl_n, deta_gly_nacl, label='delta eta')
    # ax2.legend(loc=0)

    plt.show()

if __name__ == '__main__':
    cost(float(argv[1]))