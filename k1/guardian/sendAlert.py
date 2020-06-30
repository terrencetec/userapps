# -*- coding: utf-8 -*-
"""
DON'T USE ME (see klog11046)
  - sendmail                 -> kagralib.py
  - speak_aloud              -> kagralib.py
  - vis_watchdog_tripped     -> VISfunction.py
  - vis_pay_watchdog_tripped -> VISfunction.py

Send Guardian Alert to kagra.grd.alert@gmail.com
"""

import smtplib
from email.mime.text import MIMEText
import subprocess


def sendmail(sub, text, to=None):
    username, password = 'kagra.grd.alert@gmail.com','cryogenic'
    if to is None:
        to = username
        
    host= 'smtp.gmail.com'
    port = 465
    msg = MIMEText(text)
    msg['Subject'] = sub
    msg['From'] = username
    msg['To'] = to
    
    smtp = smtplib.SMTP_SSL(host, port)
    smtp.ehlo()
    smtp.login(username, password)
    smtp.mail(username)
    smtp.rcpt(to)
    smtp.data(msg.as_string())
    smtp.quit()
    return True

def speak_aloud(text):
    ### 2019-10-15  Update by YamaT 
    # subprocess.call(["/usr/bin/ssh", "controls@k1mon0", "/kagra/apps/text2speech/announce.sh", text])
    subprocess.call(["/usr/bin/ssh", "-i", "/home/controls/.ssh/id_ed25519_grd_speak", "controls@k1mon1", text])

def vis_watchdog_tripped(optic):
    '''
    Send alerts to people.
    '''
    #sendmail(sub=optic+' watchdog tripped!', text=optic+' watchdog has tripped. Please check the status.', to='yoichi.aso@nao.ac.jp')
    speak_aloud(optic+' watchdog has tripped')
    speak_aloud(optic+' watchdog has tripped')
    speak_aloud('Please check the status of '+optic)        

def vis_pay_watchdog_tripped(optic):
    '''
    Send alerts to people.
    '''
    #sendmail(sub=optic+' watchdog tripped!', text=optic+' watchdog has tripped. Please check the status.', to='yoichi.aso@nao.ac.jp')
    speak_aloud(optic+' payload watchdog has tripped')
    speak_aloud(optic+' payload watchdog has tripped')
    speak_aloud('Please check the status of '+optic)        

    
    

