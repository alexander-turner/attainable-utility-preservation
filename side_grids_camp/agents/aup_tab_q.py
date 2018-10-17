from ai_safety_gridworlds.environments.shared import safety_game
from collections import defaultdict
import experiments.environment_helper as environment_helper
import numpy as np


class AUPTabularAgent:
    name = "Tabular AUP"
    epsilon = 0.25  # chance of choosing a random action in training

    def __init__(self, env, N=200, do_state_penalties=False, num_rpenalties=10, discount=.999, num_episodes=1000):
        """Trains using the simulator and e-greedy exploration to determine a greedy policy.

        :param env: Simulator.
        :param N: Maximal impact % the agent can have.
        """
        self.actions = range(env.action_spec().maximum + 1)
        self.discount = discount
        self.aup_episodes = num_episodes
        self.penalty_episodes = self.aup_episodes
        self.N = N
        self.do_state_penalties = do_state_penalties
        self.goal_reward = env.GOAL_REWARD

        if do_state_penalties:
            self.name = 'Relative Reachability'
            self.penalty_episodes /= 10
            self.penalties = environment_helper.derive_possible_rewards(env)
        else:
            self.penalties = [defaultdict(np.random.random) for _ in range(num_rpenalties)]
        if len(self.penalties) == 0:
            self.name = 'Vanilla'  # no penalty applied!
        else:
            self.penalty_Q = defaultdict(lambda: np.zeros((len(self.penalties), len(self.actions))))

        for penalty_idx in range(len(self.penalties)):
            self.train(env, type=penalty_idx)

        # Train AUP according to the inferred composite reward - (L_1 change in penalty_Q)
        self.training_performance = np.zeros((2, num_episodes))
        self.train(env)

    def train(self, env, type='AUP'):
        is_AUP = type == 'AUP'
        num_trials = 1 if is_AUP else 1
        for _ in range(num_trials):
            if is_AUP:
                self.AUP_Q = defaultdict(lambda: np.zeros(len(self.actions)))
            for episode in range(self.aup_episodes if is_AUP else self.penalty_episodes):
                time_step = env.reset()
                while not time_step.last():
                    last_board = str(time_step.observation['board'])
                    action = self.behavior_action(last_board, type)
                    time_step = env.step(action)
                    self.update_greedy(last_board, action, time_step, type)

                if is_AUP:
                    ret, _, perf, _ = environment_helper.run_episode(self, env)
                    self.training_performance[0][episode] += ret / num_trials
                    self.training_performance[1][episode] += perf / num_trials
        env.reset()

    def act(self, obs):
        return self.AUP_Q[str(obs['board'])].argmax()

    def behavior_action(self, board, type):
        """Returns the e-greedy action for the state board string."""
        greedy = self.AUP_Q[board].argmax() if type == 'AUP' else self.penalty_Q[board][type].argmax(axis=0)
        if np.random.random() < self.epsilon or len(self.actions) == 1:
            return greedy
        else:  # choose anything else
            return np.random.choice(self.actions, p=[1.0 / (len(self.actions) - 1) if i != greedy
                                                     else 0 for i in self.actions])

    def get_penalty(self, board, action):
        if len(self.penalties) == 0: return 0
        action_attainable = self.penalty_Q[board][:, action]
        null_attainable = self.penalty_Q[board][:, safety_game.Actions.NOTHING]
        null_sum = sum(abs(null_attainable))

        # Scaled difference between taking action and doing nothing
        return sum(abs(action_attainable - null_attainable)) / (self.N * .01 * null_sum) if null_sum \
            else 1.01  # ImpactUnit is 0!

    def update_greedy(self, last_board, action, time_step, pen_idx='AUP'):
        """Perform TD update on observed reward."""
        def calculate_update(pen_idx='AUP'):
            """Do the update for the main function (or the penalty function at the given index)."""
            learning_rate = 1
            new_board = str(time_step.observation['board'])
            
            if pen_idx != 'AUP':
                reward = self.penalties[pen_idx](new_board) if self.do_state_penalties \
                    else self.penalties[pen_idx][new_board]
                new_Q, old_Q = self.penalty_Q[new_board][pen_idx].max(), \
                               self.penalty_Q[last_board][pen_idx, action]
            else:
                reward = time_step.reward - self.get_penalty(last_board, action)
                new_Q, old_Q = self.AUP_Q[new_board].max(), self.AUP_Q[last_board][action]
            return learning_rate * (reward + self.discount * new_Q - old_Q)

        if pen_idx != 'AUP':
            for i in range(len(self.penalties)):
                self.penalty_Q[last_board][i, action] += calculate_update(i)
            if self.do_state_penalties:
                self.penalty_Q[last_board][:, action] = np.clip(self.penalty_Q[last_board][:, action],
                                                                      0, self.goal_reward)
        else:
            self.AUP_Q[last_board][action] += calculate_update()