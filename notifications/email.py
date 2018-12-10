import smtplib
import logging
import time

logger = logging.getLogger(__name__)


def send_email( recipient, body):
    subject = 'ED7 - Trading - MAS'
    FROM = 'e.durso7@gmail.com'
    pwd = 'SparkSpark88'
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body
    user = 'e.durso7@gmail.com'
    
    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        logger.info("email sent with following body: " + str(body))
        return 0
    except Exception as e:
        logger.error("Error when sending email: " + str(e))

    return 1


def try_to_send_email(body):
    counter = 0
    while True or counter == 5:
        res = send_email(['e.durso@live.com'], body)
        if res == 0:
            break

        logger.error("error in sending email, trying again in 5 seconds")
        time.sleep(5)
        counter +=1
    if counter == 5:
        logger.error("Email has not been sent")
