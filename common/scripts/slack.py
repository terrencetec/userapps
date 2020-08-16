#!/usr/bin/python3

import requests
import json


class PostMan():
    '''


    '''
    def __init__(self,token):
        self.token = token
                
    def chat_post(self,channel,text='no text'):
        '''
        Parameters
        ----------    
        text : `str`, optional
            text.
        
        Returns
        -------
        ans : ``
            ans
        '''
        url = "https://slack.com/api/chat.postMessage"
        headers = {'Content-Type': 'application/json'}
        params = {
            'token':self.token,
            'channel':channel,
            'text': text, 
            }
        ans = requests.post(url, params=params, headers=headers)
        return ans

    def files_upload(self,fname,text='no text',title='no title'):
        ''' 
        
        Parameters
        ----------    
        fname : `str`
            file name.
        text : `str`, optional
            text.
        title : `str`, optional
            title.

        Returns
        -------
        ans : ``
            ans
        '''
        url = "https://slack.com/api/files.upload"
        files = {'file': open(fname, 'rb')}
        param = {
            'token':self.token, 
            'channels':'test',
            'filename':fname,
            'initial_comment':text,
            'title':title,
            }
        ans = requests.post(url=url,params=param, files=files)
        return ans

# ------------------------------------------------------------------------------

def save_image(filename, image):
    '''
    '''
    with open(filename, "wb") as file:
        file.write(image)
            
def download_image_from_yamat(url,name,password):
    '''
    '''
    response = requests.get(url, timeout=100, auth=(name,password))
    if response.status_code != 200:
        raise RuntimeError("Request did not succeed.")
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        raise RuntimeError("This is not image file.")
    return response.content

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import argparse
    from _password import token
    parser = argparse.ArgumentParser(description='Slack Bot')
    parser.add_argument('channel', help='')
    parser.add_argument('text', help='')
    args = parser.parse_args()
    channel = args.channel
    text = args.text
    
    # Post messages
    postman = PostMan(token)
    ans = postman.chat_post(channel,text)
