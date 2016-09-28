from __future__ import print_function, division
from elasticsearch import Elasticsearch
import requests
from pdb import set_trace
from funcs import *
from my_csr import *
import re

###########
# label is initialized to be "none", can be changed to be "pos" or "neg"
###########

class my_es:
    def __init__(self,index='reddit',doc_type="iama"):
        self.es = Elasticsearch()  # use default of localhost, port 9200
        self.index=index
        self.doc_type="iama"
        

    def save(self):
        # Return a response of the top 100 IAMA Reddit posts of all time
        response = requests.get("http://api.reddit.com/r/iama/top/?t=all&limit=100",
                                headers={"User-Agent": "TrackMaven"})

        fields = ['title', 'selftext', 'author', 'score',
                  'ups', 'downs', 'num_comments', 'url', 'created']

        # Loop through results and add each data dictionary to the ES "reddit" index
        for i, iama in enumerate(response.json()['data']['children']):
            content = iama['data']
            doc = {}
            for field in fields:
                doc[field] = content[field]
            doc['label']='none'
            self.es.index(index="reddit", doc_type='iama', id=i, body=doc)



    ##### methods need to be created ####
    # search for keyword, filtered by label=="none"
    def search(self,where,keyword):
        body = {"query": {"filtered": {"query": {"multi_match": {"query": keyword, "fields": where}},
                                       "filter": {"term": {"label": "none"}}}}}
        num = self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=0)["hits"]["total"]
        return self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=num)


    # get document by id
    def get(self, id):
        return self.es.get(index=self.index, doc_type=self.doc_type, id=id)

    # change the label
    def labeling(self, id, label):
        body={"doc": {"label": label}}
        self.es.update(index=self.index,doc_type=self.doc_type,id=id,body=body)

    # retrieve training examples (already labeled ones "label"=="pos" or "label"=="neg")
    def get_labeled(self):

        num = self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=0)["hits"]["total"]
        return self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=num)

    # retrieve examples have not been labeled yet ("label"=="none")
    def get_unlabeled(self):
        body = {"query": {"filtered": {"query": {"match_all": {}},
                                       "filter": {"bool": {"must": [{"term": {"label": "none"}}]}}}}}
        num = self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=0)["hits"]["total"]
        return self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=num)

    # relabel everyVessel as none
    def restart(self):
        body = {"query": {"match_all": {}}}
        num = self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=0)["hits"]["total"]
        for i in xrange(num):
            self.labeling(i,"none")

    # featurize stuffs, we want the vocabulary back
    def featurization(self):

        ##### para
        word = {}
        doc = {}
        docs = 0
        corpus=[]
        n_features=4000
        #####

        def str_clean(dirty_string):
            return re.sub(r"<(.*?)>|\n|(\\(.*?){)|}|[!$%^&*()_+|~\-={}\[\]:\";'<>?,.\/\\]|[0-9]|[@]", '',
                              dirty_string).encode('ascii', 'ignore')

        body = {"query": {"match_all": {}}}
        num = self.es.search(index=self.index, doc_type=self.doc_type, body=body, size=0)["hits"]["total"]
        res=self.es.search(index=self.index, doc_type=self.doc_type,body=body, size=num)["hits"]["hits"]
        for i in xrange(num):
            row=res[i]["_source"]["title"]+" "+res[i]["_source"]["text"]
            row=str_clean(row)
            row_c=Counter(row.split())
            corpus.append(row_c)
            word, doc, docs = tf_idf_inc(row_c, word, doc, docs)
        tfidf = {}
        words = sum(word.values())
        for key in doc.keys():
            tfidf[key] = word[key] / words * np.log(docs / doc[key])
        keys = np.array(tfidf.keys())[np.argsort(tfidf.values())][-n_features:]

        for i, row in enumerate(corpus):
            tmp = 0
            data = []
            col = []
            for key in keys:
                if key in row.keys():
                    data.append(float(row[key]))
                    col.append(tmp)
                tmp = tmp + 1
            nor = np.linalg.norm(data,2)
            if not nor == 0:
                for k in xrange(len(data)):
                    data[k] = data[k] / nor
            body = {"doc": {"feature_data":  ','.join(map(str,data)), "feature_indices": ','.join(map(str,col)), "voc": ','.join(keys)}}
            self.es.update(index=self.index, doc_type=self.doc_type, id=res[i]["_id"], body=body)



if __name__ == "__main__":
    voc=my_es().featurization()
    res=my_es().get(0)
    set_trace()
    print(res)