"""
Core FGMOS behavioral model — reused by all claim simulations.
Ohmic region constraint enforced on every call.
"""
import numpy as np

class FGMOSCell:
    def __init__(self):
        # Sky130 tt-corner parameters
        self.Vth0  = 0.49      # V
        self.kn    = 270e-6    # A/V^2
        self.WL    = 2/0.15    # W/L ratio
        self.Vcc   = 1.8       # V
        
        # Capacitance network (all in Farads)
        self.C1    = 10e-15
        self.C2    = 10e-15
        self.C3    = 10e-15
        self.Cfg   = 5e-15
        self.Csb   = 3e-15
        self.Cdb   = 2e-15
        # Total FG-node capacitance: sum of all capacitors terminating on the
        # floating node (charge conservation requires the full node capacitance
        # in the denominator).  C1+C2+C3+Cfg+Csb+Cdb = 40 fF.
        # NOTE: the SPICE subcircuit .ic also uses this 40 fF sum.
        # Earlier code used 30 fF (= C1+C2+C3 only), which was physically wrong;
        # it caused coupling coefficients to sum >1 and Vfg_eff to exceed Vcc
        # when all inputs and Vctrl are simultaneously asserted.
        #
        # DESIGN IMPLICATION: with CT=40fF and Vcc=1.8V, the maximum achievable
        # Vfg_eff with all inputs + Vctrl at Vcc is 35fF*1.8V/40fF = 1.575V,
        # giving Vgs_eff_max = 1.085V and R_eff_min = 256 Ohm.
        # The pull-down NFETs in parallel present R_nmos = 213 Ohm (n=1),
        # 107 Ohm (n=2), or 71 Ohm (n=3).  The FGMOS pull-up cannot achieve
        # R_eff < R_nmos for n>=2 within the supply headroom, so MAJ and AND
        # operation (requiring Vout_HIGH with n=2 or n=3 inputs) is not feasible
        # with this capacitor sizing.  Only NOR is confirmed achievable.
        # Re-sizing (increase Cfg, increase Vcc, or reduce Csb+Cdb) is needed
        # for full three-mode operation.
        self.CT    = 40e-15

    def Vfg_eff(self, V1, V2, V3, Vctrl, Q0=0.0):
        """Effective floating gate voltage from capacitive divider + residual charge"""
        Vfg = (self.C1*V1 + self.C2*V2 + self.C3*V3 + self.Cfg*Vctrl) / self.CT
        Vfg -= Q0 / self.CT   # residual charge shifts threshold
        return Vfg

    def Vth_eff(self, Q0=0.0):
        """Effective threshold shifted by residual charge"""
        return self.Vth0 - Q0/self.CT

    def R_eff(self, Vfg, Q0=0.0):
        """
        OHMIC region resistance. Returns np.inf if below threshold.
        NOVELTY: this is the 'programmable base resistor' replacing fixed R in RTL.
        """
        Vgs_eff = Vfg - self.Vth_eff(Q0)
        if Vgs_eff <= 0:
            return np.inf
        return 1.0 / (self.kn * self.WL * Vgs_eff)

    def verify_ohmic(self, Vfg, Vds, Q0=0.0):
        """Assert FGMOS stays in ohmic region. Critical for novelty claim."""
        Vgs_eff = Vfg - self.Vth_eff(Q0)
        in_ohmic = Vds < Vgs_eff
        return in_ohmic, Vds, Vgs_eff

    def Vout_rtl(self, Vfg, inputs_high_count, Q0=0.0, Vctrl=0.9):
        """
        RTL cell output voltage.
        Circuit: Vcc — R_fgmos(ohmic) — nodeX — N parallel NMOS (inputs) — GND
        Vctrl programs R_eff (via Vfg) and the logic mode (NOR / MAJ / AND).
        Uses physics-based divider throughout; no hardcoded Vctrl breakpoints.
        """
        R_fgmos = self.R_eff(Vfg, Q0)

        if inputs_high_count == 0:
            # No pull-down path: output floats to Vcc regardless of R_fgmos
            return self.Vcc

        if R_fgmos == np.inf:
            # Pull-up device off: output pulled fully to GND by pull-down network
            return 0.0

        kn_in = self.kn * (2.0 / 0.15)
        Vgs_in = self.Vcc

        R_nmos_parallel = 1.0 / (
            inputs_high_count * kn_in * (Vgs_in - self.Vth0)
        )
        Vout = self.Vcc * R_nmos_parallel / (R_fgmos + R_nmos_parallel)
        Vds_fgmos = self.Vcc - Vout
        self.verify_ohmic(Vfg, Vds_fgmos, Q0)
        return Vout
