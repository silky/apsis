from flask import Flask, request, jsonify
from flask_negotiate import consumes, produces
from apsis.models.ParamInformation import *
from apsis.models.Candidate import Candidate
import json

import logging

#customize port and context root here if wanted
WS_PORT = 5000
CONTEXT_ROOT = ""

logging.basicConfig(level=logging.DEBUG)

#init Flask, give it core package name of our stuff
app = Flask('apsis')

@app.route(CONTEXT_ROOT + "/", methods=["GET"])
def test_ws():
    """
    Method to be used e.g. from the browser
    to test if the ws is up and running."
    """

    return "<h1>Welcome to the APSIS REST API.</h1><p>Enjoy. " \
           "Perhaps the documentation might be shown here soon.</p>"


@app.route(CONTEXT_ROOT + "/experiments", methods=["GET"])
def list_experiments(experiment_id):
    """
    GET Method to list experiments. Filterable by experiment_id.

    TO BE DEFINED, not the most urgent function.
    => could also use filtering by query params here
    """
    return "NOT IMPLEMENTED YET - MAYBE IN NEXT RELEASE."

@app.route(CONTEXT_ROOT + "/experiments", methods=["POST"])
@consumes('application/json')
@produces('application/json')
def register_experiment():
    """
    POST Method to be used to create a new request

    Expecting JSON Object like this, duck typing the constructor of
    optimization core. Only objects need to be replaced by a JSON
    object containing one property and its value being the arguments
    to the object's constructor.

    {"experiments": [
            {
                experiment_id: "my_experiment_uuid",
                param_defs: [
                    {"LowerUpperNumericParamDef": [0, 20]}
                ],
                num_gp_restarts: 20,
                minimization: true,
                ...
            }
        ]
    }
    """
    logging.debug("POST /experiments")

    data_received = request.get_json()
    experiments_received = data_received.get("experiments", None)

    if experiments_received is None:
         return "ERORR experiments not found in body", 500

    logging.debug("Received Experiments " + jsonify(experiments_received))
    #TODO parse experiment and trigger core instantiation

    #TODO return new experiment ids, or the given ones if any
    created_experiment_ids = ["NEW EXPERIMENT ID"]

    return_data = {"created_experiments" : created_experiment_ids}
    return jsonify(return_data)

@app.route(CONTEXT_ROOT + "/experiments/<experiment_id>/working", methods=["POST"])
@consumes('application/json')
@produces('application/json')
def working(experiment_id):
    """
    POST method to post new information from a worker targetting at the cores
    working method. Needs to be given the experiment_id of the experiment
    to which the result belongs.

    POST DATA
    ---------
    candidate: dict
        dict representing Candidate object.
    status: String
        indicating status of this candidate: "finished", "working",...
    [worker_id]: String
        A string id describing a worker.
    [can_be_killed=False]: boolean
        If this worker can be killed.
    """
    logging.debug("POST experiments/<id>/working for experiment id " + experiment_id)

    request_body = request.get_json()

    if(request_body is None):
        return "ERORR (1) - request body empty", 500

    #mandatory
    serialized_candidate = request_body.get('candidate', None)
    candidate_status = request_body.get('status', None)

    #optional
    worker_id = request_body.get('worker_id', None)
    can_be_killed = request_body.get('can_be_killed', False)

    if(serialized_candidate is not None and candidate_status is not None):
        deserialized_candidate = Candidate.from_dict(serialized_candidate)
        logging.debug("Deserialized candidate in state " +
                      str(type(candidate_status)) +  ": " +
                      str(candidate_status) + " "
                      + str(deserialized_candidate))

        #TODO use experiment id to register working in the appropriate experiment
        #TODO call to OptimizationCoreInterface.working
        #TODO return the continue value for the experiment posted
        return jsonify({"continue": True}), 200

    else:
        return "ERORR (2) - candidate object was not given", 500


@app.route(CONTEXT_ROOT + "/experiments/<experiment_id>/candidate", methods=["GET"])
@produces('application/json')
def next_candidate(experiment_id):
    logging.debug("GET experiments/<id>/candidate for experiment id " +
                  experiment_id)

    #TODO use experiment id to obtain next candidate from
    #sample code for testing follows
    test_point = [1, 1, 1]
    for i in range(0, len(test_point)):
        test_point[i] = random.gauss(0, 10)
    test_candidate = Candidate(test_point)

    #return test candidate as dict and then bring to json
    return jsonify(test_candidate.__dict__), 200


logging.info("APSIS web service starting at " + str(WS_PORT))
app.run(debug=True, port=WS_PORT)


