# This is a temporary file which contains Functions, Objects and Classes
# (FOC) which will be used to calculate the metrics for Manuscripts.
# These are supposed to replace the current FOC that manuscripts uses to
# calculate the metrics as they are too naive and are not expandable.
#
# This file will also contain some helper functions which will be used
# to analyse the data retrieved from elasticsearch and for visualization
# purposes. 
# We hope to eventually integrate the FOC in this file into the main
# manuscripts branch.

 
# - If we want to seggregate the values by date: we use a date histogram.
# - If we want to seggregate the values by members or organizations: we can 
# use a `terms` aggregation with one or multiple nested aggregations which 
# give a numeric value.
#
# We can convert the output values into a dataframe for easy processing and 
# apply filters for date and other conditions as we like.
# 
# Right now, we are looking at 3 ways to seggregate the data: based on users 
# and orgs and by period(week, month, year).
# 
# Item classes:
# So, we can proceed in this manner: For each metric/group of metrics we can have 
# a class and that class can have functions for the metrics that come under that class. 
# For ex:
# 
# Let there be an Issues class. Inside that Issues class: we'll have functions such as: 
# `count`, `sum`, `average`, `percentile`, `max`, `min` i.e one function for each metric 
# that is based on aggregation of the field. It is not necessary that all the functions 
# are in all the classes because we do not calculate all the aggregations for every 
# Item(Issue, Commit, PR).

import pandas as pd
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch_dsl import A, Q, Search

import sys
import logging

logger = logging.getLogger(__name__)

# ------ New Classes and functions ------ #

class Metric():
    """
    The base class of all the necessary metrics that are going to be calculated.
    How is this different from the previously created metric classes?
    Good question, here is how: The previous classes used normal python data structures
    and functions to query elasticsearch and get the results.
    This class is using the Search class in elasticsearch_dsl module, so the
    base object in this class is the search object. Other es_dsl objects such as 
    Aggregations, Queries and Filters can be added to this base object and that will
    allow us to neatly add filters, create nested aggregations and such. 
    """

    def __init__(self, url=None, index=None):
        """Initialization of necessary parameters
    
        :client: the address/url of the elasticsearch instance to be used?
                 default: http://localhost:9200/ (optional)
        :index: name of the elasticsearch index that is to be queried (required)
        """
        self.parent_id = 0
        self.child_id = 0.1
    
        if url:
            self.es = Elasticsearch(url)
        else:
            logger.debug("No custom url provided, using default: http://localhost:9200/")
            self.es = Elasticsearch()
    
        if not index:
            logger.error("Please provide an index to query!")
            sys.exit(1)
        
        self.index = index
        self.s = Search(using=self.es, index=self.index)
    
        self.queries = {"must":[], "must_not":[]}
        self.filters = []
        self.aggregations = []
        self.size = 10000 # temporary hack to get all the data
        self.period = "month" # default period to create buckets from in date histogram
        self.precision_threshold = 3000 # accuracy that we want when counting the number of items

    def add_query(self, key_val={}):
        q = Q("match", **key_val)
        self.s = self.s.query(q)
        self.queries['must'].append(q)

    def add_inverse_query(self, key_val={}):
        q = Q("match", **key_val)
        self.s = self.s.query(~q)
        self.queries['must_not'].append(q)

    def show_queries(self):
        return self.s.to_dict()['query']

    def increment_parent(self):
        self.parent_id += 1

    def get_results(self):
        response = self.s.execute()
        aggregations = response.aggregations.to_dict()
        agg_list = []
        for i in range(self.parent_id):
            try:
                agg_list.append(buckets_to_df(aggregations[str(i)]['buckets']))
            except:
                agg_list.append(aggregations[str(i)])
        return agg_list

    def by_authors(self):
        # here, for commits, should we bucket by committer or by author?
        agg = A("terms", field="author_name", missing="others", size=self.size)
        try:
            # for issues and PRs
            agg.metric(self.child_id, "cardinality", field="id_in_repo")
        except:
            # for commits
            agg.metric(self.child_id, "cardinality", field="hash")
        #else:
        #    logger.error("Invalid es index to apply 'by_authors' filter!")
        self.s.aggs.bucket(self.parent_id, agg)
        self.s = self.s.extra(size=0)
        self.increment_parent()
        self.aggregations.append(agg)
        return self

    def by_organizations(self):
        agg = A("terms", field="user_org", missing="others", size=self.size)
        # the git enrich index does not mention the user org anywhere.
        # TODO: open an issue after this?
        # this functions is currently only for issues and PRs
        agg.metric(self.child_id, "cardinality", field="id_in_repo")
        self.s.aggs.bucket(self.parent_id, agg)
        self.s = self.s.extra(size=0)
        self.increment_parent()
        self.aggregations.append(agg)
        return self

    def by_period(self):
        try:
            agg = A("date_histogram", field="created_at", interval=self.period)
            agg.metric(self.child_id, "cardinality", field="id_in_repo")
        except:
            agg = A("date_histogram", field="commit_date", interval=self.period)
            agg.metric(self.child_id, "cardinality", field="hash")
        self.s.aggs.bucket(self.parent_id, agg)
        self.s = self.s.extra(size=0)
        self.increment_parent()
        self.aggregations.append(agg)
        return self

    def is_open(self):
        query = {"state":"open"}
        self.add_query(query)

    def is_closed(self):
        query = {"state":"closed"}
        self.add_query(query)


class Git(Metric):
    pass


# ------- Helper functions ------ #
def buckets_to_df(buckets):
    """ Takes in aggregation bucket objects and converts them into a pandas dataframe
    after cleaning the buckets. If a DateTime field is present(usually having the name:
    "key_as_string") parses it to datetime object and then it uses it as key.
    """
    cleaned_buckets = []
    for item in buckets:
        if type(item)==str:
            cleaned_buckets.append(item)

        temp = {}
        for key, val in item.items():
            try:
                value = val['value']
                temp['value'] = value
            except:
                temp[key] = val
        cleaned_buckets.append(temp)

    if "key_as_string" in temp.keys():
        ret_df = pd.DataFrame.from_records(cleaned_buckets)
        ret_df = ret_df.rename(columns={"key":"date_in_seconds"})
        ret_df['key'] = pd.to_datetime(ret_df['key_as_string'])
        ret_df = ret_df.drop(["key_as_string", "doc_count"], axis=1)
        ret_df = ret_df.set_index("key")
    else:
        ret_df = pd.DataFrame.from_records(cleaned_buckets, index="key")

    return ret_df

def term_buckets_to_df(buckets):
    pass