DELTA_TIME = 1  # days each timestep
SIMULATION_TIME_MONTHS = 24  # number of months
TIMESTEPS = (
    30 * SIMULATION_TIME_MONTHS // DELTA_TIME
)  # number of simulation timesteps
MONTE_CARLO_RUNS = 1  # number of runs

# Cold start phase parameters (add these)
COLD_START_DURATION_MONTHS = SIMULATION_TIME_MONTHS   # Duration in epochs (timesteps)
COLD_START_DURATION_TIMESTEPS = (
    COLD_START_DURATION_MONTHS * 30 // DELTA_TIME
)