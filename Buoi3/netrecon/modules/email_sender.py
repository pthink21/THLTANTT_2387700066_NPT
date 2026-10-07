import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import parseaddr


def send_email(recipient, report, audit):
    if not recipient:
        return {'status': 'not_requested'}
    if '\r' in recipient or '\n' in recipient or parseaddr(recipient)[1] != recipient or '@' not in recipient:
        raise ValueError('Invalid email recipient')
    mode = os.getenv('SMTP_MODE', 'disabled')
    if mode == 'disabled':
        return {'status': 'not_configured', 'detail': 'Set SMTP_MODE and SMTP credentials in local .env'}
    message = EmailMessage()
    message['Subject'] = 'NetRecon | Nguyễn Phúc Thịnh | 2387700066'
    message['From'] = os.getenv('SMTP_USER') or 'netrecon@localhost'
    message['To'] = recipient
    message.set_content(report)
    host = os.getenv('SMTP_HOST', '127.0.0.1' if mode == 'local' else 'smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT', '1025' if mode == 'local' else '587'))
    try:
        if mode == 'local' and host not in ('127.0.0.1', 'localhost'):
            raise ValueError('Local SMTP mode only supports loopback')
        if mode not in ('local', 'starttls'):
            raise ValueError('SMTP_MODE must be local/starttls/disabled')
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            if mode == 'starttls':
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASS'])
            smtp.send_message(message)
        audit.write('email_sent', transport=mode)
        return {'status': 'sent', 'transport': mode}
    except (OSError, smtplib.SMTPException, KeyError, ValueError) as exc:
        audit.write('email_failed', reason=type(exc).__name__)
        return {'status': 'failed', 'detail': type(exc).__name__}
