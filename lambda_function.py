import json
import sys
import openai
import boto3
ssm = boto3.client('ssm')
twitter_sec = json.loads(ssm.get_parameter(Name='twitter_sec', WithDecryption=True)['Parameter']['Value'])

def lambda_handler(event, context):
    print("hello lambda")
    print(twitter_sec)
    return 'Hello from AWS Lambda using Python' + sys.version + '!'

if __name__ == "__main__":
    # C9でデバッグ用
    lambda_handler("","")