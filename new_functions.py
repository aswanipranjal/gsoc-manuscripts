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

import sys
import logging

from collections import OrderedDict
from datetime import datetime, timezone

import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_dsl import A, Q, Search

logger = logging.getLogger(__name__)

# ---------------------------------USAGE ------------------------------------- #
# 
# EXAMPLE: 1
# ----------
# from new_functions import Metric
#
# >> github = Metric(url, index, start, end)
# 
# >> github.get_cardinality("author_uuid") 
# This will add a author_uuid aggregation to the aggregations dict inside github 
# object
#
# >> github.get_results()
# This will return a response from elasticsearch in the form of a dictionary having
# aggregations as one of the keys. The value for that(a dict itself) will have '0' 
# as a key with the value containing the total number of unique authors in the repo 
# who created an issue/pr.
#
# >> github.by_authors()
# This will pop the last added aggregation from the aggregation list (here the 'cardinality'  
# agg) and seggregate the aggreagtion by user buckets. Here, by authors will create 
# a nested aggregation with cardinality as child agg.
# 
# >> github.get_results()
# This will loop through all the aggregations that have been added to the github object
# and add them to the Search object in the sequence in which they were added. Then it'll 
# query elasticsearch using the Search().execute() method and return a dict of the 
# values that it gets from elasticsearch.
# 
# --------------------------------------------------------------------------------
# 
# EXAMPLE:2
# ---------
# The idea is that the user can use the chainability of functions to create nested aggs
# and add queries seamlessly.
# 
# >> github = Metric(url, index, start_date, end_date) # initialize the object
# >> github.add_query({"name1":"value1"}) # add query
# >> github.add_inverse_query({"name2":"value2"}) # add inverse query
# >> github.show_queries() # list all the queries that have been added to the Search object
# {"must":[Match(name1=value1)], "must_not":[Match(name2=value2)]}
# 
# 
# >> github.get_sum(field="field1") # here field is mandatory to customise the field to aggregate
#s
# >> github.get_cardinality(field="field2")
# 
# >> github.by_authors() 
# This will pop cardinality agg from the OrderedDict of aggs and add it as a child agg       
# under the authors aggregation then add the whole aggregation into the OrderedDict.
# This functionality will allow us to keep on chaining methods to get levels of nested
# aggregations!
# 
# >> github.by_organizations()
# This will pop the by_authors aggregation from the dict and add it as a child aggregation 
# to itself. Then it will be added back into the dict.
# 
# >> github.get_results()
# Here we will have 2 aggregations, one a simple sum on 'field1' and another Double nested
# aggregation where we are getting the cardinality for 'field2' per user per organization
# in which the users belong to. Ain't this fascinating? Just keep chaining along!!!!

