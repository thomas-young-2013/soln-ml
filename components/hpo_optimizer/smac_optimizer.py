import time
import numpy as np
from litesmac.scenario.scenario import Scenario
from litesmac.facade.smac_facade import SMAC
from components.hpo_optimizer.base_optimizer import BaseHPOptimizer


class SMACOptimizer(BaseHPOptimizer):
    def __init__(self, evaluator, config_space,
                 time_limit=None, evaluation_limit=None, trials_per_iter=1, seed=1):
        super().__init__(evaluator, config_space, seed)
        self.time_limit = time_limit
        self.evaluation_num_limit = evaluation_limit
        self.trials_per_iter = trials_per_iter

        scenario_dict = {
            'abort_on_first_run_crash': False,
            "run_obj": "quality",
            "cs": config_space,
            "deterministic": "true"
        }

        self.optimizer = SMAC(scenario=Scenario(scenario_dict),
                              rng=np.random.RandomState(self.seed),
                              tae_runner=self.evaluator)
        self.trial_cnt = 0
        self.configs = list()
        self.perfs = list()

    def run(self):
        while True:
            evaluation_num = len(self.perfs)
            if self.evaluation_num_limit is not None and evaluation_num > self.evaluation_num_limit:
                break
            if self.time_limit is not None and time.time() - self.start_time > self.time_limit:
                break
            self.iterate()
        return np.max(self.perfs)

    def iterate(self):
        _start_time = time.time()
        for _ in range(self.trials_per_iter):
            self.optimizer.iterate()

            runhistory = self.optimizer.solver.runhistory
            runkeys = list(runhistory.data.keys())
            for key in runkeys[self.trial_cnt:]:
                reward = 1. - runhistory.data[key][0]
                self.perfs.append(reward)
                self.configs.append(runhistory.ids_config[key[0]])
            self.trial_cnt = len(runhistory.data.keys())
        iteration_cost = time.time() - _start_time

        return np.max(self.perfs), iteration_cost