#!/usr/bin/env python3
"""
gsl_dynamic_simulation.py

Multi-Year Dynamic Water-Salt-Forage-Livestock Simulation Engine
Adapts the methodology of Alonso et al. (2013) to the Great Salt Lake playa.

Tracks root-zone soil water/salt accumulation, salinity-dependent halophyte yield 
decay (Maas-Hoffman model), metabolic livestock salt-excretion demands, and 
cumulative water-budget impacts on the basin over a 20-year predictive horizon.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class GSLBiosalineSimulation:
    def __init__(self, years=20, initial_ECe=8.0, irrigation_regime="brackish"):
        self.years = years
        self.dt = 1.0  # Time step: 1 year
        self.time_steps = int(self.years / self.dt)
        
        # --- Basin & Climate Inputs ---
        self.precip = 0.30            # Annual precipitation (m/yr, ~300mm)
        self.playa_area_ha = 200000.0 # Total exposed playa area (2,000 km^2 to hectares)
        self.GSL_deficit_m3 = 1.234e9 # 1.234 km^3/yr survival deficit
        
        # --- Soil Hydrology & Salinity (Alonso et al. Parameters) ---
        self.root_zone_depth = 1.0    # meters
        self.soil_porosity = 0.40     
        self.field_capacity = 0.25    
        self.leaching_fraction = 0.15 # Fraction of water passing past root zone
        
        # Select irrigation water quality (ECw in dS/m)
        if irrigation_regime == "brackish":
            self.EC_w = 4.0           # Shallow brackish groundwater
            self.irrigation_volume = 0.70  # m/yr applied (7,000 m3/ha/yr)
        elif irrigation_regime == "hypersaline":
            self.EC_w = 25.0          # Direct lake brine pumping
            self.irrigation_volume = 0.90  # Higher volume needed for leaching
        else:  # Rain-fed / Extensive
            self.EC_w = 0.0
            self.irrigation_volume = 0.0

        # --- Forage Yield Crop Parameters (Distichlis spicata / Saltgrass) ---
        self.Y_max = 14.0             # Max yield under zero stress (t DM/ha/yr)
        self.salinity_threshold = 10.0 # Threshold soil ECe before yield decline (dS/m)
        self.salinity_slope = 0.022   # 2.2% yield drop per dS/m above threshold
        
        # --- Livestock Parameters ---
        self.cow_DM_requirement = 4.0 # t DM/cow/yr
        self.base_drinking_m3 = 18.25 # Baseline clean drinking water (50 L/day)
        
        # --- Initialize State Trajectories ---
        self.EC_e_history = np.zeros(self.time_steps)
        self.yield_history = np.zeros(self.time_steps)
        self.max_herd_history = np.zeros(self.time_steps)
        self.total_water_consumption = np.zeros(self.time_steps)
        
        self.EC_e = initial_ECe

    def maas_hoffman_yield(self, EC_e):
        """Calculates salinity-stressed forage yield."""
        if EC_e <= self.salinity_threshold:
            return self.Y_max
        else:
            yield_fraction = 1.0 - self.salinity_slope * (EC_e - self.salinity_threshold)
            return max(0.0, self.Y_max * yield_fraction)

    def calculate_drinking_premium(self, forage_salinity):
        """Computes animal drinking water scaling due to physiological salt loads."""
        # Higher forage salt forces increased renal flushing
        if forage_salinity < 10.0:
            return 1.0
        return min(3.5, 1.0 + 0.12 * (forage_salinity - 10.0))

    def run_simulation(self):
        for t in range(self.time_steps):
            # 1. Update Root-Zone Soil Salinity (Mass Balance of Salts)
            # EC_e acts as a proxy for total dissolved solids accumulation
            salt_in = self.irrigation_volume * self.EC_w
            salt_out = self.leaching_fraction * self.irrigation_volume * (self.EC_e * 1.5)
            
            # Change in soil solution salinity concentration
            delta_EC_e = (salt_in - salt_out) / (self.root_zone_depth * self.field_capacity)
            self.EC_e = max(1.0, self.EC_e + delta_EC_e * self.dt)
            
            # 2. Compute Stressed Forage Yield
            current_yield = self.maas_hoffman_yield(self.EC_e)
            
            # 3. Calculate Dynamic Carrying Capacity of the Playa Footprint
            if current_yield > 0.1:
                ha_per_cow = self.cow_DM_requirement / current_yield
                # Assuming 25% of the total playa is put under active cultivation
                target_area = 0.25 * self.playa_area_ha
                max_sustainable_herd = target_area / ha_per_cow
            else:
                max_sustainable_herd = 0.0
            
            # 4. Determine Dynamic Water Footprint
            # Forage salt content mirrors soil solution concentration
            drinking_multiplier = self.calculate_drinking_premium(self.EC_e)
            per_head_drinking = self.base_drinking_m3 * drinking_multiplier
            
            irrigation_total = (0.25 * self.playa_area_ha) * self.irrigation_volume * 10000.0 / 1e9 # m3
            herd_drinking_total = max_sustainable_herd * per_head_drinking
            total_water_m3 = irrigation_total + herd_drinking_total

            # Save state metrics
            self.EC_e_history[t] = self.EC_e
            self.yield_history[t] = current_yield
            self.max_herd_history[t] = max_sustainable_herd
            self.total_water_consumption[t] = total_water_m3

def generate_plots():
    years_arr = np.arange(1, 21)
    
    # Run Scenarios
    sim_brackish = GSLBiosalineSimulation(years=20, initial_ECe=8.0, irrigation_regime="brackish")
    sim_brackish.run_simulation()
    
    sim_hyper = GSLBiosalineSimulation(years=20, initial_ECe=8.0, irrigation_regime="hypersaline")
    sim_hyper.run_simulation()

    plt.rcParams.update({"font.size": 10, "figure.dpi": 130, "axes.spines.right": False, "axes.spines.top": False})
    fig, axs = plt.subplots(2, 2, figsize=(11, 8))

    # Plot 1: Soil Salinity Degradation
    axs[0, 0].plot(years_arr, sim_brackish.EC_e_history, color="blue", lw=2, label="Brackish Pumping (4 dS/m)")
    axs[0, 0].plot(years_arr, sim_hyper.EC_e_history, color="crimson", lw=2, label="Lake Brine Pumping (25 dS/m)")
    axs[0, 0].set_ylabel("Soil Solution Salinity $EC_e$ (dS/m)")
    axs[0, 0].set_xlabel("Years of Continuous Operation")
    axs[0, 0].set_title("Topsoil Salinity Accumulation")
    axs[0, 0].legend(frameon=False)

    # Plot 2: Forage Yield Loss
    axs[0, 1].plot(years_arr, sim_brackish.yield_history, color="blue", lw=2)
    axs[0, 1].plot(years_arr, sim_hyper.yield_history, color="crimson", lw=2)
    axs[0, 1].set_ylabel("Forage Yield $Y$ (t DM/ha/yr)")
    axs[0, 1].set_xlabel("Years of Continuous Operation")
    axs[0, 1].set_title("Halophyte Crop Yield Collapse (Maas-Hoffman)")

    # Plot 3: Dynamic Sustainable Stocking Capacity
    axs[1, 0].plot(years_arr, sim_brackish.max_herd_history / 1e3, color="blue", lw=2)
    axs[1, 0].plot(years_arr, sim_hyper.max_herd_history / 1e3, color="crimson", lw=2)
    axs[1, 0].set_ylabel("Max Sustainable Herd ($10^3$ Head)")
    axs[1, 0].set_xlabel("Years of Continuous Operation")
    axs[1, 0].set_title("System Carrying Capacity Trajectory")

    # Plot 4: Basin Water Impact vs GSL Deficit
    gsl_deficit_km3 = 1.234
    axs[1, 1].plot(years_arr, sim_brackish.total_water_consumption / 1e9, color="blue", lw=2, label="Brackish Operation Demand")
    axs[1, 1].plot(years_arr, sim_hyper.total_water_consumption / 1e9, color="crimson", lw=2, label="Lake Brine Operation Demand")
    axs[1, 1].axhline(gsl_deficit_km3, color="darkblue", ls="--", lw=1.5, label="Total GSL Survival Deficit")
    axs[1, 1].set_ylabel("Freshwater Consumption (km$^3$/yr)")
    axs[1, 1].set_xlabel("Years of Continuous Operation")
    axs[1, 1].set_title("Water Consumption vs Lake Deficit Threshold")
    axs[1, 1].legend(frameon=False, loc="lower right")

    plt.tight_layout()
    plt.savefig("fig_gsl_dynamic_predictions.pdf")
    print("Successfully generated: fig_gsl_dynamic_predictions.pdf")

if __name__ == "__main__":
    generate_plots()
