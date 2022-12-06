# Effective usage of AWS spot instances for processing workload 
### Course: Large Scale Computing
### Academic year: 2022 / 2023
### Authors: Kamil Krzempek, Michał Węgrzyn
## Theoretical study

### AWS spot instances

Amazon EC2 Spot Instances are spare compute capacity in the AWS cloud, which are far more affordable than On-Demand instances (price difference is between 70% and 90% of On-Demand pricing).
Spot instances differs from On-Demand ones in only one aspect - they can be interrupted.
When EC2 needs the capacity back, it will emit a notification two minutes before interruption.
The interruption might mean terminating, stopping or hibernating the instance, depending on what was specified in the Spot request.

AWS Spot Instances provide opportunity to run massively scalable workloads, but impact of interruptions still needs to be taken into account. Certain best practices needs to be followed while architecting applications meant to be run on Spot Instances. 

This project aims to explore possibilities that Spot Instances offer by running some example workloads with automatized handling of interruptions.

### Workload

Type of workload we chose for this project is rendering using Blender. Rendering is generally computationally heavy operation, done frame-by-frame. Blender CLI allows to render specific frames or range of frames. There are a lot of Blender demo scenes we can use for our examples.

Rendering workloads are naturally fault-tolerant and seem to be good match for our Spot Instances showcase. We could reduce impact of interruptions by, for example, regularly uploading rendered frames to some S3 bucket and having one instance dedicated to distributing rendering tasks to other instances.

### Proposed scope of the project

- implement solution for distributed rendering using Blender
- interruptions will be detected and actions will be taken to achieve maximum effectiveness - including making a research about existing spot instances management solutions and possibly using them
- solution will be run for a few example workloads with different parameters (like instance count or different methods of detecting interruption)
- gather statistics like time needed or interruption count (including comparison based on size of the machines)
- compare costs of Spot vs On-Demand instances

## Sources

- [Best practices for handling EC2 Spot Instance interruptions - AWS blog post](https://aws.amazon.com/blogs/compute/best-practices-for-handling-ec2-spot-instance-interruptions/)
- [Blender CLI docs](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- [Library of Blender demo scenes](https://www.blender.org/download/demo-files/)