#!/usr/bin/env python3
"""
gsl_grazing_water.py

Water-salt-forage-livestock balance for a halophyte grazing operation on the
exposed playa of the Great Salt Lake (GSL), and a dust-suppression accounting
for the revegetated cover. Companion model to the GSL extension paper.

The headline purpose is NOT to show that a large ranch "works" -- it is to
BOUND the livestock element against the basin's binding constraint, which is
water, not salt. The model therefore compares the freshwater demand of a
saline-forage cattle operation against the lake's estimated annual survival
deficit, and identifies the only water-defensible regime (extensive,
non-irrigated grazing on the revegetation cover).

All inputs are sourced or flagged as assumptions. Outputs: console report plus
three PDF figures for the appendix.

Grounding figures (see paper references):
  * GSL survival deficit ~326 billion gal/yr (~1.234 km^3/yr) of additional
    inflow needed (Abbott et al. 2023 GSL emergency report).
  * ~73% of water / ~60% of surface area already lost; ag diversion (mostly
    alfalfa/hay) ~74% of diverted water (Abbott et al. 2023).
  * Exposed lakebed of order ~2,000 km^2 (~800 mi^2; Perry sampling 2016-2018);
    arsenic/mercury-bearing dust; ~2.66 M downwind residents (Utah DWR).
  * Global beef water footprint ~15,400 L/kg, dominated by feed
    (Mekonnen & Hoekstra 2012) -- used only as an external sanity anchor.
  * Halophyte forage / biosaline livestock context: Masters et al. 2007;
    Hasnain 2023; Abebe & Tu 2024; Rao et al. 2017; Alonso et al. 2013.
"""
import numpy as np

# ============================ CONSTANTS / INPUTS ============================
GAL_TO_M3   = 3.785411784e-3        # m3 per US gallon
M3_PER_KM3  = 1.0e9

# ---- GSL binding constraint (grounded) ----
DEFICIT_GAL = 326e9                  # gal/yr additional inflow needed
DEFICIT_KM3 = DEFICIT_GAL * GAL_TO_M3 / M3_PER_KM3
A_PLAYA_KM2 = 2000.0                 # exposed lakebed, order of magnitude
POP_DOWNWIND = 2.66e6                # residents downwind of dust

# ---- animal demand (grounded / assumption) ----
DM_PER_COW   = 4.0                   # t dry matter / cow / yr (~2.5% of 450 kg/day)
DRINK_L_DAY  = 50.0                  # L/day baseline drinking water (beef cow)
SALT_PREMIUM = 2.0                   # multiplier on drinking for saline-forage diet
DRINK_M3_YR  = DRINK_L_DAY * 365 / 1000.0 * SALT_PREMIUM   # m3/cow/yr

# ---- forage productivity & irrigation (assumption bands) ----
# Irrigated, productive halophyte forage:
Y_IRR_LO, Y_IRR_HI = 8.0, 15.0       # t DM / ha / yr
I_IRR_LO, I_IRR_HI = 5000.0, 9000.0  # m3 / ha / yr net irrigation (incl. leaching)
# Non-irrigated / rain-fed extensive (precip ~300 mm desert):
Y_RAINFED = 2.0                      # t DM / ha / yr (extensive, low density)

print("="*72)
print("  GSL HALOPHYTE GRAZING -- WATER-BUDGET BOUNDING MODEL")
print("="*72)
print(f"GSL annual survival deficit: {DEFICIT_GAL:.3e} gal/yr "
      f"= {DEFICIT_KM3:.3f} km^3/yr")
print(f"Exposed playa (dust source): ~{A_PLAYA_KM2:.0f} km^2; "
      f"downwind residents ~{POP_DOWNWIND:.2e}")
print(f"Per-cow forage demand: {DM_PER_COW:.1f} t DM/yr | "
      f"drinking (x{SALT_PREMIUM:.0f} saline premium): {DRINK_M3_YR:.1f} m3/cow/yr\n")

# ===================== 1. PER-COW WATER, IRRIGATED REGIME ====================
def per_cow_water_irrigated(Y, I):
    """Freshwater per cow per year (m3) under irrigated forage."""
    forage_ha_per_cow = DM_PER_COW / Y          # ha needed to feed one cow
    forage_water = forage_ha_per_cow * I        # m3/yr irrigation for that forage
    return forage_water + DRINK_M3_YR, forage_water, DRINK_M3_YR

