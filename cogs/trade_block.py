import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime

import config
import helpers

log = logging.getLogger("CoachBot.TradeBlock")

class TradeBlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # data structure: {user_id: {"team_name": str, "players": [{"name": str, "description": str, "timestamp": str}]}}
        self.trade_data = {}

    async def cog_load(self):
        self.bot.loop.create_task(self.initialize_data())
        
    async def initialize_data(self):
        await self.bot.wait_until_ready()
        self.trade_data = await self.bot.db.load("trade_block.json")

    @app_commands.command(name="tradeblock_add", description="Add a player to your trade block")
    @app_commands.describe(player="The player you are shopping", looking_for="What you want in return")
    async def add_player(self, interaction: discord.Interaction, player: str, looking_for: str):
        if config.ALLOWED_COMMAND_CHANNELS and interaction.channel.name not in config.ALLOWED_COMMAND_CHANNELS:
            await interaction.response.send_message("Let's keep the trade talk in the correct channel, mate.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        
        if user_id not in self.trade_data:
            # Try to figure out their team name from Draft config, or fallback to Discord name
            draft_config = await self.bot.db.load(config.DRAFT_CONFIG_FILE)
            team_name = interaction.user.display_name
            # If we had a direct mapping we'd use it, for now display name is best

            self.trade_data[user_id] = {
                "team_name": team_name,
                "players": []
            }
            
        # Update team name just in case they changed it
        self.trade_data[user_id]["team_name"] = interaction.user.display_name
            
        # Check if player already on block
        for p in self.trade_data[user_id]["players"]:
            if p["name"].lower() == player.lower():
                p["description"] = looking_for
                p["timestamp"] = datetime.now().isoformat()
                await self.bot.db.save("trade_block.json", self.trade_data)
                
                embed = helpers.format_embed(
                    f"🔄 Trade Block Updated: {player}",
                    f"**{interaction.user.mention}** updated the asking price for **{player}**.\n\n**Looking for:** {looking_for}",
                    config.COLOUR_AFL
                )
                await interaction.response.send_message(embed=embed)
                return

        if len(self.trade_data[user_id]["players"]) >= 10:
             await interaction.response.send_message("Mate, you can't put your entire list on the block. Max 10 players. Drop someone first.", ephemeral=True)
             return

        self.trade_data[user_id]["players"].append({
            "name": player,
            "description": looking_for,
            "timestamp": datetime.now().isoformat()
        })
        
        await self.bot.db.save("trade_block.json", self.trade_data)
        
        embed = helpers.format_embed(
            f"🛒 New to the Trade Block: {player}",
            f"**{interaction.user.mention}** is shopping **{player}**.\n\n**Looking for:** {looking_for}\n\n*Slide into their DMs with an offer.*",
            config.COLOUR_DRAFT
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tradeblock_remove", description="Remove a player from your trade block")
    @app_commands.describe(player="The player to remove")
    async def remove_player(self, interaction: discord.Interaction, player: str):
        user_id = str(interaction.user.id)
        
        if user_id not in self.trade_data or not self.trade_data[user_id]["players"]:
            await interaction.response.send_message("You don't have anyone on the trade block!", ephemeral=True)
            return
            
        initial_len = len(self.trade_data[user_id]["players"])
        self.trade_data[user_id]["players"] = [p for p in self.trade_data[user_id]["players"] if p["name"].lower() != player.lower()]
        
        if len(self.trade_data[user_id]["players"]) < initial_len:
            await self.bot.db.save("trade_block.json", self.trade_data)
            await interaction.response.send_message(f"✅ Removed **{player}** from your trade block. Off the market.", ephemeral=True)
        else:
             await interaction.response.send_message(f"Couldn't find **{player}** on your trade block. Check spelling.", ephemeral=True)

    @app_commands.command(name="tradeblock", description="View everyone's current trade blocks")
    @app_commands.describe(member="Optional: View a specific coach's block")
    async def view_block(self, interaction: discord.Interaction, member: discord.Member = None):
        if not self.trade_data:
            await interaction.response.send_message("The trade block is empty. Everyone is hugging their players.")
            return

        embed = discord.Embed(title="🛒 The Trade Floor", color=config.COLOUR_DRAFT)
        
        has_content = False
        
        if member:
            user_id = str(member.id)
            if user_id in self.trade_data and self.trade_data[user_id]["players"]:
                has_content = True
                desc = ""
                for p in self.trade_data[user_id]["players"]:
                    desc += f"**{p['name']}** - *Wants: {p['description']}*\n"
                embed.add_field(name=f"{member.display_name}'s Block", value=desc, inline=False)
            else:
                 await interaction.response.send_message(f"**{member.display_name}** has no players on the block.")
                 return
        else:
            for user_id, data in self.trade_data.items():
                if data["players"]:
                    has_content = True
                    desc = ""
                    for p in data["players"]:
                        desc += f"• **{p['name']}** - *Wants: {p['description']}*\n"
                    
                    coach_name = data.get("team_name", f"Coach {user_id}")
                    embed.add_field(name=f"🛡️ {coach_name}", value=desc, inline=False)

        if not has_content:
            await interaction.response.send_message("The trade block is completely empty right now. Get negotiating.")
            return

        embed.set_footer(text="Use /tradeblock_add to list your players here.")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TradeBlock(bot))
