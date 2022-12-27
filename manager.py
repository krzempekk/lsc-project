import os
import argparse
import boto3
import requests

parser = argparse.ArgumentParser(
    description="Manager script for distributed rendering using Blender",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("frame_start", help="Number of first frame to render")
parser.add_argument("frame_end", help="Number of last frame to render")
parser.add_argument("-b", "--blend_file", help=".blend file name", required=True)
parser.add_argument("-s", "--task-size", help="Number of frames per one task sent to worker instance", default=10)
parser.add_argument("-db", "--download_bucket", help="Name of S3 bucket from which .blend file will be downloaded")
parser.add_argument("-ub", "--upload_bucket",
                    help="Name of S3 bucket to which rendered frames will be uploaded. If omitted, no upload will happen")
args = parser.parse_args()

# autoscaling_client = boto3.client('autoscaling')
#
# autoscaling_group_instances = autoscaling_client\
#     .describe_auto_scaling_groups(AutoScalingGroupNames=['lsc-auto-scaling-01'])\
#     .get('AutoScalingGroups')[0]\
#     .get('Instances')
#
# autoscaling_group_instance_ids = list(map(lambda metadata: metadata['InstanceId'], autoscaling_group_instances))
#
# print(autoscaling_group_instances)
# print(autoscaling_group_instance_ids)

sqs_client = boto3.client('sqs')

response = sqs_client.send_message(
    QueueUrl='lsc-queue-1',
    MessageAttributes={
        'frame_start': {
            'DataType': 'Number',
            'StringValue': '1'
        },
        'frame_end': {
            'DataType': 'Number',
            'StringValue': '3'
        },
        'upload_bucket_name': {
            'DataType': 'String',
            'StringValue': 'lsc-project-01'
        },
        'download_bucket_name': {
            'DataType': 'String',
            'StringValue': 'lsc-project-01'
        },
        'blend_file': {
            'DataType': 'String',
            'StringValue': 'halloween_spider.blend'
        }
    },
    MessageBody="rendering task"
)

print(response['MessageId'])

