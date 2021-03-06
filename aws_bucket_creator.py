import argparse
import boto3
from botocore.exceptions import ClientError
import sys


# The prefix that the profile user is allowed to create users in
USER_PATH = '/s3wizard/'


parser = argparse.ArgumentParser(
    description="Create an AWS bucket and the user going with it, \
    and/or associate a user to a bucket")

parser.add_argument('-e', '--existing-bucket', action='store_true',
                    help='Do not exit if bucket already exists')
parser.add_argument('-E', '--existing-user', action='store_true',
                    help='Do not exit if user already exists')
parser.add_argument('-a', '--regenerate-api-access', action='store_true',
                    help='Regenerate API access for user')


parser.add_argument('-b', '--bucket', type=str, nargs=1,
                    required=True,
                    help='The bucket name')

parser.add_argument('-u', '--user', type=str, nargs=1,
                    required=True,
                    help='The user name')

parser.add_argument('-p', '--profile', type=str, nargs=1,
                    required=True,
                    help='AWS command line profile name')

parser.add_argument('-r', '--region', type=str, nargs=1,
                    required=True,
                    help='The region for the bucket')

parser.add_argument('-P', '--policy', type=str, nargs='*',
                    required=True,
                    help='A policy to attach to the user')

args = parser.parse_args()
profile = args.profile[0]
bucket_name = args.bucket[0]
user_name = args.user[0]
region = args.region[0]
policies = args.policy
must_create_bucket = not args.existing_bucket
must_create_user = not args.existing_user
regenerate_api_access = args.regenerate_api_access

print('Testing connectivity of profile {} by\
 checking if the bucket exists'.format(profile))

session = boto3.Session(profile_name=profile)

s3 = session.resource('s3')
iam = session.resource('iam')
s3_client = session.client('s3')
iam_client = session.client('iam')

# Check if the bucket already exists

try:
    error = True
    out = s3_client.head_bucket(Bucket=bucket_name)
except ClientError:
    error = False

if error is True:
    print(' Bucket {} already exists'.format(bucket_name))
    if must_create_bucket:
        sys.exit(1)

print('Creating the bucket {}'.format(bucket_name))
bucket = s3.Bucket(bucket_name)
try:
    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
            'LocationConstraint': region})
except ClientError as e:
    if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
        print(' Bucket already exists, it should (may) \
 have been spotted earlier')
        if must_create_bucket:
            sys.exit(1)
    else:
        print(' Unknown error {}'.format(e.response))
        sys.exit(100)

print('Creating user {}{}'.format(USER_PATH, user_name))
try:
    user_exists = True
    iam_client.get_user(
        UserName=user_name
    )
except ClientError as e:
    user_exists = False
    if e.response['Error']['Code'] == 'NoSuchEntity':
        pass
    else:
        print(' Unknown error {}'.format(e.response))
        sys.exit(100)


if user_exists is True:
    print(' User {} already exists.'.format(user_name))
    if must_create_user is True:
        sys.exit(2)
user = iam.User(user_name)

try:
    user.create(Path=USER_PATH)
except ClientError as e:
    if e.response['Error']['Code'] == 'EntityAlreadyExists':
        print(' User already exists, it should (may) \
 have been spotted earlier')
        if must_create_user:
            sys.exit(2)
    else:
        print(' Unknown error: {}'.format(e.response))
print('Waiting for bucket to be created')
bucket.wait_until_exists()
print('Waiting for user to be created')
user_waiter = iam_client.get_waiter('user_exists')
user_waiter.wait(UserName=user_name)

print('Attaching policies to user {}'.format(user_name))
for policy_name in policies:
    print(' {}'.format(policy_name))
    policy = iam.Policy(policy_name)
    try:
        policy.attach_user(UserName=user_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidInputException':
            print(' Invalid policy ARN: {}'.format(policy_name))

# We regenerate API codes only if asked or the user is new
# We arrived here with must_create_user is True only if the user didn't exist

if (must_create_user is True) or ((must_create_user is False) and (regenerate_api_access is True)):
    print('Managing API access for user')
    for access_key in user.access_keys.all():
        try:
            access_key.delete()
        except ClientError as e:
            print(' Unknown error: {}'.format(e.response))
    print('Generating API access {}'.format(user_name))
    key_pair = user.create_access_key_pair()
    print('[{}]\naws_access_key_id = {}\naws_secret_access_key = {}'.format(key_pair.user_name,
                                                  key_pair.id,
                                                  key_pair.secret))

