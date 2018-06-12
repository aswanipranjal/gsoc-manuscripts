from new_functions import Index, EQCC, buckets_to_df, calculate_bmi

class PullRequests(EQCC):
    def __init__(self, index_obj, esfilters={}, interval=None, offset=None):
        super().__init__(index_obj, esfilters, interval, offset)
        super().add_query({"pull_request":"true"})

class Issues(EQCC):

    def __init__(self, index_obj, esfilters={}, interval=None, offset=None):
        super().__init__(index_obj, esfilters, interval, offset)
        super().add_query({"pull_request":"false"})