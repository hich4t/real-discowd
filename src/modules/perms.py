import json, aiofiles
from discord.ext import commands

filename = "./perms.json"
perms = {}

def permswrite():
    open(filename, "w").write(json.dumps(perms))

async def apermswrite():
    async with aiofiles.open(filename, "w") as file:
        await file.write(json.dumps(perms))

try:
    perms = json.loads(open(filename, "r").read())
except Exception as e:
    print(e)
    permswrite()

def check_permissions(userid: int):
    return perms.get(str(userid), [])

async def write_permissions(userid: int, perm: list):
    perms[str(userid)] = perm
    await apermswrite()

def all_permissions():
    return perms

async def change_permissions(userid: int, permissions: str):
    uperms = check_permissions(userid)
    perms = permissions.split(";")
    changes = {"added": [], "removed": [], "unchanged": []}
    for perm in perms:
        if perm not in uperms:
            uperms.append(perm)
            changes["added"].append(perm)
        else:
            uperms.remove(perm)
            changes["removed"].append(perm)
    
    await write_permissions(userid, uperms)
    for uperm in uperms:
        if uperm not in changes["added"] and uperm not in changes["removed"]:
            changes["unchanged"].append(uperm)
    return changes

def permission(required_perm):
    async def predicate(ctx):
        user_perms = check_permissions(str(ctx.author.id))
        if required_perm in user_perms or "*" in user_perms:
            return True
        else:
            await ctx.respond(f":x: You lack the `{required_perm}` permission!", ephemeral=True)
            return False
    return commands.check(predicate)