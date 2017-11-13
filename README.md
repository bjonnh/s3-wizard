# aws-bucket-creator
A simple and dirty script to make buckets, users and give the right permissions.
It is meant for a really specific use case, so don't expect it to work for you.

TODO:
- Make API key generation optional
- Remove comments by default (add a debug mode)
- Add a basic example for the user policy

It requires boto3 to work.

# Example of use
(assumes that you made the credentials for the user my-s3-wizard and gave it the
right to make buckets, users and change permissions, look at
example_policy_for_wizard_user.json for an example) 
```shell 
$ aws_bucket_creator -b machines-backups -u precious-setup -p my-s3-wizard \
-r us-east-1 -e -E -a -P arn:aws:iam::1234567890:policy/UserAccessPolicy 
```

This will:
- create a *machines-backups* bucket (ignore if it doesn't exist) (in region *us-east-1*)
- create a user *precious-setup*  (ignore if it exists)
- give to the user the policy arn:aws:iam::1234567890:policy/UserAccessPolicy  (use example_policy_for_end_user.json for a complex example)
- generate new API keys for the user and remove the previous ones (so careful with that)

It returns the keys in a format suitable for the aws command line tool

# Policy for users: example_policy_for_end_user.json
 An example of a policy for your end users. Replace the your-bucket-name by your bucket.
 This will give access for your users only on a directory with their name on that specific bucket.
 
 Useful for backups.

Highly inspired by some posts on StackOverflow, credits to whomever I was reading at that time.
# Policy for the wizard user: example_policy_for_wizard_user.json
This is an example policy for the administrator user that will create the users.

It only has the right to create users in the path user/s3wizard (so it cannot mess with users it didn't create)


