#DTSkypeBot

Little piece of python code to make Skype API breakage little bit softy. Instead of API usage this bot parses updates in Skype DB and create new messages by Skype UI clicking. Currently supports only group chats (direct conversations haven't /get blob command and direct messaging through contact search still not implemented)

##Requirements
###Software
  - Linux desktop distro (currently tested only in Ubuntu 12.04, i dunno about status on any other distro)
  - Beanstalkd daemon
  - Skype for Linux

###Libraries
   - Werkzeug
   - urllib2 (mostly for message parsers)
   - xpresser
   - sqlite3
   - pprint (for debug only, can be dropped actually)

##Install
**NOTE!** Install process described only for Ubuntu 12.04 and image resources combined only for this distro. If you want to get it working on another distro - please fix image resources.

1. Install all required libraries and software (including git submodules)
2. Copy config.sample.py to config.py and resources/chats.sample.db to resources/chats.db
3. Fix config to fit your test skype account
4. Check that Skype launch icon placed in Unity launch bar.
5. start terminal and run module \__main\__.py file

```sh
$ cd dtskypebot
$ python __main__.py
```

##Chats
During startup skypebot will launch something like REST API on host/port defined in config.py for chats management purposes and will launch skype instance for messaging. So, skypebot must be started only in graphical terminal (inside X)

Before serving requests from chats any chat must be registred inside skypebot db. To do this you need add your account to the target char with SPEAKER role. After this type
```
/get blob
```
in target chat. You will recieve something like this:
```
blob=6an6wp2aSQ5gW9UU2bNQgH48UUQ4GGkyZ9VIZ8uNskdaHLvqoUYswhm6Q7tPjVaqFOloplYzeQuvVIuOhjTUTjRym2h4RNknavVWpp8LbFFAwskJnQTf9C
```
Copy this string and with curl or any other request tool execute /chat_registration command:
```
curl 'http://<api_http_host>:<api_http_port>/chat_registration?blob=6an6wp2aSQ5gW9UU2bNQgH48UUQ4GGkyZ9VIZ8uNskdaHLvqoUYswhm6Q7tPjVaqFOloplYzeQuvVIuOhjTUTjRym2h4RNknavVWpp8LbFFAwskJnQTf9C'
```
After few moments message about registration will be visible in terminal and you will be able to test your bot with simple "echo" command

##Messages parsing
Go and check messages.py. Every message parser curently just expression match test, that runs through list of available expressions and fire up first occurance of True match. Simple and effective.

For any other purposes check rest.py for direct chat messaging through API, bot shutdown and chat drop routines.

Hacking and extending are welcome.

##Disclaimer
This is just a proof of concept. Testing and commit requests will be appreciated, but don't expect too much from.
