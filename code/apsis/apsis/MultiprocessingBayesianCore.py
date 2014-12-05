from apsis.OptimizationCoreInterface import OptimizationCoreInterface, \
    ListBasedCore
from apsis.RandomSearchCore import RandomSearchCore
from apsis.models.Candidate import Candidate
from apsis.models.ParamInformation import NumericParamDef, PositionParamDef
from apsis.bayesian.AcquisitionFunctions import ExpectedImprovement
import numpy as np
import GPy
import logging
from apsis.utilities.randomization import check_random_state
import multiprocessing
from multiprocessing import Process, Queue

class MultiprocessingBayesianCore(ListBasedCore, Process):
    """
    This implements a simple bayesian optimizer.

    It is simple because it only implements the simplest form - no freeze-thaw,
    (currently) now multiple workers, only numeric parameters.
    """
    SUPPORTED_PARAM_TYPES = [NumericParamDef, PositionParamDef]

    kernel = None
    acquisition_function = None
    acquisition_hyperparams = None

    random_state = None
    random_searcher = None

    num_precomputed = None
    just_refitted = True
    refit_necessary = False
    refit_running = False

    refit_process = None
    pending_process = None

    #queues for webservice.:
    status_update_queue = None
    pending_queue = None

    #internal queues
    refit_queue = None
    generated_pending_queue = None

    pending_min_threshold = 10
    terminate_event = None


    gp = None

    initial_random_runs = 10
    num_gp_restarts = 10

    def __init__(self, params, status_update_queue, pending_queue, terminate_event):
        super(MultiprocessingBayesianCore, self).__init__(params)
        if params.get('param_defs', None) is None:
            raise ValueError("Parameter definition list is missing!")
        if not self._is_all_supported_param_types(params["param_defs"]):
            raise ValueError(
                "Param list contains parameters of unsopported types. "
                "Supported types are  " + str(self.SUPPORTED_PARAM_TYPES))

        self.param_defs = params["param_defs"]
        self.minimization = params.get('minimization', True)
        self.initial_random_runs = params.get('initial_random_runs',
                                              self.initial_random_runs)
        self.random_state = check_random_state(params.get('random_state', None))
        self.acquisition_hyperparams = params.get('acquisition_hyperparams',
                                                  None)
        self.acquisition_function = params.get('acquisition',
                                               ExpectedImprovement)(
            self.acquisition_hyperparams)
        self.num_gp_restarts = params.get('num_gp_restarts',
                                          self.num_gp_restarts)

        self.pending_min_threshold = params.get('pending_min_threshold', self.pending_min_threshold)

        dimensions = len(self.param_defs)
        self.kernel = params.get('kernel',
                                 GPy.kern.rbf)(dimensions, ARD=True)
        logging.debug("Kernel input dim " + str(self.kernel.input_dim))
        logging.debug("Kernel %s", str(self.kernel))
        self.random_searcher = RandomSearchCore({'param_defs': self.param_defs,
                                            "random_state": self.random_state})
        for i in range(self.initial_random_runs):
            self.pending_candidates.append(self.random_searcher.
                                           next_candidate())

        self.num_precomputed = params.get('num_precomputed', 0)
        self.refit_queue = Queue()
        self.generated_pending_queue = Queue()

        self.terminate_event = terminate_event
        self.status_update_queue = status_update_queue
        self.pending_queue = pending_queue

    def run(self):
        while (True):
            if self.terminate_event.is_set():
                self.terminate_gracefully()
            #new gps?
            while not self.refit_queue.empty():
                self.gp = self.refit_queue.get()
                self.just_refitted = True
                #kill the pending process.
                if self.pending_process is not None:
                    self.pending_process.terminate()
                #and empty the queue.
                while not self.generated_pending_queue.empty():
                    self.generated_pending_queue.get()
                #and empty the pending queue.
                while not self.pending_queue.empty():
                    self.pending_queue.get()
                del self.pending_candidates[:]

            #new points?

            while not self.status_update_queue.empty():
                candidate, status, worker_id = self.status_update_queue.get()
                self.working(candidate, status, worker_id)

            if self.refit_necessary and (self.refit_process is None or not self.refit_process.is_alive()):
                self.refit_necessary = False
                self.refit_process = RefitProcess(self.refit_queue, self.finished_candidates, self.param_defs, self.kernel, self.num_gp_restarts)
                self.refit_process.start()

            #new pending proposals?
            while not self.generated_pending_queue.empty():
                self.pending_candidates.append(self.generated_pending_queue.get())
                self.pending_queue.put(self.pending_candidates[-1])
            #pending empty?
            if self.pending_queue.empty() or self.pending_queue.qsize() < self.pending_min_threshold:
                if len(self.finished_candidates) < self.initial_random_runs:
                    self.generated_pending_queue.append(self.random_searcher.next_candidate())
                else:
                    self.pending_process = GeneratePending(self.generated_pending_queue, self.acquisition_function, self.param_defs, self.gp, self.num_precomputed, self.best_candidate, self.minimization, self.just_refitted)
                    self.pending_process.start()
                    just_refitted = False



    def working(self, candidate, status, worker_id=None, can_be_killed=False):
        super(MultiprocessingBayesianCore, self).working(
            candidate, status, worker_id, can_be_killed)
        logging.debug("Worker " + str(worker_id) + " informed me about work "
                                                   "in status " + str(status)
                      + "on candidate " + str(candidate))

        # first check if this point is known. if it is in finished, tell the
        # worker to kill the computation.
        if not self.transfer_to_working(candidate):
            return False

        # if finished remove from working and put to finished list.
        if status == "finished":
            self.deal_with_finished(candidate)

            # invoke the refitting
            if len(self.finished_candidates) >= self.initial_random_runs:
                self.refit_necessary = True
            return False

        elif status == "working":
            self.working_candidates.remove(candidate)
            self.working_candidates.append(candidate)
            return True

        elif status == "pausing":
            self.working_candidates.remove(candidate)
            self.pending_candidates.append(candidate)

            return False

        else:
            logging.error("Worker " + worker_id + " posted candidate to core "
                                                  "with non correct status "
                                                  "value " + status)

        return True

    def terminate_gracefully(self):
        if self.pending_process is not None:
            self.pending_process.terminate()
        if self.refit_process is not None:
            self.refit_process.terminate()
        self.terminate()


