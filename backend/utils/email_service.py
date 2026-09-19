import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("email_service")

# SMTP Configuration from Environment Variables (or defaults)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DEFAULT_SENDER = os.getenv("SMTP_SENDER", "alerts@ransomguard.io")


def is_smtp_configured() -> bool:
    """Check if real SMTP credentials are provided."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    plain_text: Optional[str] = None,
    smtp_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send an email via SMTP or fallback to simulated security dispatch.
    """
    host = smtp_override.get("host") if smtp_override else SMTP_HOST
    port = smtp_override.get("port") if smtp_override else SMTP_PORT
    user = smtp_override.get("user") if smtp_override else SMTP_USER
    password = smtp_override.get("password") if smtp_override else SMTP_PASSWORD

    sender = user or DEFAULT_SENDER

    # If SMTP is configured, attempt real connection
    if host and user and password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"RansomGuard SOC <{sender}>"
            msg["To"] = to_email

            if plain_text:
                msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, password)
                server.sendmail(sender, [to_email], msg.as_string())

            logger.info(f"Email successfully delivered to {to_email} via SMTP ({host})")
            return {
                "success": True,
                "mode": "smtp",
                "message": f"Security alert email sent directly to {to_email}",
            }
        except Exception as e:
            logger.error(f"SMTP delivery failed to {to_email}: {e}")
            return {
                "success": False,
                "mode": "smtp_error",
                "error": str(e),
                "message": f"SMTP Error: {e}",
            }

    # If no SMTP credentials, run formatted security dispatch simulation
    logger.info(f"[SIMULATED EMAIL DISPATCH] To: {to_email} | Subject: {subject}")
    return {
        "success": True,
        "mode": "simulated",
        "message": f"Alert email generated and dispatched to {to_email} (Demo SOC Dispatch). To connect live SMTP, set SMTP_USER & SMTP_PASSWORD in backend/.env",
    }


def send_test_security_email(to_email: str) -> Dict[str, Any]:
    """Send a test security notification email."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subject = "🛡️ RansomGuard Security Node — Test Alert Notification"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0F172A; color: #F8FAFC; margin: 0; padding: 24px; }}
        .card {{ max-width: 540px; margin: auto; background: #1E293B; border-radius: 16px; padding: 28px; border: 1px solid #334155; }}
        .header {{ display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #334155; padding-bottom: 16px; }}
        .badge {{ background: #2563EB; color: white; padding: 4px 10px; border-radius: 99px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
        .title {{ font-size: 18px; font-weight: bold; color: #60A5FA; margin-top: 16px; }}
        .info-box {{ background: #0F172A; border-radius: 10px; padding: 14px; margin: 16px 0; font-family: monospace; font-size: 13px; color: #94A3B8; }}
        .footer {{ font-size: 11px; color: #64748B; margin-top: 20px; text-align: center; border-top: 1px solid #334155; padding-top: 14px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <span class="badge">RansomGuard Node</span>
          <span style="font-size: 12px; color: #94A3B8;">Channel Test</span>
        </div>
        <div class="title">Security Notification Channel Verified</div>
        <p style="font-size: 13px; color: #CBD5E1; line-height: 1.5;">
          This is a test notification from your <strong>RansomGuard Autonomous Surveillance System</strong>. Your security email channel has been successfully verified.
        </p>
        <div class="info-box">
          <div>• Dispatch Time: {now_str}</div>
          <div>• Recipient: {to_email}</div>
          <div>• Monitoring Engine: Active (v1.0.0)</div>
          <div>• Threat Defense: Armed</div>
        </div>
        <div class="footer">
          &copy; {datetime.now().year} RansomGuard Security Operations • Autonomous Behavioral Defense
        </div>
      </div>
    </body>
    </html>
    """

    plain = f"RansomGuard Security Notification: Channel verified for {to_email} at {now_str}."
    return send_email(to_email, subject, html, plain)


def send_threat_incident_email(to_email: str, threat_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send an urgent ransomware threat incident alert email."""
    threat_level = threat_data.get("threat_level", "CRITICAL").upper()
    file_path = threat_data.get("file_path", "Unknown")
    process_name = threat_data.get("process_name", "Unknown Process")
    pid = threat_data.get("pid", "N/A")
    score = threat_data.get("confidence", threat_data.get("risk_score", 95))
    timestamp = threat_data.get("timestamp", datetime.now(timezone.utc).isoformat())

    subject = f"🚨 [RANSOMGUARD ALERT] {threat_level} Threat Detected on {process_name}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0F172A; color: #F8FAFC; margin: 0; padding: 24px; }}
        .card {{ max-width: 580px; margin: auto; background: #1E293B; border-radius: 16px; padding: 28px; border: 1px solid #EF4444; }}
        .badge {{ background: #EF4444; color: white; padding: 4px 10px; border-radius: 99px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
        .title {{ font-size: 20px; font-weight: bold; color: #F87171; margin-top: 14px; }}
        .info-box {{ background: #0F172A; border-radius: 10px; padding: 14px; margin: 16px 0; font-family: monospace; font-size: 13px; color: #E2E8F0; line-height: 1.6; border-left: 3px solid #EF4444; }}
        .action {{ background: #EF4444; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; display: inline-block; font-weight: bold; font-size: 13px; margin-top: 8px; }}
        .footer {{ font-size: 11px; color: #64748B; margin-top: 24px; text-align: center; border-top: 1px solid #334155; padding-top: 14px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div>
          <span class="badge">URGENT SECURITY ALERT</span>
        </div>
        <div class="title">Ransomware Activity Detected ({threat_level})</div>
        <p style="font-size: 13px; color: #CBD5E1; line-height: 1.5;">
          The RansomGuard Machine Learning Detection Engine has flagged suspicious high-entropy encryption or rapid I/O file modifications.
        </p>
        <div class="info-box">
          <div><strong>Process:</strong> {process_name} (PID: {pid})</div>
          <div><strong>Target Target/File:</strong> {file_path}</div>
          <div><strong>Threat Confidence:</strong> {score}%</div>
          <div><strong>Timestamp:</strong> {timestamp}</div>
        </div>
        <p style="font-size: 12px; color: #94A3B8;">
          Please open your RansomGuard SOC Dashboard immediately to review, isolate, or terminate the offending process.
        </p>
        <div class="footer">
          &copy; {datetime.now().year} RansomGuard Incident Response Node
        </div>
      </div>
    </body>
    </html>
    """

    plain = f"URGENT: {threat_level} ransomware activity detected by {process_name} on {file_path}. Threat Confidence: {score}%."
    return send_email(to_email, subject, html, plain)
