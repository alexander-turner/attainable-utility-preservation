from __future__ import print_function
from ai_safety_gridworlds.environments import side_effects_burning_building as burning, side_effects_sokoban as sokoban, \
    side_effects_sushi_bot as sushi, side_effects_vase as vase, survival_incentive as survival, \
    side_effects_conveyor_belt as conveyor, side_effects_coffee_bot as coffee
from agents.aup_tab_q import AUPTabularAgent
from environment_helper import *
import matplotlib.pyplot as plt

# Plot setup
#plt.switch_backend('TkAgg')
plt.style.use('ggplot')

games = [(sokoban.SideEffectsSokobanEnvironment, {'level': 0}),
         (sushi.SideEffectsSushiBotEnvironment, {'level': 0}),
         (coffee.SideEffectsCoffeeBotEnvironment, {'level': 0}),
         (survival.SurvivalIncentiveEnvironment, {'level': 0})]

# Discount
discounts = [1 - 2**(-n) for n in range(1, 11)]
fig, ax = plt.subplots()
ax.set_ylabel('Performance')
ax.set_xlabel('Discount')

for (game, kwargs) in games:
    stats = []
    for discount in discounts:
        env = game(**kwargs)
        tabular_agent = AUPTabularAgent(env, discount=discount)
        stats.append(tabular_agent.training_performance[1][-1])
    ax.plot(discounts, stats, label=game.name, marker='^')
ax.legend(loc=4)
fig.savefig(os.path.join(os.path.dirname(__file__), 'discount.pdf'), bbox_inches='tight')

# N
budgets = np.arange(0, 300, 30)
fig, ax = plt.subplots()
ax.set_ylabel('Performance')
ax.set_xlabel('Total Impact %')

for (game, kwargs) in games:
    stats = []
    for budget in budgets:
        env = game(**kwargs)
        tabular_agent = AUPTabularAgent(env, N=budget)
        stats.append(tabular_agent.training_performance[1][-1])
    ax.plot(budgets, stats, label=game.name, marker='^')
ax.legend(loc=4)
fig.savefig(os.path.join(os.path.dirname(__file__), 'N.pdf'), bbox_inches='tight')

# N
nums = range(1, 15)
fig, ax = plt.subplots()
ax.set_ylabel('Performance')
ax.set_xlabel('Number of Random Reward Functions')

for (game, kwargs) in games:
    stats = []
    for num in nums:
        env = game(**kwargs)
        tabular_agent = AUPTabularAgent(env, num_rpenalties=num)
        stats.append(tabular_agent.training_performance[1][-1])
    ax.plot(nums, stats, label=game.name, marker='^')
ax.legend(loc=4)
fig.savefig(os.path.join(os.path.dirname(__file__), 'num_rewards.pdf'), bbox_inches='tight')