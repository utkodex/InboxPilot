from email_auto.email_sender import EmailSender


a=EmailSender()
recipient_email= "bizzboosterdata@gmail.com" 
subject= "Subject check" 
body= "This is a test email from the EmailSender2 class."

a.send_email(recipient_email, subject, body)