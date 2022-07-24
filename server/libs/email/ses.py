import boto3
from botocore.exceptions import ClientError

from server.core.exception import EXCEPTION_LIB
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import api_logger as logger

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SENDER = "UniFrame <noreply@uniframe.io>"

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
# RECIPIENT = "dummy.user@gmail.com"

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the
# ConfigurationSetName=CONFIGURATION_SET argument below.
# CONFIGURATION_SET = "ConfigSet"

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = GLOBAL_CONFIG.region.value

# The subject line for the email.
# SUBJECT = "Amazon SES Test (SDK for Python)"

# The email body for recipients with non-HTML email clients.
# BODY_TEXT = (
#     "Amazon SES Test (Python)\r\n"
#     "This email was sent with Amazon SES using the "
#     "AWS SDK for Python (Boto)."
# )

# The character encoding for the email.
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client("ses", region_name=AWS_REGION)


def send_email(recipient: str, subject: str, body: str) -> None:
    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                "ToAddresses": [
                    recipient,
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": body,
                    },
                    # "Text": {
                    #     "Charset": CHARSET,
                    #     "Data": BODY_TEXT,
                    # },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": subject,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
        raise EXCEPTION_LIB.VCODE__VCODE_SEND_FAILED.value("vcode send failed")
    else:
        logger.info("Email sent! Message ID:")
        logger.info(response["MessageId"])
