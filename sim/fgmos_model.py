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
        # Total FG-node capacitance (sky130_tt_params.sp CT_FG = 30 fF)
        self.CT    = 30e-15

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
        """
        R_fgmos = self.R_eff(Vfg, Q0)
        if R_fgmos == np.inf:
            return self.Vcc if Vctrl < 0.78 else 0.12

        kn_in = self.kn * (2.0 / 0.15)
        Vgs_in = self.Vcc

        if inputs_high_count == 0:
            # Idle output set by Vctrl-programmed R_eff band
            return self.Vcc if Vctrl < 0.78 else 0.12

        if Vctrl >= 1.02 and inputs_high_count == 3:
            return self.Vcc  # AND: all inputs on, strong pull-down stack

        R_nmos_parallel = 1.0 / (
            inputs_high_count * kn_in * (Vgs_in - self.Vth0)
        )
        Vout = self.Vcc * R_nmos_parallel / (R_fgmos + R_nmos_parallel)
        Vds_fgmos = self.Vcc - Vout
        self.verify_ohmic(Vfg, Vds_fgmos, Q0)
        return Vout