print("--- 1. PER-COW FRESHWATER, IRRIGATED FORAGE ---")
print(f"{'yield(t/ha)':>11} {'irrig(m3/ha)':>12} {'forage(m3)':>11} "
      f"{'drink(m3)':>10} {'total(m3/cow)':>13}")
for Y in (Y_IRR_LO, Y_IRR_HI):
    for I in (I_IRR_LO, I_IRR_HI):
        tot, f, d = per_cow_water_irrigated(Y, I)
        print(f"{Y:>11.0f} {I:>12.0f} {f:>11.0f} {d:>10.1f} {tot:>13.0f}")
print("  (forage irrigation dominates drinking by ~50-150x)\n")

# ============== 2. HERD SIZE AT WHICH DEMAND = LAKE DEFICIT ==================
print("--- 2. IRRIGATED HERD SIZE THAT CONSUMES THE ENTIRE LAKE DEFICIT ---")
deficit_m3 = DEFICIT_KM3 * M3_PER_KM3
for label, (Y, I) in {
    "best case (15 t/ha, 5000 m3/ha)": (Y_IRR_HI, I_IRR_LO),
    "central   (10 t/ha, 7000 m3/ha)": (10.0, 7000.0),
    "worst case (8 t/ha, 9000 m3/ha)": (Y_IRR_LO, I_IRR_HI),
}.items():
    per_cow, _, _ = per_cow_water_irrigated(Y, I)
    n_break = deficit_m3 / per_cow
    print(f"  {label}: {per_cow:>5.0f} m3/cow -> {n_break:>10,.0f} cows "
          f"= entire {DEFICIT_KM3:.2f} km^3/yr deficit")
print("  Context: US beef-cow herd ~28-30 million; Utah ~0.8 M cattle.")
print("  => An IRRIGATED operation of only a few hundred-thousand head consumes")
print("     all the water the lake needs to survive. 'Super-large-scale' is out.\n")

# ============= 3. NON-IRRIGATED EXTENSIVE REGIME (THE DEFENSIBLE ONE) ========
print("--- 3. NON-IRRIGATED EXTENSIVE GRAZING (water-defensible regime) ---")
ha_per_cow_rf = DM_PER_COW / Y_RAINFED       # ha/cow rain-fed
# Max herd if the ENTIRE exposed playa is revegetated and grazed extensively:
playa_ha = A_PLAYA_KM2 * 100.0               # 1 km2 = 100 ha
n_max = playa_ha / ha_per_cow_rf
water_nmax_km3 = n_max * DRINK_M3_YR / M3_PER_KM3
print(f"  Rain-fed yield {Y_RAINFED:.0f} t DM/ha -> {ha_per_cow_rf:.1f} ha/cow")
print(f"  If ALL ~{A_PLAYA_KM2:.0f} km^2 playa is revegetated & grazed: "
      f"max ~{n_max:,.0f} cows")
print(f"  Their drinking water: {water_nmax_km3:.5f} km^3/yr "
      f"= {100*water_nmax_km3/DEFICIT_KM3:.2f}% of the lake deficit (negligible)")
print("  => Livestock is defensible only as a low-density co-product of")
print("     revegetation; water is negligible, but the ceiling is ~10^5 head,")
print("     i.e. a fraction of one state's herd -- not an industrial beef source.\n")

# ===================== 4. DUST SUPPRESSION (the real product) ===============
print("--- 4. DUST-SUPPRESSION BENEFIT (decoupled from cattle) ---")
EMIS_CUT = 0.85          # fractional reduction in wind erosion over vegetated cover
for frac in (0.10, 0.25, 0.50, 1.00):
    a_veg = frac * A_PLAYA_KM2
    print(f"  Revegetate {frac*100:>3.0f}% of playa ({a_veg:>6.0f} km^2): "
          f"~{EMIS_CUT*frac*100:>4.1f}% basin dust-flux reduction "
          f"(arsenic-bearing PM10 over {POP_DOWNWIND:.2e} residents)")
print("  The dust benefit scales with VEGETATED AREA, independent of cattle.\n")

# ---- external sanity anchor: beef water footprint ----
WF_BEEF = 15400.0        # L/kg beef (Mekonnen & Hoekstra 2012)
print("--- external sanity anchor ---")
print(f"  Global beef water footprint ~{WF_BEEF:,.0f} L/kg (feed-dominated);")
print("  consistent with irrigation, not drinking, being the binding term.\n")

