import smtplib

FromEmail 	= "no-reply@furaffinity.net"
SmtpServer 	= "localhost"	# Asuming a smtp server is running localy OR remotely and accepts
							# unauthenticated connectons from the web frontend.

def SendVerificationEmail(ToEmail, ValidationUrl):
	msg 	= "Thank you for registering with ferrox\nPlease click or copy/pase the following url to verify your account:\n" + ValidationUrl
	Subject = "Ferrox verification"
	headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n" % (FromEmail, ToEmail, Subject)
	server = smtplib.SMTP("localhost")
	server.sendmail(FromEmail, ToEmail, headers + msg)
	server.quit()