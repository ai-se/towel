from __future__ import print_function, division

# Get source directory
import sys
import os

root = os.getcwd().split('src')[0] + 'src'
sys.path.append(os.path.abspath(root))
import click
import numpy as np
from sklearn import svm
from utils.utils import Vessel
from TermFrequency import TermFrequency
from time import time
from random import shuffle
from utils.ES_CORE import ESHandler
from utils.ABCD import ABCD
from sklearn.feature_extraction.text import TfidfTransformer
from scipy.sparse import csr_matrix
from collections import Counter
# from utils.funcs import *
from pdb import set_trace

__author__ = 'Rahul Krishna'

OPT = Vessel(
        FORCE_INJEST=False,
        VERBOSE_MODE=False)


def masking(csrmat, mask):
    if mask == []:
        return csrmat
    tmp = np.identity(csrmat.shape[1])
    for x in mask:
        tmp[x, x] = 0;
    my_mask = csr_matrix(tmp)
    re = csrmat * my_mask
    return re


class FeatureMap:
    def __init__(self, raw_data, n=1000, scroll=None, features=None):
        self.data = raw_data
        self._class = list()
        self.doc_id = list()
        self.mappings = list()
        self.features = features if features is not None else range(
                len(self.data['header']))
        self.scroll = scroll
        self._init_mapping()

    def _init_mapping(self):
        vocab = self.data['header']
        self.header = [vocab[feat] for feat in self.features]
        numel = range(len(self.data["meta"]))
        if self.scroll:
            shuffle(numel)
        self.mappings = self.data["matrix"][numel[:self.scroll]]
        for idx in numel[:self.scroll]:
            # instance = self.data["matrix"][idx]
            # self.mappings = csr_vstack(self.mappings, instance)
            self._class.append(self.data["meta"][idx]['label'])
            self.doc_id.append(self.data["meta"][idx]['doc_id'])
        ### masking ###
        self.mappings = self.mappings[:, self.features]

    def pop(self, idx):
        if isinstance(idx, list):
            return (self.mappings.pop(idx), \
                    self._class.pop(idx), \
                    self.doc_id.pop(idx))
        else:
            return [(self.mappings.pop(i), \
                     self._class.pop(i), \
                     self.doc_id.pop(i))
                    for i in idx]

    def update_mapping(self, instances):
        for inst in instances:
            array = inst[0]
            self.mappings = csr_vstack(self.mappings,
                                       array[0][:, self.features])
            self._class.append(inst[1])
            self.doc_id.append(inst[2])
        return self

    def sampling(self,sample):
        self._class = np.array(self._class)[sample]
        self.doc_id = np.array(self.doc_id)[sample]
        self._ifeatures = self._ifeatures[sample]

    ## NOT USING IT
    def refresh(self, data):
        self.refresh_label()
        new_doc_ids = [i for i, a_row in enumerate(data["meta"]) if
                       not a_row["doc_id"] in self.doc_id]
        for idx in new_doc_ids:
            self.mappings = csr_vstack(self.mappings, data["matrix"][idx][:,
                                                      self.features])
            self._class.append(a_row['label'])
            self.doc_id.append(a_row['doc_id'])

        return self.tf()

    # def refresh_label(self):
    #     self._class=[ESHandler().get_document(_id)["_source"]["label"] for
    # _id in self.doc_id]

    def tf_idf(self, mask=[]):
        self._ifeatures = masking(self.mappings[:self.scroll], mask)
        transformer = TfidfTransformer(norm='l2', use_idf=True,
                                       smooth_idf=True, sublinear_tf=True)
        self._ifeatures = transformer.fit_transform(self._ifeatures,
                                                    self._class)
        return self

    def tf(self, mask=[], addon =[]):

        def concurrent(mat,addon):
            if addon:
                addons = np.zeros((mat.shape[0], len(addon)))
                for i,pair in enumerate(addon):
                    for j in xrange(mat.shape[0]):
                        addons[j,i] = np.min((mat[j,pair[0]],mat[j,pair[1]]))
                return np.hstack((mat.toarray(),addons))
            else:
                return mat


        self._ifeatures = masking(self.mappings, mask)
        self._ifeatures = concurrent(self._ifeatures, addon)
        transformer = TfidfTransformer(norm='l2', use_idf=False,
                                       smooth_idf=True, sublinear_tf=False)
        self._ifeatures = transformer.fit_transform(self._ifeatures)
        return self