# ============================== PLOTS =======================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 11, "figure.dpi": 140,
                     "axes.spines.top": False, "axes.spines.right": False})

herds = np.logspace(3, 7, 200)      # 1e3 .. 1e7 cows

# Fig A: freshwater demand vs herd size, irrigated bands + rain-fed, deficit line
figA, axA = plt.subplots(figsize=(6.6, 4.4))
pc_best, _, _ = per_cow_water_irrigated(Y_IRR_HI, I_IRR_LO)
pc_worst, _, _ = per_cow_water_irrigated(Y_IRR_LO, I_IRR_HI)
dem_best  = herds * pc_best  / M3_PER_KM3
dem_worst = herds * pc_worst / M3_PER_KM3
dem_rf    = herds * DRINK_M3_YR / M3_PER_KM3
axA.fill_between(herds, dem_best, dem_worst, color="crimson", alpha=0.18,
                 label="irrigated forage (band)")
axA.plot(herds, dem_best, color="crimson", lw=1.5)
axA.plot(herds, dem_worst, color="crimson", lw=1.5)
axA.plot(herds, dem_rf, color="green", lw=2.2, label="non-irrigated (drinking only)")
axA.axhline(DEFICIT_KM3, color="navy", lw=2.0, ls="--",
            label=f"GSL survival deficit ({DEFICIT_KM3:.2f} km$^3$/yr)")
# mark where irrigated crosses deficit
nx_best  = deficit_m3 / pc_best
nx_worst = deficit_m3 / pc_worst
axA.axvspan(nx_worst, nx_best, color="navy", alpha=0.08)
axA.set_xscale("log"); axA.set_yscale("log")
axA.set_xlabel("Herd size (head)")
axA.set_ylabel("Freshwater demand (km$^3$/yr)")
axA.set_title("Cattle freshwater demand vs the lake's survival deficit\n"
              "(irrigated forage crosses the deficit at ~10$^5$-10$^6$ head)")
axA.legend(frameon=False, fontsize=9, loc="upper left")
figA.tight_layout(); figA.savefig("fig_gsl_water_vs_herd.pdf")

# Fig B: defensible regime -- land footprint & drinking water vs herd (rain-fed)
figB, axB = plt.subplots(figsize=(6.6, 4.4))
land_km2 = herds * ha_per_cow_rf / 100.0
axB.plot(herds, land_km2, color="green", lw=2.2, label="grazing land required (km$^2$)")
axB.axhline(A_PLAYA_KM2, color="saddlebrown", ls=":", lw=1.8,
            label=f"exposed playa available (~{A_PLAYA_KM2:.0f} km$^2$)")
axB.axvline(n_max, color="gray", ls="--", lw=1.2)
axB.text(n_max*0.62, A_PLAYA_KM2*1.25, f"ceiling ~{n_max:,.0f} head",
         fontsize=9, color="gray")
axB.set_xscale("log"); axB.set_yscale("log")
axB.set_xlabel("Herd size (head)")
axB.set_ylabel("Grazing land required (km$^2$)")
axB.set_title("Non-irrigated extensive regime: land, not water, is the limit\n"
              "(drinking water stays <1% of the lake deficit throughout)")
axB.legend(frameon=False, fontsize=9, loc="upper left")
figB.tight_layout(); figB.savefig("fig_gsl_defensible_regime.pdf")

# Fig C: dust-flux reduction vs revegetated area (the actual product)
figC, axC = plt.subplots(figsize=(6.6, 4.2))
fr = np.linspace(0, 1, 100)
axC.plot(fr*A_PLAYA_KM2, EMIS_CUT*fr*100, color="darkorange", lw=2.5)
axC.fill_between(fr*A_PLAYA_KM2, 0, EMIS_CUT*fr*100, color="darkorange", alpha=0.15)
axC.set_xlabel("Revegetated playa area (km$^2$)")
axC.set_ylabel("Basin dust-flux reduction (%)")
axC.set_title("Dust suppression scales with vegetated area, not herd size\n"
              f"(arsenic-bearing PM10 over ~{POP_DOWNWIND/1e6:.2f} M downwind residents)")
figC.tight_layout(); figC.savefig("fig_gsl_dust_benefit.pdf")

print("Wrote: fig_gsl_water_vs_herd.pdf, fig_gsl_defensible_regime.pdf, "
      "fig_gsl_dust_benefit.pdf")
