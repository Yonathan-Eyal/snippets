import boto3

def get_instance_name(instance):
    for tag in instance['Tags']:
        if tag['Key'] == 'Name':
            return tag['Value']
    return ''

def get_launch_template_name(template):
    for tag in template['Tags']:
        if tag['Key'] == 'Name':
            return tag['Value']
    return ''

def get_auto_scaling_group_name(group):
    for tag in group['Tags']:
        if tag['Key'] == 'Name':
            return tag['Value']
    return ''

def check_ami_usage(ami_id):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_instances(Filters=[{'Name': 'image-id', 'Values': [ami_id]}])
    ami_used = False

    if response['Reservations']:
        ami_used = True
        print(f"The AMI {ami_id} is used by the following EC2 instances:")
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_name = get_instance_name(instance)
                print(f"Instance ID: {instance_id}, Name: {instance_name}")

    response = ec2_client.describe_launch_templates()
    if 'LaunchTemplates' in response:
        launch_templates = response['LaunchTemplates']
        filtered_templates = []
        for template in launch_templates:
            if 'LaunchTemplateData' in template:
                if 'BlockDeviceMappings' in template['LaunchTemplateData']:
                    for mapping in template['LaunchTemplateData']['BlockDeviceMappings']:
                        if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                            if mapping['Ebs']['SnapshotId'] == ami_id:
                                ami_used = True
                                filtered_templates.append(template)
                                break

        if filtered_templates:
            print(f"The AMI {ami_id} is used by the following Launch Templates:")
            for template in filtered_templates:
                template_id = template['LaunchTemplateId']
                template_name = get_launch_template_name(template)
                print(f"Launch Template ID: {template_id}, Name: {template_name}")
        else:
            print(f"The AMI {ami_id} is not used by any Launch Templates.")

    autoscaling_client = boto3.client('autoscaling')
    response = autoscaling_client.describe_auto_scaling_groups()
    if 'AutoScalingGroups' in response:
        autoscaling_groups = response['AutoScalingGroups']
        filtered_groups = []
        for group in autoscaling_groups:
            mixed_instances_policy = group.get('MixedInstancesPolicy')
            if mixed_instances_policy:
                launch_template = mixed_instances_policy.get('LaunchTemplate')
                if launch_template and launch_template.get('LaunchTemplateId') == ami_id:
                    ami_used = True
                    filtered_groups.append(group)

        if filtered_groups:
            print(f"The AMI {ami_id} is used by the following Auto Scaling Groups:")
            for group in filtered_groups:
                group_name = group['AutoScalingGroupName']
                group_name = get_auto_scaling_group_name(group)
                print(f"Auto Scaling Group Name: {group_name}, Name: {group_name}")
        else:
            print(f"The AMI {ami_id} is not used by any Auto Scaling Groups.")

    if not ami_used:
        print(f"The AMI {ami_id} is not used by any EC2 instances, Launch Templates, or Auto Scaling Groups.")
        return False

def check_all_amis_usage():
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_images(Owners=['self'])

    unused_amis = []

    if response['Images']:
        print("Checking AMI usage...")
        for image in response['Images']:
            ami_id = image['ImageId']
            print(f"Checking AMI ID: {ami_id}")
            if not check_ami_usage(ami_id):
                unused_amis.append(ami_id)
            print("")
    else:
        print("No images found.")


    print("Summary of unused AMIs:")
    if unused_amis:
       for ami_id in unused_amis:
           print(f"AMI ID: {ami_id} is not used by any EC2 instances, Launch Templates, or Auto Scaling Groups.")
    else:
        print("All AMIs are currently in use.")


check_all_amis_usage()
