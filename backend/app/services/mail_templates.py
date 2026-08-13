"""HTML and plain-text email templates for GuardianX transactional mail.

Templates include GuardianX branding, a clear CTA button, a fallback
plain-text URL, expiration information and a security notice. They never embed
sensitive data beyond the single-use link the recipient is meant to click.
"""

from dataclasses import dataclass
from html import escape

from app.core.config import settings


@dataclass(frozen=True)
class EmailContent:
    subject: str
    text: str
    html: str


_BRAND = "GuardianX"
_ACCENT = "#111827"          # header / footer background
_CTA_BG = "#0ea5e9"          # call-to-action button color
_CTA_TEXT = "#ffffff"


def _shell(
    *,
    heading: str,
    preheader: str,
    paragraphs: list[str],
    button_text: str | None,
    button_url: str | None,
    footnote: str,
) -> str:
    """Wrap body content in a branded, responsive HTML email shell."""
    button_html = ""
    if button_text and button_url:
        button_html = (
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            'style="margin: 24px auto;">'
            '<tr><td align="center">'
            '<a href="{url}" style="display:inline-block;padding:14px 28px;'
            'background:{bg};color:{txt};text-decoration:none;'
            'border-radius:8px;font-weight:600;font-size:15px;">{label}</a>'
            "</td></tr></table>"
        ).format(url=escape(button_url), bg=_CTA_BG, txt=_CTA_TEXT, label=escape(button_text))

    paragraphs_html = "\n".join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;'
        f'color:#374151;">{escape(text)}</p>'
        for text in paragraphs
    )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(preheader)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6f8;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#f4f6f8;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:560px;background-color:#ffffff;border-radius:12px;
                      overflow:hidden;border:1px solid #e2e8f0;">
          <tr>
            <td style="background-color:{_ACCENT};padding:22px 28px;">
              <span style="color:#ffffff;font-size:20px;font-weight:700;">
                {escape(_BRAND)}
              </span>
            </td>
          </tr>
          <tr>
            <td style="padding:28px;">
              <h1 style="margin:0 0 16px;font-size:22px;color:#0f172a;">
                {escape(heading)}
              </h1>
              {paragraphs_html}
              {button_html}
              <p style="margin:24px 0 0;font-size:13px;color:#64748b;
                        line-height:1.5;">
                {escape(footnote)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="background-color:{_ACCENT};padding:16px 28px;">
              <span style="color:#94a3b8;font-size:12px;">
                {escape(_BRAND)} — AI-Powered Personal Cyber Defense Platform
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def build_verification_email(
    *,
    username: str,
    verify_url: str,
    expires_minutes: int,
) -> EmailContent:
    """Email the user a single-use email-verification link."""
    subject = f"Verify your {settings.APP_NAME} account"
    intro = (
        f"Hi {username},\n\n"
        f"Welcome to {settings.APP_NAME}. Please confirm your email address "
        f"to activate your account."
    )
    text = (
        f"{intro}\n\n"
        f"Click to verify: {verify_url}\n\n"
        f"This link expires in {expires_minutes} minutes.\n"
        f"If you did not create an account, you can safely ignore this email.\n"
    )
    html = _shell(
        heading=f"Verify your email address",
        preheader=subject,
        paragraphs=[
            f"Hi {username}, welcome to {settings.APP_NAME}. Please confirm "
            "your email address to activate your account.",
        ],
        button_text="Verify email address",
        button_url=verify_url,
        footnote=(
            f"This link expires in {expires_minutes} minutes. "
            f"If the button does not work, copy and paste this URL into your "
            f"browser: {verify_url} · If you did not create an account, you "
            "can safely ignore this email."
        ),
    )
    return EmailContent(subject=subject, text=text, html=html)


def build_reset_email(
    *,
    username: str,
    reset_url: str,
    expires_minutes: int,
) -> EmailContent:
    """Build the single-use password-reset link email."""
    subject = f"Reset your {settings.APP_NAME} password"
    text = (
        f"Hi {username},\n\n"
        f"We received a request to reset your {settings.APP_NAME} password. "
        f"Use the link below to choose a new one:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {expires_minutes} minutes.\n"
        f"If you did not request this, you can safely ignore this email, and "
        f"your password will remain unchanged.\n"
    )
    html = _shell(
        heading="Reset your password",
        preheader=subject,
        paragraphs=[
            f"Hi {username}, we received a request to reset your "
            f"{settings.APP_NAME} password. Use the button below to choose a "
            "new one.",
        ],
        button_text="Reset password",
        button_url=reset_url,
        footnote=(
            f"This link expires in {expires_minutes} minutes. If the button "
            f"does not work, copy and paste this URL into your browser: "
            f"{reset_url} · If you did not request this, you can safely "
            "ignore this email."
        ),
    )
    return EmailContent(subject=subject, text=text, html=html)


def build_welcome_email(*, username: str) -> EmailContent:
    """Build the post-signup welcome email."""
    subject = f"Welcome to {settings.APP_NAME}"
    text = (
        f"Hi {username},\n\n"
        f"Your {settings.APP_NAME} account has been created. Please verify "
        f"your email address to activate it — a verification link is on its "
        f"way to you separately.\n\n"
        f"If you did not create this account, you can safely ignore this "
        f"email.\n"
    )
    html = _shell(
        heading="Welcome to GuardianX",
        preheader=subject,
        paragraphs=[
            f"Hi {username}, your {settings.APP_NAME} account has been "
            "created. Please verify your email address to activate it — a "
            "verification link has been sent to you in a separate email.",
            "If you did not create this account, you can safely ignore this "
            "email.",
        ],
        button_text=None,
        button_url=None,
        footnote="This is a system-generated message; replies are not monitored.",
    )
    return EmailContent(subject=subject, text=text, html=html)