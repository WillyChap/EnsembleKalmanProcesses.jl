import Pkg
Pkg.activate(@__DIR__)
using Distributions
using ArgParse
using Random
using NCDatasets
using EnsembleKalmanProcesses
using EnsembleKalmanProcesses.ParameterDistributions


# Define discrete values
levs = [
    103.564777, 111.232861, 119.468701, 128.314335, 137.814911, 148.018925,
    158.978458, 170.74945, 183.391984, 196.970589, 211.554573, 227.218376,
    244.04195, 262.111165, 281.51825, 302.362264, 324.749599, 348.794524,
    374.61977, 402.357153, 432.148253, 464.145127, 498.511097, 535.421572,
    574.253445, 612.859539, 649.191852, 682.746052, 713.734565, 742.353574,
    768.78426, 793.193951, 815.737181, 836.556666, 855.78421, 873.541541,
    889.941075, 905.086637, 919.074108, 931.992043, 943.92222, 954.94017,
    965.115643, 974.513059, 983.191911, 991.207145, 997.527726
]

function gaussian_index_prior_probs(μ::Int64, σ::Int64)
    prior_dist = Normal(μ, σ)
    probs = pdf.(prior_dist, indices)
    return probs ./ sum(probs)  # Normalize
end


param_names = ["psteer", "plaunch", "source"]

# Set parameter priors
indices = collect(1:length(levs))
# Get prior probabilities
probs_psteer = gaussian_index_prior_probs(27, 5)
probs_plaunch = gaussian_index_prior_probs(17, 5)

# Make Categorical over indices
cat_dist_psteer = Categorical(probs_psteer)
cat_dist_plaunch = Categorical(probs_plaunch)

# wrap this into Parameterized
param_dist_psteer = Parameterized(cat_dist_psteer)
param_dist_plaunch = Parameterized(cat_dist_plaunch)

# Now create param_dict
param_dict_psteer = Dict(
    "distribution" => param_dist_psteer,
    "constraint" => no_constraint(),
    "name" => param_names[1]
)

param_dict_plaunch = Dict(
    "distribution" => param_dist_plaunch,
    "constraint" => no_constraint(),
    "name" => param_names[2]
)

# Finally
prior_psteer = ParameterDistribution(param_dict_psteer)
prior_plaunch = ParameterDistribution(param_dict_plaunch)
prior_source = constrained_gaussian(param_names[3], 1, 0.2, 0, 3)

priors = combine_distributions([prior_psteer, prior_plaunch, prior_source]);

# Construct initial ensemble
N_ens = 30
rng_seed = 44

rng = Random.seed!(Random.GLOBAL_RNG, rng_seed)
initial_params = construct_initial_ensemble(rng, priors, N_ens)

# for making sure that the steering level is always below the launch level.
for j in 1:N_ens
    if initial_params[2, j] > initial_params[1, j]
        # Swap the values in column j of row 1 and row 2 using tuple assignment
        initial_params[1, j], initial_params[2, j] = initial_params[2, j], initial_params[1, j]
    end
end

println("Is every element of row 2 smaller than row 1? ",
    all(initial_params[2, :] .<= initial_params[1, :]))

# to transform unconstrained to constrained params: impacts only prior_source.
initial_params_constrained = transform_unconstrained_to_constrained(priors, initial_params)

# to replace indices with pressue levels. 
initial_params_constrained[1, 1:end] =  levs[map(Int, initial_params_constrained[1, 1:end])]
initial_params_constrained[2, 1:end] =  levs[map(Int, initial_params_constrained[2, 1:end])]

# Open a new NetCDF file
ds = Dataset("./Initial_Parameters.nc", "c")

# Determine ensemble size
ensemble_size = size(initial_params_constrained, 2)

# Define the "ensemble" dimension with the given size
defDim(ds, "ensemble", ensemble_size)

# Create a coordinate variable "ensemble" that goes from 1 to ensemble_size
ens_var = defVar(ds, "ensemble", Int64, ("ensemble",))
ens_var[:] = 1:ensemble_size

for (i, pname) in enumerate(param_names)
    # Create a variable for each parameter with dimension "ensemble"
    var = defVar(ds, pname, Float64, ("ensemble",))
    # Populate the variable with the corresponding row
    var[:] = initial_params_constrained[i, :]
end

# Close the dataset
close(ds)