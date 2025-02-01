import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self):
        self.from_email = "ssb2024.2025@gmail.com"
        self.from_password = "vpon ryms zupv owmt"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, to_email, subject, html_content):
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_email, self.from_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_verification_code(self, to_email, code):
        subject = "Email Verification"
        html_content = self._get_verification_email_template(code)
        return self.send_email(to_email, subject, html_content)

    def send_password_reset(self, to_email, reset_link):
        subject = "Password Reset Request"
        html_content = self._get_password_reset_template(reset_link)
        return self.send_email(to_email, subject, html_content)

    def _get_verification_email_template(self, code):
        return f"""
        <html>
        <head>
            <style>
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .verification-code {{
                    background-color: #ffffff;
                    border: 1px solid #e1e1e1;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .code {{
                    font-size: 32px;
                    letter-spacing: 5px;
                    color: #007bff;
                    font-weight: bold;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="verification-code">
                    <h2>Verification Code</h2>
                    <p>Your verification code is:</p>
                    <div class="code">{code}</div>
                    <p>This code will expire in 2 minutes.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_password_reset_template(self, reset_link):
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9f9f9;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px;">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. If you didn't make this request, please ignore this email.</p>
                <p>Click the button below to reset your password (valid for 10 minutes):</p>
                <p>
                    <a href="{reset_link}" 
                       target="_self"
                       style="display: inline-block; 
                              background-color: #007bff; 
                              color: white; 
                              padding: 10px 20px; 
                              text-decoration: none; 
                              border-radius: 5px;">
                        Reset Password
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
