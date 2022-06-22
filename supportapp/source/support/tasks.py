import logging
import textwrap

from django.core.mail import EmailMessage
from drfsite.celery import app

logger = logging.getLogger(__name__)


@app.task(name='send_email_notify')
def send_email_notify(data: dict):
    to = data.get('email')
    message = data.get('ticket_message')
    answer_message = data.get('answer_message')
    link = data.get('ticket_url')
    subj = f"You have new reply to your ticket " \
           f"{textwrap.shorten(message, width=30, placeholder='...')}"
    body = f"Support has reply to yor ticket:\n " \
           f"\t{message}\n" \
           f"------------------------------\n" \
           f"Reply message:\n" \
           f"\t{answer_message}\n" \
           f"------------------------------\n" \
           f"\nTo check your ticket, press to link: {link}"
    email = EmailMessage(subj, body, to=[to])
    try:
        email.send()
    except Exception as exc:
        logger.warning(f'EMAIL was not sent. Reason: {exc}')
    return True