class SVM:
    "Classifiers"

    def __init__(self, disp, opt=None):

        if opt:
            global OPT
            OPT = opt

        self.disp = disp
        self.TF = TermFrequency(site='english',
                                force_injest=OPT.FORCE_INJEST,
                                verbose=OPT.VERBOSE_MODE)
        self.helper = ESHandler(es=self.TF.es, force_injest=False)

        # Initialize attributes
        self.round = 0
        self.results = {"result": []}
        self.CONTROL = None
        self.mask=[]
        self.addon=[]

    @staticmethod
    def vprint(string):
        if OPT.VERBOSE_MODE:
            print(string)

    @staticmethod
    def fselect(all_docs, n_features=4000):
        transformer = TfidfTransformer(norm='l2', use_idf=True
                                       , smooth_idf=True, sublinear_tf=True)
        tfidf_mtx = transformer.fit_transform(all_docs)
        key_features = np.argsort(tfidf_mtx.sum(axis=0)).tolist()[0][
                       -n_features:]
        return key_features

    def featurize(self):
        t = time()
        train_tfm = self.TF.matrix(CONTROL=False, LABELED=True)
        all_tfm = self.TF.matrix(CONTROL=False, LABELED=False)
        self.vprint("Get TFM. {} seconds elapsed".format(time() - t))
        t = time()
        self.top_feat = self.fselect(all_docs=all_tfm["matrix"])
        self.vprint("Feature selection. {} seconds elapsed".format(time() - t))
        t = time()

        ## Save TF-IDF score
        self.vocab = [train_tfm['header'][i] for i in self.top_feat]
        # self.TRAIN = FeatureMap(raw_data=train_tfm,
        # features=self.top_feat).tf()
        self.vprint("Featurization. {} seconds elapsed".format(time() - t))
        return self

    def update_matrix(self):
        pass

    def rerun(self, mask=list()):
        "Masking"
        tmp = np.identity(len(self.vocab))
        for x in mask:
            tmp[x, x] = 0;
        my_mask = csr_matrix(tmp)
        TO_REVIEW = [self.TEST.pop(idx) for idx in
                     self.sort_order_uncertain[:50]]
        self.TRAIN.update_mapping(TO_REVIEW)
        return self

    def more_inf(self,mat,label):
        inf=[]
        for i in xrange(mat.shape[1]):
            col=csr_matrix(mat[:,i].transpose().toarray())
            what=col.indices
            pos=np.array(label)[what].tolist().count("pos")
            all=len(what)
            more={"all": all, "pos": pos}
            inf.append(more)
        return inf


    def run(self, mask=[], addon=[]):
        if mask:
            self.mask = mask
        if addon:
            self.addon = addon

        self.round += 1
        self.clf = svm.SVC(kernel='linear', probability=True)

        # Update training matrix
        t = time()
        train_tfm = self.TF.matrix(CONTROL=False, LABELED=True)
        # self.TRAIN = self.TRAIN.refresh(data=train_tfm)
        self.TRAIN = FeatureMap(raw_data=train_tfm,
                                features=self.top_feat).tf(mask=self.mask, addon=self.addon)

        self.vprint(
            "UPDATE TFM for TRAIN. {} seconds elapsed".format(time() - t))
        t = time()

        self.clf.fit(self.TRAIN._ifeatures, self.TRAIN._class)

        #### Aggressive Undersampling ####

        # labels=np.array(self.TRAIN._class)
        # poses = np.where(labels == "pos")[0]
        # negs = np.where(labels == "neg")[0]
        # train_dist = self.clf.decision_function(self.TRAIN._ifeatures[negs])
        # negs_sel = np.argsort(np.abs(train_dist))[::-1][:len(poses)]
        # sample = poses.tolist() + negs[negs_sel].tolist()
        #
        # self.TRAIN.sampling(sample)
        # self.clf.fit(self.TRAIN._ifeatures, self.TRAIN._class)

        ##################################

        self.vprint("TRAIN SVM. {} seconds elapsed".format(time() - t))
        t = time()


        #### re-labeling, pick suspicious documents from training set ####
        conf = np.array(self.clf.predict_proba(self.TRAIN._ifeatures))
        labels = np.array(self.TRAIN._class)
        poses = np.where(labels == "pos")[0]
        negs = np.where(labels == "neg")[0]
        pos_at = list(self.clf.classes_).index("pos")
        prob_pos = conf[poses,pos_at]
        prob_neg = conf[negs, pos_at]
        pos_order = np.argsort(prob_pos)[:int(self.disp/2)]
        neg_order = np.argsort(prob_neg)[::-1][:int(self.disp/2)]
        self.important = negs[neg_order].tolist() + poses[pos_order].tolist()
        self.important_prob =  prob_neg[neg_order].tolist() + prob_pos[pos_order].tolist()
        self.important_docs = [self.helper.get_document(
            _id=self.TRAIN.doc_id[i]) for i in
                            self.important]

        ##################################################################


        # Update test matrix
        test_tfm = self.TF.matrix(CONTROL=False, LABELED=False)
        if self.round<=1:
            self.tot = len(test_tfm["meta"])
            """
            "
            " NOTE: "pronunciation" TAG has been used. UPDATE THIS LATER (WOF)
            "
            """
            # set_trace()
            self.num_pos = len([a for a in test_tfm["meta"] if any([elm in a[
                'tags'] for elm in self.helper.es.RELEVANT_TAG_NAME ])])
        self.vprint(
            "Load from ES for TEST. {} seconds elapsed".format(time() - t))
        t = time()
        self.TEST = FeatureMap(raw_data=test_tfm,
                               features=self.top_feat).tf(mask=self.mask, addon=self.addon)

        self.vprint("Get TFM for TEST. {} seconds elapsed".format(time() - t))
        t = time()

        # Number of responsive documents.
        preds = self.clf.predict(self.TEST._ifeatures)
        self.tot_pos = 100*len([a for a in preds if a=="pos"])/self.num_pos
        self.tot_reviewed = 100*((self.tot - len(preds))/self.tot)
        pred_proba = self.clf.predict_proba(self.TEST._ifeatures)
        pos_at = list(self.clf.classes_).index("pos")
        self.coef = self.clf.coef_.toarray()[0]
        self.dual_coef = self.clf.dual_coef_.toarray()[0]
        self.more = self.more_inf(self.TRAIN._ifeatures, self.TRAIN._class)

        if not pos_at:
            self.coef = -self.coef
            self.dual_coef = -self.dual_coef

        support = self.clf.support_
        self.prob = pred_proba[:, pos_at]

        self.sort_order_certain = np.argsort(1 - self.prob)
        self.sort_order_support = np.argsort(1 - np.abs(self.dual_coef))

        # self.sort_order_uncertain = np.argsort(np.abs(pred_proba[:, 0] - 0.5))

        ## test dis ##
        dist = self.clf.decision_function(self.TEST._ifeatures)
        self.sort_order_uncertain = np.argsort(np.abs(dist))
        ##############


        self.certain = [self.helper.get_document(
                _id=self.TEST.doc_id[i]) for i in
                        self.sort_order_certain[:self.disp]]
        self.uncertain = [self.helper.get_document(
                _id=self.TEST.doc_id[i]) for i in
                          self.sort_order_uncertain[:self.disp]]
        self.support_vec = [self.helper.get_document(
                _id=self.TRAIN.doc_id[i]) for i in
                            support[self.sort_order_support[:max((list(np.abs(self.dual_coef)).count(1),self.disp))]]]

        self.vprint("SUMMARIZED. {} seconds elapsed".format(time() - t))
        t = time()

        return self.stats()

    def stats(self,mask=[],addon=[]):
        if mask:
            self.mask=mask
        if addon:
            self.addon=addon
        t = time()

        # --Stats--

        self.CONTROL = FeatureMap(
            raw_data=self.TF.matrix(CONTROL=True, LABELED=True),
            features=self.top_feat).tf(addon=self.addon)

        self.vprint(
            "Get TFM for CONTROL. {} seconds elapsed".format(time() - t))
        t = time()

        # Turnovers
        preds = self.clf.predict(self.CONTROL._ifeatures)
        pred_proba = self.clf.predict_proba(self.CONTROL._ifeatures)
        pos_at = list(self.clf.classes_).index("pos")
        self.proba = pred_proba[:, pos_at]
        turnover = [i for i in xrange(len(self.proba)) if
                    not self.CONTROL._class[i] == preds[i]]
        sort_order = np.argsort(0.5 - np.abs(self.proba[turnover] - 0.5))
        self.real_order = np.array(turnover)[sort_order][:self.disp]
        self.turnovers = [self.helper.get_document(_id=self.CONTROL.doc_id[i])
                          for i in self.real_order]

        self.vprint("TURNOVERS. {} seconds elapsed".format(time() - t))
        t = time()


        # Stats
        self.abcd = ABCD(before=self.CONTROL._class, after=preds)
        self.STATS = [k.stats() for k in self.abcd()]

        self.vprint("Get STATS. {} seconds elapsed".format(time() - t))
        t = time()
        ###########
        self.results['result'].append({
            "the_round"    : self.round,
            "consistency"  : 0,
            "turnover_prob": ','.join(
                    map(str, self.proba[self.real_order])),
            "turnover"     : self.turnovers,
            "fscore"       : self.STATS[1],
            "num_turnovers": len(self.turnovers),
            "num_pos": self.tot_pos,
            "num_reviewed": self.tot_reviewed
        })

        return self

    @staticmethod
    def ranges(lst):
        pass

    def get_response(self):
        try:
            onlyPos = np.array([coef for coef in self.coef if coef > 0])
            onlyCert = np.array([cert for cert in self.prob if cert > 0.5])
            certainRanges = np.percentile(onlyCert, [25, 50, 90]).tolist()
            postermRanges = np.percentile(onlyPos,  [25, 50, 90]).tolist()
        except:
            set_trace()
        return {
            "the_round"       : self.round,
            "coef"            : ','.join(map(str, self.coef)),
            "support"         : self.important_docs,
            "dual_coef"       : ','.join(
                    map(str, self.important_prob)),
            "certain_prob"    : ','.join(
                    map(str, self.prob[self.sort_order_certain])),
            "uncertain_prob"  : ','.join(
                    map(str, self.prob[self.sort_order_uncertain])),
            "certain"         : self.certain,
            "uncertain"       : self.uncertain,
            "vocab"           : self.vocab,
            "the_round"       : self.round,
            "consistency"     : 0,
            "turnover_prob"   : ','.join(
                    map(str, self.proba[self.real_order])),
            "turnover"        : self.turnovers,
            "pos"             : self.STATS[1],
            "neg"             : self.STATS[0],
            "more_coef"       : self.more,
            "rCertain"        : ','.join(map(str, certainRanges)),
            "rPosterm"        : ','.join(map(str, postermRanges))
        }

    def get_concurrency(self,term):

        def score_pos(labels):
            return labels.count("pos")*2-len(labels)

        disp_num = 100
        term_ind = csr_matrix(self.TRAIN._ifeatures[:, term].transpose().toarray()).indices


        ###########
        labels= np.array(self.TRAIN._class)[term_ind]
        if len(Counter(labels).keys()) < 2:
            return [],[]
        clf = svm.SVC(kernel='linear', probability=True)
        clf.fit(self.TRAIN._ifeatures[term_ind],labels)
        pos_at = list(clf.classes_).index("pos")
        coef = clf.coef_.toarray()[0]

        if not pos_at:
            coef = -coef

        order = np.argsort(np.abs(coef))[::-1].tolist()[:disp_num]
        order_score = coef[order].tolist()
        ###########


        # scores=[]
        # for x in xrange(len(self.vocab)):
        #     if x == term:
        #         score = 0
        #     else:
        #         x_ind = csr_matrix(self.TRAIN._ifeatures[:, x].transpose().toarray()).indices
        #         and_ind = list(set(term_ind) & set(x_ind))
        #         score = score_pos(np.array(self.TRAIN._class)[and_ind].tolist())
        #     scores.append(score)
        # num=np.min((len(scores)-scores.count(0),disp_num))
        # scores=np.array(scores)
        #
        # order = np.argsort(np.abs(scores))[::-1].tolist()[:num]
        # order_score = scores[order].tolist()

        return order, order_score

    def get_determinant(self, id):

        # Determinants (Nearest neighbors to turnovers in training set)

        def w_dist(csr1, csr2, coef):
            ind_1 = csr1.indices
            ind_2 = csr2.indices
            sum = 0
            inds = list(set(ind_1) | set(ind_2))
            for ind in inds:
                sum = sum + np.abs(coef[ind]) * (csr1[0, ind] - csr2[0, ind]) ** 2
            return np.sqrt(sum/np.sum(np.abs(coef)))

        t = time()
        disp_num = 10
        dists = []
        for j, can in enumerate(self.TRAIN._ifeatures):
            dist = w_dist(self.CONTROL._ifeatures[id], can, self.coef)
            dists.append(dist)
        sorted_order_dists = np.argsort(dists)[:disp_num]
        dists=np.array(dists)[sorted_order_dists].tolist()
        determinants = [self.helper.get_document(_id=self.TRAIN.doc_id[i])
                             for i in sorted_order_dists]
        self.vprint("DETERMINENTS. {} seconds elapsed".format(time() - t))
        return determinants, dists

        #######






# ----Command Line Interface----
@click.command()
@click.option('--force', default="false",
              help='Flags: True/False. Create force injest documents to ES.')
@click.option('--debug', default="false",
              help='Flags: True/False. Enter verbose mode (display all '
                   'outputs to stdout.\n')
def cmd(force, debug):
    global OPT
    OPT.also(
            FORCE_INJEST=force.lower() == 'true',
            VERBOSE_MODE=debug.lower() == 'true'
    )
    # set_trace()
    print(
            "\nRunning: model.py with settings: \n\t--force={FORCE}\n "
            "\t--debug={DEBUG}".format(
                    FORCE=force,
                    DEBUG=debug))
    classifier = SVM()
    return classifier.run()


if __name__ == '__main__':
    cmd()
