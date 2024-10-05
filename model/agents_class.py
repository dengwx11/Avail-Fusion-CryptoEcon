from dataclasses import dataclass, field

@dataclass
class Stake:
    initial_price: float
    agents_balances: list
    upper_bound: int = field(default=0)
    rewards: float = field(default=0.0)
    agents_scaled_balances: list = field(init=False)
    agents_rewards: list = field(init=False)

    def __post_init__(self):
        self.agents_scaled_balances = [balance * self.initial_price for balance in self.agents_balances]
        self.agents_rewards = [0 for _ in self.agents_balances] 


    def update_rewards(self, reward_values):
        if len(reward_values) != len(self.agents_balances):
            raise ValueError("Wrong Match!")
        self.agents_rewards = reward_values

    def set_upper_bound(self):
        self.upper_bound = sum(self.agents_scaled_balances)

    def set_rewards(self, new_rewards):
        self.rewards = new_rewards

    def update_balances(self, new_balances):
        if len(new_balances) != len(self.agents_balances):
            raise ValueError("Wrong len match!")
        self.agents_balances = new_balances
        self.update_scaled_balances()

    def update_scaled_balances(self):
        self.agents_scaled_balances = [balance * self.initial_price for balance in self.agents_balances]


