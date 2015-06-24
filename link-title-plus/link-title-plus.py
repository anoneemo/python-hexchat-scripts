from html.parser import HTMLParser
import glob
import os
import re
import requests
import threading
import hexchat
import urllib3
requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings()

__module_name__ = "Link Title Plus"
__module_author__ = "Anoneemo"
__module_version__ = "0.6"
__module_description__ = "Display website title when a link is posted in chat or, up to your choice, publicly announce it in channel"

# IMPORTANT: Scroll to line 62 to choose the channels the script will be allowed to announce the title on (optional)
# This is a fork of PDog's link-title.py script
#
# TODO: Merge py2/py3 branches <PDog>
# TODO: adding/removing channels live on hexchat through a command

events = ("Channel Message", "Channel Action",
          "Channel Msg Hilight", "Channel Action Hilight",
          "Private Message", "Private Message to Dialog",
          "Private Action", "Private Action to Dialog")

def find_yt_script():
    script_path = os.path.join(hexchat.get_info("configdir"),
                               "addons", "get-youtube-video-info.py")

    if glob.glob(script_path):
        return re.compile("https?://(?!(w{3}\.)?youtu\.?be(\.|/))")
    else:
        return re.compile("https?://")

def snarfer(html_doc):
    try:
        snarf = html_doc[html_doc.index("<title>")+7:html_doc.index("</title>")][:431]
    except ValueError:
        snarf = ""
    return snarf

def print_title(url, chan, nick, mode):
    try:
        r = requests.get(url, verify=False)
        if r.headers["content-type"].split("/")[0] == "text":
            html_doc = r.text
            r.close()
            title = snarfer(html_doc)
            title = HTMLParser().unescape(title)
            chanmodes = hexchat.find_context(channel=chan).get_info("modes")
            
            # WARNING: If you are on the same channel on two (or more) different networks,
            # the script could not work or have unexpected behaviour. 
            # The above case is not being handled. Beware.
            #
            # Select the channels on which the script will publicly print the title
            # by replacing firstchannel, secondchannel, third channel etc.
            # you can also delete them or add them but you have to maintain the same syntax
            # do not delete the apix ( ' ' )
            if chan == '#firstchannel' or chan == '#secondchannel' or chan == '#thirdchannel':
                # PRINT IN CHANNEL
                # WARNING: In case two or more people in the same channel are using this script,
		# deleting or commenting the line with URL in it is strongly suggested
                # (could lead to endless chain-reactions otherwise)
                #
                # If channel has colors disabled
                if "c" in chanmodes:
                    msg = u":: {0} " + \
                          u":: URL: {1} " + \
                          u"::"
                    msg = msg.format(title, url, nick, mode)      
                # If channel has colors enabled
                else:
                    msg = u"\002::\002\0034 {0} \003" + \
	                  u"\002:: URL:\002 \00318\037{1}\017 " + \
                          u"\002::\002"              
                    msg = msg.format(title, url, nick, mode)
                # Weird context and timing issues with threading, hence:
                hexchat.command("TIMER 0.1 DOAT {0} MSG {0} {1}".format(chan, msg))
            else:
                # PRINT LOCALLY
                msg = u"\n" + \
                       u"\0033\002::\003 TITLE:\002 \0034{0} \003\n" + \
                       u"\0033\002::\003 URL:\002 \00318\037{1}\017 \n" + \
                       u"\0033\002::\003 POSTED BY:\002 {3}{2} \n" + \
                       u"\n"
                msg = msg.format(title, url, nick, mode)
                # Weird context and timing issues with threading, hence:
                hexchat.command("TIMER 0.1 DOAT {0} ECHO {1}".format(chan, msg))
    except requests.exceptions.RequestException as e:
        print(e)

def event_cb(word, word_eol, userdata, attr):
    # ignore znc playback
    if attr.time:
        return
    
    word = [(word[i] if len(word) > i else "") for i in range(4)]
    chan = hexchat.get_info("channel")
    
    for w in word[1].split():
        stripped_word = hexchat.strip(w, -1, 3)
        
        if find_yt_script().match(stripped_word):
            url = stripped_word

            if url.endswith(","):
                url = url[:-1]
                
            threading.Thread(target=print_title, args=(url, chan, word[0], word[2])).start()

    return hexchat.EAT_NONE
            

for event in events:
    hexchat.hook_print_attrs(event, event_cb)

hexchat.prnt(__module_name__ + " version " + __module_version__ + " loaded")
