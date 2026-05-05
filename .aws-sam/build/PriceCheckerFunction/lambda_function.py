import os
import json
import boto3
import requests
from bs4 import BeautifulSoup

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")

headers = {"User-Agent": "Mozilla/5.0"}


def get_price(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    price_tag = soup.find("p", {"class": "price_color"})
    if price_tag:
        price_text = price_tag.get_text().strip()
        price = float(price_text.replace("£", "").replace("Â", "").strip())
        return price
    return None


def get_title(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.find("h1")
        return title.get_text().strip() if title else "the book"
    except:
        return "the book"


def send_email_alert(notify_email, sender_email, price, target_price, url, title):
    if not notify_email or not sender_email:
        return
    ses = boto3.client("ses")
    subject = f"Price Alert: {title} is now £{price:.2f}!"
    body_html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px">
        <h2 style="color:#e63946">Price Drop Alert!</h2>
        <p><strong>{title}</strong> is now below your target price.</p>
        <table style="border-collapse:collapse;width:100%">
          <tr><td style="padding:8px;border:1px solid #ddd">Current price</td>
              <td style="padding:8px;border:1px solid #ddd"><strong>£{price:.2f}</strong></td></tr>
          <tr><td style="padding:8px;border:1px solid #ddd">Your target</td>
              <td style="padding:8px;border:1px solid #ddd">£{target_price:.2f}</td></tr>
        </table>
        <p><a href="{url}" style="display:inline-block;margin-top:16px;padding:10px 20px;
           background:#e63946;color:#fff;text-decoration:none;border-radius:4px">Buy Now</a></p>
      </body>
    </html>
    """
    ses.send_email(
        Source=sender_email,
        Destination={"ToAddresses": [notify_email]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Html": {"Data": body_html}},
        },
    )
    print(f"Alert email sent to {notify_email}")


def lambda_handler(event, context):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": cors, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        url = body.get("url", "").strip()
        target_price = float(body.get("target_price", 0))
        notify_email = body.get("email", "").strip()

        if not url or not target_price or not notify_email:
            return {
                "statusCode": 400,
                "headers": cors,
                "body": json.dumps({"error": "url, target_price, and email are all required"}),
            }

        price = get_price(url)
        if price is None:
            return {
                "statusCode": 422,
                "headers": cors,
                "body": json.dumps({"error": "Could not find a price on that page. Make sure it is a books.toscrape.com product URL."}),
            }

        title = get_title(url)
        price_dropped = price <= target_price

        if price_dropped:
            send_email_alert(notify_email, SENDER_EMAIL, price, target_price, url, title)

        return {
            "statusCode": 200,
            "headers": cors,
            "body": json.dumps({
                "title": title,
                "current_price": round(price, 2),
                "target_price": round(target_price, 2),
                "price_dropped": price_dropped,
                "email_sent": price_dropped,
                "message": f"Current price is £{price:.2f}. {'Price dropped — alert sent to your email!' if price_dropped else 'Price has not dropped yet. Check back later.'}"
            }),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors,
            "body": json.dumps({"error": str(e)}),
        }
