#!/bin/bash
set -euo pipefail

QUEUE_URL="https://sqs.ap-southeast-1.amazonaws.com/544885083148/augminted-jobs"
BUCKET="augminted-pipeline-prod"

mkdir -p /home/ec2-user/worker/{inputs,jobs,outputs,logs}

while true; do
  echo "Polling SQS..."

  MSG=$(aws sqs receive-message \
    --queue-url "$QUEUE_URL" \
    --max-number-of-messages 1 \
    --wait-time-seconds 10 \
    --visibility-timeout 600 \
    --output json 2>/dev/null || echo '{}')

  if [ -z "$MSG" ]; then
    MSG='{}'
  fi

  BODY=$(printf '%s' "$MSG" | python3 -c 'import sys,json
try:
    data=json.load(sys.stdin)
    msgs=data.get("Messages", [])
    print(msgs[0]["Body"] if msgs else "")
except Exception:
    print("")
')

  RECEIPT=$(printf '%s' "$MSG" | python3 -c 'import sys,json
try:
    data=json.load(sys.stdin)
    msgs=data.get("Messages", [])
    print(msgs[0]["ReceiptHandle"] if msgs else "")
except Exception:
    print("")
')

  if [ -z "$BODY" ]; then
    echo "No messages..."
    sleep 5
    continue
  fi

  JOB_ID=$(printf '%s' "$BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin)["job_id"])')
  INPUT_PATH=$(printf '%s' "$BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin)["input_path"])')

  echo "Processing job: $JOB_ID"
  cat > "/tmp/${JOB_ID}-status.json" <<EOF
{"job_id":"$JOB_ID","status":"processing"}
EOF
aws s3 cp "/tmp/${JOB_ID}-status.json" "s3://$BUCKET/status/${JOB_ID}.json"
mkdir -p "/home/ec2-user/worker/inputs/$JOB_ID/photos" "/home/ec2-user/worker/jobs" "/home/ec2-user/worker/outputs" "/home/ec2-user/worker/logs"

  aws s3 cp "s3://$BUCKET/$INPUT_PATH" "/home/ec2-user/worker/inputs/$JOB_ID/photos/main.jpg"

  cat > "/home/ec2-user/worker/jobs/$JOB_ID.yaml" <<EOF
job_id: $JOB_ID
category: table
photos_dir: inputs/$JOB_ID/photos
EOF

  set +e
  docker run --rm \
    --entrypoint python \
    -e TRIPO_API_KEY=$TRIPO_API_KEY \
    -v /home/ec2-user/worker/inputs:/app/inputs \
    -v /home/ec2-user/worker/jobs:/app/jobs \
    -v /home/ec2-user/worker/outputs:/app/outputs \
    -v /home/ec2-user/worker/logs:/app/logs \
    544885083148.dkr.ecr.ap-southeast-1.amazonaws.com/augminted-runner:latest \
    run_job.py "jobs/$JOB_ID.yaml" \
    2>&1 | tee "/home/ec2-user/worker/logs/${JOB_ID}.log"
RUN_STATUS=${PIPESTATUS[0]}
set -e

if [ "$RUN_STATUS" -ne 0 ]; then
  cat > "/tmp/${JOB_ID}-status.json" <<EOF
{"job_id":"$JOB_ID","status":"failed"}
EOF

  aws s3 cp "/tmp/${JOB_ID}-status.json" "s3://$BUCKET/status/${JOB_ID}.json"

  echo "Docker job failed for $JOB_ID"
  continue
fi
  if [ -f "/home/ec2-user/worker/outputs/${JOB_ID}_safety.glb" ]; then
    aws s3 cp "/home/ec2-user/worker/outputs/${JOB_ID}_safety.glb" "s3://$BUCKET/outputs/$JOB_ID/model.glb"
  fi

  if [ -f "/home/ec2-user/worker/outputs/${JOB_ID}_safety.usdz" ]; then
    aws s3 cp "/home/ec2-user/worker/outputs/${JOB_ID}_safety.usdz" "s3://$BUCKET/outputs/$JOB_ID/model.usdz"
  fi

  if [ -f "/home/ec2-user/worker/outputs/${JOB_ID}_safety.glb" ] || [ -f "/home/ec2-user/worker/outputs/${JOB_ID}_safety.usdz" ]; then
    aws sqs delete-message \
      --queue-url "$QUEUE_URL" \
      --receipt-handle "$RECEIPT"
cat > "/tmp/${JOB_ID}-status.json" <<EOF
{"job_id":"$JOB_ID","status":"done"}
EOF
aws s3 cp "/tmp/${JOB_ID}-status.json" "s3://$BUCKET/status/${JOB_ID}.json"
    echo "Finished job: $JOB_ID"
  else
    echo "No output files found for $JOB_ID — leaving message undeleted for retry/debug"
  fi
done
