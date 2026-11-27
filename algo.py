from snake import *

#distance check
def manhattan_dist(env, locations):
    fx, fy = env.fruitlocation
    return sorted(
        locations,
        key=lambda loc: abs(fx - loc[0][0]) + abs(fy - loc[0][1]),
        reverse=True
    )

#agent that chooses moves based on some principle
def safe_random_agent(env):
    hx, hy = env.gamesnake.head
    valid_moves = []

    for direction, (dx, dy) in DIRECTIONS.items():
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < env.rad and 0 <= ny < env.rad and env.board[nx][ny] != 1:
            valid_moves.append(direction)

    #if trap w/no valid move pick any direction to end the game
    if valid_moves:
        return choice(valid_moves) 
    else: 
        return 'up'

#dfs agent
def dfs_agent(env):
    hx, hy = env.gamesnake.head
    explored = set()
    valid_locations = []

    #initial valid locations to explore from start pos
    for direction, (dx, dy) in DIRECTIONS.items():
        #prevent snake run into itself
        if direction == OPPOSITES.get(direction):
            continue
        sx, sy = hx + dx, hy + dy
        if 0 <= sx < env.rad and 0 <= sy < env.rad and env.board[sx][sy] != 1:
            valid_locations.append(((sx, sy), direction))
            explored.add((sx, sy))

    #intial sort by closest to fruit
    valid_locations = manhattan_dist(env, valid_locations)

    while valid_locations:
        curr_pos, first_move = valid_locations.pop()
        new_locations = []
        cx, cy = curr_pos
        if env.board[cx][cy] == 2:
            return first_move

        for direction, (dx, dy) in DIRECTIONS.items():
            if direction == OPPOSITES.get(direction):
                continue

            nx, ny = cx + dx, cy + dy
            if 0 <= nx < env.rad and 0 <= ny < env.rad and env.board[nx][ny] != 1:
                if (nx, ny) not in explored:
                    explored.add((nx, ny))
                    new_locations.append(((nx, ny), first_move))

        for location in manhattan_dist(env, new_locations):
            valid_locations.append(location)

    return 'up'