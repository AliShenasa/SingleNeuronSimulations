"""
This is a custom final assignment

Figure Description:
This is the DNa02 neuron from the drosophila brain with all the synapses it receives.
Synapses are represented as dots with the color indicating the voltage decay from that synapse to the output synapse.
The colormap is on the right with a minimum of 1 indicating no decay (cyan) and maximum of 55.07 indicating a 55.07x decay (magenta).

The neuron skeleton is taken from neuprint.janelia.org which is a database of drosophila brain electron microscopy images and neuron segmentation.
The data file contains the results of passive conductance simulations through the neuron.
Voltage was injected at all input synapses and measured at an output synapse at the bottom of the neuron.
The ratio between the voltage of an input and the output synapse is used to get the voltage decay ratio. 

note: The thickness of neuron segments is not displayed so some synapses appear to not connect to the neuron

To run the program use:
python Shenasa_Ali_BME163_Assignment_Week8.py -i DNa02_all_points.txt.py -o Shenasa_Ali_BME163_Assignment_Week8.png

The data file is a text file, but I added .py to filename so I could upload it to canvas
"""

from neuprint import Client
from neuprint import fetch_neurons, fetch_synapse_connections, fetch_adjacencies
from neuprint import merge_neuron_properties
from neuprint import NeuronCriteria as NC
from neuprint.utils import tqdm

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import matplotlib.pyplot as plt
import matplotlib.patches as mplpatches
import argparse


# plt.style.use("BME163")

parser = argparse.ArgumentParser()
parser.add_argument('--infile','-i', type=str, action='store', help='input file')
parser.add_argument('--outfile','-o', type=str, action='store', help='output file')
args = parser.parse_args()
infile = args.infile
outfile = args.outfile


