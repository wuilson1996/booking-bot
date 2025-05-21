from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
import smtplib
import email.message
from email import encoders
from .models import *
from time import sleep
from .generate_sample_date import *
from datetime import timedelta
import logging

def send(Email_send, Password, Email_receiver, Affair, Text, Text_html, host, port):
    msg = MIMEMultipart()
    msg['From'] = Email_send				#correo para el logeo
    msg['To'] = Email_receiver				#correoa quien se envia
    msg['Subject'] = Affair					#asunto de el envio de correo
    msg.attach(MIMEText(Text, 'plain'))
    server=smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()
    server.login(msg['From'],Password)
    server.sendmail(msg['From'],msg['To'],msg.as_string())
    server.quit()
    generate_log(f"correo fue enviado con exito a {msg['To']}:", BotLog.HISTORY)
		
def send_notification(current_date, n):
	email_smtp = EmailSMTP.objects.all().last()
	email_send = MessageEmail.objects.filter(type_message=MessageEmail.NOTIFY).first()
	if email_smtp and email_send:
		for e in email_send.email.all():
			send(
                email_smtp.email,
                email_smtp.password,
                e.email,
                email_send.asunto.replace("{date}", generate_date_with_month_time(str(current_date)).split(" ")[0]).replace("{n}", str(n)),
                email_send.message.replace("{date}", generate_date_with_month_time(str(current_date)).split(" ")[0]).replace("{n}", str(n)),
                "",
                email_smtp.host,
                email_smtp.port
            )
	else:
		generate_log(f"Configure: EmailSMTP y MessageEmail", BotLog.HISTORY)
	
def notification_programer():
    _date_from = now()
    logging.info(f"[-] Ejecutando notificacion: {str(_date_from)}")
    occupancys = []
    for p in ProcessActive.objects.all():
        if p.occupancy not in occupancys:
            occupancys.append(p.occupancy)
    for i in range(180):
        totalFeria = 0
        for ocp in occupancys:
            try:
                avail_sf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date())).last()
                avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                    type_avail = int(ocp),
                    avail_suites_feria = avail_sf
                ).last()
                if avail_sf_cant:
                    totalFeria += avail_sf_cant.avail
                    if int(ocp) == 2:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 1,
                            avail_suites_feria = avail_sf
                        ).last()
                        totalFeria += avail_sf_cant.avail
                else:
                    if int(ocp) == 5:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 4,
                            avail_suites_feria = avail_sf
                        ).last()
                        totalFeria += avail_sf_cant.avail if avail_sf_cant else 0
            except Exception as e:
                generate_log(f"Error check notifications: {str(e)}", BotLog.HISTORY)
                logging.info(f"[-] Error check notifications: {str(e)}")

        try:
            avail_with_date = AvailWithDate.objects.filter(date_from=str(_date_from.date())).first()
            if avail_with_date:
                if avail_with_date.avail != "":
                    totalFeria -= int(avail_with_date.avail)
                    if i < 60:
                        if totalFeria <= -3:
                            send_notification(str(_date_from), totalFeria)
                    else:
                        if totalFeria <= -2:
                            send_notification(str(_date_from), totalFeria)
        except Exception as e:
            generate_log(f"Error check2 notifications: {str(e)}", BotLog.HISTORY)
            logging.info(f"[-] Error check2 notifications: {str(e)}")
        sleep(5)
        _date_from += timedelta(days=1)