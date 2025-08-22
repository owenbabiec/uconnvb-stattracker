import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def send_mail(send_from, send_to, subject, text, files=None,
              server="smtp-mail.outlook.com", port=587,
              username=None, password=None, use_tls=True):
    
    assert isinstance(send_to, list), "send_to must be a list of email addresses"

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(fil.read(), Name=basename(f))
        part['Content-Disposition'] = f'attachment; filename="{basename(f)}"'
        msg.attach(part)

    try:
        smtp = smtplib.SMTP(server, port)
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if username and password:
            smtp.login(username, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


if __name__ == '__main__':
    send_mail(send_from="test@example.com", send_to=["recipient@example.com"], subject="Test", text="Hello!", server="localhost", port=1025)

