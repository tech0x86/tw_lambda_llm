#!/bin/bash
docker run -d --name cont_lambda openai_py_slim
docker exec -it cont_lambda /bin/bash