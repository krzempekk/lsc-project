import os
import argparse
import boto3
import requests

parser = argparse.ArgumentParser(
    description="Worker script for distributed rendering using Blender",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-q", "--queue-name", help="SQS queue from which tasks will be taken")
# parser.add_argument("frame_start", help="Number of first frame to render")
# parser.add_argument("frame_end", help="Number of last frame to render")
# parser.add_argument("-b", "--blend_file", help=".blend file name", required=True)
# parser.add_argument("-db", "--download_bucket", help="Name of S3 bucket from which .blend file will be downloaded")
# parser.add_argument("-ub", "--upload_bucket",
#                     help="Name of S3 bucket to which rendered frames will be uploaded. If omitted, no upload will happen")
args = parser.parse_args()

s3_client = boto3.client("s3")
sqs_client = boto3.client('sqs')

queue_name = args.queue_name


def is_instance_interrupted():
    r = requests.get('http://169.254.169.254/latest/meta-data/spot/instance-action')
    return r.status_code == 200


def process_task(task_args):
    frame_start = int(task_args['frame_start'])
    frame_end = int(task_args['frame_end'])
    upload_bucket_name = task_args['upload_bucket_name']
    download_bucket_name = task_args['download_bucket_name']
    blend_file = task_args['blend_file']

    if download_bucket_name is not None:
        if not os.path.exists("blend"):
            os.makedirs("blend")
        s3_client.download_file(download_bucket_name, blend_file, f"blend/{blend_file}")

    for frame_index in range(frame_start, frame_end + 1):
        os.system(f"blender -b ./blend/{blend_file} -o ./renders/frame_##### -f {frame_index}")
        if upload_bucket_name is not None:
            s3_client.upload_file(f"./renders/frame_{frame_index:05}.png", upload_bucket_name,
                                  f"frame_{frame_index:05}.png")
        if is_instance_interrupted():
            print("Instance interrupted, quitting...")
            return frame_index + 1, frame_end
    return None


def get_task_from_queue():
    response = sqs_client.receive_message(
        QueueUrl=queue_name,
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
        QueueUrl=queue_name,
        ReceiptHandle=receipt_handle
    )

    message_attributes = message.get('MessageAttributes')

    message_args = {
        'frame_start': int(message_attributes.get('frame_start').get('StringValue')),
        'frame_end': int(message_attributes.get('frame_end').get('StringValue')),
        'upload_bucket_name': message_attributes.get('upload_bucket_name').get('StringValue'),
        'download_bucket_name': message_attributes.get('download_bucket_name').get('StringValue'),
        'blend_file': message_attributes.get('blend_file').get('StringValue')
    }

    return message_args


while True:
    task = get_task_from_queue()
    print(f"received task: {task}")
    if task is not None:
        process_task(task)
