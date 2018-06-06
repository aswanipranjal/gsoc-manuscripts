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

import sys
import logging

from collections import OrderedDict
from datetime import datetime, timezone

import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_dsl import A, Q, Search



logger = logging.getLogger(__name__)

# ------ New Classes and functions ------ #

# here is how the class can be used:
# from new_functions import Metric
# >> github = Metric(url, index, start, end)
# 
# >> github.cardinaliry("users") 
# now this will add a user aggregation to the github object
# >> github.by_authors()
# this will pop the last added aggregation from the aggregation list 
# seggregate the aggreagtion by user buckets.
# 
# >> github.get_cardinality("commits").by_authors() # OR
# gives us the number of commits by authors
# >> github.min("author_date").by_authors()
# this should give us the min date i.e the first dates when the authors made their 
# first commits and from that we can calculate the new users per month

# DEVELOPER's NOTE:
# Some of the parameters for function definitions have been referenced from the 
# old esquery.py file, because they are the correct implementation for that function.


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

    def __init__(self, url=None, index=None, start=None, end=None, esfilters={},
                 interval=None, offset=None):
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
            self.es = Elasticsearch("http://localhost:9200/")
    
        if not index:
            logger.error("Please provide an index to query!")
            sys.exit(1)
        
        self.index = index
        self.s = Search(using=self.es, index=self.index)
    
        self.queries = {"must":[], "must_not":[]}
        self.filters = {}
        self.filters.update(esfilters)
        self.aggregations = OrderedDict()
        self.size = 10000 # temporary hack to get all the data
        self.precision_threshold = 3000 # accuracy that we want when counting the number of items
        self.start = start
        self.end = end
        self.interval = interval if interval else "month"
        self.offset = offset

    def add_query(self, key_val={}):
        q = Q("match", **key_val)
        self.s = self.s.query(q)
        self.queries['must'].append(q)

    def add_inverse_query(self, key_val={}):
        q = Q("match", **key_val)
        self.s = self.s.query(~q)
        self.queries['must_not'].append(q)

    def show_queries(self):
        return self.queries

    def increment_parent(self):
        self.parent_id += 1

    def increment_child(self):
        self.child_id += 0.1

    def is_open(self):
        query = {"state":"open"}
        self.add_query(query)

    def is_closed(self):
        query = {"state":"closed"}
        self.add_query(query)

    def get_sum(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("sum", field=field)
        self.aggregations['sum_' + field] = agg
        return self

    def get_average(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("avg", field=field)
        self.aggregations['avg_' + field] = agg
        return self

    def get_percentile(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("percentiles", field=field)
        self.aggregations['percentile_' + field] = agg
        return self

    def get_terms(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("terms", field=field, size=self.size, order={"_count":"desc"})
        self.aggregations['terms_' + field] = agg
        return self

    def get_min(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("min", field=field)
        self.aggregations['min_' + field] = agg
        return self

    def get_max(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("max", field=field)
        self.aggregations['max_' + field] = agg
        return self

    def get_cardinality(self, field=None):
        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("cardinality", field=field, precision_threshold=self.precision_threshold)
        self.aggregations['cardinality_' + field] = agg
        return self

    def set_range(self, date_field=None, start=None, end=None):
        start = start if start else self.start
        end = end if end else self.end

        if not date_field:
            date_field = "grimoire_creation_date"
        start_end = {}
        start_end["gte"] = "%s" % start.isoformat()
        start_end["lte"] = "%s" % end.isoformat()
        query_range = {date_field: start_end}
        self.s = self.s.filter("range", **query_range)
        return self

    def by_authors(self, field=None):
        # here, for commits, should we bucket by committer or by author?
        # Parent aggregation
        agg_field = field if field else "author_name"
        agg = A("terms", field=agg_field, missing="others", size=self.size)
        # child aggregation is the last added aggregation
        child_agg = self.aggregations.popitem()
        # add child agg to parent agg
        agg.metric(self.child_id, child_agg[1])
        # insert this agg to the agg dict. This agg essentially replaces
        # the last agg that was in the agg dict
        self.aggregations["terms_" + agg_field] = agg
        return self

    def by_organizations(self, field=None):
        # the git enrich index does not mention the user org anywhere.
        # TODO: open an issue after this?
        # this functions is currently only for issues and PRs
        agg_field = field if field else "user_org"
        agg = A("terms", field=agg_field, missing="others", size=self.size)
        child_agg = self.aggregations.popitem()
        agg.metric(self.child_id, child_agg[1])
        self.aggregations["terms_" + agg_field] = agg
        return self

    def by_period(self, period=None, timezone=None, field=None, start=None, end=None):
        
        hist_period = period if period else self.interval
        time_zone = timezone if timezone else "UTC"
        start = start if start else self.start
        end = end if end else self.end
        bounds = self.get_bounds(start, end)
        date_field = field if field else "grimoire_creation_date"
        agg = A("date_histogram", field=date_field, interval=hist_period,
                time_zone=time_zone, min_doc_count=0, **bounds)

        child_agg = self.aggregations.popitem()
        agg.metric(self.child_id, child_agg[1])
        self.aggregations["date_histogram_" + child_agg[0]] = agg
        return self

    def get_bounds(self, start=None, end=None):

        # Extend bounds so we have data until start and end
        start = start.replace(microsecond=0)
        start_ts = start.replace(tzinfo=timezone.utc).timestamp()
        start_ts_ms = start_ts * 1000  # ES uses ms
        end = end.replace(microsecond=0)
        end_ts = end.replace(tzinfo=timezone.utc).timestamp()
        end_ts_ms = end_ts * 1000  # ES uses ms
        bounds_data = {"min": start_ts_ms, "max": end_ts_ms}
        bounds = {"extended_bounds": bounds_data}
        return bounds

    def get_results(self, dataframe=False):
        """
        dataframe: if true, return values as a pandas dataframe
        """
        for key, val in self.aggregations.items():
            self.s.aggs.bucket(self.parent_id, val)
            self.increment_parent()
        
        self.s = self.s.extra(size=0)
        response = self.s.execute()
        return response.to_dict()

    def get_ts(self):
        res = self.get_results()

        ts = {"date": [], "value": [], "unixtime": []}

        if 'buckets' not in res['aggregations'][str(self.parent_id-1)]:
            raise RuntimeError("Aggregation results have no buckets in time series results.")

        for bucket in res['aggregations'][str(self.parent_id-1)]['buckets']:
            ts['date'].append(bucket['key_as_string'])
            if str(self.child_id) in bucket:
                # We have a subaggregation with the value
                # If it is percentiles we get the median
                if 'values' in bucket[str(self.child_id)]:
                    val = bucket[str(self.child_id)]['values']['50.0']
                    if val == 'NaN':
                        # ES returns NaN. Convert to None for matplotlib graph
                        val = None
                    ts['value'].append(val)
                else:
                    ts['value'].append(bucket[str(self.child_id)]['value'])
            else:
                ts['value'].append(bucket['doc_count'])
            # unixtime comes in ms from ElasticSearch
            ts['unixtime'].append(bucket['key'] / 1000)

        return ts

    def get_aggs(self):
        res = self.get_results()
        if 'aggregations' in res and 'values' in res['aggregations'][str(self.parent_id-1)]:
            try:
                agg = res['aggregations'][str(self.parent_id-1)]['values']["50.0"]
                if agg == 'NaN':
                    # ES returns NaN. Convert to None for matplotlib graph
                    agg = None
            except:
                raise RuntimeError("Multivalue aggregation result not supported")
        elif 'aggregations' in res and 'value' in res['aggregations'][str(self.parent_id-1)]:
            agg = res['aggregations'][str(self.parent_id-1)]['value']
        else:
            agg = res['hits']['total']

        return agg


    def get_trend(self):
        ts = self.get_ts()
        last = ts['value'][len(ts['value']) - 1]
        prev = ts['value'][len(ts['value']) - 2]

        trend = last - prev
        trend_percentage = None
        if last == 0:
            if prev > 0:
                trend_percentage = -100
            else:
                trend_percentage = 0
        else:
            trend_percentage = int((trend / last) * 100)

        return (last, trend_percentage)

    def show_search_object(self):
        # This function is purely for debugging purposes
        return self.s.to_dict()

# ------- Helper functions ------ #

def calculate_bmi(closed, submitted):
    # takes as input 2 dictionaries, usually time series buckets generated by
    # get_ts() function in the Metric class
    if sorted(closed.keys()) != sorted(submitted.keys()):
        raise AttributeError("The buckets supplied are not congruent!")

    dates = closed['date']
    closed_values = closed['value']
    submitted_values = submitted['value']
    ratios = []
    for x, y in zip(closed_values, submitted_values):
        if y==0:
            ratios.append(0)
        else:
            ratios.append(x/y)
    dates = ["{}-{}".format(date[:4], date[5:7]) for date in dates]
    return {"Period":dates, "Closed/Submitted":ratios}


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