from neuprint import Client
from neuprint import fetch_neurons
from neuprint import NeuronCriteria as NC
from neuprint.utils import tqdm

import matplotlib.pyplot as plt
import matplotlib.patches as mplpatches



neuprint_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFoc2hlbmFzQHVjc2MuZWR1IiwibGV2ZWwiOiJub2F1dGgiLCJpbWFnZS11cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQVRYQUp4cURuTUpYSTIxeUdJS2F1TW85Z1loeTlMYnFpY1lXdTU1Z3lnTT1zOTYtYz9zej01MD9zej01MCIsImV4cCI6MTg0NTM2MzcyNn0.gg5e-azTnwjr4BmOKjmP5qyqmawsnSrOusEggAMZ06c'
c = Client('neuprint.janelia.org',
           dataset='hemibrain:v1.1',
           token=neuprint_token)


# Select neuron
neuronType = 'DNa02'
criteria = NC(type=neuronType) 
neuron_df, roi_counts_df = fetch_neurons(criteria)

bodyid = neuron_df['bodyId'][0]
neuronToSim = bodyid


def neuprint_to_um(num):
    """
    Given a number from neuprint, return it in micrometers
    1 unit from neuprint is 8 nanometers
    """
    return num * 8 / 1000


# Get its skeleton
print("loading data:")
s = c.fetch_skeleton(neuronToSim, format='pandas')

# Convert columns using neuprints voxel size to micrometers
for col in ['x', 'y', 'z', 'radius']:
    s[col] = s[col].map(neuprint_to_um)


# Merge skeleton rows with their parent row to create segments
s['bodyId'] = neuronToSim 
segments = s.merge(s, 'inner',
                   left_on=['bodyId', 'rowId'],
                   right_on=['bodyId', 'link'],
                   suffixes=['_child', '_parent'])



# Figure measurments in inches
figureWidth = 4
figureHeight = 6
panelWidth = 3
panelHeight = 5
spacing = 0.05

panel = plt.axes([spacing, spacing, panelWidth/figureWidth, panelHeight/figureHeight])

### Plot Skeleton
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


### Plot Scale Bar

# where to place scale bar
scalexpos = 100
scaleypos = 300
scalewidth = 20 # width in micrometers
scaleheight = 0.5

# Create scale bar and add it to the panel
scalebar = mplpatches.Rectangle([scalexpos, scaleypos],
                                 scalewidth, scaleheight,
                                 linewidth=0,
                                 facecolor='black')
panel.add_patch(scalebar)

# Add scale bar text just above scale bar 
panel.text(scalexpos+scalewidth/2, scaleypos-1,
                "{:g}".format(scalewidth)+"μm",
                fontsize=5,
                ha = 'center',
                va = 'bottom',
                color = 'black',
                )


panel.invert_yaxis() # flip the y axis so it looks like the view from neuprint
panel.set_aspect('equal')
panel.tick_params(bottom=False, labelbottom=False,
                    left=False, labelleft=False,
                    right=False, labelright=False,
                    top=False, labeltop=False,)


plt.savefig("DNa02skel.png", dpi=600)