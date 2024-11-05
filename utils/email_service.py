from flask_mail import Message

def send_password_reset(mail, email, reset_link):
    msg = Message("Password Reset Request", sender='korirjulius001@gmail.com', recipients=[email])
    msg.body = f"Click the following link to reset your password: {reset_link}"
    mail.send(msg)
