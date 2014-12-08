__author__ = 'ajauch'


class Experiment(object):
    experiment_id = None
    param_defs = None
    minimization = None

    def __init__(self, experiment_id, param_defs, minimization=True):
        super(Experiment, self).__init__()

        self.experiment_id = experiment_id
        self.param_defs = param_defs
        self.minimization = minimization

    @staticmethod
    def from_dict(dict):
        """
        Converting from a dictionary duck typed to match experiment to
        Experiment

        Parameters
        -----------
        dict: dict
            The dictionary duck typed to match Experiment.
        """
        experiment_id = dict.get('experiment_id', None)
        param_defs = dict.get('param_defs', None)
        minimization = dict.get('minimization', None)

        if experiment_id is None:
            raise ValueError("Experiment.from_dict expects 'experiment_id' "
                             "to be set.")
        if param_defs is None:
            raise ValueError("Experiment.from_dict expects 'param_defs' "
                             "to be set.")

        if minimization is None:
            raise ValueError("Experiment.from_dict expects 'minimization' "
                             "to be set.")

        return Experiment(experiment_id, param_defs, minimization)

class BayesianExperiment(Experiment):
    num_gp_restarts = None
    initial_random_runs = None
    random_state = None
    acquisition_function = None
    acquisition_hyperparams = None
    kernel = None
    num_precomputed = None

    def __init__(self, experiment_id, param_defs, minimization, num_gp_restarts,
                 initial_random_runs, random_state, acquisition_function,
                 acquisition_hyperparams, kernel, num_precomputed):
        super(BayesianExperiment, self).__init__(experiment_id, param_defs,
                        minimization)

        self.num_gp_restarts = num_gp_restarts
        self.initial_random_runs = initial_random_runs
        self.random_state = random_state
        self.acquisition_function = acquisition_function
        self.acquisition_hyperparams = acquisition_hyperparams
        self.kernel = kernel
        self.num_precomputed = num_precomputed

    @staticmethod
    def from_dict(dict):
        """
        Converting from a dictionary duck typed to match experiment to
        Experiment

        Parameters
        -----------
        dict: dict
            The dictionary duck typed to match Experiment.
        """
        experiment_id = dict.get('experiment_id', None)
        param_defs = dict.get('param_defs', None)
        minimization = dict.get('minimization', None)
        num_gp_restarts = dict.get('num_gep_restarts', None)
        initial_random_runs = dict.get('initial_random_runs', None)
        random_state = dict.get('random_state', None)
        acquisition_function = dict.get('acquisition_function', None)
        acquisition_hyperparams = dict.get('acquisition_hyperparams', None)
        kernel = dict.get('kernel', None)
        num_precomputed = dict.get('num_precomputed', None)

        #check if the necessary exist
        if experiment_id is None:
            raise ValueError("Experiment.from_dict expects 'experiment_id' "
                             "to be set.")
        if param_defs is None:
            raise ValueError("Experiment.from_dict expects 'param_defs' "
                             "to be set.")

        # if minimization is None:
        #     raise ValueError("Experiment.from_dict expects 'minimization' "
        #                      "to be set.")
        # if num_gp_restarts is None:
        #     raise ValueError("Experiment.from_dict expects 'num_gp_restarts' "
        #                      "to be set.")
        # if initial_random_runs is None:
        #     raise ValueError("Experiment.from_dict expects 'initial_random_runs' "
        #                      "to be set.")
        # if acquisition_function is None:
        #     raise ValueError("Experiment.from_dict expects 'acquisition_function' "
        #                      "to be set.")
        # if acquisition_hyperparams is None:
        #     raise ValueError("Experiment.from_dict expects 'acquisition_hyperparams' "
        #                      "to be set.")
        # if kernel is None:
        #     raise ValueError("Experiment.from_dict expects 'kernel' "
        #                      "to be set.")
        # if num_precomputed is None:
        #     raise ValueError("Experiment.from_dict expects 'num_precomputed' "
        #                      "to be set.")

        return BayesianExperiment(experiment_id, param_defs, minimization,
                                  num_gp_restarts, initial_random_runs,
                                  random_state, acquisition_function,
                                  acquisition_hyperparams, kernel,
                                  num_precomputed)

    def as_params_dict(self):
        params_dict = None

        params_dict['param_defs'] = self.param_defs

        if self.minimization is not None:
            params_dict['minimization'] = self.minimization

        if self.num_gp_restarts is not None:
            params_dict['num_gp_restarts'] = self.num_gp_restarts

        if self.initial_random_runs is None:
            params_dict['initial_random_runs'] = self.initial_random_runs

        if self.acquisition_function is None:
            params_dict['acquisition_function'] = self.acquisition_function

        if self.acquisition_hyperparams is None:
            params_dict['acquisition_hyperparams'] = self.acquisition_hyperparams

        if self.kernel is None:
            params_dict['kernel'] = self.kernel

        if self.num_precomputed is None:
            params_dict['num_precomputed'] = self.num_precomputed




