from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks
from .utils.chat_formatting import pagify, box
import os
import re
import shlex

class FlipCommands:
    """Custom commands

    Creates commands used to display text"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/flipcom/commands.json"
        self.c_commands = dataIO.load_json(self.file_path)

    @commands.group(aliases=["flipc"], pass_context=True, no_pm=True)
    async def flipcom(self, ctx):
        """Custom commands management"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @flipcom.command(name="add", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def flipc_add(self, ctx, command : str, *, text):
        """Adds a custom command

        Example:
        [p]flipcom add yourcommand Text you want

        CCs can be enhanced with arguments:
        https://twentysix26.github.io/Red-Docs/red_guide_command_args/
        """
        server = ctx.message.server
        command = command.lower()
        if command in self.bot.commands:
            await self.bot.say("That command is already a standard command.")
            return
        if server.id not in self.c_commands:
            self.c_commands[server.id] = {}
        cmdlist = self.c_commands[server.id]
        if command not in cmdlist:
            cmdlist[command] = text
            self.c_commands[server.id] = cmdlist
            dataIO.save_json(self.file_path, self.c_commands)
            await self.bot.say("Custom command successfully added.")
        else:
            await self.bot.say("This command already exists. Use "
                               "`{}flipcom edit` to edit it."
                               "".format(ctx.prefix))

    @flipcom.command(name="edit", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def flipc_edit(self, ctx, command : str, *, text):
        """Edits a custom command

        Example:
        [p]flipcom edit yourcommand Text you want
        """
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist[command] = text
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("Custom command successfully edited.")
            else:
                await self.bot.say("That command doesn't exist. Use "
                                   "`{}flipcom add` to add it."
                                   "".format(ctx.prefix))
        else:
            await self.bot.say("There are no custom commands in this server."
                               " Use `{}flipcom add` to start adding some."
                               "".format(ctx.prefix))

    @flipcom.command(name="delete", pass_context=True)
    @checks.mod_or_permissions(administrator=True)
    async def flipc_delete(self, ctx, command : str):
        """Deletes a custom command

        Example:
        [p]flipcom delete yourcommand"""
        server = ctx.message.server
        command = command.lower()
        if server.id in self.c_commands:
            cmdlist = self.c_commands[server.id]
            if command in cmdlist:
                cmdlist.pop(command, None)
                self.c_commands[server.id] = cmdlist
                dataIO.save_json(self.file_path, self.c_commands)
                await self.bot.say("Custom command successfully deleted.")
            else:
                await self.bot.say("That command doesn't exist.")
        else:
            await self.bot.say("There are no custom commands in this server."
                               " Use `{}flipcom add` to start adding some."
                               "".format(ctx.prefix))

    @flipcom.command(name="list", pass_context=True)
    async def flipc_list(self, ctx):
        """Shows custom commands list"""
        server = ctx.message.server
        commands = self.c_commands.get(server.id, {})

        if not commands:
            await self.bot.say("There are no custom commands in this server."
                               " Use `{}flipcom add` to start adding some."
                               "".format(ctx.prefix))
            return

        commands = ", ".join([ctx.prefix + c for c in sorted(commands)])
        commands = "Custom commands:\n\n" + commands

        if len(commands) < 1500:
            await self.bot.say(box(commands))
        else:
            for page in pagify(commands, delims=[" ", "\n"]):
                await self.bot.whisper(box(page))

    async def on_message(self, message):
        if len(message.content) < 2 or message.channel.is_private:
            return

        server = message.server
        prefix = self.get_prefix(message)

        if not prefix:
            return

        if server.id in self.c_commands and self.bot.user_allowed(message):
            cmdlist = self.c_commands[server.id]
            cmd = self.get_command(message)
            if cmd in cmdlist:
                cmd = cmdlist[cmd]
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)
            elif cmd.lower() in cmdlist:
                cmd = self.format_cc(cmd, message)
                await self.bot.send_message(message.channel, cmd)
                cmd = cmdlist[cmd.lower()]

    def get_prefix(self, message):
        for p in self.bot.settings.get_prefixes(message.server):
            if message.content.startswith(p):
                return p
        return False
		
    def get_command(self, message):
        prefix = self.get_prefix(message)
        return message.content.split(" ")[prefix.count(' ')][len(prefix):]

    def format_cc(self, command, message):
        results = re.findall("\{([^}]+)\}", command)
        for result in results:
            param = self.transform_parameter(result, message)
            command = command.replace("{" + result + "}", param)
        return command

    def is_int(self, s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
        
    def transform_parameter(self, result, message):
        """
        For security reasons only specific objects are allowed
        Internals are ignored
        """
        raw_result = "{" + result + "}"
        
        if self.is_int(result):
            command = self.get_prefix(message) + self.get_command(message)
            
            message_content = message.content[len(command)+1:]
            message_mentions_re = re.findall("<@!?&?[0-9]*>", message_content)
            
            message_mentioned = message.mentions
            message_mentioned_str = [mentioned.mention for mentioned in message_mentioned]
            
            message_content_split = shlex.split(message_content)
            
            for mentioned in message_mentions_re:
                if mentioned in message_mentioned_str:
                    user = message_mentioned[message_mentioned_str.index(mentioned)]
                    user_name = user.nick
                    
                    if user_name == None:
                        user_name = user.name
                        
                    message_content_split = [message.replace(mentioned, user_name) for message in message_content_split]
            
            message_content_split = [message.replace("@", "") for message in message_content_split]
        
            try:
                return message_content_split[int(result)]
            except IndexError:
                return ""
        
        if result == "content":
            command = self.get_prefix(message) + self.get_command(message)
            
            message_content = message.content[len(command)+1:]
            message_mentions_re = re.findall("<@!?&?[0-9]*>", message_content)
            
            message_mentioned = message.mentions
            message_mentioned_str = [mentioned.mention for mentioned in message_mentioned]
            
            for mentioned in message_mentions_re:
                if mentioned in message_mentioned_str:
                    user = message_mentioned[message_mentioned_str.index(mentioned)]
                    user_name = user.nick
                    
                    if user_name == None:
                        user_name = user.name
                        
                    message_content = message_content.replace(mentioned, user_name)
            
            message_content = message_content.replace("@", "")
            
            return message_content

        objects = {
            "message" : message,
            "author"  : message.author,
            "channel" : message.channel,
            "server"  : message.server,
        }
        if result in objects:
            return str(objects[result])
        try:
            first, second = result.split(".")
        except ValueError:
            return raw_result
        if first in objects and not second.startswith("_"):
            first = objects[first]
        else:
            return raw_result
        return str(getattr(first, second, raw_result))


def check_folders():
    if not os.path.exists("data/flipcom"):
        print("Creating data/flipcom folder...")
        os.makedirs("data/flipcom")


def check_files():
    f = "data/flipcom/commands.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty commands.json...")
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(FlipCommands(bot))
