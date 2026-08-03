# --- bot.py ---
import os
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

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
    try:
        await member.send(
            f"👋 Welcome to the server!\n\n"
            f"To get access, you need to be in our Roblox group.\n"
            f"Run `/verify <your_roblox_username>` in the server to verify."
        )
    except discord.Forbidden:
        pass


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

        # Step 3: fetch full Roblox profile
        roblox_profile = await get_roblox_profile(session, roblox_id)

    # Step 4: assign verified role
    role = guild.get_role(VERIFIED_ROLE_ID)
    if role is None:
        await interaction.followup.send(
            "⚠️ Verified role not found. Contact an admin.",
            ephemeral=True,
        )
        return

    try:
        await member.add_roles(role, reason=f"Verified as Roblox user: {roblox_username}")
    except discord.Forbidden:
        await interaction.followup.send(
            "⚠️ Bot doesn't have permission to assign roles. Contact an admin.",
            ephemeral=True,
        )
        return

    # Step 5: confirm to the user
    await interaction.followup.send(
        f"✅ Verified! Welcome in, **{roblox_username}**.",
        ephemeral=True,
    )

    # Step 6: fire webhook log with full profile card
    await send_verify_log(member, roblox_username, roblox_id, roblox_profile)


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


# --- Roblox helpers ---

async def get_roblox_user_id(session: aiohttp.ClientSession, username: str):
    payload = {"usernames": [username], "excludeBannedUsers": True}
    try:
        async with session.post(
            "https://users.roblox.com/v1/usernames/users",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            users = data.get("data", [])
            return users[0]["id"] if users else None
    except Exception:
        return None


async def is_in_group(session: aiohttp.ClientSession, user_id: int, group_id: int) -> bool:
    url = f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return False
            data = await resp.json()
            return any(entry["group"]["id"] == group_id for entry in data.get("data", []))
    except Exception:
        return False


async def get_roblox_profile(session: aiohttp.ClientSession, user_id: int) -> dict:
    profile = {
        "display_name": "Unknown",
        "description": "No description.",
        "created": "Unknown",
        "avatar_url": None,
        "profile_url": f"https://www.roblox.com/users/{user_id}/profile",
    }

    try:
        async with session.get(
            f"https://users.roblox.com/v1/users/{user_id}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                profile["display_name"] = data.get("displayName", data.get("name", "Unknown"))
                profile["description"] = data.get("description") or "No description."
                created_raw = data.get("created", "")
                profile["created"] = created_raw[:10] if created_raw else "Unknown"
    except Exception:
        pass

    try:
        async with session.get(
            f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
            f"?userIds={user_id}&size=420x420&format=Png&isCircular=false",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                items = data.get("data", [])
                if items:
                    profile["avatar_url"] = items[0].get("imageUrl")
    except Exception:
        pass

    return profile


async def send_verify_log(
    member: discord.Member,
    roblox_username: str,
    roblox_id: int,
    profile: dict,
):
    webhook_url = os.environ.get("VERIFY_LOG_WEBHOOK")
    if not webhook_url:
        return

    owner = member.guild.owner
    owner_mention = owner.mention if owner else "Unknown"

    embed = {
        "title": "✅ New Verification",
        "color": 5763719,
        "fields": [
            {
                "name": "Discord",
                "value": f"{member.mention}\n`{member.name}` (ID: `{member.id}`)",
                "inline": True,
            },
            {
                "name": "Roblox",
                "value": f"[{roblox_username}]({profile['profile_url']})\nID: `{roblox_id}`",
                "inline": True,
            },
            {
                "name": "Display Name",
                "value": profile["display_name"],
                "inline": True,
            },
            {
                "name": "Account Created",
                "value": profile["created"],
                "inline": True,
            },
            {
                "name": "Roblox Bio",
                "value": profile["description"][:1024],
                "inline": False,
            },
            {
                "name": "Profile Link",
                "value": profile["profile_url"],
                "inline": False,
            },
        ],
        "footer": {
            "text": f"Joined Discord: {member.joined_at.strftime('%Y-%m-%d') if member.joined_at else 'Unknown'}"
        },
        "timestamp": discord.utils.utcnow().isoformat(),
    }

    if profile["avatar_url"]:
        embed["thumbnail"] = {"url": profile["avatar_url"]}

    payload = {
        "content": f"📋 New member verified — heads up {owner_mention}",
        "embeds": [embed],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 204):
                    print(f"[WEBHOOK] Failed: HTTP {resp.status}")
    except Exception as e:
        print(f"[WEBHOOK] Exception: {e}")


bot.run(TOKEN)