class RefitProcess(Process):
    finished_candidates = None

    param_defs = None
    kernel = None
    num_gp_restarts = None
    refit_queue = None
    gp = None

    def __init__(self, refit_queue, finished_candidates, param_defs, kernel,
                 num_gp_restarts):
        super(RefitProcess, self).__init__()
        self.finished_candidates = finished_candidates
        self.param_defs = param_defs
        self.kernel = kernel
        self.num_gp_restarts = num_gp_restarts
        self.refit_queue = refit_queue

    def run(self):
        self._refit_gp()

    def _refit_gp(self):
        #empty the pendings because they differ after refitting
        #TODO change
        self.pending_candidates = []
        self.just_refitted = True

        candidate_matrix = np.zeros((len(self.finished_candidates),
                                     len(self.param_defs)))
        results_vector = np.zeros((len(self.finished_candidates), 1))

        for i in range(len(self.finished_candidates)):
            candidate_matrix[i, :] = self._warp_in(
                self.finished_candidates[i].as_vector()
            )
            results_vector[i] = self.finished_candidates[i].result

        logging.debug("refitting gp with values %s and results %s",
                      str(candidate_matrix), str(results_vector))

        self.gp = GPy.models.GPRegression(candidate_matrix, results_vector,
                                          self.kernel)
        self.gp.constrain_bounded('.*lengthscale*', 0.1, 1.)
        self.gp.constrain_bounded('.*noise*', 0.1, 1.)
        logging.debug("Generated gp model. Refitting now.")
        # ensure restart
        self.gp.optimize_restarts(num_restarts=self.num_gp_restarts,
                                  verbose=False)
        logging.debug("Finished generating model.")
        self.refit_queue.put(self.gp)

    def _warp_in(self, param_vector):
        """
        Warps the parameter vector, using the warp_in function for each
        self.param_defs.
        """
        logging.debug("Param_vector: %s" % str(param_vector))
        for i in range(len(param_vector)):
            logging.debug("Warping in. %f to %f" % (param_vector[i],
                                self.param_defs[i].warp_in(param_vector[i])))
            param_vector[i] = self.param_defs[i].warp_in(
                param_vector[i]
            )
        logging.debug("New param_vector: %s" % str(param_vector))
        return param_vector

class GeneratePending(Process):
    acquisition_function = None
    param_defs = None
    gp = None
    best_candidate = None
    minimization = None
    num_precomputed = None
    pending_proposal_queue = None
    just_refitted = None

    def __init__(self, pending_proposal_queue, acquisition_function,
                 param_defs, gp, num_precomputed, best_candidate, minimzation, just_refitted):
        super(GeneratePending, self).__init__()
        self.pending_proposal_queue = pending_proposal_queue
        self.acquisition_function = acquisition_function
        self.param_defs = param_defs
        self.gp = gp
        self.num_precomputed = num_precomputed
        self.best_candidate = best_candidate
        self.minimization = minimzation
        self.just_refitted = just_refitted
        ##TODO do checking of the strings.

    def run(self):
        acquisition_params = {'param_defs': self.param_defs,
                              'gp': self.gp,
                              'cur_max': self.best_candidate.result,
                              "minimization": self.minimization
        }

        logging.debug("Running acquisition with args %s",
                      str(acquisition_params))

        new_candidate_points = self.acquisition_function.compute_proposal(
            acquisition_params, refitted=self.just_refitted,
            number_proposals=self.num_precomputed+1)

        for point in new_candidate_points:
            for i in range(len(point)):
                point[i] = self.param_defs[i].warp_out(
                    point[i]
                )
            point_candidate = Candidate(point)

            self.pending_proposal_queue.put(point_candidate)