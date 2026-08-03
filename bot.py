# --- bot.py ---
import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
from roblox import get_roblox_user_id, is_in_group

TOKEN = os.environ["DISCORD_TOKEN"]
GROUP_ID = int(os.environ["ROBLOX_GROUP_ID"])
VERIFIED_ROLE_ID = int(os.environ["VERIFIED_ROLE_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"[BOT] Online as {bot.user} | Guild ID: {GUILD_ID}")


@bot.event
async def on_member_join(member: discord.Member):
    """
    Optional: DM new members telling them to verify.
    Does NOT auto-verify — they need to run /verify with their Roblox username.
    """
    try:
        await member.send(
            f"👋 Welcome to the server!\n\n"
            f"To get access, you need to be in our Roblox group.\n"
            f"Run `/verify <your_roblox_username>` in the server to verify."
        )
    except discord.Forbidden:
        pass  # DMs closed, they'll figure it out


@tree.command(
    name="verify",
    description="Verify your Roblox account to get access.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(roblox_username="Your exact Roblox username")
async def verify(interaction: discord.Interaction, roblox_username: str):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    member = interaction.user

    async with aiohttp.ClientSession() as session:
        # Step 1: resolve username → user ID
        roblox_id = await get_roblox_user_id(session, roblox_username)
        if roblox_id is None:
            await interaction.followup.send(
                f"❌ Couldn't find a Roblox account named **{roblox_username}**.\n"
                f"Check your spelling and try again.",
                ephemeral=True,
            )
            return

        # Step 2: check group membership
        in_group = await is_in_group(session, roblox_id, GROUP_ID)

    if not in_group:
        await interaction.followup.send(
            f"❌ **{roblox_username}** is not in the Roblox group.\n"
            f"Join the group first, then run `/verify` again.",
            ephemeral=True,
        )
        return

    # Step 3: assign verified role
    role = guild.get_role(VERIFIED_ROLE_ID)
    if role is None:
        await interaction.followup.send(
            "⚠️ Verified role not found. Contact an admin.",
            ephemeral=True,
        )
        return

    try:
        await member.add_roles(role, reason=f"Verified as Roblox user: {roblox_username}")
        await interaction.followup.send(
            f"✅ Verified! Welcome in, **{roblox_username}**.",
            ephemeral=True,
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "⚠️ Bot doesn't have permission to assign roles. Contact an admin.",
            ephemeral=True,
        )


@tree.command(
    name="unverify",
    description="Remove your verified role.",
    guild=discord.Object(id=GUILD_ID),
)
async def unverify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    if role and role in interaction.user.roles:
        await interaction.user.remove_roles(role, reason="Self-unverified")
        await interaction.followup.send("✅ Verified role removed.", ephemeral=True)
    else:
        await interaction.followup.send("You don't have the verified role.", ephemeral=True)


@tree.command(
    name="checkverify",
    description="[Admin] Re-check if a member is still in the Roblox group.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(member="The Discord member to check")
@app_commands.default_permissions(administrator=True)
async def checkverify(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    has_role = role in member.roles if role else False
    await interaction.followup.send(
        f"{'✅' if has_role else '❌'} {member.mention} {'has' if has_role else 'does not have'} the verified role.",
        ephemeral=True,
    )


bot.run(TOKEN)# --- bot.py ---
import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import aiohttp
from roblox import get_roblox_user_id, is_in_group

TOKEN = os.environ["DISCORD_TOKEN"]
GROUP_ID = int(os.environ["ROBLOX_GROUP_ID"])
VERIFIED_ROLE_ID = int(os.environ["VERIFIED_ROLE_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"[BOT] Online as {bot.user} | Guild ID: {GUILD_ID}")


@bot.event
async def on_member_join(member: discord.Member):
    """
    Optional: DM new members telling them to verify.
    Does NOT auto-verify — they need to run /verify with their Roblox username.
    """
    try:
        await member.send(
            f"👋 Welcome to the server!\n\n"
            f"To get access, you need to be in our Roblox group.\n"
            f"Run `/verify <your_roblox_username>` in the server to verify."
        )
    except discord.Forbidden:
        pass  # DMs closed, they'll figure it out


@tree.command(
    name="verify",
    description="Verify your Roblox account to get access.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(roblox_username="Your exact Roblox username")
async def verify(interaction: discord.Interaction, roblox_username: str):
    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    member = interaction.user

    async with aiohttp.ClientSession() as session:
        # Step 1: resolve username → user ID
        roblox_id = await get_roblox_user_id(session, roblox_username)
        if roblox_id is None:
            await interaction.followup.send(
                f"❌ Couldn't find a Roblox account named **{roblox_username}**.\n"
                f"Check your spelling and try again.",
                ephemeral=True,
            )
            return

        # Step 2: check group membership
        in_group = await is_in_group(session, roblox_id, GROUP_ID)

    if not in_group:
        await interaction.followup.send(
            f"❌ **{roblox_username}** is not in the Roblox group.\n"
            f"Join the group first, then run `/verify` again.",
            ephemeral=True,
        )
        return

    # Step 3: assign verified role
    role = guild.get_role(VERIFIED_ROLE_ID)
    if role is None:
        await interaction.followup.send(
            "⚠️ Verified role not found. Contact an admin.",
            ephemeral=True,
        )
        return

    try:
        await member.add_roles(role, reason=f"Verified as Roblox user: {roblox_username}")
        await interaction.followup.send(
            f"✅ Verified! Welcome in, **{roblox_username}**.",
            ephemeral=True,
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "⚠️ Bot doesn't have permission to assign roles. Contact an admin.",
            ephemeral=True,
        )


@tree.command(
    name="unverify",
    description="Remove your verified role.",
    guild=discord.Object(id=GUILD_ID),
)
async def unverify(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    if role and role in interaction.user.roles:
        await interaction.user.remove_roles(role, reason="Self-unverified")
        await interaction.followup.send("✅ Verified role removed.", ephemeral=True)
    else:
        await interaction.followup.send("You don't have the verified role.", ephemeral=True)


@tree.command(
    name="checkverify",
    description="[Admin] Re-check if a member is still in the Roblox group.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(member="The Discord member to check")
@app_commands.default_permissions(administrator=True)
async def checkverify(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    role = interaction.guild.get_role(VERIFIED_ROLE_ID)
    has_role = role in member.roles if role else False
    await interaction.followup.send(
        f"{'✅' if has_role else '❌'} {member.mention} {'has' if has_role else 'does not have'} the verified role.",
        ephemeral=True,
    )


bot.run(TOKEN)