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
from os import walk
from pdb import set_trace
from elasticsearch import Elasticsearch


class xml2elastic:
    def __init__(i):
        pass

    @staticmethod
    def decode(dir):
        "Extact Title, Body, and Tags"
        tree = ET.parse('{}/Posts.xml'.format(dir))
        root = tree.getroot()
        line = []
        for child in root:
            attr = child.attrib
            if 'Tags' in attr:
                tags = re.sub(r'[<>]', ' ', attr['Tags']).encode('ascii', 'ignore')
                body = re.sub(r"<(.*?)>|\n|(\\(.*?){)|}|[!$%^&*()_+|~\-={}\[\]:\";'<>?,.\/\\]|[0-9]|[@]", ' ',
                              attr['Body']).encode('ascii', 'ignore')
        return tags, body

    @classmethod
    def parse_em_all(i, dir, fresh=True):
        print("Injesting: {}\r".format(dir), end='')
        es = Elasticsearch()
        mapping = {
            dir: {
                "properties": {
                    "body": {"type": "string"},
                    "tags": {"type": "string"},
                }
            }
        }

        try:
            es.indices.create("stackexchange")
        except:
            if fresh:
                es.indices.delete(index='stackexchange', ignore=[400, 404])
            es.indices.create("stackexchange", ignore=400)

        es.indices.put_mapping(index="stackexchange", doc_type=dir, body=mapping)

        tags, body = i.decode(dir)
        for idx, (tag, text) in enumerate(zip(tags, body)):
            content = {
                "body": text,
                "tags": tag
            }
            es.index(index='stackexchange', doc_type=dir, id=idx, body=content)


def injest():
    datasets = []
    for (dirpath, _, _) in walk('{}/data/'.format(root)):
        datasets.append(os.path.abspath(dirpath))

    for dat in datasets[1:]:
        xml2elastic.parse_em_all(dat)


if __name__ == "__main__":
    injest()
