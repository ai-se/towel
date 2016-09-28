"""
This is a sample kibana dashboard framework
"""

from __future__ import print_function, division

import csv

from elasticsearch import Elasticsearch


class kibana_test:
    @classmethod
    def ingest(self):
        es = Elasticsearch()
        # define a mapping
        mapping = {
            "trip": {
                "properties": {
                    "duration": {"type": "integer"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "start_station_number": {"type": "integer"},
                    "start_station": {
                        "type": "string",
                        # Index this field, so it is searchable,
                        # but index the value exactly as specified.
                        # Do not analyze it.
                        "index": "not_analyzed"},
                    "end_station_number": {"type": "integer"},
                    "end_station": {
                        "type": "string",
                        "index": "not_analyzed"},
                    "bike_number": {"type": "string"},
                    "member_type": {"type": "string"}
                }
            }
        }

        try:
            es.indices.create("bikeshare")
        except:
            es.indices.put_mapping(index="bikeshare", doc_type="trip", body=mapping)

        # Import csv file from disk
        with open('data0.csv', 'rb') as csvfile:
            reader = csv.reader(csvfile)
            reader.next()  # this skips the header
            for id, row in enumerate(reader):
                duration = int(int(row[0]) / 100)
                content = {
                    "duration": duration,
                    "start_date": row[1],
                    "end_date": row[2],
                    "start_station_number": row[3],
                    "start_station": row[4],
                    "end_station_number": row[5],
                    "end_station": row[6],
                    "bike_number": row[7],
                    "member_type": row[8]
                }
                print('{}\r'.format(id), end="")
                es.index(index="bikeshare", doc_type="trip", id=id, body=content)


if __name__ == "__main__":
    kibana_test.ingest()
