# Manuscripts: GSoC'18

The [manuscripts project](https://github.com/chaoss/grimoirelab-manuscripts) is part of the grimoirelab toolset and is used to produce Reports based on enriched elasticsearch indices.

This repository has been set up to track the status of the work that is being done on the Manuscripts project under Google Summer of Code 18.

### Coordination procedures:

We will be discussing about the progress of this project every `Wednesday at 13:00 CEST or 16:30 IST` at the `#grimoirelab` channel on [**FREENODE IRC**](https://webchat.freenode.net/). The transcripts of the meetings (chats) are available in the [IRC-transcripts](https://github.com/aswanipranjal/gsoc-manuscripts/tree/master/IRC-transcripts) folder. 

There will also be a weekly [blog post](https://aswanipranjal.github.io/posts/), every tuesday night/wednesday morning, detailing: what I did that week, the challenges I faced and the amazing things that I learned.
I will also be posting the summary of the week's meeting on the [mailing lists](https://lists.linuxfoundation.org/mailman/listinfo/oss-health-metrics) of CHAOSS. Along with a small writeup of what I plan to do the coming week and the transcripts for that week's meeting.

The [Growth-Maturity-Decline Work Group](https://github.com/chaoss/wg-gmd) is working on defining the GMD metrics in a better way and trying ways to implement them. They have a fortnightly zoom meeting at `18:00 CEST` or `11:00 CDT`, every other `Thursday`. You can join in via this [zoom link](https://unomaha.zoom.us/j/720431288). The next meeting will be on 31st May 2018

We are planning to keep all the communication open so that everyone is free to participate and help us grow! Hence all the Issues and PRs made for this project will be listed here.

---
## Issues and Pull Requests made:
All the issues and PRs created during the project will be listed out here.

### Overall Coordination and Infrastructure setup (Primary Tickets):
These tickets are concerning how to structure the code that is being generated and about general discussions on how to proceed with the project.

- [chaoss/grimoirelab-manuscripts/issues/50](https://github.com/chaoss/grimoirelab-manuscripts/issues/50): This issue tackles the problem of adding new code regarding the GMD metrics into CHAOSS.
- [chaoss/grimoirelab/issues/106](https://github.com/chaoss/grimoirelab/issues/106): This issue is regarding exploring different visualisation techniques to describe the metrics so that the users can unserstand the analysis better.
- [chaoss/grimoirelab/issues/108](https://github.com/chaoss/grimoirelab/issues/108): This issue is regarding setting up the documentation for GSoC.

### ReDesigning Manuscripts:
These tickets are related to designing new functions, classes and methods to calculate the metrics and reports:

- [x] [chaoss/grimoirelab-manuscripts/issues/62](https://github.com/chaoss/grimoirelab-manuscripts/issues/62): Creating chainable functions and New Classes to calculate the Metrics.
- [x] [chaoss/grimoirelab-manuscripts/issues/66](https://github.com/chaoss/grimoirelab-manuscripts/issues/66): issue describing implementation of the new functions.
- [X] [chaoss/grimoirelab-manuscripts/pull/67](https://github.com/chaoss/grimoirelab-manuscripts/pull/67): PR adding new functions to the manuscripts repository. Closes [#62](https://github.com/chaoss/grimoirelab-manuscripts/issues/62) and [#59](https://github.com/chaoss/grimoirelab-manuscripts/issues/59)
- [chaoss/grimoirelab-manuscripts/issues/70](https://github.com/chaoss/grimoirelab-manuscripts/issues/70): Issue about generating reports using the enhanced functions and classes created.
- [chaoss/grimoirelab-manuscripts/issues/81](https://github.com/chaoss/grimoirelab-manuscripts/issues/81): Issue regarding generation and indexing of data to elasticsearch that is to be used to test the new functions, classes and report generated.
- [chaoss/grimoirelab-manuscripts/pull/80](https://github.com/chaoss/grimoirelab-manuscripts/pull/80): PR adding the functionality to calculate the OVERVIEW section of the report created from the new functions.
- [x] [TESTS] [grimoirelab-manuscripts/pull/71](https://github.com/chaoss/grimoirelab-manuscripts/pull/71): PR adding new tests and updating old tests for the new functions in manuscripts2
- [x] [chaoss/grimoirelab-manuscripts/pull/73](https://github.com/chaoss/grimoirelab-manuscripts/pull/73): PR adding the initial infrastructure to calculate the reports from new functions
- [x] [chaoss/grimoirelab-manuscripts/pull/74](https://github.com/chaoss/grimoirelab-manuscripts/pull/74): PR moving the `get_aggs` and `get_timeseries` **functions** into the `Query` class in manuscripts2.
- [] [chaoss/grimoirelab-manuscripts/issues/72](https://github.com/chaoss/grimoirelab-manuscripts/issues/72): Issue regarding renaming the ugly files into something more beautiful and clear.
- [x] [chaoss/grimoirelab-manuscripts/pull/78](https://github.com/chaoss/grimoirelab-manuscripts/pull/78): PR renaming files in manuscripts2 for into elasticsearch.py and updating the tests accordingly. Closes [#72](https://github.com/chaoss/grimoirelab-manuscripts/issues/72).
- [x] [chaoss/grimoirelab-manuscripts/pull/79](https://github.com/chaoss/grimoirelab-manuscripts/pull/79): PR updating the tests for manuscripts2.

### Understanding GMD metrics and related work:
What are GMD-metrics? How can we calculate them:
- [chaoss/wg-gmd/issues/1](https://github.com/chaoss/wg-gmd/issues/1): Some of the metrics in GMD need more descriptions and more elabotration on how to implement them.
- [chaoss/wg-gmd/issues/5](https://github.com/chaoss/wg-gmd/issues/5): What are abandoned issues? 
- [chaoss/wg-gmd/issues/6](https://github.com/chaoss/wg-gmd/issues/6): should open issue age be calculated by averaging all the values or should they be used directly and visualised as a graph?
- [chaoss/wg-gmd/issues/7](https://github.com/chaoss/wg-gmd/issues/7): How exactly is closed issue duration supposed to be described?
- [x] [chaoss/wg-gmd/issues/8](https://github.com/chaoss/wg-gmd/issues/8): First response to issue duration, what is considered as a first response to an issue?
- [x] [chaoss/grimoirelab-elk/pull/383](https://github.com/chaoss/grimoirelab-elk/pull/383): This PR adds code to calculate the first response to issue duration in enriched github_issues index. Closes [wg-gmd/issues/8](https://github.com/chaoss/wg-gmd/issues/8)
- [x] [chaoss/wg-gmd/issues/9](https://github.com/chaoss/wg-gmd/issues/9): Who are considered as new contributors?
- [chaoss/wg-gmd/issues/10](https://github.com/chaoss/wg-gmd/issues/10): Which are these new oranizations?
- [chaoss/grimoirelab-elk/issues/364](https://github.com/chaoss/grimoirelab-elk/issues/364): Adding code to generate fields in enriched to calcualte the metrics under GMD 
- [chaoss/wg-gmd/issues/14](https://github.com/chaoss/wg-gmd/issues/14): Who can be considered as a maintainer of the project?

### Enrichment of indices and metrics calculation:
- [x] [chaoss/grimoirelab-elk/issues/394](https://github.com/chaoss/grimoirelab-elk/issues/394): This issue is regarding the enrichment of `github pull_requests` data separately in an elasticsearch index so that some of the metrics under GMD can be calculated through that index.
- [x] [chaoss/grimoirelab-elk/pull/399](https://github.com/chaoss/grimoirelab-elk/pull/399): Using perceval's `category` parameter, we enrich the data for pull requests. PR by [Valerio](https://github.com/valeriocos). Closes [#394](https://github.com/chaoss/grimoirelab-elk/issues/394)
- [x] [chaoss/grimoirelab-elk/pull/398](https://github.com/chaoss/grimoirelab-elk/pull/398): Another solution for [#394](https://github.com/chaoss/grimoirelab-elk/issues/394). Not accepted.
- [x] [chaoss/grimoirelab-elk/pull/401](https://github.com/chaoss/grimoirelab-elk/pull/401): Code to calculate the enriched data for PRs.
- [chaoss/grimoirelab-elk/issues/405](https://github.com/chaoss/grimoirelab-elk/issues/405):
- [chaoss/grimoirelab-perceval/issues/408](https://github.com/chaoss/grimoirelab-perceval/issues/408):
- 

### Enhancing Manuscripts on the basis of the Metrics:
- [chaoss/grimoirelab-manuscripts/issues/56](https://github.com/chaoss/grimoirelab-manuscripts/issues/56): The classes in github_issues and github_pr have been implemented using the master class of ITS data source as the parent class. That needs to be changed so that the code can be consistent.
- [x] [chaoss/grimoirelab-manuscripts/issues/59](https://github.com/chaoss/grimoirelab-manuscripts/issues/59): This issue is about updation of the current metrics and creation of new and better functions which provide more functionality to the users.

### Visualisations:
- TODO

### General correction to current Manuscripts structure and functions:
These issues concern general maintainance and enhancements on manuscripts:
- [x] [ISSUE][chaoss/grimoirelab-manuscripts/issues/49](https://github.com/chaoss/grimoirelab-manuscripts/issues/49): Setting up a menu option for manuscripts when no arguments were provided.
- [x] [PULL REQUEST][chaoss/grimoirelab-manuscripts/pull/55](https://github.com/chaoss/grimoirelab-manuscripts/pull/55): PR adding the menue option for manuscripts. Closes [#49](https://github.com/chaoss/grimoirelab-manuscripts/issues/49)
- [x] [ISSUE][chaoss/grimoirelab-manuscripts/issues/48](https://github.com/chaoss/grimoirelab-manuscripts/issues/48): Manuscripts uses a 01-01-2015 as a date for calculating metrics if a start date is not given. This issue is regarding making that date into a more specific or related one.
- [x] [PULL REQUEST][chaoss/grimoirelab-manuscripts/pull/69](https://github.com/chaoss/grimoirelab-manuscripts/pull/69): Adds the default start date as the first date from all the data sources. Closes [#48](https://github.com/chaoss/grimoirelab-manuscripts/issues/48).
- [x] [chaoss/grimoirelab-manuscripts/issues/57](https://github.com/chaoss/grimoirelab-manuscripts/issues/57): converting the queries in esquery.py file into objects from the elasticsearch_dsl module.

- Pull requests converting esquery.py file to fully use elasticsearch_dsl python module.
	- [x] [chaoss/grimoirelab-manuscripts/pull/58](https://github.com/chaoss/grimoirelab-manuscripts/pull/58)
	- [x] [chaoss/grimoirelab-manuscripts/pull/63](https://github.com/chaoss/grimoirelab-manuscripts/pull/63)
	- [x] [chaoss/grimoirelab-manuscripts/pull/64](https://github.com/chaoss/grimoirelab-manuscripts/pull/64)
- [x] [chaoss/grimoirelab-manuscripts/issues/60](https://github.com/chaoss/grimoirelab-manuscripts/issues/60): Expand on the above PR to make manuscripts fully dependent on elasticsearch_dsl.py

---
## Blog Posts (Week wise):

- [Community Bonding](https://aswanipranjal.github.io/posts/communitybonding)
- [Week-1](https://aswanipranjal.github.io/posts/week-1/)
- [Week-2](https://aswanipranjal.github.io/posts/week-2/)
- [Week-3](https://aswanipranjal.github.io/posts/week-3/)
- [Week-4](https://aswanipranjal.github.io/posts/week-4/)
- [Week-5](https://aswanipranjal.github.io/posts/week-5/)
- [Week-7](https://aswanipranjal.github.io/posts/week-7/)
- [Week-8](https://aswanipranjal.github.io/posts/week-8/)
- [Week-9](https://aswanipranjal.github.io/posts/week-9/)
- [Week-10](https://aswanipranjal.github.io/posts/week-10/)
- [Week-11](https://aswanipranjal.github.io/posts/week-11/)