# --------------------------------DEVELOPER's NOTE---------------------------------#
# Some of the parameters for function definitions and functions have been referenced from 
# the old esquery.py file, because they are the correct implementation for that function.
# ---------------------------------------------------------------------------------#

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
        :start: date to start looking at the fields (from date)
        :end: date to stop looking at the fields (to date)
        :esfilters: TODO: this is still to be implemented
        :interval: interval to use for timeseries data
        :offset: TODO: this is still to be implemented
        """
        self.parent_id = 0 # starting parent id to use
        self.child_id = 0.1 # starting child id (sub aggregation) to use
    
        if url:
            self.es = Elasticsearch(url) # client to use
        else:
            logger.debug("No custom url provided, using default: http://localhost:9200/")
            self.es = Elasticsearch("http://localhost:9200/")
    
        if not index:
            logger.error("Please provide an index to query!")
            sys.exit(1)
        
        self.index = index # index to query data from
        self.s = Search(using=self.es, index=self.index) # create the search object
        # this search object is the main thing differentiating this class from the
        # old classes and methods
        
        self.queries = {"must":[], "must_not":[]} # a query dict to store the queries
        self.filters = {} # to store the filters
        self.filters.update(esfilters) 

        # an ordered aggregation dict so that the nested aggregations can be created easily
        self.aggregations = OrderedDict()

        self.size = 10000 # temporary hack to get all the data
        self.precision_threshold = 3000 # accuracy that we want when counting the number of items

        self.start = start
        self.end = end
        self.interval = interval if interval else "month"
        self.offset = offset

    def add_query(self, key_val={}):
        """Add a es_dsl query object to the es_dsl Search object"""

        q = Q("match", **key_val)
        self.s = self.s.query(q)
        self.queries['must'].append(q)

    def add_inverse_query(self, key_val={}):
        """Add a es_dsl inverse query object to the es_dsl Search object"""

        q = Q("match", **key_val)
        self.s = self.s.query(~q)
        self.queries['must_not'].append(q)

    def show_queries(self):
        """Show the query dict containing _all_ the queries"""
        return self.queries

    def increment_parent(self):
        """Increments the parent id by one"""

        self.parent_id += 1

    def increment_child(self):
        """Increments the child id by one"""

        self.child_id += 0.1

    def is_open(self):
        """Add the 'state':'open' filter to the Search object"""

        query = {"state":"open"}
        self.add_query(query)

    def is_closed(self):
        """Add the 'state':'closed' filter to the Search object"""

        query = {"state":"closed"}
        self.add_query(query)

    def get_sum(self, field=None):
        """Create a sum aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("sum", field=field)
        self.aggregations['sum_' + field] = agg
        return self

    def get_average(self, field=None):
        """Create a avg aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("avg", field=field)
        self.aggregations['avg_' + field] = agg
        return self

    def get_percentile(self, field=None):
        """Create a percentile aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("percentiles", field=field)
        self.aggregations['percentile_' + field] = agg
        return self

    def get_terms(self, field=None):
        """Create a terms aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("terms", field=field, size=self.size, order={"_count":"desc"})
        self.aggregations['terms_' + field] = agg
        return self

    def get_min(self, field=None):
        """Create a min aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("min", field=field)
        self.aggregations['min_' + field] = agg
        return self

    def get_max(self, field=None):
        """Create a max aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("max", field=field)
        self.aggregations['max_' + field] = agg
        return self

    def get_cardinality(self, field=None):
        """Create a cardinality aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("cardinality", field=field, precision_threshold=self.precision_threshold)
        self.aggregations['cardinality_' + field] = agg
        return self

    def set_range(self, date_field=None, start=None, end=None):
        """Add a range filter to the Search object
        If no start or end date is provided, the initial values for start and 
        end dates are used
        """

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
        """Create a nested aggregation object under which the last added
        aggregation will be added as a child aggregation and the parent 
        aggregation will work over it. Replace that child agg with this
        agg in the aggregations Ordered Dict.
        Reference: EXAMPLE:2
        """
        
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
        """Create a nested aggregation object under which the last added
        aggregation will be added as a child aggregation and the parent 
        aggregation will work over it. Replace that child agg with this
        agg in the aggregations Ordered Dict.
        Reference: EXAMPLE:2
        """

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
        """Create a date histogram aggregation using the last added aggregation for the
        current object. Add this date_histogram aggregation into the aggregations Ordered
        Dict
        """
        
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
        """Get bounds for the date_histogram"""

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
        """Loop though the aggregations dict and add them to the Search object
        in order in which they were created. Query elasticsearch with the Search
        object and return a dict containing the results
        dataframe: if true, return values as a pandas dataframe
        """

        for key, val in self.aggregations.items():
            self.s.aggs.bucket(self.parent_id, val)
            self.increment_parent()
        
        self.s = self.s.extra(size=0)
        response = self.s.execute()
        return response.to_dict()

    def get_ts(self):
        """Parse a date_histogram aggregation and return cleaned values"""

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
        """Return the values of single valued aggregations"""

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
        """Using gat_ts() compare the current Metric value with it's previous period's value
        Return the last period value and relative change.
        """

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
    