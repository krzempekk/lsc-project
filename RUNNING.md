# How to run?

1. Set proper values for `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` variables in `instance_script`.
2a. Use init_resources.py script to create required AWS resources
OR
2b. Create following AWS resources manually:
   - One or two S3 buckets 
     - one for input `.blend` files (input bucket) 
     - second for output frames in `.png` format (output bucket) 
     - input and output bucket can be the same bucket
   - One SQS queue
     - Name should be `lsc-queue-1`
   - One EC2 launch template
     - AMI `Ubuntu`
     - Instance type `t2.medium`
     - Key pair `vockey`
     - Paste `instance_script` contents as User Data
   - One EC2 Auto Scaling Group with Spot instances, which uses created EC2 launch template
3. Run `manager.py` script (can be locally, but AWS credentials need to be present in `.aws/credentials` file) with proper parameters
   - `.blend` input file name
   - range of frames to render (start and end frame)
   - number of tasks to which frames range will be split
   - download bucket from which `.blend` files will be downloaded by workers
   - upload bucket to which `.png` frames will be sent by workers