# Create client for neuprint
c = Client('neuprint.janelia.org',
           dataset='hemibrain:v1.1',
           token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFoc2hlbmFzQHVjc2MuZWR1IiwibGV2ZWwiOiJub2F1dGgiLCJpbWFnZS11cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQVRYQUp4cURuTUpYSTIxeUdJS2F1TW85Z1loeTlMYnFpY1lXdTU1Z3lnTT1zOTYtYz9zej01MD9zej01MCIsImV4cCI6MTg0NTM2MzcyNn0.gg5e-azTnwjr4BmOKjmP5qyqmawsnSrOusEggAMZ06c')

c.fetch_version()


# Select neuron
neuronType = 'DNa02'#'hDeltaA'#'PEN_a(PEN1)'
criteria = NC(type=neuronType) 
neuron_df, roi_counts_df = fetch_neurons(criteria)

bodyid = neuron_df['bodyId'][0]
neuronToSim = bodyid


# Get its skeleton
print("loading data:")
s = c.fetch_skeleton(neuronToSim, format='pandas')
s['bodyId'] = neuronToSim 
s['color'] = 'black'
segments = s.merge(s, 'inner',
                   left_on=['bodyId', 'rowId'],
                   right_on=['bodyId', 'link'],
                   suffixes=['_child', '_parent'])

# Get full list of input synapse properties
input_syns = fetch_synapse_connections(None, neuronToSim, client=c)

# Get the name and type of the upstream partners and add them to the inputs object
neuronToSim_df, connToSim_df = fetch_adjacencies(None, neuronToSim)
connToSim_df = merge_neuron_properties(neuronToSim_df, connToSim_df, ['type', 'instance'])
input_syns['type'] = [connToSim_df[connToSim_df['bodyId_pre'] == i].type_pre.values[0] for i in input_syns['bodyId_pre']]

input_syns['instance'] = [connToSim_df[connToSim_df['bodyId_pre'] == i].instance_pre.values[0] for i in input_syns['bodyId_pre']]

# Find the nearest node for each synapse
input_syns['coords'] = list(zip(input_syns["x_post"], input_syns["y_post"], input_syns["z_post"]))
tree = cKDTree(list(zip(s["x"], s["y"], s["z"])))
input_syns['swcid'] = input_syns['coords'].apply(lambda x: tree.query(x)[1]+1)

# Get full list of output synapse properties
output_syns = fetch_synapse_connections(neuronToSim, client=c)

# Get the name and type of the downstream partners and add them to the outputs object
neuronToMon_df, connToMon_df = fetch_adjacencies(neuronToSim,None)
connToMon_df = merge_neuron_properties(neuronToMon_df, connToMon_df, ['type', 'instance'])
output_syns['type'] = [connToMon_df[connToMon_df['bodyId_post'] == i].type_post.values[0] for i in output_syns['bodyId_post']]
output_syns['instance'] = [connToMon_df[connToMon_df['bodyId_post'] == i].instance_post.values[0] for i in output_syns['bodyId_post']]

# Find the nearest node for each synapse
output_syns['coords'] = list(zip(output_syns["x_pre"], output_syns["y_pre"], output_syns["z_pre"]))
tree = cKDTree(list(zip(s["x"], s["y"], s["z"])))
output_syns['swcid'] = output_syns['coords'].apply(lambda x: tree.query(x)[1]+1)


# Output voltage location
output_voltage_syns = output_syns.iloc[[5]]

# Plot

def plotSkeleton(segments, panel):
    print("plotting skeleton:")
    for index, seg in tqdm(segments.iterrows(), total=len(segments)):
        panel.plot([seg['x_child'], seg['x_parent']],
                [seg['z_child'], seg['z_parent']],
                marker='o', 
                markersize=0,
                linewidth=0.25,
                markeredgewidth=0,
                color = (0.7, 0.7, 0.7),
                )


figureWidth = 4.5
figureHeight = 6
panelWidth = 3
panelHeight = 5
sideWidth = 0.25
sideHeight = 5
spacing = 0.05

plt.figure(figsize=(figureWidth, figureHeight))

# Plot the voltage decay at each input
data_list = []
with open(infile) as file:
    for index, line in enumerate(file):
        if index == 0:
            continue
        splitline = line.strip().split()
        data = {'in_swcid': int(splitline[0]),
                'in_voltage': float(splitline[1]),
                'in_time': float(splitline[2]),
                'out_swcid': int(splitline[3]),
                'out_voltage': float(splitline[4]),
                'out_time': float(splitline[5])}
        data_list.append(data)

volt_ratio_list = [data['in_voltage'] / data['out_voltage'] for data in data_list]

palette = [(int(color), 255-int(color), 255) for color in np.linspace(0, 255, 256)]
def volt_to_color(volt_ratio, volt_ratio_list):
    norm_ratio = (volt_ratio - min(volt_ratio_list))/(max(volt_ratio_list) - min(volt_ratio_list))
    return (norm_ratio, 1-norm_ratio, 1)
        

panel_main = plt.axes([spacing, spacing, panelWidth/figureWidth, panelHeight/figureHeight])

# Plot skeleton
plotSkeleton(segments, panel_main)

def vdr_to_syn_size(vdr ,maxVDR, maxSynSize=1.5, minSynSize=0.6, minVDRthreshold=19):
    """
    Given a voltage decay ratio and the maxVDR,
    return the size of the synapse
    such that the size is constant until it meets a threshold, then it linearly increases
    """

    if (vdr < minVDRthreshold):
        return minSynSize

    intercept = minSynSize - (maxSynSize - minSynSize)/(maxVDR - minVDRthreshold) * minVDRthreshold
    synSize = (maxSynSize - minSynSize)/(maxVDR - minVDRthreshold) * vdr + intercept
    return synSize


# Plot input synapses
print("plotting synapses:")
for input_data in tqdm(data_list):
    syns = input_syns[input_syns['swcid'] == input_data['in_swcid']]
    volt_ratio = input_data['in_voltage'] / input_data['out_voltage']
    syn_size = vdr_to_syn_size(volt_ratio, max(volt_ratio_list), minSynSize=0, minVDRthreshold=0)
    panel_main.plot(syns['x_post'], syns['z_post'],
                marker='o', 
                markersize=syn_size,
                linewidth=0,
                markeredgewidth=0,
                color = volt_to_color(volt_ratio, volt_ratio_list),
                )

# Plot output synapse
panel_main.plot(output_voltage_syns['x_post'], output_voltage_syns['z_post'],
                marker='o', 
                markersize=0.6,
                linewidth=0,
                markeredgewidth=0,
                color = 'green',
                )

panel_main.text(output_voltage_syns['x_post'], output_voltage_syns['z_post'],
                '   Output',
                fontsize=5,
                ha = 'left',
                va = 'center',
                color = 'green',
                )

# Plot Scale Bar
scalexpos = 12000
scaleypos = 38000
scalewidth = 20000/8 # width in micrometers
scaleheight = 20

scalebar = mplpatches.Rectangle([scalexpos, scaleypos],
                                 scalewidth, scaleheight,
                                 linewidth=0,
                                 facecolor='black')
panel_main.add_patch(scalebar)

panel_main.text(scalexpos+scalewidth/2, scaleypos-10,
                "{:g}".format(scalewidth*8/1000)+"μm",
                fontsize=5,
                ha = 'center',
                va = 'bottom',
                color = 'black',
                )

panel_main.invert_yaxis()
panel_main.set_aspect('equal')
panel_main.tick_params(bottom=False, labelbottom=False,
                    left=False, labelleft=False,
                    right=False, labelright=False,
                    top=False, labeltop=False,)

# Plot Colormap
panel_side = plt.axes([spacing + panelWidth/figureWidth + spacing, spacing,
                       sideWidth/figureWidth, sideHeight/figureHeight])

for i in np.linspace(min(volt_ratio_list), max(volt_ratio_list), 256):
    space = (max(volt_ratio_list) - min(volt_ratio_list))/255
    rectangle = mplpatches.Rectangle([0, i], 1, space,
                                     linewidth=0,
                                     facecolor=volt_to_color(i, volt_ratio_list))
    panel_side.add_patch(rectangle)


panel_side.set_ylabel('Voltage Decay Ratio',
                       labelpad = -25,
                       rotation = 270)
panel_side.set_xlim([0, 1])
panel_side.set_ylim([min(volt_ratio_list), max(volt_ratio_list)])
panel_side.set_yticks([min(volt_ratio_list), max(volt_ratio_list)])
panel_side.tick_params(bottom=False, labelbottom=False,
                      left=False, labelleft=False,
                      right=True, labelright=True,
                      top=False, labeltop=False,)


plt.savefig(outfile, dpi=1200)