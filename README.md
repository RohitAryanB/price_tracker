# Price Checker — Setup Guide

## Project structure
```
lambda_price_checker/
├── lambda_function.py   ← your Lambda code
├── template.yaml        ← SAM/CloudFormation (cron + permissions)
└── README.md
```

---

## 1 · Verify your email addresses in SES

Before the function can send emails you must verify both addresses
in the AWS SES console (or via CLI):

```bash
# verify the sender
aws ses verify-email-identity --email-address you@example.com

# verify the recipient (only required while your account is in SES sandbox)
aws ses verify-email-identity --email-address recipient@example.com
```

> **SES Sandbox** — new AWS accounts start in sandbox mode where *both*
> sender and recipient must be verified. To send to any address, request
> production access in the SES console → "Account dashboard" → "Request production access".

---

## 2 · Install dependencies (for local testing)

```bash
pip install requests beautifulsoup4 boto3
```

---

## 3 · Deploy with AWS SAM (recommended)

```bash
# Install SAM CLI if needed
pip install aws-sam-cli

# Build & deploy (interactive first run)
sam build
sam deploy --guided \
  --parameter-overrides \
    NotifyEmail=recipient@example.com \
    SenderEmail=you@example.com \
    TargetPrice=55
```

SAM will create:
- The Lambda function
- An **EventBridge rule** that fires `rate(1 hour)` — your cron job
- An IAM policy granting `ses:SendEmail` to the function

---

## 4 · Deploy with plain CloudFormation (alternative)

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name BookPriceChecker \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    NotifyEmail=recipient@example.com \
    SenderEmail=you@example.com \
    TargetPrice=55
```

---

## 5 · Test manually

```bash
aws lambda invoke \
  --function-name BookPriceChecker \
  --payload '{}' \
  response.json && cat response.json
```

---

## Customising the schedule

Edit `template.yaml` → `Schedule` property:

| Frequency | Value |
|-----------|-------|
| Every hour | `rate(1 hour)` |
| Every 30 min | `rate(30 minutes)` |
| Daily at 09:00 UTC | `cron(0 9 * * ? *)` |
| Every hour on the hour | `cron(0 * * * ? *)` |

---

## Environment variables

| Variable | Description |
|---|---|
| `TARGET_PRICE` | Alert when price ≤ this value (default `60`) |
| `NOTIFY_EMAIL` | Email address to receive alerts |
| `SENDER_EMAIL` | SES-verified sender address |
