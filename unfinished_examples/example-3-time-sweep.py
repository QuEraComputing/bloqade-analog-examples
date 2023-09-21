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
# # Whitepaper Example 3:

# %%
from bloqade.atom_arrangement import Chain
import bloqade
import numpy as np
import os


from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.models import ColumnDataSource, HoverTool, CrosshairTool

output_notebook()

n_atoms = 11
lattice_const = 6.1
min_time_step = 0.05

rabi_amplitude_values = [0.0, 15.8, 15.8, 0.0]
rabi_detuning_values = [-16.33, -16.33, 16.33, 16.33]
durations = [0.8, "sweep_time", 0.8]

time_sweep_z2_prog = (
    Chain(n_atoms, lattice_const)
    .rydberg.rabi.amplitude.uniform.piecewise_linear(durations, rabi_amplitude_values)
    .detuning.uniform.piecewise_linear(durations, rabi_detuning_values)
)

time_sweep_z2_job = time_sweep_z2_prog.batch_assign(
    sweep_time=np.linspace(min_time_step, 2.4, 20)
)  # starting at 0.0 not feasible, just use min_time_step

# run_async to emulator
emu_job = time_sweep_z2_job.braket.local_emulator().run(shots=10000).report()

# run_async to HW
"""
batch=(
    time_sweep_z2_job.parallelize(lattice_const * 3)
    .braket.aquila()
    .run_async(shots=100,ignore_error=True)
    .remove_tasks("Unaccepted")
)
bloqade.save("example-3-time-sweep-job.json",batch)
"""

# retrieve results from HW
hw_future = bloqade.load(
    os.getcwd() + "/docs/examples/" + "example-3-time-sweep-job.json"
)
hw_job = hw_future.report()


def get_z2_probabilities(report):
    z2_probabilities = []

    for count in report.counts:
        z2_probability = count["01010101010"] / sum(list(count.values()))
        z2_probabilities.append(z2_probability)

    return z2_probabilities


source = ColumnDataSource(
    data={
        "times": list(np.linspace(0.1, 2.4, 20)),
        "emu_z2_probabilities": get_z2_probabilities(emu_job),
        "hw_z2_probabilities": get_z2_probabilities(hw_job),
    }
)

z2_probabilities_plt = figure(
    x_axis_label="Annealing time (μs)",
    y_axis_label="Z_2 state probability",
    toolbar_location="right",
    tools="save",
)

z2_probabilities_plt.axis.axis_label_text_font_size = "15pt"
z2_probabilities_plt.axis.major_label_text_font_size = "10pt"

legend_labels = ["Emulator", "Hardware"]
source_keys = ["emu_z2_probabilities", "hw_z2_probabilities"]
colors = ["grey", "purple"]

for legend_label, source_key, color in zip(legend_labels, source_keys, colors):
    line = z2_probabilities_plt.line(
        x="times",
        y=source_key,
        source=source,
        legend_label=legend_label,
        line_width=2,
        color=color,
    )

    z2_probabilities_plt.circle(
        x="times", y=source_key, source=source, line_width=2, color=color
    )

    z2_probabilities_plt.add_tools(
        HoverTool(
            renderers=[line],
            tooltips=[
                ("Backend", legend_label),
                ("Z_2 state probability", f"@{source_key}"),
                ("Annealing time (μs)", "@times"),
            ],
            mode="vline",
        )
    )

z2_probabilities_plt.add_tools(CrosshairTool(dimensions="height"))

show(z2_probabilities_plt)

# %%
