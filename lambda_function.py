import json
import os
import time
import boto3
from openai import OpenAI
from requests_oauthlib import OAuth1Session
from datetime import datetime, timedelta, timezone

# 環境設定と認証情報の取得
def setup_environment():
    ssm = boto3.client('ssm')
    twitter_sec = json.loads(ssm.get_parameter(Name='twitter_sec', WithDecryption=True)['Parameter']['Value'])
    openai_sec = json.loads(ssm.get_parameter(Name='open_ai', WithDecryption=True)['Parameter']['Value'])
    os.environ["OPENAI_API_KEY"] = openai_sec["API_KEY"]
    ASSISTANT_ID = openai_sec["ASSISTANT_ID"]
    twitter = OAuth1Session(twitter_sec["CK"], client_secret=twitter_sec["CS"], resource_owner_key=twitter_sec["AT"], resource_owner_secret=twitter_sec["AS"])
    return twitter, ASSISTANT_ID


# 日付に基づくキャラクターの選択
def choose_character():
    jst_timezone = timezone(timedelta(hours=9))  # JSTタイムゾーンの設定
    current_date = datetime.now(jst_timezone).strftime("%m月%d日")
    day = datetime.now(jst_timezone).day
    char_set = "青葉" if day % 2 == 0 else "クドリャフカ"
    return current_date, char_set

# OpenAIに質問する
def ask_openai(client, thread, current_date, char_set, ASSISTANT_ID):
    user_prompt = f"{current_date} 答えるキャラクター:{char_set}"
    print(f"user_prompt: {user_prompt}")

    # ユーザーメッセージの追加
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_prompt)

    # アシスタントにリクエスト
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    while True:
        time_start = time.time()
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            print(f"End run in: {time.time() - time_start}")
            break
        if time_start + 10 < time.time():
            print("Time out ERROR")
            break
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc")
    resp = messages.data[0].content[0].text.value
    print(f"resp: {resp}")
    return resp

# ツイートとリプライの送信
def tweet_and_reply(twitter, text, char_set, client, thread, ASSISTANT_ID):
    tweet_id = tweet_text_only(twitter, text)
    alternate_char_sets = ["青葉", "クドリャフカ"]
    alternate_char_sets.remove(char_set)  # 使われたchar_setを削除

    # 1回目のリプライ
    first_reply_char_set = alternate_char_sets[0]
    first_reply_response = get_openai_response_for_tweet(client, thread, text, first_reply_char_set, ASSISTANT_ID)
    first_reply_text = f"{first_reply_response}"
    first_reply_id = tweet_text_only(twitter, first_reply_text, tweet_id)

    # 2回目のリプライ（1回目のリプライを基に）
    second_reply_char_set = char_set  # 最初のchar_setに戻る
    second_reply_response = get_openai_response_for_tweet(client, thread, first_reply_text, second_reply_char_set, ASSISTANT_ID)
    second_reply_text = f"{second_reply_response}"
    tweet_text_only(twitter, second_reply_text, first_reply_id)
    
# ツイートのみを送信
def tweet_text_only(twitter, text, reply_to_id=None):
    tweet_data = {"text": text}
    if reply_to_id:
        tweet_data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
    headers = {"Content-Type": "application/json"}
    response = twitter.post("https://api.twitter.com/2/tweets", headers=headers, data=json.dumps(tweet_data))
    if response.status_code not in [200, 201]:
        raise Exception(f"Tweet post failed: {response.status_code}, {response.text}")
    tweet_id = response.json()["data"]["id"]
    print(f"Tweeted: {tweet_id}")
    return tweet_id

# ツイートに対するOpenAIのレスポンスを取得
def get_openai_response_for_tweet(client, thread, tweet, char_set, ASSISTANT_ID):
    prompt = f"キャラクター: {char_set} として次の投稿内容の感想を書いて。:  {tweet}"
    print(f"prompt: {prompt}")

    # ユーザーメッセージの追加
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)

    # アシスタントにリクエスト
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    while True:
        time_start = time.time()
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            print(f"End run in: {time.time() - time_start}")
            break
        if time_start + 10 < time.time():
            print("Time out ERROR")
            break
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc")
    response = messages.data[0].content[0].text.value
    print(f"Response: {response}")
    return response



# Lambdaハンドラー
def lambda_handler(event, context):
    twitter, ASSISTANT_ID = setup_environment()
    current_date, char_set = choose_character()
    client = OpenAI()
    thread = client.beta.threads.create()
    response_text = ask_openai(client, thread, current_date, char_set, ASSISTANT_ID)
    tweet_and_reply(twitter, response_text, char_set, client, thread, ASSISTANT_ID)
    return 0

if __name__ == "__main__":
    lambda_handler("", "")
