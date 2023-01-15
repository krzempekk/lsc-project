import boto3
import json
import base64

from botocore.exceptions import ClientError

AUTOSCALING_GROUP = 'autoscaling_group'
INPUT_BUCKET = "lsc-input-bucket"
OUTPUT_BUCKET = "lsc-output-bucket"
LAUNCH_TEMPLATE = 'worker_template_1'
SUBNET_ID = 'subnet-03e534aca29c1c6f1'

MIN_INSTANCES = 4
MAX_INSTANCES = 4

sqs = boto3.resource('sqs')
ec2_client = boto3.client('ec2')
sqs_client = boto3.client('sqs')
s3_client = boto3.client('s3')
autoscaling_client = boto3.client('autoscaling')
session = boto3.Session()

cleanup_resources_info = {}

# Create base64-encoded script based on the base script file and current credentials
credentials = session.get_credentials().get_frozen_credentials()
instance_script_file = open("./instance_script", "r")
instance_script = instance_script_file.read().format(
    access_key_id=credentials.access_key,
    secret_access_key=credentials.secret_key,
    session_token=credentials.token
)
instance_script_file.close()
instance_script64 = base64.b64encode(instance_script.encode('ascii')).decode('ascii')

# Create resources
print("Creating a launch template...")
try:
    response = ec2_client.create_launch_template(
        LaunchTemplateName=LAUNCH_TEMPLATE,
        LaunchTemplateData={
            'ImageId': 'ami-06878d265978313ca',
            'InstanceType': 't2.medium',
            'KeyName': 'vockey',
            'UserData': instance_script64,
        }
    )
    print(response)
except ClientError as e:
    if e.response['Error']['Code'] == 'EntityAlreadyExists':
        print("Launch template already exists")
    else:
        print(f"Unexpected error: %s {e}")
cleanup_resources_info['launch_template_name'] = LAUNCH_TEMPLATE

print("Creating an autoscaling group...")
response = autoscaling_client.create_auto_scaling_group(
    AutoScalingGroupName=AUTOSCALING_GROUP,
    MixedInstancesPolicy={
        'LaunchTemplate': {
            'LaunchTemplateSpecification': {
                'LaunchTemplateName': LAUNCH_TEMPLATE,
                'Version': '$Latest'
            },
        },
        'InstancesDistribution': {
            'OnDemandPercentageAboveBaseCapacity': 0,
            'SpotAllocationStrategy': 'price-capacity-optimized',
        }
    },
    MinSize=MIN_INSTANCES,
    MaxSize=MAX_INSTANCES,
    VPCZoneIdentifier=SUBNET_ID
)
print(response)
cleanup_resources_info['autoscaling_group_name'] = AUTOSCALING_GROUP

print("Creating task SQS queue...")
queue = sqs.create_queue(QueueName='lsc-queue-1')
print(queue)
cleanup_resources_info['sqs_url'] = queue.url

print("Creating notification SQS queue...")
queue = sqs.create_queue(QueueName='lsc-queue-2')
print(queue)
cleanup_resources_info['sqs_notif_queue_url'] = queue.url

print("Creating input S3 bucket...")
response = s3_client.create_bucket(Bucket=INPUT_BUCKET)
print(response)
cleanup_resources_info['input_bucket'] = INPUT_BUCKET

print("Creating output S3 bucket...")
response = s3_client.create_bucket(Bucket=OUTPUT_BUCKET)
print(response)
cleanup_resources_info['output_bucket'] = OUTPUT_BUCKET

# Save resources info to a json file
with open("./cleanup_resources_info.json", "w+") as cleanup_resources_file:
    cleanup_resources_file.write(json.dumps(cleanup_resources_info))
