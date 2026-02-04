#!/usr/bin/env python3
"""
AWS Account Reset Script
========================
Deletes all user-created resources in an AWS account while preserving:
- AWS-managed policies and roles
- Root account
- Specified IAM users (e.g., ola-admin)

⚠️  WARNING: This script is DESTRUCTIVE. Review carefully before running!

Usage:
    python reset_aws_account.py --dry-run      # Preview what would be deleted
    python reset_aws_account.py --execute      # Actually delete resources
"""

import boto3
import argparse
import sys
import time
from botocore.exceptions import ClientError, EndpointConnectionError
from concurrent.futures import ThreadPoolExecutor, as_completed

# IAM users to preserve (add more as needed)
PRESERVE_IAM_USERS = {"ola-admin"}

# Regions to clean (add/remove as needed)
REGIONS_TO_CLEAN = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
]

class AWSAccountReset:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.session = boto3.Session()
        self.deleted_resources = []
        self.errors = []
        
    def log(self, message, level="INFO"):
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"{prefix}[{level}] {message}")
        
    def log_delete(self, resource_type, resource_id, region="global"):
        action = "Would delete" if self.dry_run else "Deleting"
        self.log(f"{action}: {resource_type} - {resource_id} ({region})")
        self.deleted_resources.append((resource_type, resource_id, region))
        
    def handle_error(self, resource_type, resource_id, error):
        self.log(f"Error with {resource_type} {resource_id}: {error}", "ERROR")
        self.errors.append((resource_type, resource_id, str(error)))

    # =========================================================================
    # S3 Cleanup
    # =========================================================================
    def delete_s3_buckets(self):
        """Delete all S3 buckets and their contents"""
        self.log("=== Cleaning S3 Buckets ===")
        s3 = self.session.client("s3")
        s3_resource = self.session.resource("s3")
        
        try:
            buckets = s3.list_buckets().get("Buckets", [])
        except ClientError as e:
            self.handle_error("S3", "list_buckets", e)
            return
            
        for bucket in buckets:
            bucket_name = bucket["Name"]
            try:
                self.log_delete("S3 Bucket", bucket_name)
                if not self.dry_run:
                    # Delete all versions (for versioned buckets)
                    bucket_obj = s3_resource.Bucket(bucket_name)
                    bucket_obj.object_versions.delete()
                    bucket_obj.objects.delete()
                    s3.delete_bucket(Bucket=bucket_name)
            except ClientError as e:
                self.handle_error("S3 Bucket", bucket_name, e)

    # =========================================================================
    # DynamoDB Cleanup
    # =========================================================================
    def delete_dynamodb_tables(self, region):
        """Delete all DynamoDB tables in a region"""
        self.log(f"=== Cleaning DynamoDB Tables ({region}) ===")
        dynamodb = self.session.client("dynamodb", region_name=region)
        
        try:
            paginator = dynamodb.get_paginator("list_tables")
            for page in paginator.paginate():
                for table_name in page.get("TableNames", []):
                    try:
                        self.log_delete("DynamoDB Table", table_name, region)
                        if not self.dry_run:
                            dynamodb.delete_table(TableName=table_name)
                    except ClientError as e:
                        self.handle_error("DynamoDB Table", table_name, e)
        except ClientError as e:
            self.handle_error("DynamoDB", f"list_tables ({region})", e)

    # =========================================================================
    # Lambda Cleanup
    # =========================================================================
    def delete_lambda_functions(self, region):
        """Delete all Lambda functions in a region"""
        self.log(f"=== Cleaning Lambda Functions ({region}) ===")
        lambda_client = self.session.client("lambda", region_name=region)
        
        try:
            paginator = lambda_client.get_paginator("list_functions")
            for page in paginator.paginate():
                for func in page.get("Functions", []):
                    func_name = func["FunctionName"]
                    try:
                        self.log_delete("Lambda Function", func_name, region)
                        if not self.dry_run:
                            lambda_client.delete_function(FunctionName=func_name)
                    except ClientError as e:
                        self.handle_error("Lambda Function", func_name, e)
        except ClientError as e:
            self.handle_error("Lambda", f"list_functions ({region})", e)

    # =========================================================================
    # API Gateway Cleanup
    # =========================================================================
    def delete_api_gateways(self, region):
        """Delete all API Gateway REST APIs and HTTP APIs"""
        self.log(f"=== Cleaning API Gateway ({region}) ===")
        
        # REST APIs
        apigw = self.session.client("apigateway", region_name=region)
        try:
            apis = apigw.get_rest_apis().get("items", [])
            for api in apis:
                api_id = api["id"]
                api_name = api.get("name", api_id)
                try:
                    self.log_delete("API Gateway REST API", f"{api_name} ({api_id})", region)
                    if not self.dry_run:
                        apigw.delete_rest_api(restApiId=api_id)
                except ClientError as e:
                    self.handle_error("API Gateway REST API", api_id, e)
        except ClientError as e:
            self.handle_error("API Gateway", f"get_rest_apis ({region})", e)
            
        # HTTP APIs (API Gateway v2)
        apigwv2 = self.session.client("apigatewayv2", region_name=region)
        try:
            apis = apigwv2.get_apis().get("Items", [])
            for api in apis:
                api_id = api["ApiId"]
                api_name = api.get("Name", api_id)
                try:
                    self.log_delete("API Gateway HTTP API", f"{api_name} ({api_id})", region)
                    if not self.dry_run:
                        apigwv2.delete_api(ApiId=api_id)
                except ClientError as e:
                    self.handle_error("API Gateway HTTP API", api_id, e)
        except ClientError as e:
            self.handle_error("API Gateway v2", f"get_apis ({region})", e)

    # =========================================================================
    # SQS Cleanup
    # =========================================================================
    def delete_sqs_queues(self, region):
        """Delete all SQS queues in a region"""
        self.log(f"=== Cleaning SQS Queues ({region}) ===")
        sqs = self.session.client("sqs", region_name=region)
        
        try:
            queues = sqs.list_queues().get("QueueUrls", [])
            for queue_url in queues:
                try:
                    self.log_delete("SQS Queue", queue_url, region)
                    if not self.dry_run:
                        sqs.delete_queue(QueueUrl=queue_url)
                except ClientError as e:
                    self.handle_error("SQS Queue", queue_url, e)
        except ClientError as e:
            self.handle_error("SQS", f"list_queues ({region})", e)

    # =========================================================================
    # SNS Cleanup
    # =========================================================================
    def delete_sns_topics(self, region):
        """Delete all SNS topics in a region"""
        self.log(f"=== Cleaning SNS Topics ({region}) ===")
        sns = self.session.client("sns", region_name=region)
        
        try:
            paginator = sns.get_paginator("list_topics")
            for page in paginator.paginate():
                for topic in page.get("Topics", []):
                    topic_arn = topic["TopicArn"]
                    try:
                        self.log_delete("SNS Topic", topic_arn, region)
                        if not self.dry_run:
                            sns.delete_topic(TopicArn=topic_arn)
                    except ClientError as e:
                        self.handle_error("SNS Topic", topic_arn, e)
        except ClientError as e:
            self.handle_error("SNS", f"list_topics ({region})", e)

    # =========================================================================
    # EventBridge Cleanup
    # =========================================================================
    def delete_eventbridge_rules(self, region):
        """Delete all EventBridge rules in a region"""
        self.log(f"=== Cleaning EventBridge Rules ({region}) ===")
        events = self.session.client("events", region_name=region)
        
        try:
            # Get all event buses first
            buses = events.list_event_buses().get("EventBuses", [])
            for bus in buses:
                bus_name = bus["Name"]
                
                # List rules on this bus
                paginator = events.get_paginator("list_rules")
                for page in paginator.paginate(EventBusName=bus_name):
                    for rule in page.get("Rules", []):
                        rule_name = rule["Name"]
                        # Skip AWS managed rules
                        if rule.get("ManagedBy"):
                            continue
                        try:
                            # Remove targets first
                            targets = events.list_targets_by_rule(
                                Rule=rule_name, EventBusName=bus_name
                            ).get("Targets", [])
                            if targets and not self.dry_run:
                                target_ids = [t["Id"] for t in targets]
                                events.remove_targets(
                                    Rule=rule_name, 
                                    EventBusName=bus_name, 
                                    Ids=target_ids
                                )
                            
                            self.log_delete("EventBridge Rule", f"{rule_name} ({bus_name})", region)
                            if not self.dry_run:
                                events.delete_rule(Name=rule_name, EventBusName=bus_name)
                        except ClientError as e:
                            self.handle_error("EventBridge Rule", rule_name, e)
                            
                # Delete custom event buses (not default)
                if bus_name != "default" and not bus_name.startswith("aws."):
                    try:
                        self.log_delete("EventBridge Bus", bus_name, region)
                        if not self.dry_run:
                            events.delete_event_bus(Name=bus_name)
                    except ClientError as e:
                        self.handle_error("EventBridge Bus", bus_name, e)
                        
        except ClientError as e:
            self.handle_error("EventBridge", f"list_rules ({region})", e)

    # =========================================================================
    # CloudWatch Cleanup
    # =========================================================================
    def delete_cloudwatch_resources(self, region):
        """Delete CloudWatch alarms, dashboards, and log groups"""
        self.log(f"=== Cleaning CloudWatch ({region}) ===")
        cw = self.session.client("cloudwatch", region_name=region)
        logs = self.session.client("logs", region_name=region)
        
        # Alarms
        try:
            paginator = cw.get_paginator("describe_alarms")
            for page in paginator.paginate():
                for alarm in page.get("MetricAlarms", []):
                    alarm_name = alarm["AlarmName"]
                    try:
                        self.log_delete("CloudWatch Alarm", alarm_name, region)
                        if not self.dry_run:
                            cw.delete_alarms(AlarmNames=[alarm_name])
                    except ClientError as e:
                        self.handle_error("CloudWatch Alarm", alarm_name, e)
        except ClientError as e:
            self.handle_error("CloudWatch", f"describe_alarms ({region})", e)
            
        # Dashboards
        try:
            dashboards = cw.list_dashboards().get("DashboardEntries", [])
            for dashboard in dashboards:
                name = dashboard["DashboardName"]
                try:
                    self.log_delete("CloudWatch Dashboard", name, region)
                    if not self.dry_run:
                        cw.delete_dashboards(DashboardNames=[name])
                except ClientError as e:
                    self.handle_error("CloudWatch Dashboard", name, e)
        except ClientError as e:
            self.handle_error("CloudWatch", f"list_dashboards ({region})", e)
            
        # Log Groups
        try:
            paginator = logs.get_paginator("describe_log_groups")
            for page in paginator.paginate():
                for lg in page.get("logGroups", []):
                    lg_name = lg["logGroupName"]
                    try:
                        self.log_delete("CloudWatch Log Group", lg_name, region)
                        if not self.dry_run:
                            logs.delete_log_group(logGroupName=lg_name)
                    except ClientError as e:
                        self.handle_error("CloudWatch Log Group", lg_name, e)
        except ClientError as e:
            self.handle_error("CloudWatch Logs", f"describe_log_groups ({region})", e)

    # =========================================================================
    # Cognito Cleanup
    # =========================================================================
    def delete_cognito_resources(self, region):
        """Delete Cognito User Pools and Identity Pools"""
        self.log(f"=== Cleaning Cognito ({region}) ===")
        
        # User Pools
        cognito_idp = self.session.client("cognito-idp", region_name=region)
        try:
            paginator = cognito_idp.get_paginator("list_user_pools")
            for page in paginator.paginate(MaxResults=60):
                for pool in page.get("UserPools", []):
                    pool_id = pool["Id"]
                    pool_name = pool.get("Name", pool_id)
                    try:
                        # Delete domain first if exists
                        try:
                            pool_desc = cognito_idp.describe_user_pool(UserPoolId=pool_id)
                            domain = pool_desc.get("UserPool", {}).get("Domain")
                            if domain and not self.dry_run:
                                cognito_idp.delete_user_pool_domain(
                                    Domain=domain, UserPoolId=pool_id
                                )
                        except ClientError:
                            pass
                            
                        self.log_delete("Cognito User Pool", f"{pool_name} ({pool_id})", region)
                        if not self.dry_run:
                            cognito_idp.delete_user_pool(UserPoolId=pool_id)
                    except ClientError as e:
                        self.handle_error("Cognito User Pool", pool_id, e)
        except ClientError as e:
            self.handle_error("Cognito", f"list_user_pools ({region})", e)
            
        # Identity Pools
        cognito_identity = self.session.client("cognito-identity", region_name=region)
        try:
            pools = cognito_identity.list_identity_pools(MaxResults=60).get("IdentityPools", [])
            for pool in pools:
                pool_id = pool["IdentityPoolId"]
                pool_name = pool.get("IdentityPoolName", pool_id)
                try:
                    self.log_delete("Cognito Identity Pool", f"{pool_name} ({pool_id})", region)
                    if not self.dry_run:
                        cognito_identity.delete_identity_pool(IdentityPoolId=pool_id)
                except ClientError as e:
                    self.handle_error("Cognito Identity Pool", pool_id, e)
        except ClientError as e:
            self.handle_error("Cognito Identity", f"list_identity_pools ({region})", e)

    # =========================================================================
    # EC2 Cleanup
    # =========================================================================
    def delete_ec2_resources(self, region):
        """Delete EC2 instances, security groups, key pairs, etc."""
        self.log(f"=== Cleaning EC2 ({region}) ===")
        ec2 = self.session.client("ec2", region_name=region)
        
        # Terminate instances
        try:
            instances = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped", "pending"]}]
            )
            instance_ids = []
            for reservation in instances.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_ids.append(instance["InstanceId"])
                    
            if instance_ids:
                self.log_delete("EC2 Instances", str(instance_ids), region)
                if not self.dry_run:
                    ec2.terminate_instances(InstanceIds=instance_ids)
                    # Wait for termination
                    waiter = ec2.get_waiter("instance_terminated")
                    waiter.wait(InstanceIds=instance_ids)
        except ClientError as e:
            self.handle_error("EC2 Instances", "terminate", e)
            
        # Delete key pairs
        try:
            key_pairs = ec2.describe_key_pairs().get("KeyPairs", [])
            for kp in key_pairs:
                kp_name = kp["KeyName"]
                try:
                    self.log_delete("EC2 Key Pair", kp_name, region)
                    if not self.dry_run:
                        ec2.delete_key_pair(KeyName=kp_name)
                except ClientError as e:
                    self.handle_error("EC2 Key Pair", kp_name, e)
        except ClientError as e:
            self.handle_error("EC2", f"describe_key_pairs ({region})", e)
            
        # Delete custom security groups (not default)
        try:
            sgs = ec2.describe_security_groups().get("SecurityGroups", [])
            for sg in sgs:
                if sg["GroupName"] == "default":
                    continue
                sg_id = sg["GroupId"]
                try:
                    self.log_delete("EC2 Security Group", f"{sg['GroupName']} ({sg_id})", region)
                    if not self.dry_run:
                        ec2.delete_security_group(GroupId=sg_id)
                except ClientError as e:
                    self.handle_error("EC2 Security Group", sg_id, e)
        except ClientError as e:
            self.handle_error("EC2", f"describe_security_groups ({region})", e)
            
        # Delete EBS volumes (unattached)
        try:
            volumes = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            ).get("Volumes", [])
            for vol in volumes:
                vol_id = vol["VolumeId"]
                try:
                    self.log_delete("EBS Volume", vol_id, region)
                    if not self.dry_run:
                        ec2.delete_volume(VolumeId=vol_id)
                except ClientError as e:
                    self.handle_error("EBS Volume", vol_id, e)
        except ClientError as e:
            self.handle_error("EC2", f"describe_volumes ({region})", e)
            
        # Delete snapshots owned by this account
        try:
            account_id = self.session.client("sts").get_caller_identity()["Account"]
            snapshots = ec2.describe_snapshots(OwnerIds=[account_id]).get("Snapshots", [])
            for snap in snapshots:
                snap_id = snap["SnapshotId"]
                try:
                    self.log_delete("EBS Snapshot", snap_id, region)
                    if not self.dry_run:
                        ec2.delete_snapshot(SnapshotId=snap_id)
                except ClientError as e:
                    self.handle_error("EBS Snapshot", snap_id, e)
        except ClientError as e:
            self.handle_error("EC2", f"describe_snapshots ({region})", e)
            
        # Delete Elastic IPs
        try:
            eips = ec2.describe_addresses().get("Addresses", [])
            for eip in eips:
                alloc_id = eip.get("AllocationId")
                if alloc_id:
                    try:
                        self.log_delete("Elastic IP", eip.get("PublicIp", alloc_id), region)
                        if not self.dry_run:
                            ec2.release_address(AllocationId=alloc_id)
                    except ClientError as e:
                        self.handle_error("Elastic IP", alloc_id, e)
        except ClientError as e:
            self.handle_error("EC2", f"describe_addresses ({region})", e)

    # =========================================================================
    # IAM Cleanup (Global)
    # =========================================================================
    def delete_iam_resources(self):
        """Delete IAM users, roles, policies (preserving AWS-managed and specified users)"""
        self.log("=== Cleaning IAM Resources (Global) ===")
        iam = self.session.client("iam")
        
        # Delete custom policies
        try:
            paginator = iam.get_paginator("list_policies")
            for page in paginator.paginate(Scope="Local"):  # Only customer-managed
                for policy in page.get("Policies", []):
                    policy_arn = policy["Arn"]
                    policy_name = policy["PolicyName"]
                    try:
                        # Detach from all entities first
                        if not self.dry_run:
                            # Detach from users
                            users = iam.list_entities_for_policy(
                                PolicyArn=policy_arn, EntityFilter="User"
                            ).get("PolicyUsers", [])
                            for user in users:
                                iam.detach_user_policy(UserName=user["UserName"], PolicyArn=policy_arn)
                            # Detach from roles
                            roles = iam.list_entities_for_policy(
                                PolicyArn=policy_arn, EntityFilter="Role"
                            ).get("PolicyRoles", [])
                            for role in roles:
                                iam.detach_role_policy(RoleName=role["RoleName"], PolicyArn=policy_arn)
                            # Detach from groups
                            groups = iam.list_entities_for_policy(
                                PolicyArn=policy_arn, EntityFilter="Group"
                            ).get("PolicyGroups", [])
                            for group in groups:
                                iam.detach_group_policy(GroupName=group["GroupName"], PolicyArn=policy_arn)
                            # Delete all versions except default
                            versions = iam.list_policy_versions(PolicyArn=policy_arn).get("Versions", [])
                            for version in versions:
                                if not version["IsDefaultVersion"]:
                                    iam.delete_policy_version(PolicyArn=policy_arn, VersionId=version["VersionId"])
                                    
                        self.log_delete("IAM Policy", policy_name)
                        if not self.dry_run:
                            iam.delete_policy(PolicyArn=policy_arn)
                    except ClientError as e:
                        self.handle_error("IAM Policy", policy_name, e)
        except ClientError as e:
            self.handle_error("IAM", "list_policies", e)
            
        # Delete roles (except AWS service-linked and preserved)
        try:
            paginator = iam.get_paginator("list_roles")
            for page in paginator.paginate():
                for role in page.get("Roles", []):
                    role_name = role["RoleName"]
                    # Skip AWS service-linked roles and AWS reserved paths
                    if role["Path"].startswith("/aws-service-role/") or \
                       role["Path"].startswith("/service-role/") or \
                       role_name.startswith("AWSServiceRole"):
                        continue
                    try:
                        if not self.dry_run:
                            # Detach managed policies
                            attached = iam.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", [])
                            for policy in attached:
                                iam.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])
                            # Delete inline policies
                            inline = iam.list_role_policies(RoleName=role_name).get("PolicyNames", [])
                            for policy_name in inline:
                                iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                            # Remove from instance profiles
                            profiles = iam.list_instance_profiles_for_role(RoleName=role_name).get("InstanceProfiles", [])
                            for profile in profiles:
                                iam.remove_role_from_instance_profile(
                                    InstanceProfileName=profile["InstanceProfileName"],
                                    RoleName=role_name
                                )
                                
                        self.log_delete("IAM Role", role_name)
                        if not self.dry_run:
                            iam.delete_role(RoleName=role_name)
                    except ClientError as e:
                        self.handle_error("IAM Role", role_name, e)
        except ClientError as e:
            self.handle_error("IAM", "list_roles", e)
            
        # Delete instance profiles
        try:
            paginator = iam.get_paginator("list_instance_profiles")
            for page in paginator.paginate():
                for profile in page.get("InstanceProfiles", []):
                    profile_name = profile["InstanceProfileName"]
                    try:
                        self.log_delete("IAM Instance Profile", profile_name)
                        if not self.dry_run:
                            # Remove roles first
                            for role in profile.get("Roles", []):
                                try:
                                    iam.remove_role_from_instance_profile(
                                        InstanceProfileName=profile_name,
                                        RoleName=role["RoleName"]
                                    )
                                except ClientError:
                                    pass
                            iam.delete_instance_profile(InstanceProfileName=profile_name)
                    except ClientError as e:
                        self.handle_error("IAM Instance Profile", profile_name, e)
        except ClientError as e:
            self.handle_error("IAM", "list_instance_profiles", e)
            
        # Delete users (except preserved)
        try:
            paginator = iam.get_paginator("list_users")
            for page in paginator.paginate():
                for user in page.get("Users", []):
                    user_name = user["UserName"]
                    if user_name in PRESERVE_IAM_USERS:
                        self.log(f"Preserving IAM User: {user_name}")
                        continue
                    try:
                        if not self.dry_run:
                            # Delete access keys
                            keys = iam.list_access_keys(UserName=user_name).get("AccessKeyMetadata", [])
                            for key in keys:
                                iam.delete_access_key(UserName=user_name, AccessKeyId=key["AccessKeyId"])
                            # Delete MFA devices
                            mfas = iam.list_mfa_devices(UserName=user_name).get("MFADevices", [])
                            for mfa in mfas:
                                iam.deactivate_mfa_device(UserName=user_name, SerialNumber=mfa["SerialNumber"])
                                iam.delete_virtual_mfa_device(SerialNumber=mfa["SerialNumber"])
                            # Remove from groups
                            groups = iam.list_groups_for_user(UserName=user_name).get("Groups", [])
                            for group in groups:
                                iam.remove_user_from_group(GroupName=group["GroupName"], UserName=user_name)
                            # Detach policies
                            attached = iam.list_attached_user_policies(UserName=user_name).get("AttachedPolicies", [])
                            for policy in attached:
                                iam.detach_user_policy(UserName=user_name, PolicyArn=policy["PolicyArn"])
                            # Delete inline policies
                            inline = iam.list_user_policies(UserName=user_name).get("PolicyNames", [])
                            for policy_name in inline:
                                iam.delete_user_policy(UserName=user_name, PolicyName=policy_name)
                            # Delete login profile
                            try:
                                iam.delete_login_profile(UserName=user_name)
                            except ClientError:
                                pass
                            # Delete signing certificates
                            certs = iam.list_signing_certificates(UserName=user_name).get("Certificates", [])
                            for cert in certs:
                                iam.delete_signing_certificate(UserName=user_name, CertificateId=cert["CertificateId"])
                            # Delete SSH public keys
                            ssh_keys = iam.list_ssh_public_keys(UserName=user_name).get("SSHPublicKeys", [])
                            for ssh_key in ssh_keys:
                                iam.delete_ssh_public_key(UserName=user_name, SSHPublicKeyId=ssh_key["SSHPublicKeyId"])
                                
                        self.log_delete("IAM User", user_name)
                        if not self.dry_run:
                            iam.delete_user(UserName=user_name)
                    except ClientError as e:
                        self.handle_error("IAM User", user_name, e)
        except ClientError as e:
            self.handle_error("IAM", "list_users", e)
            
        # Delete groups
        try:
            paginator = iam.get_paginator("list_groups")
            for page in paginator.paginate():
                for group in page.get("Groups", []):
                    group_name = group["GroupName"]
                    try:
                        if not self.dry_run:
                            # Detach policies
                            attached = iam.list_attached_group_policies(GroupName=group_name).get("AttachedPolicies", [])
                            for policy in attached:
                                iam.detach_group_policy(GroupName=group_name, PolicyArn=policy["PolicyArn"])
                            # Delete inline policies
                            inline = iam.list_group_policies(GroupName=group_name).get("PolicyNames", [])
                            for policy_name in inline:
                                iam.delete_group_policy(GroupName=group_name, PolicyName=policy_name)
                                
                        self.log_delete("IAM Group", group_name)
                        if not self.dry_run:
                            iam.delete_group(GroupName=group_name)
                    except ClientError as e:
                        self.handle_error("IAM Group", group_name, e)
        except ClientError as e:
            self.handle_error("IAM", "list_groups", e)

    # =========================================================================
    # CloudFormation Cleanup
    # =========================================================================
    def delete_cloudformation_stacks(self, region):
        """Delete all CloudFormation stacks"""
        self.log(f"=== Cleaning CloudFormation Stacks ({region}) ===")
        cfn = self.session.client("cloudformation", region_name=region)
        
        try:
            paginator = cfn.get_paginator("list_stacks")
            for page in paginator.paginate(StackStatusFilter=[
                "CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE",
                "UPDATE_ROLLBACK_COMPLETE", "IMPORT_COMPLETE", "IMPORT_ROLLBACK_COMPLETE"
            ]):
                for stack in page.get("StackSummaries", []):
                    stack_name = stack["StackName"]
                    # Skip nested stacks (they'll be deleted with parent)
                    if stack.get("ParentId"):
                        continue
                    try:
                        self.log_delete("CloudFormation Stack", stack_name, region)
                        if not self.dry_run:
                            cfn.delete_stack(StackName=stack_name)
                    except ClientError as e:
                        self.handle_error("CloudFormation Stack", stack_name, e)
        except ClientError as e:
            self.handle_error("CloudFormation", f"list_stacks ({region})", e)

    # =========================================================================
    # Secrets Manager Cleanup
    # =========================================================================
    def delete_secrets(self, region):
        """Delete all Secrets Manager secrets"""
        self.log(f"=== Cleaning Secrets Manager ({region}) ===")
        sm = self.session.client("secretsmanager", region_name=region)
        
        try:
            paginator = sm.get_paginator("list_secrets")
            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    secret_name = secret["Name"]
                    # Skip AWS-managed secrets
                    if secret.get("OwningService"):
                        continue
                    try:
                        self.log_delete("Secret", secret_name, region)
                        if not self.dry_run:
                            sm.delete_secret(
                                SecretId=secret_name,
                                ForceDeleteWithoutRecovery=True
                            )
                    except ClientError as e:
                        self.handle_error("Secret", secret_name, e)
        except ClientError as e:
            self.handle_error("Secrets Manager", f"list_secrets ({region})", e)

    # =========================================================================
    # Step Functions Cleanup
    # =========================================================================
    def delete_step_functions(self, region):
        """Delete all Step Functions state machines"""
        self.log(f"=== Cleaning Step Functions ({region}) ===")
        sfn = self.session.client("stepfunctions", region_name=region)
        
        try:
            paginator = sfn.get_paginator("list_state_machines")
            for page in paginator.paginate():
                for sm in page.get("stateMachines", []):
                    sm_arn = sm["stateMachineArn"]
                    sm_name = sm["name"]
                    try:
                        self.log_delete("Step Function", sm_name, region)
                        if not self.dry_run:
                            sfn.delete_state_machine(stateMachineArn=sm_arn)
                    except ClientError as e:
                        self.handle_error("Step Function", sm_name, e)
        except ClientError as e:
            self.handle_error("Step Functions", f"list_state_machines ({region})", e)

    # =========================================================================
    # KMS Cleanup
    # =========================================================================
    def schedule_kms_key_deletion(self, region):
        """Schedule deletion of customer-managed KMS keys"""
        self.log(f"=== Scheduling KMS Key Deletion ({region}) ===")
        kms = self.session.client("kms", region_name=region)
        
        try:
            paginator = kms.get_paginator("list_keys")
            for page in paginator.paginate():
                for key in page.get("Keys", []):
                    key_id = key["KeyId"]
                    try:
                        # Check if customer managed
                        key_info = kms.describe_key(KeyId=key_id)["KeyMetadata"]
                        if key_info["KeyManager"] != "CUSTOMER":
                            continue
                        if key_info["KeyState"] in ["PendingDeletion", "Disabled"]:
                            continue
                            
                        self.log_delete("KMS Key (scheduled)", key_id, region)
                        if not self.dry_run:
                            kms.schedule_key_deletion(KeyId=key_id, PendingWindowInDays=7)
                    except ClientError as e:
                        self.handle_error("KMS Key", key_id, e)
        except ClientError as e:
            self.handle_error("KMS", f"list_keys ({region})", e)

    # =========================================================================
    # ECR Cleanup
    # =========================================================================
    def delete_ecr_repositories(self, region):
        """Delete all ECR repositories and images"""
        self.log(f"=== Cleaning ECR Repositories ({region}) ===")
        ecr = self.session.client("ecr", region_name=region)
        
        try:
            paginator = ecr.get_paginator("describe_repositories")
            for page in paginator.paginate():
                for repo in page.get("repositories", []):
                    repo_name = repo["repositoryName"]
                    try:
                        self.log_delete("ECR Repository", repo_name, region)
                        if not self.dry_run:
                            ecr.delete_repository(repositoryName=repo_name, force=True)
                    except ClientError as e:
                        self.handle_error("ECR Repository", repo_name, e)
        except ClientError as e:
            self.handle_error("ECR", f"describe_repositories ({region})", e)

    # =========================================================================
    # Main Cleanup Orchestration
    # =========================================================================
    def cleanup_region(self, region):
        """Clean up all resources in a specific region"""
        self.log(f"\n{'='*60}")
        self.log(f"Processing Region: {region}")
        self.log(f"{'='*60}\n")
        
        # Order matters - delete dependent resources first
        self.delete_cloudformation_stacks(region)
        time.sleep(2)  # Wait for stack deletion to start
        
        self.delete_lambda_functions(region)
        self.delete_api_gateways(region)
        self.delete_step_functions(region)
        self.delete_sqs_queues(region)
        self.delete_sns_topics(region)
        self.delete_eventbridge_rules(region)
        self.delete_dynamodb_tables(region)
        self.delete_cognito_resources(region)
        self.delete_secrets(region)
        self.delete_ecr_repositories(region)
        self.delete_cloudwatch_resources(region)
        self.delete_ec2_resources(region)
        self.schedule_kms_key_deletion(region)
        
    def run(self):
        """Run the full account cleanup"""
        print("\n" + "="*60)
        print("AWS ACCOUNT RESET SCRIPT")
        print("="*60)
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No resources will be deleted")
        else:
            print("\n⚠️  EXECUTE MODE - Resources WILL be deleted!")
            print("\nYou have 10 seconds to cancel (Ctrl+C)...")
            time.sleep(10)
            
        # Get current identity
        sts = self.session.client("sts")
        identity = sts.get_caller_identity()
        print(f"\nAccount: {identity['Account']}")
        print(f"User: {identity['Arn']}")
        print(f"Preserving IAM users: {PRESERVE_IAM_USERS}")
        print(f"Regions to clean: {REGIONS_TO_CLEAN}")
        
        # Global resources first
        self.delete_s3_buckets()
        self.delete_iam_resources()
        
        # Regional resources
        for region in REGIONS_TO_CLEAN:
            try:
                self.cleanup_region(region)
            except EndpointConnectionError:
                self.log(f"Region {region} not available, skipping", "WARN")
            except Exception as e:
                self.handle_error("Region", region, e)
                
        # Summary
        print("\n" + "="*60)
        print("CLEANUP SUMMARY")
        print("="*60)
        print(f"\nResources {'to delete' if self.dry_run else 'deleted'}: {len(self.deleted_resources)}")
        print(f"Errors encountered: {len(self.errors)}")
        
        if self.errors:
            print("\nErrors:")
            for resource_type, resource_id, error in self.errors[:20]:
                print(f"  - {resource_type} {resource_id}: {error}")
            if len(self.errors) > 20:
                print(f"  ... and {len(self.errors) - 20} more errors")
                
        if self.dry_run:
            print("\n✅ Dry run complete. Run with --execute to actually delete resources.")
        else:
            print("\n✅ Cleanup complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Reset AWS account by deleting all user-created resources"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    group.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete resources (DESTRUCTIVE!)"
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        help="Specific regions to clean (default: common regions)"
    )
    
    args = parser.parse_args()
    
    if args.regions:
        global REGIONS_TO_CLEAN
        REGIONS_TO_CLEAN = args.regions
        
    resetter = AWSAccountReset(dry_run=args.dry_run)
    
    try:
        resetter.run()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
