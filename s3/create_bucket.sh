#!/bin/bash
source .env

aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID --profile $PROFILE
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY --profile $PROFILE
aws configure set region $AWS_DEFAULT_REGION --profile $PROFILE


if [[ "$ENDPOINT_URL" == http://localhost* ]]; then
  echo "LocalStack rilevato, avvio retry loop per S3..."

  MAX_RETRIES=10
  RETRY_INTERVAL=2
  READY=false

  for ((i=1; i<=MAX_RETRIES; i++)); do
    echo "Tentativo $i: controllo se S3 è pronto..."
    aws --endpoint-url "$ENDPOINT_URL" s3 ls > /dev/null 2>&1
    if [ $? -eq 0 ]; then
      READY=true
      break
    fi
    sleep $RETRY_INTERVAL
  done

  if [ "$READY" = false ]; then
    echo "S3 non è pronto dopo $MAX_RETRIES tentativi. Esco."
    exit 1
  fi
else
  echo "AWS reale rilevato."
fi

if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  echo "Bucket $BUCKET_NAME already exists. Skipping creation."
else
  CMD="aws s3api create-bucket --bucket $BUCKET_NAME --region $AWS_DEFAULT_REGION"

  if [ -n "$ENDPOINT_URL" ]; then
    CMD="$CMD --endpoint-url $ENDPOINT_URL"
  fi

  if [ -n "$PROFILE" ]; then
    CMD="$CMD --profile $PROFILE"
  fi

  if [ "$AWS_DEFAULT_REGION" != "us-east-1" ]; then
    CMD="$CMD --create-bucket-configuration LocationConstraint=$AWS_DEFAULT_REGION"
  fi

  echo "Creating bucket with command: $CMD"
  eval $CMD
fi
