from snake import *
from algo import *

#benchmarking test function
def test(board_size, trials, agent):
    wins = 0
    for i in range(trials):
        env = Env(rad=board_size)
        result = env.play(agent)
        if result['won']:
            wins += 1

    losses = trials - wins
    win_percent = round((wins / trials * 100), 2)
    lose_percent = 100 - win_percent

    print(f"Win %: {win_percent}, Loss % {lose_percent}")

test(4, 10000, safe_random_agent)
test(4, 10000, dfs_agent)

