# AWS公式のPythonランタイムベースイメージを使用
# pullエラー時はログアウトを。
# docker logout public.ecr.aws
FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y vim
# 必要なPythonライブラリをインストール
RUN pip3 install openai

# アプリケーションのソースコードをコンテナにコピー
COPY . .

# Lambdaランタイムが関数ハンドラを呼び出すためのコマンドを指定
# 公式lambdaイメージの場合はこの指定で問題ない
CMD ["lambda_function.lambda_handler"]
