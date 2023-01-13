import os
import argparse
import boto3
import requests
import time

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
parser.add_argument("-tq", "--task-queue-name", help="SQS queue from to which rendering tasks will be sent",
                    required=True)
parser.add_argument("-nq", "--notification-queue-name",
                    help="SQS queue from which notifications about task completion will be received", required=True)
args = parser.parse_args()

frame_start = int(args.frame_start)
frame_end = int(args.frame_end)
blend_file = args.blend_file
task_count = int(args.task_count)
download_bucket = args.download_bucket
upload_bucket = args.upload_bucket
task_queue_name = args.task_queue_name
notification_queue_name = args.notification_queue_name

sqs_client = boto3.client('sqs')


def send_single_task(task_frame_start, task_frame_end, upload_bucket, download_bucket, blend_file):
    response = sqs_client.send_message(
        QueueUrl=task_queue_name,
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


def get_confirmation_from_queue():
    response = sqs_client.receive_message(
        QueueUrl=notification_queue_name,
        AttributeNames=['All'],
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        VisibilityTimeout=10,
        WaitTimeSeconds=10
    )

    if response.get('Messages') is None:
        return None

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']

    sqs_client.delete_message(
        QueueUrl=notification_queue_name,
        ReceiptHandle=receipt_handle
    )

    message_attributes = message.get('MessageAttributes')

    message_args = {
        'rendered_frame_start': int(message_attributes.get('rendered_frame_start').get('StringValue')),
        'rendered_frame_end': int(message_attributes.get('rendered_frame_end').get('StringValue')),
        'is_interrupted': int(message_attributes.get('is_interrupted').get('StringValue')),
    }

    return message_args


tasks = []
interruption_count = 0
time_start = time.time()

for i in range(task_count):
    frame_count = frame_end - frame_start + 1
    task_frame_start = frame_start + i * frame_count // task_count
    task_frame_end = frame_start + (i + 1) * frame_count // task_count - 1 if i < task_count - 1 else frame_end
    send_single_task(task_frame_start, task_frame_end, upload_bucket, download_bucket, blend_file)
    tasks.append((task_frame_start, task_frame_end))

print(f"Added tasks: {tasks}")

while len(tasks) != 0:
    print(f"{len(tasks)} tasks remaining...")
    confirmation = get_confirmation_from_queue()
    if confirmation is not None:
        interruption_count += confirmation['is_interrupted']
        rendered_frame_start = confirmation['rendered_frame_start']
        rendered_frame_end = confirmation['rendered_frame_end']

        original_task = list(filter(lambda x: x[0] == rendered_frame_start, tasks))[0]
        tasks.remove(original_task)
        if original_task[1] != rendered_frame_end:
            print(f"Task {original_task} completed partially. Re-adding unfinished part - ({rendered_frame_end}, {original_task[1]})")
            send_single_task(rendered_frame_end + 1, original_task[1], upload_bucket, download_bucket, blend_file)
            tasks.append((rendered_frame_end + 1, original_task[1]))
        else:
            print(f"Task {original_task} fully completed!")

time_elapsed = time.time() - time_start
print(f"All task completed! Elapsed time: {time_elapsed}")
