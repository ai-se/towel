"""
Main Web-Interface file.
"""

from __future__ import division, print_function

import os
import sys

root = os.getcwd().split("towel")[0] + "towel/src"
sys.path.append(root)

from flask import Flask, render_template, request, jsonify, json, redirect, \
    url_for
from utils.ES_CORE import ESHandler
from core.model import SVM
from utils.utils import Vessel
import numpy as np
from pdb import set_trace
import click

app = Flask(__name__)
ESHandler = ESHandler(force_injest=False)
container = Vessel(
        OPT=None,
        SVM=None,
        round=0
)

stepsize = 50


@app.route('/hello/')
def hello():
    return render_template('hello.html')


@app.route('/charts/')
def charts():
    return render_template('charts.html')


@app.route('/init', methods=['POST'])
def init():
    res = ESHandler.get_labeled()
    pos = len(
            [1 for x in res['hits']['hits'] if x["_source"]["label"] == "pos"])
    control = ESHandler.get_control()
    pos_control = len([1 for x in control['hits']['hits'] if
                       x["_source"]["label"] == "pos"])
    res = {
        "num_labeled": res['hits']['total'],
        "num_pos"    : pos,
        "the_round"  : container.round,
        "num_control": control['hits']['total'],
        "control_pos": pos_control
    }
    return jsonify(**res)


@app.route('/search', methods=['POST'])
def search():
    # someVessel = request.form['elastic'].strip()
    # res = ESHandler.search(someVessel)
    someVessel = request.form['elastic']
    res = ESHandler.query_string(someVessel)
    # set_trace()
    return jsonify(**res)


@app.route('/labeling', methods=['POST'])
def labeling():
    id = int(request.form['id'].strip())
    label = request.form['label'].strip()
    # set_trace()
    if label == "none":
        return "none"
    ESHandler.set_label(id, label)
    res = ESHandler.get_labeled()
    pos = len(
            [1 for x in res['hits']['hits'] if x["_source"]["label"] == "pos"])
    res = {
        "num_labeled": res['hits']['total'],
        "num_pos"    : pos
    }
    return jsonify(**res)


@app.route('/labelingControl', methods=['POST'])
def labelingControl():
    id = int(request.form['id'].strip())
    label = request.form['label'].strip()

    # set_trace()
    if label == "none":
        return "none"
    ESHandler.set_label(id, label)
    container.SVM = container.SVM.stats()
    response = container.SVM.get_response()
    control = ESHandler.get_control()
    pos_control = len([1 for x in control['hits']['hits'] if
                       x["_source"]["label"] == "pos"])
    res = {
        "num_control": control['hits']['total'],
        "control_pos": pos_control
    }
    response.update(res)
    return jsonify(**response)


@app.route('/restart', methods=['POST'])
def restart():
    ESHandler.reset_labels()
    return "done"


@app.route('/feature', methods=['POST'])
def feature():
    # To do
    global container
    container.also(SVM=SVM(disp=stepsize, opt=container.OPT).featurize())
    return "done"


@app.route('/train', methods=['POST'])
def train():
    # set_trace()
    mask = json.loads(request.form['mask'])
    addon = json.loads(request.form['addon'])
    if container.SVM is None:
        container.also(SVM=SVM(disp=stepsize, opt=container.OPT).featurize())
    container.SVM = container.SVM.run(mask=mask, addon=addon)
    print("Training done...")
    response = container.SVM.get_response()
    return jsonify(response)


@app.route('/get_concurrency', methods=['POST'])
def get_concurrency():
    term = json.loads(request.form['term'])
    concurrency, scores = container.SVM.get_concurrency(term)
    return jsonify({"term": term, "concurrency": concurrency, "concurrency_scores": scores})


@app.route('/plot', methods=['POST'])
def plot():
    # set_trace()
    return redirect(url_for("charts"))


@app.route('/plotdata', methods=['POST', 'GET'])
def plotdata():
    container.SVM.stats()
    # click.launch("http://localhost:{}/charts/".format(
    #         container.site_settings.port))
    try:
        return jsonify(container.SVM.results)
    except:
        set_trace()


@app.route('/determinant', methods=['POST'])
def determinant():
    id = request.form['id']
    determinant, dist = container.SVM.get_determinant(id)
    return jsonify({"determinant": determinant, "dist": dist})

@app.route('/autoreview', methods=['POST'])
def autoreview():
    queue = json.loads(request.form['queue'])
    max_relevant = 50
    max_irrelevant = 450
    if queue:
        label_me = True
        if isinstance(queue[0], unicode) and str(queue[0]) == "random":
            res = ESHandler.get_unlabeled()["hits"]["hits"]
            tolabel = np.random.choice(res, stepsize, replace=False)

        elif isinstance(queue[0], unicode) and str(queue[0]) == "smart":
            tolabel = \
                ESHandler.get_specific(label=ESHandler.es.RELEVANT_TAG_NAME,
                                       total=stepsize,
                                       must=True)["hits"]["hits"]
            tolabel.extend(
                    ESHandler.get_specific(label=ESHandler.es.RELEVANT_TAG_NAME,
                                           must=False,
                                           total=stepsize)["hits"][
                        "hits"])
            np.random.shuffle(tolabel)
            tolabel = tolabel[:stepsize]

        else:
            tolabel = queue

        for num, which in enumerate(tolabel):
            new_tag = "pos" if any([me in ESHandler.es.RELEVANT_TAG_NAME for me
            in which['_source']['tags']]) \
                else "neg"

            ESHandler.set_label(which["_id"], new_tag)

    res0 = ESHandler.get_labeled()
    pos = len([1 for x in res0['hits']['hits'] if x["_source"]["label"] ==
               "pos"])
    res = {
        "num_labeled": res0['hits']['total'],
        "num_pos"    : pos,
        "the_round"  : container.round
    }
    return jsonify(**res)


# --- CLI ---
@click.command()
@click.option('--debug', default=False, type=click.BOOL,
              help='Flags: True/False. Render site in debug mode.')
@click.option('--force', default=False, type=click.BOOL,
              help='Flags: True/False. Create force injest documents to ES.')
@click.option('--port', default=8000, type=click.INT,
              help='Port to deploy the site on.\n')
@click.option('--verbose', default=False, type=click.BOOL,
              help='Flags: True/False. Display all outputs to stdout.\n')
def deploy(debug, force, verbose, port):
    global container

    container.also(
            site_settings=Vessel(
                    port=port)
    )

    container.also(
            OPT=Vessel(
                    FORCE_INJEST=force,
                    VERBOSE_MODE=verbose,
            )
    )
    app.run(debug=debug, use_debugger=debug, port=int(port))


if __name__ == "__main__":
    deploy()
