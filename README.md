# What is pybot?

Pybot is a full featured IRC bot written in Python. It was originally developed to integrate many sources of information into IRC channels, and has since then evolved into a full featured bot.

PyBot was originally written by Gustavo Niemeyer. Home page of the original project: http://labix.org/pybot

# End user features

* easy administration through local console;
* may join multiple servers and multiple channels at once
  (implemented without threads);
* remembers last state, even if killed;
* full online control (just talk to him);
* load, reload and unload modules at runtime;
* flexible user registry, allowing automatic identification
  and manual identification under different nicks;
* very flexible permission system;
* full online help;
* auto recover from network errors;
* lots of additional functionalities through available modules;
* even basic functionality is implemented using modules;
* random answers, to humanify the bot a little bit;
* persistence implemented with transparent pickling and sqlite database;

# Developer features

* nice API for inter-module communication;
* object oriented;
* hook system for multidispatch with priority setting;
* message priority;
* example modules;
* user registry allows pluggable meta-data;

# Requirements

Pybot requires the [sqlite](http://sqlite.org) SQL database library,
and its [python module](http://pysqlite.sf.net).

# Download

At this moment PyBot is not versioned, and you can only 

Originally, PyBot was hosted on SourceForge in CVS repository:

http://sourceforge.net/projects/pybot

# Standard modules

(*) modules which are part of the basic infrastructure, loaded without user intervention

## modulecontrol (*)

Takes care of loading, reloading, and unloading modules dynamically and when pybot starts up.

## servercontrol (*)

Basic server control. Takes care of initial setup as well as joining and leaving channels on the fly.

## permissions (*)

Provides access control for pybot. Most of the other modules access exported functions from this module to verify if users have given privilege.

## userdata (*)

Provides some general user data storage, and exports some functions providing this information for other modules.

## help (*)

Provides online help system.

## options (*)

Provides user access to the global options instance. Also takes care of maintaining persistent variables between runs, if any exists (pickle).

## timer (*)

Provides an API allowing modules to be called once in a while.

## pong (*)

Answers ping requests, and pings servers from time to time.

## log

Allows searching in logs, and checking what was the last time the bot has seen somebody.

## rss

Generic RSS module. It's based on Mark Pilgrim's "ultra liberal" parser, and allows one to send news from any RSS feed to any user/channel/server.

## ignore

Allows ignoring given users/channels/servers.

## uptime

Maintains and shows pybot uptime.

## infopack

Uses external databases to add knowledge to the bot. Each database may add its own trigger, default messages (when the trigger was sucessful, but no keys were found), help, etc. Available infopacks are acronyms (extracted from GNU vera), tcp/udp ports, and airports (both extracted from infobot).

## messages

Allow users to leave messages to named users. These messages will be sent when the named user gets into some channel or talks (usefull if he was just away).

## forward

Forwards messages between choosen channels and/or servers.

## notes

Allows maintaining general shared information about given topics.

## eval

Evaluates python expressions in protected environment.

## repeat

Repeat given message in selected server/channel once, or in given intervals.

## freshmeat

Check for new freshmeat releases and post them into selected channels/servers.

## plock

Provide simple colaborative locking mechanism (based on a system we used to have in Conectiva, that's why it's filesystem based, and have some specific requirements).

## social

Socialize pybot a little bit.

## randnum

Simple random number generator.

## xmlrpc

Provides an API to easily export functions from any module through the XMLRPC protocol, including basic authentication information. Also implements a sendmsg() remote method, allowing external services to send messages and notices using pybot (demo client included);

## remoteinfo

Allows pybot to acquire knowledge from remote URLs in a very flexible way.

## weather

Module which retrieves weather information from any station available at the NOAA.
