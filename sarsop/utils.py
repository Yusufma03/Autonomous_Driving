import numpy as np
from config_utils import load_configs

config = load_configs()

NY = config["ny"]
NDX = config["ndx"]
NCARS = config["ncars"]
CARS_SUBLANES = config["cars_sublanes"]
OBS_PROBAS = config["obs_probas"]
SUBLANES_SPEEDS_CELLS = config["sublanes_speeds_cells"]


def table_to_str(table, mode='float'):

    if len(table.shape) == 1:
        table = table.reshape(1,-1)
    
    s = ""

    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            if mode == 'float':
                s += "%.1f" % table[i,j]
            else:
                s += "%d" % table[i,j]
            if i != table.shape[0]-1 or j != table.shape[1]-1:
                s += ' '

    return s

def make_y0_transition_matrix(action):

    assert action in ["none", "left", "right"]

    p = np.identity(NY)
    if action == "left":
        p[1:,:] = np.roll(p[1:,:], -1, axis=1)
    elif action == "right":
        p[:-1,:] = np.roll(p[:-1,:], 1, axis=1)

    return p

def make_dx_transition_matrix(y0, car):

    assert y0 >= 0 and y0 < NY
    assert car >= 1 and car < NCARS

    speed = SUBLANES_SPEEDS_CELLS[CARS_SUBLANES[car]] - SUBLANES_SPEEDS_CELLS[y0]

    p = np.identity(NDX)

    # TODO : this only works when speed = +/- 1 !!!!
    if speed > 0:
        p[:-speed, :] = np.roll(p[:-speed, :], speed, axis=1)
        p[-speed:,:] = 0
        p[-speed:,-1] = 1.0

        p[0,:] = 0 
        p[0,0] = 0.5
        p[0,1] = 0.5

    elif speed < 0:
        p[-speed:, :] = np.roll(p[-speed:, :], speed, axis=1)
        p[:-speed,:] = 0
        p[:-speed,0] = 1.0
        
        p[-1,:] = 0
        p[-1,-1] = 0.5
        p[-1,-2] = 0.5

    return p

def make_dx_obs_matrix():
    p = np.zeros((NDX,NDX))
    l = len(OBS_PROBAS)
    half_l = int(len(OBS_PROBAS)/2)

    for i in range(p.shape[0]):
        expanded = np.zeros(NDX + 2*half_l)
        expanded[i:i+l] = OBS_PROBAS
        squeezed = expanded[half_l:half_l+NDX]
        front_cut = expanded[:half_l]
        back_cut = expanded[half_l+NDX:]
        squeezed[0] += np.sum(front_cut)
        squeezed[-1] += np.sum(back_cut)

        p[i,:] = squeezed

    return p


