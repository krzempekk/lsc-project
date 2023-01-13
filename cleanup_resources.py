import boto3
import json

sqs_client = boto3.client('sqs')
s3_client = boto3.client('s3')
ec2_client = boto3.client('ec2')
autoscaling_client = boto3.client('autoscaling')

with open("./cleanup_resources_info.json", "r") as cleanup_resources_file:
    cleanup_resources_info = json.load(cleanup_resources_file)

print("Deleting sqs queue...")
response = sqs_client.delete_queue(QueueUrl=cleanup_resources_info['sqs_url'])
print(response)

print("Deleting input S3 bucket...")
response = s3_client.delete_bucket(Bucket=cleanup_resources_info['input_bucket'])
print(response)

print("Deleting output S3 bucket...")
response = s3_client.create_bucket(Bucket=cleanup_resources_info['output_bucket'])
print(response)

print("Deleting auto scaling group...")
response = autoscaling_client.delete_auto_scaling_group(
    AutoScalingGroupName=cleanup_resources_info['autoscaling_group_name'],
    #ForceDelete=True,
)
print(response)

print("Deleting launch template...")
response = ec2_client.delete_launch_tenplate(
    LaunchTemplateName=cleanup_resources_info['launch_template_name']
)
print(response)

print("Resources cleanup finished")
