# Copyright (c) 2000-2003 Gustavo Niemeyer <niemeyer@conectiva.com>
#
# This file is part of pybot.
# 
# pybot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# pybot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with pybot; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from pybot.locals import *
import thread
import signal
import time
import math
import os

HELP = """
The "eval <expr>" command allows you to evaluate expressions
using the python evaluation mechanism. Use the command "show
eval keywords" to check which 'keywords' are available in
the evaluation context.
""","""
This command depends on the "eval" permission. Notice that a
malicious user is able to hang me using this command, so no
untrusted users should have this permission.
"""

PERM_EVAL = """
This permission allows users to use the "eval" command. For more
information send me "help eval".
"""

TIMEOUT = 3

MAXCHARS = 300

TRANSTABLE = '                                 !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'

class Eval:
    def __init__(self):
        hooks.register("Message", self.message)
        self.dict = {}
        self.dict["__builtins__"] = {}
        self.dict.update(math.__dict__)
        del self.dict["__doc__"]
        del self.dict["__file__"]
        del self.dict["__name__"]
        self.dict["False"] = False
        self.dict["True"] = True
        self.dict["abs"] = abs
        self.dict["bool"] = bool
        self.dict["chr"] = chr
        self.dict["cmp"] = cmp
        self.dict["coerce"] = coerce
        self.dict["complex"] = complex
        self.dict["dict"] = dict
        self.dict["divmod"] = divmod
        self.dict["filter"] = filter
        self.dict["float"] = float
        self.dict["hash"] = hash
        self.dict["hex"] = hex
        self.dict["id"] = id
        self.dict["int"] = int
        self.dict["len"] = len
        self.dict["list"] = list
        self.dict["long"] = long
        self.dict["map"] = map
        self.dict["max"] = max
        self.dict["min"] = min
        self.dict["oct"] = oct
        self.dict["ord"] = ord
        self.dict["pow"] = pow
        self.dict["range"] = range
        self.dict["reduce"] = reduce
        self.dict["repr"] = repr
        self.dict["round"] = round
        self.dict["str"] = round
        self.dict["tuple"] = tuple
        self.dict["unichr"] = unichr
        self.dict["unicode"] = unicode
        self.dict["xrange"] = range
        self.dict["zip"] = zip

        # eval <expr>
        self.re1 = regexp(r"eval (?P<expr>.*?)")

        # show eval keywords
        self.re2 = regexp(r"show eval keywords?")

        # eval[uate|uation]
        mm.register_help("eval(?:uate|uation)?", HELP, "eval")

        mm.register_perm("eval", PERM_EVAL)
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm("eval")

    def fork_eval(self, expr):
        try:
            code = compile(expr, "<string>", "eval")
        except:
            return None
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            fw = os.fdopen(w, "w")
            try:
                fw.write(str(eval(code, self.dict)))
            except:
                pass
            fw.close()
            os._exit(1)
        os.close(w)
        fr = os.fdopen(r, "r")
        answer = None
        timeout = TIMEOUT
        while 1:
            try:
                _pid, status = os.waitpid(pid, os.WNOHANG)
            except os.error:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
                try:
                    os.waitpid(pid, os.WNOHANG)
                except os.error:
                    pass
                break
            if pid == _pid:
                answer = fr.read()
                break
            else:
                timeout -= 1
                if not timeout:
                    answer = ["Couldn't wait for your answer.",
                              "Processing your answer took too long.",
                              "I'm in a hurry and can't wait for "
                              "your answer."]
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.5)
                    try:
                        os.waitpid(pid, os.WNOHANG)
                    except os.error:
                        pass
                    break
                time.sleep(1)
        return answer

    def eval(self, msg, expr):
        answer = self.fork_eval(expr)
        if not answer:
            msg.answer("%:", ["Can't evaluate this",
                              "There's something wrong with this "
                              "expression"], [".", "!"])
        elif len(answer) > MAXCHARS:
            msg.answer("%:", "Your answer is too long", [".", "!"])
        else:
            msg.answer("%:", answer.translate(TRANSTABLE))

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "eval"):
                thread.start_new_thread(self.eval, (msg, m.group("expr")))
            else:
                msg.answer("%:", ["Nope", "Oops"], [".", "!"],
                                 ["You don't have this power",
                                  "You can't do this",
                                  "You're not allowed to do this"],
                                 [".", "!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "eval"):
                keywords = self.dict.keys()
                keywords.sort()
                msg.answer("%:", "The following keywords are available:",
                           ", ".join(keywords))
            else:
                msg.answer("%:", ["Nope", "Oops"], [".", "!"],
                                 ["You don't have this power",
                                  "You can't do this",
                                  "You're not allowed to do this"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Eval()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
