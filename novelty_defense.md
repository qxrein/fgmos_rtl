# Novelty Defense — FGMOS RTL Reconfigurable Logic Fabric

## Ohmic FGMOS-as-Resistor vs. Wisland 2003 Inverter Topology

Wisland et al. (2003) bias the floating-gate device in saturation as a voltage-mode CMOS inverter: the FGMOS sets a switching threshold, but the transistor still operates as a strong-inversion switch/amplifier. Logic is encoded in complementary pull-up/pull-down thresholds, not in a tunable channel resistance.

This work places the same Sky130 FGMOS exclusively in the ohmic (triode) region, where \(I_{ds} \approx k_n (W/L)(V_{fg,\mathrm{eff}} - V_{th0}) V_{ds}\) holds only when \(V_{ds} < V_{fg,\mathrm{eff}} - V_{th0}\). That constraint is checked on every `Vout_rtl` evaluation. The fixed base resistor of conventional RTL is replaced by \(R_{\mathrm{eff}} = 1/[k_n (W/L)(V_{fg,\mathrm{eff}} - V_{th0})]\). Reconfigurable NOR/MAJ/AND behavior follows from impedance ratios in a resistor–transistor divider, not from inverter threshold programming—mechanistically distinct from Wisland’s saturation/inverter paradigm.

## kT/C p-bit vs. Kim 2024 Bistable Resistor

Kim et al. (2024) obtain probabilistic bits from bistable resistive elements fabricated with non-standard 8-inch CMOS extensions. Stochasticity is material-engineered at the resistive switching layer.

Here, randomness is CMOS-native: thermal and partial-charge uncertainty on the floating node with \(C_T = 30\,\mathrm{fF}\) gives \(\sigma_0 = \sqrt{kT/C_T} \approx 83\,\mu\mathrm{V}\). Residual charge \(Q_0\) shifts \(V_{th,\mathrm{eff}} = V_{th0} - Q_0/C_T\) to the logic transition; noise then yields a tunable sigmoid \(P(V_{out}=1)\) without MTJs, ReRAM, or custom films—only MIM caps and nfet_01v8 from an open PDK.

## Sky130 Subcircuit and Reviewer Reproducibility

The netlist `fgmos_sky130_subckt.sp` is built from a Level-1 tt-corner NFET (\(W=2\,\mu\mathrm{m}\), \(L=150\,\mathrm{nm}\)) and MIM coupling capacitors (10 fF inputs, 5 fF control, within the 1–100 fF Sky130 range). Capacitive weighting on the floating gate follows established FG-MOS literature and matches the behavioral Python model. Results are reproducible with free ngspice and the open SkyWater PDK; MPW shuttles provide a concrete silicon path, addressing manufacturability concerns without proprietary decks.
