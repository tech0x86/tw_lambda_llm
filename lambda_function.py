import json
import sys
import os
import time
import boto3
from openai import OpenAI
from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone

# Twitterの認証情報の取得
ssm = boto3.client('ssm')
twitter_sec = json.loads(ssm.get_parameter(Name='twitter_sec', WithDecryption=True)['Parameter']['Value'])
openai_sec = json.loads(ssm.get_parameter(Name='open_ai', WithDecryption=True)['Parameter']['Value'])
os.environ["OPENAI_API_KEY"] = openai_sec["API_KEY"]
ASSISTANT_ID=openai_sec["ASSISTANT_ID"]

# OAuth1セッションの作成
twitter = OAuth1Session(twitter_sec["CK"], client_secret=twitter_sec["CS"], resource_owner_key=twitter_sec["AT"], resource_owner_secret=twitter_sec["AS"])
url_tweets = "https://api.twitter.com/2/tweets"

def lambda_handler(event, context):
        # クライアントの準備
    client = OpenAI()
    thread = client.beta.threads.create()
    
    # 現在の日付を取得
    current_date = datetime.now()
    day = current_date.day
    current_date = current_date.strftime("%m月%d日")
    
    # 偶数か奇数かを判定
    if day % 2 == 0:
        char_set = "青葉"
    else:
      char_set = "クドリャフカ"
    user_prompt=current_date + " 答えるキャラクター:" + char_set

    print(f"user_prompt: {user_prompt}")
    # ユーザーメッセージの追加
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt
    )
    
    # アシスタントにリクエスト
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )
    while True:
        time_start = time.time()
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == "completed":
            print(f"End run in: {time.time() - time_start}")
            break  # ループを終了
        if time_start + 10 < time.time():
            print("Time out ERROR")
            break  # タイムアウト時もループを終了
        time.sleep(1)  # 1秒待機
    
    # スレッドのメッセージリストの確認
    messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        order="desc"
    )
    # 最新のメッセージ=生成後のメッセージ を表示
    resp=messages.data[0].content[0].text.value
    print(f"resp: {resp}")
    tweet_text_only(resp)
    return 0

def tweet_text_only(text="test_tweet"):
    tweet_data = {"text": text}
    headers = {"Content-Type": "application/json"}
    response = twitter.post(url_tweets, headers=headers, data=json.dumps(tweet_data))
    if response.status_code not in [200, 201]:
        raise Exception(f"Tweet post failed: {response.status_code}, {response.text}")
    print(response.json())


if __name__ == "__main__":
    # C9でデバッグ用
    lambda_handler("","")