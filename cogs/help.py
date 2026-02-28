import discord
from discord import app_commands
from discord.ext import commands
import logging

import config
import helpers

log = logging.getLogger("CoachBot.Help")

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.categories = {
            "AFL Fantasy": {"emoji": "🏉", "commands": ["scores", "round", "ladder", "stats", "topscorers", "compare", "draftorder", "mypicks", "currentpick"]},
            "Keeper League": {"emoji": "💼", "commands": ["tradeblock", "tradeblock_add", "tradeblock_remove", "picks", "deadlines"]},
            "News & Updates": {"emoji": "📰", "commands": []},
            "Moderation": {"emoji": "🛡️", "commands": ["warn", "warnings", "clearwarnings", "mute", "kick", "ban", "purge"]},
            "Levelling": {"emoji": "⬆️", "commands": ["rank", "leaderboard", "resetxp"]},
            "Polls": {"emoji": "📊", "commands": ["poll", "endpoll"]},
            "Custom Commands": {"emoji": "⚙️", "commands": ["addcommand", "editcommand", "deletecommand", "listcommands"]},
            "Reminders": {"emoji": "⏰", "commands": ["remindme", "myreminders", "cancelreminder"]},
            "Reaction Roles": {"emoji": "🎭", "commands": ["reactionrole", "listreactionroles", "removereactionrole"]},
            "Fun": {"emoji": "🎉", "commands": ["roast", "coinflip", "8ball", "roll", "askkev", "captains", "fixture", "rookies"]},
            "Admin": {"emoji": "🔧", "commands": ["setteam", "setwelcome", "tradepick", "setdeadline", "cleardeadline", "draftpick"]}
        }
        self.admin_commands = ["clearwarnings", "purge", "resetxp", "endpoll", "addcommand", "editcommand", "deletecommand", "reactionrole", "removereactionrole", "setteam", "setwelcome", "tradepick", "setdeadline", "cleardeadline", "draftpick"]

    def get_command_signature_and_desc(self, cmd):
        sig = f"/{cmd.name}"
        if cmd.parameters:
            args = []
            for p in cmd.parameters:
                if p.required:
                    args.append(f"[{p.name}]")
                else:
                    args.append(f"<{p.name}>")
            sig += " " + " ".join(args)
            
        lock = "🔒 " if cmd.name in self.admin_commands else ""
        return f"{lock}`{sig}` - {cmd.description}"

    @app_commands.command(name="help", description="Show all available commands")
    @app_commands.describe(command="Specific command to get help for")
    async def help_command(self, interaction: discord.Interaction, command: str = None):
        commands_list = self.bot.tree.get_commands()
        
        if command:
            cmd = discord.utils.get(commands_list, name=command.lower().replace("/", ""))
            if not cmd:
                await interaction.response.send_message(f"Command `{command}` not found.", ephemeral=True)
                return
                
            embed = helpers.format_embed(
                title=f"Command Help: /{cmd.name}",
                description=cmd.description,
                colour=config.COLOUR_HELP
            )
            
            usage = f"/{cmd.name}"
            if cmd.parameters:
                for p in cmd.parameters:
                    if p.required:
                        usage += f" [{p.name}]"
                    else:
                        usage += f" <{p.name}>"
                        
            embed.add_field(name="Usage", value=f"`{usage}`\n`[]` = required, `<>` = optional", inline=False)
            
            if cmd.parameters:
                args_desc = ""
                for p in cmd.parameters:
                    args_desc += f"**{p.name}**: {p.description or 'No description'}\n"
                embed.add_field(name="Arguments", value=args_desc, inline=False)
                
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title="Keyboard Kev Help Menu",
            description="All available commands grouped by category.\n🔒 indicates admin-only.",
            color=config.COLOUR_HELP
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
        
        loaded_cmd_dict = {c.name: c for c in commands_list}
        
        for cat_name, info in self.categories.items():
            cat_cmds = []
            for cmd_name in info["commands"]:
                if cmd_name in loaded_cmd_dict:
                    cmd_obj = loaded_cmd_dict[cmd_name]
                    cat_cmds.append(self.get_command_signature_and_desc(cmd_obj))
                    
            if cat_cmds:
                embed.add_field(
                    name=f"{info['emoji']} {cat_name}",
                    value="\n".join(cat_cmds),
                    inline=False
                )
                
        categorized_names = [name for data in self.categories.values() for name in data["commands"]]
        misc_cmds = []
        for c in commands_list:
            if c.name not in categorized_names and c.name != "help":
                misc_cmds.append(self.get_command_signature_and_desc(c))
                
        if misc_cmds:
            embed.add_field(name="❓ Other", value="\n".join(misc_cmds), inline=False)
            
        embed.set_footer(text="Keyboard Kev built for Keyboard Coaches. Use /help [command] for details on any command.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
