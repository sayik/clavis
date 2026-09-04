from dataclasses import dataclass
import hashlib
import secrets
import aiosmtplib
from email.message import EmailMessage
from app.config.settings import get_settings


settings = get_settings()

@dataclass(frozen=True)
class EmailVerificationToken:
    token: str
    token_hash: str
    verification_link: str


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_email_verification_link(base_url: str) -> EmailVerificationToken:
    token = secrets.token_urlsafe(32)

    return EmailVerificationToken(
        token=token,
        token_hash=hash_token(token),
        verification_link=f"{base_url}/auth/verify-email?token={token}",
    )



"""This function holds content of the email and the subject name"""
def email_content(username: str, verification_link: str) -> tuple[str, str]:
    subject = "Verify your email"

    html = f"""
    <html>
        <body>
            <h2>Welcome, {username}!</h2>

            <p>Thanks for registering.</p>

            <p>
                Click below to verify your email:
            </p>

            <p>
                <a href="{verification_link}">
                    Verify Email
                </a>
            </p>

            <p>This link expires in 24 hours.</p>
        </body>
    </html>
    """

    return subject, html



"""This function sends the email"""

async def send_email(
    to: str,
    subject: str,
    html: str,
):
    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to

    message.set_content("Please view this email in HTML.")
    message.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


"""This is core function to send the email"""
async def send_verification_email(
    email: str,
    username: str,
    verification_link: str,
):
    subject, html = email_content(
        username,
        verification_link,
    )

    await send_email(
        to=email,
        subject=subject,
        html=html,
    )