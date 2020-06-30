
# -*- coding: utf-8 -*-
import smtplib
from email.MIMEText import MIMEText
from email.Utils import formatdate


#def create_message(from_addr, to_addr, subject, body):
#    msg = MIMEText(body)
#    msg['Subject'] = subject
#    msg['From'] = from_addr
#    msg['To'] = ",".join( to_addr )
#    msg['Date'] = formatdate()
#    return msg

def create_message( from_addr, to_addr, subject, body):
    """ creates MIMEText object """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ",".join(to_addr)    # -- ココ<1>
    msg['Date'] = formatdate(localtime=True)
    return msg

def send_via_gmail(from_addr, to_addr, msg):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login('tama.vis.exp@gmail.com', 'cryogenic')
    s.sendmail(from_addr, [to_addr], msg.as_string())
    s.close()
    

def Test():
  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['y0419fujii@gmail.com']
  msg = create_message(from_addr, to_addr, 'Test', 'This is a test')
  send_via_gmail(from_addr, to_addr, msg)
#  send_via_gmail()

def Dmp():
  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['tseki928@gmail.com']
  msg = create_message(from_addr, to_addr, 'Oops...', 'Something happened. \nThe control mode is switched to the damping mode from the observation mode.')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['ayaka.shoda@nao.ac.jp']
  msg = create_message(from_addr, to_addr, 'Oops...', 'Something happened. \nThe control mode is switched to the damping mode from the observation mode.')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['y0419fujii@gmail.com']
  msg = create_message(from_addr, to_addr, 'Oops...', 'Something happened. \nThe control mode is switched to the damping mode from the observation mode.')
  send_via_gmail(from_addr, to_addr, msg)
#  send_via_gmail()

def LockToObs():
  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['tseki928@gmail.com']
  msg = create_message(from_addr, to_addr, 'Yey!', 'Succesfully switched to the observation mode. Congrats!')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['ayaka.shoda@nao.ac.jp']
  msg = create_message(from_addr, to_addr, 'Yey!', 'Succesfully switched to the observation mode. Congrats!')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['y0419fujii@gmail.com']
  msg = create_message(from_addr, to_addr, 'Yey!', 'Succesfully switched to the observation mode. Congrats!')
  send_via_gmail(from_addr, to_addr, msg)
#  send_via_gmail()

def Oplev():
  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['tseki928@gmail.com']
  msg = create_message(from_addr, to_addr, 'Help!', 'The oplev is out of range. Please actuate picomotors and help me! \nPlease do not forget to turn off NeedPico State after the adjustment.')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['ayaka.shoda@nao.ac.jp']
  msg = create_message(from_addr, to_addr, 'Help!', 'The oplev is out of range. Please actuate picomotors and help me! \nPlease do not forget to turn off NeedPico State after the adjustment.')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['y0419fujii@gmail.com']
  msg = create_message(from_addr, to_addr, 'Help!', 'The oplev is out of range. Please actuate picomotors and help me! \nPlease do not forget to turn off NeedPico State after the adjustment.')
  send_via_gmail(from_addr, to_addr, msg)
#  send_via_gmail()

def Emergency():
  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['tseki928@gmail.com']
  msg = create_message(from_addr, to_addr, 'Emergency!', 'The suspension system got into the emergency mode. The controll is all off now. \nPlease check the system!')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['ayaka.shoda@nao.ac.jp']
  msg = create_message(from_addr, to_addr, 'Emergency!', 'The suspension system got into the emergency mode. The controll is all off now. \nPlease check the system!')
  send_via_gmail(from_addr, to_addr, msg)

  from_addr = 'tama.vis.exp@gmail.com'
  to_addr = ['y0419fujii@gmail.com']
  msg = create_message(from_addr, to_addr, 'Emergency!', 'The suspension system got into the emergency mode. The controll is all off now. \nPlease check the system!')
  send_via_gmail(from_addr, to_addr, msg)

