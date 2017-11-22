from despot import *

def load_data():
    with open('poses.json', 'r') as fin:
        parsed = json.load(fin)
    return parsed

def get_agent_poses(dic, index):
    ret = [
        v[index][:2]
        for k, v in dic.items()
    ]
    return ret

def x2belief(x):
    belief = np.zeros(ROAD_LEN+100)
    x = int(x)
    belief[x] = 0.8
    belief[x-1] = 0.1
    belief[x+1] = 0.1
    return belief

def to_belief(agent_poses):
    beliefs = []
    for pos in agent_poses:
        x, y = pos
        x_belief = x2belief(x)
        beliefs.append([x_belief, y])
    return beliefs

def shift_belief(belief, bits):
    if bits > 0:
        return np.concatenate((np.zeros(bits), belief[:-bits]))
    else:
        return np.concatenate((belief[bits:], np.zeros(bits)))

def update_belief(beliefs, observations, old_observations):
    new_beliefs = []
    for i in range(len(beliefs)):
        belief = beliefs[i]
        x_belief, y = belief
        x_obs, y_obs = observations[i]
        x_obs_old, y_obs_old = old_observations[i]
        vel_x = int(x_obs - x_obs_old)
        x_belief_shifted = shift_belief(x_belief, vel_x)
        x_belief_obs = x2belief(x_obs)
        x_belief_new = x_belief_shifted * x_belief_obs
        x_belief_new = x_belief_new / np.sum(x_belief_new)
        new_beliefs.append([x_belief_new, y_obs])
    return new_beliefs

def action2vel(action, robot_pos):
    x, y = robot_pos
    if y < BOUNDARY:
        vel_x = 4
        if action in [LEFT, STAY, RIGHT]:
            vel_x = 2
    else:
        vel_x = 2
    if (action == LEFT or action == LEFT_FAST) and y > LEFT_MOST:
        vel_y = -1
    elif (action == RIGHT or action == RIGHT_FAST) and y < RIGHT_MOST:
        vel_y = +1
    else:
        vel_y = 0

    return [vel_x, vel_y]

def load_config():
    with open('despot_config.json', 'r') as fin:
        config = json.load(fin)
    global SEARCH_DEPTH
    global GAMMA
    global GOAL
    global EPSILON
    global NUM_OF_SCENARIOS
    global TIME_LEN
    global LAMBDA
    global ROAD_LEN
    
    SEARCH_DEPTH = config['search_depth']
    GAMMA = config['gamma']
    GOAL = config['goal']
    EPSILON = config['epsilon']
    NUM_OF_SCENARIOS = config['num_of_scenarios']
    TIME_LEN = config['time_len']
    LAMBDA = config['lambda']
    ROAD_LEN = config['road_len']
        

if __name__=='__main__':
    data = load_data()
    index = 0
    load_config()
    with open('../ros-lanechanging/autocar/scripts/lane_config.json', 'r') as fin:
        parsed = json.load(fin)
        robot_start_x = parsed['autonomous_car_start_pos']
    robot_pos = [robot_start_x, 0]
    dump = []
    while robot_pos[0] < ROAD_LEN - 5:
        agent_poses_new = get_agent_poses(data, index)
        if index == 0:
            agent_belief = to_belief(agent_poses_new)
        else:
            agent_belief = update_belief(agent_belief, agent_poses_new, agent_poses_old)

        despot_tree = build_despot(robot_pos, agent_belief)
        action = planning(despot_tree)
        print(action)
        vel_x, vel_y = action2vel(action, robot_pos)
        robot_pos = [robot_pos[0] + vel_x, robot_pos[1] + vel_y]
        print(robot_pos)
        dump.append([vel_x*10, vel_y*10, index / 10.0])
        index += 1
        agent_poses_old = agent_poses_new
    
    with open('cmds.json', 'w') as fout:
        json.dump(dump, fout)
