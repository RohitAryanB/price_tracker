import os
import boto3
import requests
from bs4 import BeautifulSoup

URL = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
TARGET_PRICE = float(os.environ.get("TARGET_PRICE", "60"))
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")   # recipient email
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")   # SES-verified sender email

headers = {"User-Agent": "Mozilla/5.0"}


def get_price():
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    price_tag = soup.find("p", {"class": "price_color"})
    if price_tag:
        price_text = price_tag.get_text().strip()
        price = float(price_text.replace("£", "").replace("Â", "").strip())
        return price
    return None


def send_email_alert(price: float):
    """Send a price-drop alert via Amazon SES."""
    if not NOTIFY_EMAIL or not SENDER_EMAIL:
        print("Email env vars not set — skipping notification.")
        return

    ses = boto3.client("ses")  # region inherited from Lambda execution environment
    subject = f"📉 Price Alert: Book is now £{price:.2f}!"
    body_text = (
        f"Good news! The price of 'A Light in the Attic' has dropped.\n\n"
        f"  Current price : £{price:.2f}\n"
        f"  Target price  : £{TARGET_PRICE:.2f}\n\n"
        f"Buy it here: {URL}\n\n"
        f"-- Price Checker Bot"
    )
    body_html = f"""
    <html>
      <body style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px">
        <h2 style="color:#e63946">📉 Price Drop Alert!</h2>
        <p>Good news! <strong>A Light in the Attic</strong> is now below your target price.</p>
        <table style="border-collapse:collapse;width:100%">
          <tr>
            <td style="padding:8px;border:1px solid #ddd">Current price</td>
            <td style="padding:8px;border:1px solid #ddd"><strong>£{price:.2f}</strong></td>
          </tr>
          <tr>
            <td style="padding:8px;border:1px solid #ddd">Your target</td>
            <td style="padding:8px;border:1px solid #ddd">£{TARGET_PRICE:.2f}</td>
          </tr>
        </table>
        <p><a href="{URL}" style="display:inline-block;margin-top:16px;padding:10px 20px;
           background:#e63946;color:#fff;text-decoration:none;border-radius:4px">
           Buy Now →</a></p>
      </body>
    </html>
    """

    ses.send_email(
        Source=SENDER_EMAIL,
        Destination={"ToAddresses": [NOTIFY_EMAIL]},
        Message={
            "Subject": {"Data": subject},
            "Body": {
                "Text": {"Data": body_text},
                "Html": {"Data": body_html},
            },
        },
    )
    print(f"Alert email sent to {NOTIFY_EMAIL}")


def lambda_handler(event, context):
    price = get_price()

    if price is None:
        return {"statusCode": 500, "body": "Price not found"}

    print(f"Current Price: £{price:.2f}  |  Target: £{TARGET_PRICE:.2f}")

    if price <= TARGET_PRICE:
        print("🔥 Price dropped! Sending alert...")
        send_email_alert(price)

    return {
        "statusCode": 200,
        "body": f"Checked price: £{price:.2f}",
    }
