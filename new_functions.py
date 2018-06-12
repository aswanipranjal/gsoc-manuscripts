# This is a temporary file which contains Functions, Objects and Classes
# (FOC) which will be used to calculate the metrics for Manuscripts.
# These are supposed to replace the current FOC that manuscripts uses to
# calculate the metrics as they are too naive and are not expandable.
#
# This file will also contain some helper functions which will be used
# to analyse the data retrieved from elasticsearch and for visualization
# purposes. 
# We hope to eventually integrate the FOCs in this file into the main
# manuscripts branch.

import sys
import logging

from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from dateutil import parser

import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch_dsl import A, Q, Search

logger = logging.getLogger(__name__)


class Index():
    """Index class which will represent an index in elasticsearch"""

    def __init__(self, index, url=None):
        """
        :url: the address/url of the elasticsearch instance to be used?
                 default: http://localhost:9200/ (optional)
        :index: name of the elasticsearch index that is to be queried (required)
        """

        self.url = url if url else None
        self.index = index # index to query data from
        if self.url:
            self.es = Elasticsearch(self.url) # This allows us to query _any_ elasticsearch instance
        else:
            logger.debug("No custom url provided, using default: http://localhost:9200/")
            self.es = Elasticsearch("http://localhost:9200/")


class EQCC():
    """
    E: Elasticsearch - creates elasticsearch_dsl objects
    Q: Query - queries elasticsearch
    C: Connection - provides a connection to elasticsearch
    C: Compute - computes the basic data for a Metric

    The base class of all the necessary metrics that are going to be calculated.
    How is this different from the previously created metric classes?
    Good question, here is how: The previous classes used normal python data structures
    and functions to query elasticsearch and get the results.
    This class is using the Search class in elasticsearch_dsl module, so the
    base object in this class is the search object. Other es_dsl objects such as 
    Aggregations, Queries and Filters can be added to this base object and that will
    allow us to neatly add filters, create nested aggregations and such.
    """

    def __init__(self, index_obj, esfilters={}, interval=None, offset=None):
        """Initialization of necessary parameters

        :index_obj: An Index object containing the connection details
        :esfilters: TODO: this is still to be implemented
        :interval: interval to use for timeseries data
        :offset: TODO: this is still to be implemented
        """
        self.es = index_obj.es
        self.index = index_obj.index

        self.s = Search(using=self.es, index=self.index) # create the search object
        # this search object is the main thing differentiating this class from the
        # old classes and methods

        self.parent_id = 0 # starting parent id to use
        self.child_id = 0
        
        self.queries = {"must":[], "must_not":[]} # a query dict to store the queries
        self.filters = {} # to store the filters
        self.filters.update(esfilters) 

        # an ordered aggregation dict so that the nested aggregations can be created easily
        self.aggregations = OrderedDict()

        self.size = 10000 # temporary hack to get all the data
        self.precision_threshold = 3000 # accuracy that we want when counting the number of items

        self.start = None
        self.end = None
        self.interval = interval if interval else "month"
        self.offset = offset
        self.range = {}
        self.child_agg_counter_dict = defaultdict(int) # to keep a track of nested child aggregations
        
    def add_query(self, key_val={}):
        """Add an es_dsl query object to the es_dsl Search object"""

        q = Q("match", **key_val)
        self.s = self.s.query(q)
        self.queries['must'].append(q)

    def add_inverse_query(self, key_val={}):
        """Add an es_dsl inverse query object to the es_dsl Search object"""

        q = Q("match", **key_val)
        self.s = self.s.query(~q)
        self.queries['must_not'].append(q)

    def increment_parent(self):
        """Increments the parent id by one"""

        self.parent_id += 1

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

    def get_extended_stats(self, field=None):
        """Create an extended_stats aggregation object and add it to the aggregation dict"""

        if not field:
            raise AttributeError("Please provide field to apply aggregation to!")
        agg = A("extended_stats", field=field)
        self.aggregations['extended_stats_' + field] = agg
        return self

    def add_custom_aggregation(self, agg, name=None):
        agg_name = name if name else 'custom_agg'
        self.aggregations[agg_name] = agg

    def since(self, start, field=None):
        """
        :start: date to start looking at the fields (from date)
        """

        if not field:
            field = "grimoire_creation_date"
        self.start = start

        date_dict = {"gte":"{}".format(self.start.isoformat())}

        if field in self.range.keys():
            self.range[field].update(date_dict)
        else:
            self.range[field] = date_dict
        return self

    def until(self, end, field=None):
        """
        :end: date to stop looking at the fields (to date)
        """

        if not field:
            field = "grimoire_creation_date"
        self.end = end

        date_dict = {"lte":"{}".format(self.end.isoformat())}

        if field in self.range.keys():
            self.range[field].update(date_dict)
        else:
            self.range[field] = date_dict
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
        agg_field = field if field else "author_uuid"
        agg_key = "terms_" + agg_field

        if agg_key in self.aggregations.keys():
            agg = self.aggregations[agg_key]
        else:
            agg = A("terms", field=agg_field, missing="others", size=self.size)

        child_agg_counter = self.child_agg_counter_dict[agg_key] # 0 if not present because defaultdict
        # child aggregation is the last added aggregation
        child_name, child_agg = self.aggregations.popitem()
        # add child agg to parent agg
        agg.metric(child_agg_counter, child_agg)
        # insert this agg to the agg dict. This agg essentially replaces
        # the last agg that was in the agg dict
        self.aggregations[agg_key] = agg
        self.child_agg_counter_dict[agg_key] += 1
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
        agg_field = field if field else "author_org_name"
        agg_key = "terms_" + agg_field

        if agg_key in self.aggregations.keys():
            agg = self.aggregations[agg_key]
        else:
            agg = A("terms", field=agg_field, missing="others", size=self.size)

        child_agg_counter = self.child_agg_counter_dict[agg_key] # 0 if not present because defaultdict

        child_name, child_agg = self.aggregations.popitem()
        agg.metric(child_agg_counter, child_agg)
        self.aggregations[agg_key] = agg
        self.child_agg_counter_dict[agg_key] += 1

        return self

    def by_period(self, field=None, period=None, timezone=None, start=None, end=None):
        """Create a date histogram aggregation using the last added aggregation for the
        current object. Add this date_histogram aggregation into the aggregations Dict
        """
        hist_period = period if period else self.interval
        time_zone = timezone if timezone else "UTC"

        start = start if start else self.start
        end = end if end else self.end
        bounds = self.get_bounds(start, end)

        date_field = field if field else "grimoire_creation_date"
        agg_key = "date_histogram_" + date_field

        agg = A("date_histogram", field=date_field, interval=hist_period,
                time_zone=time_zone, min_doc_count=0, **bounds)

        child_agg_counter = self.child_agg_counter_dict[agg_key]

        child_name, child_agg = self.aggregations.popitem()
        agg.metric(child_agg_counter, child_agg)
        self.aggregations[agg_key] = agg
        self.child_agg_counter_dict[agg_key] += 1

        return self

    def clear_aggregation(self):
        self.aggregations = OrderedDict()

    def get_bounds(self, start=None, end=None):
        """Get bounds for the date_histogram"""

        bounds = {}
        if start or end:
            # Extend bounds so we have data until start and end
            start_ts = None
            end_ts = None
            
            if start:
                start = start.replace(microsecond=0)
                start_ts = start.replace(tzinfo=timezone.utc).timestamp()
                start_ts_ms = start_ts * 1000  # ES uses ms
            if end:
                end = end.replace(microsecond=0)
                end_ts = end.replace(tzinfo=timezone.utc).timestamp()
                end_ts_ms = end_ts * 1000  # ES uses ms

            bounds_data = {}
            if start:
                bounds_data["min"] = start_ts_ms
            if end:
                bounds_data["max"] = end_ts_ms

            bounds["extended_bounds"] = bounds_data
        return bounds

    def clean_agg_from_search(self):
        """Remove all aggregations added to the search object"""
        temp_search = self.s.to_dict()
        if 'aggs' in temp_search.keys():
            del temp_search['aggs']
            self.s.update_from_dict(temp_search)
            self.parent_id = 0

    def fetch_aggregation_results(self, dataframe=False):
        """Loop though the aggregations dict and add them to the Search object
        in order in which they were created. Query elasticsearch with the Search
        object and return a dict containing the results
        dataframe: if true, return values as a pandas dataframe
        """
        self.clean_agg_from_search()

        for key, val in self.aggregations.items():
            self.s.aggs.bucket(self.parent_id, val)
            self.increment_parent()
        
        if self.range:
            self.s = self.s.filter("range", **self.range)

        self.s = self.s.extra(size=0)
        response = self.s.execute()
        return response.to_dict()

    def fetch_results_from_source(self, *fields, dataframe=False):
        """Get all values for specific fields, from source"""

        if not fields:
            raise AttributeError("Please provide the fields to get from elasticsearch!")

        self.clean_agg_from_search()

        if self.range:
            self.s = self.s.filter("range", **self.range)

        self.s = self.s.extra(_source=fields)
        self.s = self.s.extra(size=self.size)

        response = self.s.execute()
        hits = response.to_dict()['hits']['hits']
        data = [item["_source"] for item in hits]
        if dataframe:
            return pd.DataFrame.from_records(data)
        else:
            return data

    def get_ts(self, dataframe=False):
        """Get time series data for the specified fields and period of analysis

        :dataframe: if dataframe=True, return a pandas.DataFrame obj
        """

        res = self.fetch_aggregation_results()
        ts = {"date": [], "value": [], "unixtime": []}

        if 'buckets' not in res['aggregations'][str(self.parent_id-1)]:
            raise RuntimeError("Aggregation results have no buckets in time series results.")

        for bucket in res['aggregations'][str(self.parent_id-1)]['buckets']:
            ts['date'].append(parser.parse(bucket['key_as_string']))
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
        if dataframe:
            return pd.DataFrame.from_records(ts, index="date")
        else:
            return ts

    def get_aggs(self):
        """Compute the values for single valued aggregations"""

        res = self.fetch_aggregation_results()
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
    dates = ["{}-{}".format(date.year, date.month, date.day) for date in dates]
    return {"Period":dates, "Closed/Submitted":ratios}


def buckets_to_df(buckets):
    """ Takes in aggregation bucket objects and converts them into a pandas dataframe
    after cleaning the buckets. If a DateTime field is present(usually having the name:
    "key_as_string") parses it to datetime object and then it uses it as key.
    """
    cleaned_buckets = []
    for item in buckets:
        if type(item)==str:
            return item

        temp = {}
        for key, val in item.items():
            try:
                temp[key] = val['value']
            except:
                temp[key] = val

        cleaned_buckets.append(temp)

    if "key_as_string" in temp.keys():
        ret_df = pd.DataFrame.from_records(cleaned_buckets)
        ret_df = ret_df.rename(columns={"key":"date_in_seconds"})
        ret_df['key'] = pd.to_datetime(ret_df['key_as_string'])
        ret_df = ret_df.drop(["key_as_string", "doc_count"], axis=1)
        ret_df = ret_df.set_index("key")
    elif "key" in cleaned_buckets[0].keys():
        ret_df = pd.DataFrame.from_records(cleaned_buckets) #, index="key")
    else:
        ret_df = pd.DataFrame(cleaned_buckets)

    return ret_df
    