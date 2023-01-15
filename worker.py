import os
import argparse
import boto3
import requests
import subprocess
import signal

parser = argparse.ArgumentParser(
    description="Worker script for distributed rendering using Blender",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-tq", "--task-queue-name", help="SQS queue from which tasks will be taken", required=True)
parser.add_argument("-nq", "--notification-queue-name",
                    help="SQS queue to which notifications about task completion will be sent", required=True)
args = parser.parse_args()

s3_client = boto3.client("s3")
sqs_client = boto3.client('sqs')

task_queue_name = args.task_queue_name
notification_queue_name = args.notification_queue_name


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
        program = f"xvfb-run -a blender -b ./blend/{blend_file} -o ./renders/frame_##### -f {frame_index}"
        process = subprocess.Popen(program, shell=True, preexec_fn=os.setsid)

        terminated = None
        while terminated is None:
            try:
                terminated = process.wait(15)
            except:
                if is_instance_interrupted():
                    print("Instance interrupted, quitting...")
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    return frame_start, frame_index - 1, True

        if upload_bucket_name is not None:
            s3_client.upload_file(f"./renders/frame_{frame_index:05}.png", upload_bucket_name,
                                  f"frame_{frame_index:05}.png")

        if is_instance_interrupted():
            print("Instance interrupted, quitting...")
            return frame_start, frame_index, True
    return frame_start, frame_end, False


def get_task_from_queue():
    response = sqs_client.receive_message(
        QueueUrl=task_queue_name,
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
        QueueUrl=task_queue_name,
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


def send_task_confirmation(rendered_frame_start, rendered_frame_end, is_interrupted):
    response = sqs_client.send_message(
        QueueUrl=notification_queue_name,
        MessageAttributes={
            'rendered_frame_start': {
                'DataType': 'Number',
                'StringValue': f'{rendered_frame_start}'
            },
            'rendered_frame_end': {
                'DataType': 'Number',
                'StringValue': f'{rendered_frame_end}'
            },
            'is_interrupted': {
                'DataType': 'Number',
                'StringValue': f'{1 if is_interrupted else 0}'
            },
        },
        MessageBody="rendering task confirmation"
    )

    print(response['MessageId'])


print("Starting worker")
while True:
    task = get_task_from_queue()
    print(f"received task: {task}")
    if task is not None:
        task_info = process_task(task)
        send_task_confirmation(*task_info)
