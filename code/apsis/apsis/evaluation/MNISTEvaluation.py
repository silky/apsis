from sklearn.datasets import fetch_mldata
from sklearn.cross_validation import train_test_split
from sklearn.cross_validation import cross_val_score
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.svm import NuSVC, SVC

from apsis.adapters.SimpleScikitLearnAdapter import SimpleScikitLearnAdapter
from apsis.SimpleBayesianOptimizationCore import SimpleBayesianOptimizationCore
from apsis.RandomSearchCore import RandomSearchCore
from apsis.evaluation.EvaluationFramework import EvaluationFramework
from apsis.models.ParamInformation import NumericParamDef, NominalParamDef, \
    LowerUpperNumericParamDef, FixedValueParamDef
import os
import logging
import time

logging.basicConfig(level=logging.DEBUG)

def objective_func_from_sklearn(candidate, estimator, param_defs, X, y, parameter_names, scoring="accuracy", cv=3): #gets candidate, returns candidate.
    start_time = time.time()

    param_defs_sklearn = {}
    for i in range(len(parameter_names)):
        param_defs_sklearn[parameter_names[i]] = param_defs[i]

    print("Param defs: " + str(param_defs_sklearn))

    sk_ad = SimpleScikitLearnAdapter(estimator, param_defs_sklearn)
    sk_learn_format = sk_ad.translate_vector_dict(candidate.params)
    print("sk_learn_format: " + str(sk_learn_format))

    estimator.set_params(**sk_learn_format)
    print("set params: " + str(estimator.get_params()))
    #scores = cross_val_score(estimator, X, y, scoring=scoring, cv=cv)
    #print("scores: " + str(scores))
    #candidate.result = 1 - scores.mean()

    train_data, test_data, train_target, test_target = train_test_split(X, y)

    estimator.fit(train_data, train_target)
    pred = estimator.predict(test_data)
    score = accuracy_score(test_target, pred)
    print(score)
    candidate.result = score
    cost = time.time() - start_time
    candidate.cost = cost
    print("cost: " + str(cost))
    print("")
    return candidate

if __name__ == '__main__':
    #load mnist dataset
    mnist = fetch_mldata('MNIST original',
                         data_home=os.environ.get('MNIST_DATA_CACHE', '~/.mnist-cache'))

    print("Mnist Data Size " + str(mnist.data.shape))
    print("Mnist Labels Size" + str(mnist.target.shape))

    #train test split
    mnist_data_train, mnist_data_test, mnist_target_train, mnist_target_test = \
        train_test_split(mnist.data, mnist.target, test_size=0.1, random_state=42)

    regressor = SVC(kernel="poly")
    parameter_names = ["C", "degree", "gamma", "coef0"]
    param_defs = [
        LowerUpperNumericParamDef(0,1),
        FixedValueParamDef([1,2,3]),
        LowerUpperNumericParamDef(0, 1),
        LowerUpperNumericParamDef(0,1)
    ]

    optimizer_args_random_search = {'minimization': True,
                      'initial_random_runs': 10}

    """sk_adapter = SimpleScikitLearnAdapter(regressor, param_defs,
                                              scoring="mean_squared_error",
                                              optimizer="SimpleBayesianOptimizationCore",
                                              optimizer_arguments=optimizer_args,n_iter=1)"""


    used_size = len(mnist_data_train) / 10.0
    print("Using mnist of size " + str(used_size))

    obj_func_args = {"estimator": regressor,
                     "param_defs": param_defs,
                     "X": mnist_data_train[:used_size],
                     "y": mnist_target_train[:used_size],
                     "parameter_names": parameter_names}

    ev = EvaluationFramework()

    optimizer_args_random_search = {"minimization_problem": True,
                      "param_defs": param_defs}
    optimizer_args_bayopt = {"param_defs": param_defs, "initial_random_runs": 10}

    optimizers = [
                    SimpleBayesianOptimizationCore(optimizer_args_bayopt),
                    RandomSearchCore(optimizer_args_random_search)
                 ]

    steps = 100
    ev.evaluate_optimizers(optimizers, ["BayOpt_MNIST_10Pct_GP_EI_Simple", "RandomSearch_MNist10Pct"],
                           objective_func_from_sklearn,
                           objective_func_args=obj_func_args,
                           obj_func_name="MNIST 10PCT SVC",
                           steps=steps, show_plots_at_end=True,
                           csv_write_frequency=2, plot_write_frequency=2)

    #finally do an evaluation
    #print("----------------------------------\nHyperparameter Optimization Finished\n----------------------------------")
    #print("----------------------------------\nTest EVALUATION FOLLOWS\n----------------------------------")
    #scores = cross_val_score(regressor, mnist_data_test, mnist_target_test, scoring="accuracy", cv=3)
    #print(scores)
    #print("----------------------------------\n----------------------------------")
