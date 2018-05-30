"""This file contains the logic to understand a user message request
 from YA and return a response in the format of
 a YA message object accordingly
"""
from yellowant.messageformat import MessageClass, MessageAttachmentsClass
import boto3
import botocore
from yellowant_api.models import awss3, UserIntegration


class CommandCenter(object):
    """Handles user commands
    Args:
        yellowant_integration_id (int): The integration id of a YA user
        self.commands (str): Invoke name of the command the user is calling
        args (dict): Any arguments required for the command to run
    """

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name,
                 args, application_invoke_name):
        self.yellowant_user_id = yellowant_user_id
        self.application_invoke_name = application_invoke_name
        self.yellowant_integration_id = yellowant_integration_id
        self.account_id = UserIntegration.objects.get(yellowant_integration_invoke_name=
                                                      self.application_invoke_name)
        self.aws_access_key = awss3.objects.get(id=self.account_id).AWS_APIAccessKey
        self.aws_secret_token = awss3.objects.get(id=self.account_id).AWS_APISecretAccess
        self.function_name = function_name
        self.args = args

    def parse(self):
        """The connection between yellowant commands and functions in django"""
        self.commands = {
            'start-bucket': self.create_bucket,
            'list-buckets': self.list_buckets,
        }
        return self.commands[self.function_name](self.args)

    def create_bucket(self, args):
        """ To create a bucket for storing data in AWS S3"""
        message = MessageClass()
        bucket = args["Bucket"]
        sss = boto3.client(service_name='s3', api_version=None,
                           use_ssl=True, verify=None, endpoint_url=None,
                           aws_access_key_id=self.aws_access_key,
                           aws_secret_access_key=self.aws_secret_token,
                           aws_session_token=None, config=None)
        try:
            sss.create_bucket(Bucket=bucket)
            message.message_text = "New Bucket Created"
        except botocore.errorfactory.ClientError as exception:
            # print("abcd")
            # print(e.response['Error']['Code'])
            if exception.response['Error']['Code'] == "BucketAlreadyExists":
                message.message_text = "The requested Bucket Name is not available"
        return message.to_json()

    def list_buckets(self, args):
        """ To list the buckets in  the AWS S3, no input arguments required """
        message = MessageClass()
        sss = boto3.client(service_name='s3', api_version=None,
                           use_ssl=True, verify=None, endpoint_url=None,
                           aws_access_key_id=self.aws_access_key,
                           aws_secret_access_key=self.aws_secret_token,
                           aws_session_token=None, config=None)
        response = sss.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        for bucket in buckets:
            attachment = MessageAttachmentsClass()
            attachment.title = bucket
            message.attach(attachment)

        message.message_text = "The Buckets present are:"
        return message.to_json()
