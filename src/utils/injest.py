"""
Format Posts.XML from stack exchange dumps.
"""

from __future__ import division, print_function

import os
import sys

root = os.getcwd().split('src')[0] + 'src'
sys.path.append(root)
import re
import xml.etree.ElementTree as ET
from pdb import set_trace
from elasticsearch import Elasticsearch, exceptions
from .utils import Vessel
from random import random


def defaults(**d):
    """Deafult ssetting to enable ES index"""

    The = Vessel(
            ES_HOST={
                "host": 'localhost',
                "port": 9200
            },
            INDEX_NAME="stackexchange",
            TYPE_NAME="",
            RELEVANT_TAG_NAME=["pronunciation"],
            ANALYZER_NAME="my_english",
            ANALYZER_NAME_SHINGLE="my_english_shingle")

    The.also(ES_CLIENT=Elasticsearch(
            hosts=[The.ES_HOST],
            timeout=10,
            max_retries=10,
            retry_on_timeout=True))

    The.also(ES_CLIENT_ORIG=Elasticsearch(
            hosts=[The.ES_HOST],
            timeout=10,
            max_retries=10,
            retry_on_timeout=True))

    The.also(ES_EXCEPTIONS=exceptions)

    if d:
        The.override(d)

    return The


class xml2elastic:
    def __init__(self, renew=True, verbose=False):
        self.es = defaults()
        self.renew = renew
        self.verbose = verbose
        self.init_index()

    def init_index(self):

        if self.renew:
            self.es.ES_CLIENT.indices.delete(
                    index=self.es.INDEX_NAME,
                    ignore=[400, 404])

        try:
            self.es.ES_CLIENT.indices.create(
                    index=self.es.INDEX_NAME,
                    body={
                        "settings": {
                            "analysis": {
                                "analyzer": {
                                    self.es.ANALYZER_NAME: {
                                        "type"       : "custom",
                                        "tokenizer"  : "standard",
                                        "char_filter": [
                                            "html_strip"
                                        ],
                                        "filter"     : [
                                            "lowercase",
                                            "asciifolding",
                                            "apostrophe",
                                            "my_length",
                                            "stopper",
                                            "my_snow"
                                        ]
                                    }
                                },
                                "filter"  : {
                                    "stopper"  : {
                                        "type"     : "stop",
                                        "stopwords": "_english_"
                                    },
                                    "my_snow"  : {
                                        "type"    : "snowball",
                                        "language": "English"
                                    },
                                    "my_length": {
                                        "type": "length",
                                        "min" : 2
                                    }
                                }
                            }
                        }
                    }
            )
            if self.verbose:
                print('Step 1 of 3: Indices Created.')
        except Exception, e:
            print(e)
            set_trace()
            if self.verbose:
                print('Step 1 of 3: Indices already exist.')

    def init_mapping(self, doc_type=None):
        self.es.also(TYPE_NAME=doc_type)
        mapping = {
            self.es.TYPE_NAME: {
                "properties": {
                    "title": {
                        "type"  : "multi_field",
                        "fields": {
                            "title"    : {
                                "include_in_all": True,
                                "type"          : "string",
                                "store"         : True,
                                "index"         : "not_analyzed"
                            },
                            "_analyzed": {
                                "type"       : "string",
                                "store"      : True,
                                "index"      : "analyzed",
                                "term_vector": "with_positions_offsets",
                                "analyzer"   : self.es.ANALYZER_NAME
                            }
                        }
                    },
                    "text" : {
                        "type"  : "multi_field",
                        "fields": {
                            "text"     : {
                                "include_in_all": True,
                                "type"          : "string",
                                "store"         : True,
                                "index"         : "not_analyzed"
                            },
                            "_analyzed": {
                                "type"       : "string",
                                "store"      : True,
                                "index"      : "analyzed",
                                "term_vector": "with_positions_offsets",
                                "analyzer"   : self.es.ANALYZER_NAME
                            }
                        }
                    },
                    "tag"  : {
                        "type" : "string",
                        "index": "not_analyzed"
                    },
                    "label": {
                        "type" : "string",
                        "index": "not_analyzed"
                    }
                }
            }
        }

        self.es.ES_CLIENT.indices.put_mapping(
                index=self.es.INDEX_NAME,
                doc_type=self.es.TYPE_NAME,
                body=mapping)

        if self.verbose:
            print('Step 2 of 3: Docment mapped.')

    @staticmethod
    def decode(dir):
        "Extact Title, Body, and Tags"
        tree = ET.parse('{}/Posts.xml'.format(dir))
        root = tree.getroot()
        line = []
        for child in root:
            attr = child.attrib
            if 'Tags' in attr:
                title = str(
                        attr['Title'].encode('ascii', 'ignore'))
                body = str(
                        attr['Body'].encode('ascii', 'ignore'))
                tags = re.sub(r'[<>]', ' ', attr['Tags']).encode('ascii',
                                                                 'ignore').split(
                        ' ')
                yield title, body, filter(None, tags)

    def parse(self, dir, fresh=True):

        "Parse XML to ES Database"
        if self.verbose:
            print("Injesting: {}\r".format(dir), end='\n')

        # Create Mapping 
        self.init_mapping(doc_type=dir.split('\\')[-1])
        MAX_RELEVANT = 250
        MAX_IRRELEVANT = 250
        MAX_CONTROL = 1500
        MAX_DOC = 10e32
        for idx, (title, text, tag) in enumerate(self.decode(dir)):
            if idx < 8000:
                CONTROL = True if random() < 0.2 and MAX_CONTROL > 0 else False
                if CONTROL:
                    MAX_CONTROL -= 1
                REAL_TAG = 'pos' if any([t in self.es.RELEVANT_TAG_NAME for t
                                         in tag]) else \
                    'neg'
                content = {
                    "title"     : title,
                    "text"      : text,
                    "tags"      : tag,
                    "label"     : REAL_TAG if CONTROL else 'none',
                    "is_control": "yes" if CONTROL else "no",
                    "user"      : "no"
                }
                self.es.ES_CLIENT.index(
                        index='stackexchange',
                        doc_type=dir.split('\\')[-1],
                        id=idx,
                        body=content)

                self.es.ES_CLIENT_ORIG.index(
                        index='stackexchange',
                        doc_type=dir.split('\\')[-1],
                        id=idx,
                        body=content)

                if self.verbose:
                    print("Post #{id} injested\r".format(id=idx), end="")

        if self.verbose:
            print(
                    'Step 3 of 3: Site injested. Total Documents injested: {'
                    '}.\n'.format(
                            idx))
        return self.es


if __name__ == "__main__":
    pass
