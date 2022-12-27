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
parser.add_argument("-c", "--task_count", help="Number of tasks to which frame range should be split", default=10)
parser.add_argument("-db", "--download_bucket", help="Name of S3 bucket from which .blend file will be downloaded")
parser.add_argument("-ub", "--upload_bucket",
                    help="Name of S3 bucket to which rendered frames will be uploaded. If omitted, no upload will happen")
args = parser.parse_args()

frame_start = int(args.frame_start)
frame_end = int(args.frame_end)
blend_file = args.blend_file
task_count = int(args.task_count)
download_bucket = args.download_bucket
upload_bucket = args.upload_bucket

sqs_client = boto3.client('sqs')

for i in range(task_count):
    frame_count = frame_end - frame_start + 1
    task_frame_start = frame_start + i * frame_count // task_count
    task_frame_end = frame_start + (i + 1) * frame_count // task_count - 1 if i < task_count - 1 else frame_end

    response = sqs_client.send_message(
        QueueUrl='lsc-queue-1',
        MessageAttributes={
            'frame_start': {
                'DataType': 'Number',
                'StringValue': f'{task_frame_start}'
            },
            'frame_end': {
                'DataType': 'Number',
                'StringValue': f'{task_frame_end}'
            },
            'upload_bucket_name': {
                'DataType': 'String',
                'StringValue': upload_bucket
            },
            'download_bucket_name': {
                'DataType': 'String',
                'StringValue': download_bucket
            },
            'blend_file': {
                'DataType': 'String',
                'StringValue': blend_file
            }
        },
        MessageBody="rendering task"
    )

    print(response['MessageId'])

