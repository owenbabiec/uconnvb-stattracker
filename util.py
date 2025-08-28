import smtplib
import os
from email.message import EmailMessage

def send_email_with_attachment(sender_email, sender_password, recipients, subject, body, attachments=None):
    """
    Send an email via Gmail with optional file attachments.
    
    :param sender_email: Gmail address of the sender
    :param sender_password: Gmail App Password (NOT regular password)
    :param recipient_email: Email address of the recipient
    :param subject: Subject of the email
    :param body: Body text of the email
    :param attachments: List of file paths to attach (default None)
    """
    try:
        if isinstance(recipients, str):
            recipients = [recipients]


        # Create email message
        msg = EmailMessage()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        msg.set_content(body)
        
        # Add attachments if any
        if attachments:
            for file_path in attachments:
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(file_path)
                    msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                else:
                    print(f"Warning: File {file_path} not found, skipping attachment.")
        
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        
        print(f"✅ Email sent successfully to {len(recipients)} recipients!")
    
    except Exception as e:
        print(f"❌ Error sending email: {e}")


if __name__ == '__main__':
    send_email_with_attachment(
        sender_email="owenbabiec@gmail.com",
        sender_password="wmxdajqjjexvopxh",
        recipient_email="owen.babiec@uconn.edu",
        subject="Test email send",
        body="testing",
        attachments=["C:/Users/OwenB/OneDrive/Documents/Volleyball/uconnvb-stattracker/data.csv"]
    )