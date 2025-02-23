import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config

class EmailService:
    def __init__(self):
        self.from_email = Config.EMAIL_ADDRESS
        self.from_password = Config.EMAIL_PASSWORD
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT

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
    
    def send_company_approved_notification(self, to_email):
        subject = "Company Registration Approved"
        html_content = self._get_company_approved_template()
        return self.send_email(to_email, subject, html_content)
    
    def _get_company_approved_template(self):
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .cta-button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 12px;
                    color: #888;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Your Company Registration Has Been Approved</h2>
                <p>Your company registration has been approved. You can now log in to your account.</p>
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Please create your Ethereum account if you haven't done so already. For instructions, please visit 
                        <a href="https://metamask.io" target="_blank">MetaMask</a>.
                    </li>
                    <li>After creating your MetaMask account, make sure to configure it to use the correct network.
                        In our case, you must set your network to: <strong>localhost:8545</strong>.
                    </li>
                    <li>Once your account is correctly configured, go to your notifications area on our website and click the button next to the company approval notification to verify your public address.</li>
                </ul>
                <a href="http://127.0.0.1:5000/login?next=/notifications" class="cta-button" target="_blank">Go to Notifications</a>
                <p class="footer">If you have any questions, please contact our support team.</p>
            </div>
        </body>
        </html>
        """





        
    '''
    def send_eth_credentials(self, receiver_email, eth_credentials, company_name):
        subject = "Your Company's Ethereum Account Credentials"
        html_content = self._get_eth_credentials_template(eth_credentials, company_name)
        return self.send_email(receiver_email, subject, html_content)

        
    def _get_eth_credentials_template(self, eth_credentials, company_name):
        return f"""
        <h2>Ethereum Account Created for {company_name}</h2>
        <p>Your company has been approved and an Ethereum account has been created:</p>
        <p><strong>Address:</strong> {eth_credentials['address']}</p>
        <p><strong>Private Key:</strong> {eth_credentials['private_key']}</p>
        <p><strong>Important:</strong></p>
        <ul>
            <li>Save these credentials securely</li>
            <li>Import this account to MetaMask</li>
            <li>Never share your private key</li>
            <li>We don't store your private key</li>
        </ul>
        """
    '''
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
    
    def _get_contact_email_template(self, name, email, message):
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    padding: 20px;
                }}
                h2 {{
                    color: #28a745;
                    text-align: center;
                }}
                p {{
                    line-height: 1.5;
                    font-size: 14px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #888888;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Nuovo messaggio da Contatto</h2>
                <p><strong>Nome:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Messaggio:</strong></p>
                <p>{message}</p>
                <div class="footer">
                    Sustainable Food Supply Chain ©
                </div>
            </div>
        </body>
        </html>
        """
    

    def send_contact_email(self, name, email, message):
        subject = f"Nuovo messaggio da {name}"
        html_content = self._get_contact_email_template(name, email, message)
        # Scegli l'indirizzo di destinazione (ad esempio, l'indirizzo dell'admin)
        return self.send_email(to_email=self.from_email, subject=subject, html_content=html_content)
    
    def send_admin_notification(self, user_info, company_data):
        subject = "New Company Registration Request"
        html_content = self._get_admin_notification_template(user_info, company_data)
        return self.send_email(to_email=self.from_email, subject=subject, html_content=html_content)
    
    def _get_admin_notification_template(self, user_info, company_data):
        # Create HTML email content
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2E7D32;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 0 0 5px 5px;
                }}
                .info-label {{
                    font-weight: bold;
                    color: #2E7D32;
                }}
                .divider {{
                    border-top: 1px solid #ddd;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Company Registration Request</h2>
                </div>
                <div class="content">
                    <p><span class="info-label">Requested by:</span> {user_info['name']} {user_info['surname']} ({user_info['email']})</p>
                    <div class="divider"></div>
                    <h3>Company Details:</h3>
                    <p><span class="info-label">Company Name:</span> {company_data['company_name']}</p>
                    <p><span class="info-label">Industry:</span> {company_data['company_industry']}</p>
                    <p><span class="info-label">Email:</span> {company_data['company_email']}</p>
                    <p><span class="info-label">Phone:</span> {company_data['company_phone_number']}</p>
                    <p><span class="info-label">Location:</span> {company_data['company_address']}, {company_data['company_city']}, {company_data['company_country']}</p>
                    <p><span class="info-label">Website:</span> {company_data.get('company_website', 'Not provided')}</p>
                    <div class="divider"></div>
                    <p><span class="info-label">Description:</span><br>{company_data['company_description']}</p>
                </div>
            </div>
        </body>
        </html>
        """

