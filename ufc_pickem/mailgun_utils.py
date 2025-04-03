import os
import requests

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_SENDER = f"UFC Pick'em <mailgun@{MAILGUN_DOMAIN}>"


def send_verification_email(recipient_email, token):
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    verify_link = f"https://ufcpickem.onrender.com/verify/{token}"

    return requests.post(
        url,
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": MAILGUN_SENDER,
            "to": recipient_email,
            "subject": "Verify Your Email for UFC Pick'em",
            "html": f"""
                <p>Thanks for registering! Please click the link below to verify your email:</p>
                <p><a href="{verify_link}">Verify Email</a></p>
                <p>If you didn’t register, you can ignore this email.</p>
            """
        }
    )


def send_password_reset_email(recipient_email, token):
    url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
    reset_link = f"https://ufcpickem.onrender.com/reset_password/{token}"

    return requests.post(
        url,
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": MAILGUN_SENDER,
            "to": recipient_email,
            "subject": "Reset Your UFC Pick'em Password",
            "html": f"""
                <p>You requested to reset your password. Click the link below to continue:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>If you did not request this, you can safely ignore this email.</p>
            """
        }
    )
