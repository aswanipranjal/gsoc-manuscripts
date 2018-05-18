# Manuscripts: GSoC'18

The [manuscripts project](https://github.com/chaoss/grimoirelab-manuscripts) is part of the grimoirelab toolset and is used to produce Reports based on enriched elasticsearch indices.

This repository has been set up to track the status of the work that is being done on the Manuscripts project under Google Summer of Code 18.

### Coordination procedures:

We will be discussing about the progress of this project every `Wednesday at 13:00 CEST or 16:30 IST` at the `
#grimoirelab` channel on [**FREENODE IRC**](https://webchat.freenode.net/). The transcripts of the meetings (chats) are available in the [IRC-transcripts](https://github.com/aswanipranjal/gsoc-manuscripts/tree/master/IRC-transcripts) folder. 

There will also be a weekly [blog post](https://aswanipranjal.github.io/posts/), every tuesday night/wednesday morning, detailing: what I did that week, the challenges I faced and the amazing things that I learned.
I will also be posting the summary of the week's meeting on the [mailing lists](https://lists.linuxfoundation.org/mailman/listinfo/oss-health-metrics) of CHAOSS. Along with a small writeup of what I plan to do the coming week and the transcripts for that week's meeting.

The [Growth-Maturity-Decline Work Group](https://github.com/chaoss/wg-gmd) is working on defining the GMD metrics in a better way and trying ways to implement them. They have a fortnightly zoom meeting at `18:00 CEST` or `11:00 CDT`, every other `Thursday`. You can join in via this [zoom link](https://unomaha.zoom.us/j/720431288).

We are planning to keep all the communication open so that everyone is free to participate and help us grow! Hence all the Issues and PRs made for this project will be listed here.

---
## Issues and Pull Requests made:
All the issues and PRs created during the project will be listed out here.

### Overall Coordination and Infrastructure setup (Primary Tickets):
These tickets are concerning how to structure the code that is being generated and about general discussions on how to proceed with the project.

- chaoss/grimoirelab-manuscripts#50 : This issue tackles the problem of adding new code regarding the GMD metrics into CHAOSS.
- chaoss/grimoirelab#106 : This issue is regarding exploring different visualisation techniques to describe the metrics so that the users can unserstand the analysis better.
- chaoss/grimoirelab#108 : This issue is regarding setting up the documentation for GSoC.

### Understanding GMD metrics and related work:
What are GMD-metrics? How can we calculate them:
- chaoss/grimoirelab-manuscripts#56 : The classes in github_issues and github_pr have been implemented using the master class of ITS data source as the parent class. That needs to be changed so that the code can be consistent.
- chaoss/wg-gmd#1 : Some of the metrics in GMD need more descriptions and more elabotration on how to implement them.

### General enhancements to current Manuscripts structure and functions:
These issues concern general maintainance and enhancements on manuscripts:
- [x] chaoss/grimoirelab-manuscripts#49 : Setting up a menu option for manuscripts when no arguments were provided.
- chaoss/grimoirelab-manuscripts#48 : Manuscripts uses a 01-01-2015 as a date for calculating metrics if a start date is not given. This issue is regarding making that date into a more specific or related one.

---
## Blog Posts (Week wise):

- [Community Bonding](https://aswanipranjal.github.io/posts/communitybonding)
- [Week-1](https://aswanipranjal.github.io/posts/week-1/)
