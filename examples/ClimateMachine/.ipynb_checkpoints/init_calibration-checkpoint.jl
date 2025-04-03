using Distributions
using ArgParse
# Import EnsembleKalmanProcesses modules
using EnsembleKalmanProcesses
using EnsembleKalmanProcesses.ParameterDistributions
include(joinpath(@__DIR__, "helper_funcs.jl"))


param_names = ["alpha", "Source_Lev_01", "Source_Lev_02"]

# Set parameter priors
prior_smag = constrained_gaussian(param_names[1], 0.5, 0.05, -Inf, Inf)
prior_drag = constrained_gaussian(param_names[2], 1e-3, 1e-4, -Inf, Inf)
prior_X = constrained_gaussian(param_names[3], 0.6, 0.06, -Inf, Inf)
priors = combine_distributions([prior_smag, prior_drag, prior_X])

# Construct initial ensemble
N_ens = 30
initial_params = construct_initial_ensemble(priors, N_ens)
# Generate CLIMAParameters files
params_arr = [row[:] for row in eachrow(initial_params')]
versions = map(param -> generate_cm_params(param, param_names), params_arr)

# Store version identifiers for this ensemble in a common file
open("versions_1.txt", "w") do io
    for version in versions
        write(io, "clima_param_defs_$(version).jl\n")
    end
end
