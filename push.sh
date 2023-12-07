#!/bin/bash

# AWS ECRにログイン
#docker login --username AWS --password-stdin 767853239238.dkr.ecr.ap-northeast-1.amazonaws.com

# Dockerイメージをビルド
docker build -t openai_py_slim .

# アカウントIDを取得し、変数に格納
ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

# AWS ECRにログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com

# イメージをタグ付け
docker tag openai_py_slim:latest ${ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/tweet_llm:latest

# イメージをAWS ECRにプッシュ
docker push ${ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/tweet_llm:latest

# Lambdaの更新
aws lambda update-function-code --function-name arn:aws:lambda:ap-northeast-1:${ACCOUNT_ID}:function:tweet_llm --image-uri ${ACCOUNT_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/tweet_llm:latest --no-cli-pager
