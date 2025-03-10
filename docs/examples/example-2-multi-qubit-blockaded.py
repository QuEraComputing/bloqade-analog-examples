# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     hide_notebook_metadata: false
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown]
# <a class=md-button href="example-2-multi-qubit-blockaded.py" download> Download Script </a>
# <a class=md-button href="../../assets/data/multi-qubit-blockaded-job.json" download> Download Job </a>
#
# <div class="admonition warning">
# <p class="admonition-title">Job Files for Complete Examples</p>
# <p>
# To be able to run the complete examples without having to submit your program to hardware and wait, you'll
# need to download the associated job files. These files contain the results of running the program on
# the quantum hardware.
#
# You can download the job files by clicking the "Download Job" button above. You'll then need to place
# the job file in the `data` directory that was created for you when you ran the `import` part of the script
# (alternatively you can make the directory yourself, it should live at the same level as wherever you put this script).
# </p>
# </div>
#

# %% [markdown]
# # Multi-qubit Blockaded Rabi Oscillations
# ## Introduction
# In this tutorial we will show you how to compose geometries with pulse sequences to
# perform multi-qubit blockaded Rabi oscillations. The Physics here is described in
# detail in the [whitepaper](https://arxiv.org/abs/2306.11727). But in short, we can
# use the Rydberg blockade to change the effective Rabi frequency of the entire system
# by adding more atoms to the cluster.
# %%
import os

import numpy as np
import matplotlib.pyplot as plt
from bloqade.analog import load, save, start
from bloqade.analog.atom_arrangement import Chain, Square

if not os.path.isdir("data"):
    os.mkdir("data")

# %% [markdown]
# ## Defining the Geometry
# We will start by defining the geometry of the atoms. The idea here is to cluster
# the atoms so that they are all blockaded from each other. Using a combination of the
# `Chain` and `Square` classes, as a base, one can add additional atoms to the geometry
# using the `add_position` method. This method takes a list of tuples, or a single
# tuple, of the form `(x,y)` where `x` and `y` are the coordinates of the atom in units
# of the lattice constant.

# %%

distance = 4.0
inv_sqrt_2_rounded = 2.6

geometries = {
    1: Chain(1),
    2: Chain(2, lattice_spacing=distance),
    3: start.add_position(
        [(-inv_sqrt_2_rounded, 0.0), (inv_sqrt_2_rounded, 0.0), (0, distance)]
    ),
    4: Square(2, lattice_spacing=distance),
    7: start.add_position(
        [
            (0, 0),
            (distance, 0),
            (-0.5 * distance, distance),
            (0.5 * distance, distance),
            (1.5 * distance, distance),
            (0, 2 * distance),
            (distance, 2 * distance),
        ]
    ),
}

# %% [markdown]
# ## Defining the Pulse Sequence
# Next, we will define the pulse sequence. We start from the `start` object, which is
# an empty list of atom locations. In this case, we do not need atoms to build the pulse
# sequence, but to extract the sequence, we need to call the `parse_sequence` method.
# This creates a `Sequence` object that we can apply to multiple geometries.
# %%
sequence = start.rydberg.rabi.amplitude.uniform.piecewise_linear(
    durations=["ramp_time", "run_time", "ramp_time"],
    values=[0.0, "rabi_drive", "rabi_drive", 0.0],
).parse_sequence()
# %% [markdown]

# ## Defining the Program
# Now, all that is left to do is to compose the geometry and the Pulse sequence into a
# fully defined program. We can do this by calling the `apply` method on the geometry
# and passing in the sequence. This method will return an object that can then be
# assigned parameters.
# %%
batch = (
    geometries[7]
    .apply(sequence)
    .assign(ramp_time=0.06, rabi_drive=5)
    .batch_assign(run_time=0.05 * np.arange(21))
)

# %% [markdown]
# ## Run Emulator and Hardware
# Again, we run the program on the emulator and Aquila and save the results to a file
# so we can use them later.
#
# <div class="admonition danger">
# <p class="admonition-title">Hardware Execution Cost</p>
# <p>
#
# For this particular program, 21 tasks are generated with each task having 100 shots, amounting to
#  __USD \\$27.30__ on AWS Braket.
#
# </p>
# </div>
# %%

emu_filename = os.path.join(
    os.path.abspath(""), "data", "multi-qubit-blockaded-emulation.json"
)

if not os.path.isfile(emu_filename):
    emu_batch = batch.bloqade.python().run(10000, interaction_picture=True)
    save(emu_batch, emu_filename)

filename = os.path.join(os.path.abspath(""), "data", "multi-qubit-blockaded-job.json")

if not os.path.isfile(filename):
    hardware_batch = batch.parallelize(24).braket.aquila().run_async(shots=100)
    save(hardware_batch, filename)

# %% [markdown]
# ## Plotting the Results
# First, we load the results from the file.


# %%
emu_batch = load(emu_filename)
hardware_batch = load(filename)
# hardware_batch.fetch()
# save(filename, hardware_batch)

# %% [markdown]
# The quantity of interest here is the total Rydberg density of the cluster defined as
# the sum of the Rydberg densities of each atom. We can extract this from the results
# and plot it as a function of time. We will do this for both the emulator and the
# hardware. We can use the `rydberg_densities` function to extract the densities from
# the `Report` of the `batch` object.

# %%

emu_report = emu_batch.report()
emu_densities = emu_report.rydberg_densities()
emu_densities_summed = emu_densities.sum(axis=1)

hardware_report = hardware_batch.report()
hardware_densities = hardware_report.rydberg_densities()
hardware_densities_summed = hardware_densities.sum(axis=1)


emu_run_times = emu_report.list_param("run_time")
hw_run_times = hardware_report.list_param("run_time")

fig, ax = plt.subplots()
ax.set_xlabel("Time")
ax.set_ylabel("Sum of Rydberg Densities")
# emulation
ax.plot(emu_run_times, emu_densities_summed, label="Emulator", color="#878787")
# hardware
ax.plot(hw_run_times, hardware_densities_summed, label="QPU", color="#6437FF")
ax.legend()
ax.set_xlabel("Time ($\mu s$)")
ax.set_ylabel("Sum of Rydberg Densities")
plt.show()
