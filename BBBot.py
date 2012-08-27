#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#       
#       Copyright (c) 2012 Nikola Kovacevic <nikolak@outlook.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, ip_numstr_to_quad, is_channel
import bblib as brba
from time import sleep

class BBBot(SingleServerIRCBot):
    stop = False

    def __init__(self, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.initial_channels = brba.initialch
        self.user_req_times = dict()
        self.banned_users  = brba.banned
        self.admin    = brba.admin
        self.authorized= brba.auth
        self.ircpass   = brba.password
        self.enabled = True
        self.cc='#'+brba.cc
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.privmsg('NickServ', 'IDENTIFY '+self.ircpass.strip())#strip needed?
        sleep(2) 
        for ch in self.initial_channels:
            c.join('#' + ch)
#        if we want to ghost originally intented nickname
#        if self.nickpass and c.get_nickname() != self.nickname:
#            c.privmsg('NickServ', 'GHOST %s %s' % (nickname, self.ircpass))


    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments()[0])

    def on_pubmsg(self, c, e):
        self.do_command(e, e.arguments()[0])
        return

    def on_dccmsg(self, c, e):
        c.privmsg("You said: " + e.arguments()[0])
            
    def on_dccchat(self, c, e):
        if len(e.arguments()) != 2:
            return
        args = e.arguments()[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)
        

    def do_command(self, e, cmd):
        nick = nm_to_n(e.source())
        c = self.connection
        t = e.target()
        if not is_channel(t):
            t = nick

        if nick.lower() in self.banned_users:
            return

        elif not self.enabled and not cmd.startswith('.turn'):
            return
        
            
        elif cmd=='botinfo':
            if nick.lower() in self.admin:
                c.privmsg(t,'Initial channels:')
                c.privmsg(t, self.initial_channels)
                sleep(2)
                c.privmsg(t, 'Banned users:')
                c.privmsg(t, self.banned_users)
                sleep(2)
                c.privmsg(t, 'Bot admins:')
                c.privmsg(t, self.admin)
                sleep(2)
                c.privmsg(t, 'Bot authorized users')
                c.privmsg(t, self.authorized)

        elif cmd.startswith('.turn'):
            option = cmd.replace('.turn', '').strip()
            if nick.lower() in self.admin:
                if option.lower()=='off':
                    self.enabled=False
                    c.privmsg(t,'Bot is now disabled.')
                if option.lower()=='on':
                    self.enabled=True
                    c.privmsg(t,'Bot is now enabled.')

        elif cmd.startswith('.ban'):
            user = cmd.replace('.ban', '').strip()
            if nick.lower() in self.authorized:
                if user in self.banned_users:
                    c.privmsg(t,user+' is already banned')
                else:
                    self.banned_users.append(user)
                    c.privmsg(t, user+' is banned from using BBBot.')
    

        elif cmd.startswith('.unban'):
            user = cmd.replace('.unban', '').strip()
            if nick.lower() in self.authorized:
                if user in self.banned_users:
                    self.banned_users.remove(user)
                    c.privmsg(t, user+' is now allowed to use BBBot.')
                else:
                    c.privmsg(t,user +' is not banned.')

        elif cmd.startswith('.ath'):
            user = cmd.replace('.ath', '').strip()
            if nick.lower() in self.admin:
                self.authorized.append(user)
                c.privmsg(t, user+' is added to list of authoritized users.')
        

        elif cmd.startswith('.rmath'):
            user = cmd.replace('.rmath', '').strip()
            if nick.lower() in self.admin:
                if user in self.admin:
                    c.privmsg(t, 'It\'s impossible to remove'+user)
                    return
                if user in self.authorized:
                    self.authorized.remove(user)
                    c.privmsg(t, user+' is removed from list of authoritized users.')
                else:
                    c.privmsg(t,user+' is not on the list')

        elif cmd.startswith('.join'):
            ch = cmd.replace('.join', '').strip()
            if nick.lower() in self.admin:
                c.join('#' + ch)
                
        elif cmd.startswith('.quit'):
            ch = cmd.replace('.quit', '').strip()
            if nick.lower() in self.admin:
                c.part('#' + ch + ' quitting')
                
    
        elif cmd.startswith('.add'):
            if nick.lower() in self.authorized:
                try:
                    what=cmd.split()[1].strip()
                    value=cmd.replace('.add','').replace(what,'').strip()
                except IndexError:
                    c.privmsg(t, 'Error. Proper usage .add <stream/download> <link>')
                c.privmsg(t, brba.addremove('add',what,value))
            else:
                c.privmsg(t,nick+': You\'re not allowed to add links.')

        elif cmd.startswith('.remove'):
            if nick.lower() in self.authorized:
                try:
                    what=cmd.split()[1].strip()
                    value=cmd.replace('.remove','').replace(what,'').strip()
                except IndexError:
                    c.privmsg(t, 'Error. Proper usage .remove <stream/download> <link>')
                if what=='stream' and value=='clear_all':
                    c.privmsg(t,'Removing all links, use following text to restore it if necessary!')
                    c.privmsg(t, brba.stream())
                c.privmsg(t, brba.addremove('remove',what,value))
            else:
                c.privmsg(t,nick+': You\'re not allowed to remove links.')

        elif cmd.startswith('.update'):
            if nick.lower() in self.authorized:
                try:
                    url=cmd.replace('.update','')
                except IndexError:
                    c.privmsg(t, 'index error')
                c.privmsg(t,brba.updatethread(url))
                
        elif cmd.startswith('!i'):
            if not is_channel(t): 
                return
            c.privmsg(t, brba.info())

        elif cmd.startswith('!download'):
            if not is_channel(t): 
                return
            c.privmsg(t, brba.download())
            
        elif cmd.startswith('!stream'):
            if not is_channel(t): 
                return
            c.privmsg(t, brba.stream())
            
        elif cmd.startswith('!suggest'):
            if not is_channel(t): 
                return
            suggestion=cmd.replace('!suggest','')
            c.privmsg(self.cc, '[link suggestion] : '+nick+' : '+suggestion)
            
        elif cmd == '.help':
                if nick.lower() in self.admin:
                    helpStrings = [
                                   '.turn <on/off> | turns bot on or off (ignores all commands)',
                                   '.ath <username> | adds <username> to authorized list allowing them to use .<add/remove> and .<update>',
                                   '.rmath <username> | removes <username> from authorized list',
                                   '.join <channel> | bot will join #<channel> be sure to write the channel name without # otherwise the bot will join ##<channel>',
                                   '.quit <channel> | bot will part from <channel> be sure to use <chanell> without #',
                                   '.add <stream or download> <link> | adds link to stream or download list. <link> can contain multiple words and spaces',
                                   '.remove <stream/download> <link> | Opposite of command above. Note: if you added link with multiple words this command can\'t remove only certain words. You have to enter same text as when it was added',
                                   '.update <text> | this adds text after "Latest reddit discussion thread" in !i command.',
                                   '.add sstream <link> | this will shorten <link> using goog.gl and add it to stream list'
                                   ]
                elif nick.lower() in self.authorized:
                    helpStrings = [
                                   '.add <stream or download> <link> | adds link to stream or download list. <link> can contain multiple words and spaces',
                                   '.remove <stream/download> <link> | Opposite of command above. Note: if you added link with multiple words this command can\'t remove only certain words. You have to enter same text as when it was added',
                                   '.update <text> | this adds text after "Latest reddit discussion thread" in !i command.',
                                   '.add sstream <link> | this will shorten <link> using goog.gl and add it to stream list'
                                   ]
                else: 
                    helpStrings = [
                                    '!stream | shows current list of streams',
                                    '!download | shows current list of download links',
                                    '!i | shows info about show, time untill next episode, next episode name, latest reddit discussion',
                                    '!suggest <link> | suggest link to be added to !stream list of streams'
                                    ]
                for string in helpStrings:
                    c.privmsg(nick, string)


def main():
    server = 'irc.your_server.com'
    port = 6667
    nickname = 'BBBot'
    
    bot = BBBot(nickname, server, port)
    while not bot.stop:
        try:
            bot.start()
        except:
            return 0
    
if __name__ == "__main__":
    main()
 