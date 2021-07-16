import json
import os
import discord
import uuid
import datetime
import asyncio
import motor.motor_asyncio
import aioredis
import async_timeout
import coloredlogs
import logging

from discord.http import Route
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component, ComponentContext 
from discord_slash.model import ButtonStyle

from __lib.discord_slash_permission import getdata
from __lib.config import getconfig, saveconfig


bot = commands.Bot(command_prefix="*",intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)

_config, _vcch = "", ""
with open(os.path.join(os.getcwd(), "config.json"), "r", encoding="utf-8") as f:
	_data = json.load(f)
	_redis = aioredis.from_url("redis://%s:%s" % (_data["redis"]["host"], _data["redis"]["port"]))

# Catch 
_js_vc = None

# Setup Logger
logmain = logging.getLogger("DEVThailandStage Main")
logmuteserver = logging.getLogger("DevThailandStage Checker")
logsocket = logging.getLogger("DEVThailandStage Socket")

coloredlogs.install(level="DEBUG", logger=logmain)
coloredlogs.install(level="DEBUG", logger=logmuteserver)
coloredlogs.install(level="DEBUG", logger=logsocket)

@bot.event
async def on_ready():
	global _config, _vcch
	
	logmain.debug("Loading config....")
	_config = await getconfig("config.json")
	_vcch = await getconfig("discord_config.json")
	
	logmain.debug("Createing 2 task.")

	try:
		_pubsub = _redis.pubsub()
		await _pubsub.subscribe("_VOICE_STATE_UPDATE")
	except Exception as e:
		print(e)
		logmain.error("Failed to connect redis... %s:%s " % (_config["redis"]["host"], _config["redis"]["port"]))
		logmain.error("Exiting...")

		os._exit(1)

	bot.loop.create_task(__waittimer())
	bot.loop.create_task(__servermuteleave(_pubsub))

	with open(os.path.join(os.getcwd(), "welcome.txt"), "r", encoding="utf-8") as f:
		print(f.read())
	
	logmain.info("Logged as %s" % bot.user.name)
	

# @bot.event 
# async def on_command_error(ctx, error):
# 	print(error)

@bot.event
async def on_socket_response(response):
	global _redis

	if response["t"] == "INTERACTION_CREATE":
		logsocket.debug("Recieve (INTERACTION_CREATE)")
		# print(response)
		await _redis.publish("_INTERACTION_CREATE",json.dumps(response))

	if response["t"] == "MESSAGE_UPDATE":
		logsocket.debug("Recieve (MESSAGE_UPDATE)")
		logsocket.debug("MessageID: %s // Form Channel: %s" % (response["d"]["id"],response["d"]["channel_id"])) 
		await _redis.publish("_MESSAGE_UPDATE",json.dumps(response))

	if response["t"] == "GUILD_MEMBER_UPDATE":
		logsocket.debug("Recieve (GUILD_MEMBER_UPDATE)")
		await _redis.publish("_GUILD_MEMBER_UPDATE",json.dumps(response))

@bot.event
async def on_voice_state_update(member, _, after):
	global _js_vc

	js = await __format_json(
		type="VOICE_STATE_UPDATE",
		data={
			"member": {
				"user": {
					"id": str(member.id), 
				}
			},
			"self_mute": after.self_mute, 
			"self_deaf": after.self_deaf, 
			"mute": after.mute, 
			"deaf": after.deaf, 
			"guild_id": str(member.guild.id), 
			"channel_id": None if after.channel is None else str(after.channel.id)
		}
	)

	if _js_vc is None:
		_js_vc = js

	try:
		logsocket.debug("Recieve (VOICE_STATE_UPDATE)")
		logsocket.debug("Username: %s // Self Mute: %s // Self Deaf: %s" % (member.name, after.self_mute, after.self_deaf))

		await _redis.publish("_VOICE_STATE_UPDATE",json.dumps(js))
	except KeyError as e:
		pass

@bot.event
async def on_message(msg):
	global _config, _vcch 

	if _config != "" and _vcch != "":
		await bot.process_commands(msg)

async def __format_json(type: str, data: dict):
	return {
		"t": type,
		"d": data
	}


@slash.subcommand(base="techtalk", subcommand_group="config", name="voice",  guild_ids=getdata()[0], description="Config voice room to control.", base_permissions=getdata()[1], base_default_permission=False, options=[
	create_option(
		name="channelid",
		description="Voice Channel for control room.",
		option_type=7,
		required=True
	)
])
async def voice(ctx, channelid):
	global _vcch

	if isinstance(channelid, discord.channel.VoiceChannel):
		_vcch["techtalk"]["voicechannel"] = str(channelid.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config Voice channel success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found voice room channe.l",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="text", guild_ids=getdata()[0], description="Config text room to alert tech-talk.", base_default_permission=False, options=[
	create_option(
		name="channelid",
		description="Text Channel for alert tech-talk.",
		option_type=7,
		required=True
	)
])
async def text(ctx, channelid):
	global _vcch

	if isinstance(channelid, discord.channel.VoiceChannel):
		_vcch["techtalk"]["voicechannel"] = str(channelid.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config Text channel success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found text channel.",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="control",  guild_ids=getdata()[0], description="Config control for accept hands up.", base_default_permission=False, options=[
	create_option(
		name="channelid",
		description="Text Channel for accept hand up.",
		option_type=7,
		required=True
	)
])
async def control(ctx, channelid):
	global _vcch

	if isinstance(channelid, discord.channel.TextChannel):
		_vcch["techtalk"]["controlchannel"] = str(channelid.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config Control channel room success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found control channel.",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="rolehandups",  guild_ids=getdata()[0], description="Config Hand up role.", base_default_permission=False, options=[
	create_option(
		name="roleid",
		description="Role ID for hand up.",
		option_type=9,
		required=True
	)
])
async def rolehandsup(ctx, roleid):
	global _vcch

	_role = discord.utils.get(ctx.guild.roles, id=int(roleid, 10))

	if not _role is None and isinstance(_role, discord.role.Role):
		_vcch["techtalk"]["roles"]["handup"] = str(_role.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config role hands up success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found role.",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="roleadmin",  guild_ids=getdata()[0], description="Config Hand up role.", base_default_permission=False, options=[
	create_option(
		name="roleid",
		description="Role ID for admin.",
		option_type=9,
		required=True
	)
])
async def roleadmin(ctx, roleid):
	global _vcch

	_role = discord.utils.get(ctx.guild.roles, id=int(roleid, 10))

	if not _role is None and isinstance(_role, discord.role.Role):
		_vcch["techtalk"]["roles"]["admin"] = str(_role.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config Role moderetor success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found role.",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="rolemod",  guild_ids=getdata()[0], description="Config Hand up role.", base_default_permission=False, options=[
	create_option(
		name="roleid",
		description="Role ID for moderetor.",
		option_type=9,
		required=True
	)
])
async def rolemod(ctx, roleid):
	global _vcch

	_role = discord.utils.get(ctx.guild.roles, id=int(roleid, 10))

	if not _role is None and isinstance(_role, discord.role.Role):
		_vcch["techtalk"]["roles"]["mod"] = str(_role.id)
		await saveconfig("discord_config.json", _vcch)

		embed = discord.Embed(
			title="✅ Config Role moderetor success.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	else:
		embed = discord.Embed(
			title="❌ Not found role.",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="config", name="guild",  guild_ids=getdata()[0], description="Create Topic", base_default_permission=False)
async def guild(ctx):
	global _vcch

	_vcch["techtalk"]["guildserver"] = str(ctx.author.guild.id)
	await saveconfig("discord_config.json", _vcch)

	embed = discord.Embed(
		title="✅ Config guild server success.",
		color=0x2bd957,
		timestamp=datetime.datetime.utcnow()
	)
	await ctx.send(embed=embed)

# ======================== Tech Talk Commands ======================== #
@slash.subcommand(base="techtalk", subcommand_group="topic", name="create",  guild_ids=getdata()[0], description="Create Topic", base_default_permission=False, base_permissions=getdata()[1], options=[
	create_option(
		name="startdate",
		description="Start topic [ Format: dd/mm/yyyy HH:MM ]",
		option_type=3,
		required=True
	),
	create_option(
		name="enddate",
		description="End topic [ Format: dd/mm/yyyy HH:MM ]",
		option_type=3,
		required=True
		
	),
	create_option(
		name="topic",
		description="Name Topic",
		option_type=3,
		required=True
	),
])
async def create(ctx, startdate: str, enddate: str, *, topic: str):
	# Connect DB
	_uu = str(uuid.uuid4())
	_db = await __connectmongodb()

	_s = datetime.datetime.strptime(startdate, "%d/%m/%Y %H:%M")
	_e = datetime.datetime.strptime(enddate, "%d/%m/%Y %H:%M")

	if not _s.timestamp() <= _e.timestamp():
		embed_err = discord.Embed(
			title="❌ You cannot set time future",
			description="Please set time correct.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed_err)
	
	if await __vailddatetime(startdate) and await __vailddatetime(enddate) and topic != None and topic != "":
		_db.DEVThailandStage.topic.insert_one({
			"topicid": _uu,
			"topicisstart": False,
			"isforcestart": False,
			"topicdetails": {
				"title": topic,
				"start": _s,
				"end": _e,
				"create_at": datetime.datetime.now(),
				"update_at": datetime.datetime.now()
			}
		})

		embed_main = discord.Embed(
			title="✅ Create success",
			description="Your topic ID is: "+_uu,
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		embed_main.set_footer(text="Create by "+str(ctx.author.name)+"\nNote: Please keep it secret, if it’s compromised, anyone is able to change the topic", icon_url=ctx.author.avatar_url)

		await ctx.send(embed=embed_main)
		
	elif not await __vailddatetime(startdate) and not await __vailddatetime(enddate):
		embed_main = discord.Embed(
			title="❌ Please set correct datetime this",
			description="`%d/%m/%Y %H:%M`",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)
		
		await ctx.send(embed=embed_main,delete_after=10)
	elif topic != None and topic != "":
		embed_main = discord.Embed(
			title="❌ Please set topic name",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)
		
		await ctx.send(embed=embed_main,delete_after=10)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="delete", description="Delete Topic", guild_ids=getdata()[0], options=[
	create_option(
		name="uuid",
		description="UUID Topic",
		option_type=3,
		required=True
	)
])
async def delete(ctx, uuid: str):
	# Connect DB
	_db = await __connectmongodb()

	if uuid:
		if await _db.DEVThailandStage.topic.find_one({"topicid": uuid}):
			await _db.DEVThailandStage.topic.delete_one({"topicid": uuid})
			embed_main = discord.Embed(
				title="✅ Delete success",
				color=0x2bd957,
				timestamp=datetime.datetime.utcnow()
			)
			embed_main.set_footer(text="Delete by "+str(ctx.author.name),icon_url=ctx.author.avatar_url)

			await ctx.send(embed=embed_main)
		else:
			embed_main = discord.Embed(
				title="❌ Not found topic",
				color=0xeb3b28,
				timestamp=datetime.datetime.utcnow()
			)
			
			await ctx.send(embed=embed_main,delete_after=10)

# print(_permission)
@slash.subcommand(base="techtalk", subcommand_group="topic", name="list", description="List Topic", guild_ids=getdata()[0], base_default_permission=False)
async def listtopic(ctx):
	# Connect DB
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find({}).to_list(length=10)

	embed = discord.Embed(
		title="📣 List topic",
		color=0xde3767,
		timestamp=datetime.datetime.utcnow()
	)
	
	if len(list(_find)) >= 1:
		for idx, _data in enumerate(_find):
			embed.add_field(
				name=str(idx+1)+ ". >> "+ _data["topicdetails"]["title"],
				value="Start: "+_data["topicdetails"]["start"].strftime("%d %B %Y %H:%M")+"\nEnd: " + _data["topicdetails"]["end"].strftime("%d %B %Y %H:%M"),
				inline=False
			)
	else:
		embed.description = "Noting topic found."

	embed.set_footer(text="Note. If you want UUID topic to edit. Please use command `/techtalk topic uuid` to select topic and get UUID. (for permission administrator)")
	await ctx.send(embed=embed)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="uuid", description="Get Topic UUID", guild_ids=getdata()[0], base_default_permission=False)
async def uuid_topic(ctx):
	# Connect DB
	_btn = []
	
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find({}).to_list(length=10)
	_embed_user = discord.Embed()
	

	if len(list(_find)) >= 1:
		embed = discord.Embed(
			title="📣 Please select topic",
			color=0xde3767,
			timestamp=datetime.datetime.utcnow()
		)

		for idx, _data in enumerate(_find):
			embed.add_field(
				name=str(idx+1)+ ". >> "+ _data["topicdetails"]["title"],
				value="Start: "+_data["topicdetails"]["start"].strftime("%d %B %Y %H:%M")+"\nEnd: " + _data["topicdetails"]["end"].strftime("%d %B %Y %H:%M"),
				inline=False
			)
			
			_btn.append(
				create_button(
					label=(
						str(idx+1) + "."
					), 
					custom_id=str(idx),
					style=ButtonStyle.gray
				)
			)
		
		action_row = create_actionrow(*_btn)
		await ctx.send(embed=embed,components=[
			action_row
		])

		def check(response: ComponentContext):
			_pos = int(response.component["label"].split(".")[0], 10)
			_embed_user.title = "ℹ UUID for topic: %s" % list(_find)[_pos-1]["topicdetails"]["title"]
			_embed_user.description = list(_find)[_pos-1]["topicid"]
			_embed_user.timestamp = datetime.datetime.utcnow()
			_embed_user.color = 0xde3767
			_embed_user.set_footer(text="Note: Please keep it secret, if it’s compromised, anyone is able to change the topic")	

			return ctx.author.id == response.author.id and ctx.channel.id == response.channel.id

		try:
			# response = await bot.wait_for("button_click", check=check, timeout=60)

			button_ctx: ComponentContext = await wait_for_component(bot, components=action_row, check=check)

			await ctx.author.send(embed=_embed_user)
			embed_user = discord.Embed(
				title="✅ Get success",
				color=0x2bd957,
				description="Please check DM. to get UUID topic.",
				timestamp=datetime.datetime.utcnow()
			)
			await button_ctx.edit_origin(embed=embed_user,components=[])
			# await _embed.delete()

		except TimeoutError:
			pass
	else:
		embed = discord.Embed(
			title="❌ Not founded topic create",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		await ctx.send(embed=embed)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="editname", description="Edit name topic", guild_ids=getdata()[0], options=[
	create_option(
		name="uuid",
		description="UUID Topic",
		option_type=3,
		required=True
	),
	create_option(
		name="topic_name",
		description="New topic name",
		option_type=3,
		required=True
	)
])
async def edittopicname(ctx, uuid: str, topic_name: str):
	# Connect DB
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find_one({"topicid": uuid})

	if not _find:
		embed = discord.Embed(
			title="❌ Not found topic",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	
	await _db.DEVThailandStage.topic.update_one({
		"topicid": uuid
	},
	{
		"$set": {
			"topicdetails.title": topic_name
		}
	})

	embed = discord.Embed(
		title="✅ Edit name success",
		color=0x2bd957,
		description="Change name form (%s) -> (%s)" % (_find["topicdetails"]["title"], topic_name),
		timestamp=datetime.datetime.utcnow()
	)

	await ctx.send(embed=embed)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="editdate", description="Edit start & end date topic", guild_ids=getdata()[0], options=[
	create_option(
		name="uuid",
		description="UUID Topic",
		option_type=3,
		required=True
	),
	create_option(
		name="startdate",
		description="New startdate [ Format: dd/mm/yyyy HH:MM ]",
		option_type=3,
		required=True
	),
	create_option(
		name="enddate",
		description="New enddate [ Format: dd/mm/yyyy HH:MM ]",
		option_type=3,
		required=True
	)
])
async def edittopicname(ctx, uuid: str, startdate: str, enddate: str):
	# Connect DB
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find_one({"topicid": uuid})

	if not _find:
		embed = discord.Embed(
			title="❌ Not found topic",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed)
	
	_s = datetime.datetime.strptime(startdate, "%d/%m/%Y %H:%M")
	_e = datetime.datetime.strptime(enddate, "%d/%m/%Y %H:%M")

	if not _s.timestamp() <= _e.timestamp():
		embed_err = discord.Embed(
			title="❌ You cannot set time future",
			description="Please set time correct.",
			color=0x2bd957,
			timestamp=datetime.datetime.utcnow()
		)

		return await ctx.send(embed=embed_err)

	await _db.DEVThailandStage.topic.update_one({
		"topicid": uuid
	},
	{
		"$set": {
			"topicdetails.start": _s,
			"topicdetails.end": _e,
			"topicdetails.update_at": datetime.datetime.now()
		}
	})

	embed = discord.Embed(
		title="✅ Edit name success",
		color=0x2bd957,
		description="Change datetime form (%s - %s) -> (%s - %s)" % (
			_find["topicdetails"]["start"].strftime("%d %B %Y %H:%M"),
			_find["topicdetails"]["end"].strftime("%d %B %Y %H:%M"), 
			_s.strftime("%d %B %Y %H:%M"),
			_e.strftime("%d %B %Y %H:%M")
		),
		timestamp=datetime.datetime.utcnow()
	)

	await ctx.send(embed=embed)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="forcestart", description="Forcestart topic", guild_ids=getdata()[0], options=[
	create_option(
		name="uuid",
		description="UUID Topic",
		option_type=3,
		required=True
	)
])
async def forcestart(ctx, uuid: str):
	# Connect DB
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find_one({"topicid": uuid})

	if not _find:
		embed_main = discord.Embed(
			title="❌ Not found topic",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)
			
		return await ctx.send(embed=embed_main,delete_after=10)

	await _db.DEVThailandStage.topic.update_one({
		"topicid": uuid
	},
	{
		"$set": {
			"isforcestart": True,
			"topicdetails.update_at": datetime.datetime.now()
		}
	})

	embed_main = discord.Embed(
		title="✅ Started topic: %s" % _find["topicdetails"]["title"],
		color=0x2bd957,
		timestamp=datetime.datetime.utcnow()
	)
	
	await ctx.send(embed=embed_main)

@slash.subcommand(base="techtalk", subcommand_group="topic", name="forcestop", description="Forcestop topic", guild_ids=getdata()[0], options=[
	create_option(
		name="uuid",
		description="UUID Topic",
		option_type=3,
		required=True
	)
])
async def forcestop(ctx, uuid: str):
	# Connect DB
	_db = await __connectmongodb()
	_find = await _db.DEVThailandStage.topic.find_one({"topicid": uuid})

	if not _find:
		embed_main = discord.Embed(
			title="❌ Not found topic",
			color=0xeb3b28,
			timestamp=datetime.datetime.utcnow()
		)
			
		return await ctx.send(embed=embed_main,delete_after=10)

	await _db.DEVThailandStage.topic.update_one({
		"topicid": uuid
	},
	{
		"$set": {
			"isforcestart": False,
			"topicdetails.update_at": datetime.datetime.now()
		}
	})

	embed_main = discord.Embed(
		title="✅ Stopped topic: %s" % _find["topicdetails"]["title"],
		color=0x2bd957,
		timestamp=datetime.datetime.utcnow()
	)

	await ctx.send(embed=embed_main)

async def __waittimer():	
	global _vcch

	_db = await __connectmongodb()

	while True:
		_find = _db.DEVThailandStage.topic.find({})

		for _data in await _find.to_list(length=100):
			if datetime.datetime.strptime(_data["topicdetails"]["start"].strftime("%d/%m/%Y %H:%M"), "%d/%m/%Y %H:%M").replace(microsecond=0).timestamp() <= (datetime.datetime.now().replace(microsecond=0).timestamp()) and not _data["topicisstart"]:
				# print("OK")
				await _db.DEVThailandStage.topic.update_one({
					"topicid": _data["topicid"]
				},
				{
					"$set": {
						"topicisstart": True
					}
				})
				
				_pubsub = _redis.pubsub()

				await _pubsub.subscribe(
					"_INTERACTION_CREATE", 
					"_GUILD_MEMBER_UPDATE", 
					"_VOICE_STATE_UPDATE", 
					"_MESSAGE_UPDATE"
				)

				bot.loop.create_task(__tasks(
					uuid=_data["topicid"],
					vcid=_vcch["techtalk"]["voicechannel"],
					chid=_vcch["techtalk"]["textchannel"],
					ctid=_vcch["techtalk"]["controlchannel"],
					channel=_pubsub
				))

			if _data["isforcestart"] and not _data["topicisstart"]:
				await _db.DEVThailandStage.topic.update_one({
					"topicid": _data["topicid"]
				},
				{
					"$set": {
						"topicisstart": True
					}
				})

				_pubsub = _redis.pubsub()
				await _pubsub.subscribe(
					"_INTERACTION_CREATE", 
					"_GUILD_MEMBER_UPDATE", 
					"_VOICE_STATE_UPDATE", 
					"_MESSAGE_UPDATE"
				)

				bot.loop.create_task(__tasks(
					uuid=_data["topicid"],
					vcid=_vcch["techtalk"]["voicechannel"],
					chid=_vcch["techtalk"]["textchannel"],
					ctid=_vcch["techtalk"]["controlchannel"],
					channel=_pubsub
				))

		await asyncio.sleep(1)

async def __servermuteleave(channel: aioredis.client.PubSub):
	global _vcch

	_db = await __connectmongodb()

	logmuteserver.info("Waitng check message")
	while True:
		try:
			try:
				async with async_timeout.timeout(timeout=1):
					msg = await channel.get_message(ignore_subscribe_messages=True)

					if msg is not None:
						_js = json.loads(msg["data"])

						if "d" in _js and "t" in _js and not _js["t"] is None:
							if _js["t"] == "VOICE_STATE_UPDATE" and _js["d"]["channel_id"] != None:
								_find = await _db.DEVThailandStage.users.find_one({"status": {"$in": ["SALFLEAVE","FORCELEAVE"]}})
								if not _find is None:
									_guild = bot.get_guild(int(_vcch["techtalk"]["guildserver"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
									
									# print(_js["d"]["channel_id"])
									if _js["d"]["channel_id"] != _vcch["techtalk"]["voicechannel"] and _find["status"] == "FORCELEAVE":
										await _mem.edit(mute=False)

									elif _find["status"] == "SALFLEAVE":
										# print(_mem)
										await _mem.edit(mute=False)

									# Delete it!
									_db.DEVThailandStage.users.delete_one({
										"userid": str(_js["d"]["member"]["user"]["id"])
									})

								if not await _db.DEVThailandStage.users.find_one({"status": "NULL"}) is None and str(_js["d"]["channel_id"]) != _vcch["techtalk"]["voicechannel"]:
									_guild = bot.get_guild(int(_vcch["techtalk"]["guildserver"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))

									await _mem.edit(mute=False)

									# Delete it!
									_db.DEVThailandStage.users.delete_one({
										"userid": str(_js["d"]["member"]["user"]["id"])
									})

			except asyncio.TimeoutError:
				pass

		except Exception as e:
			logmuteserver.error(e)
			logmuteserver.debug("Type error: %s" % type(e).__name__)
			logmuteserver.debug("File: %s" % __file__),
			logmuteserver.debug("Line error: %s" % e.__traceback__.tb_lineno)


async def __tasks(uuid: str, vcid: str, chid: str, ctid: str, channel: aioredis.client.PubSub):	
	global _vcch

	_db = await __connectmongodb()

	_find = await _db.DEVThailandStage.topic.find_one({
		"topicid": uuid
	})

	_msgdata = None
	
	if not _find is None:
		embed = discord.Embed(
			title="Topic: %s" % str(_find["topicdetails"]["title"]),
			description="If you want to talk. Please \"✋ Hand Up\"",
			color=0x349beb,
			timestamp=datetime.datetime.utcnow()
		)

		embed.add_field(name="Hand up ✋",value="-")
		embed.set_footer(text=bot.user.name,icon_url=bot.user.avatar_url)

		ch = bot.get_channel(int(chid))

		btn = [
			create_button(
				label="Hand up ✋",
				custom_id="up_topic",
				style=ButtonStyle.green
			),
			create_button(
				label="Hand down ❌",
				custom_id="down_topic",
				style=ButtonStyle.red
			)
		]

		msg = await ch.send(embed=embed,components=[
			create_actionrow(*btn)
		])

		del btn

		# Get ID
		_msgdata = msg
		bot.loop.create_task(__isended(uuid, _msgdata))

		while True:
			try:
				try:
					async with async_timeout.timeout(timeout=1):
						msg = await channel.get_message(ignore_subscribe_messages=True)

						if msg is not None:
							_js = json.loads(msg["data"])
							if "d" in _js and "t" in _js and not _js["t"] is None:
								if _js["t"] == "INTERACTION_CREATE" and _js["d"]["type"] >= 3 and str(_js["d"]["channel_id"]) == chid:
									_guild = bot.get_guild(int(_js["d"]["guild_id"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
									_role = discord.utils.get(_mem.roles, id=_vcch["techtalk"]["roles"]["admin"]) # Admin
									_role_mod = discord.utils.get(_mem.roles, id=_vcch["techtalk"]["roles"]["mod"]) # Mod

									if _role is None or not _role_mod is None:
										if not _mem.voice is None and str(_mem.voice.channel.id) == vcid:
											_col = _db.DEVThailandStage
											_val = ""
											if _js["d"]["data"]["custom_id"] == "up_topic" or _js["d"]["data"]["custom_id"] == "down_topic":
												if _js["d"]["data"]["custom_id"] == "up_topic":
													if not await _col.waitingtalk.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": str(uuid)}):
														# Get MSG.
														_ch = bot.get_channel(id=int(ctid ,10))
														
														# Create Message
														_embed = discord.Embed(
															title="✋ %s want to talk." %  str(_js["d"]["member"]["user"]["username"]),
															timestamp=datetime.datetime.utcnow(),
															color=0x3e72ed,
															description="%s requests to talk!, If you would like to accept the request, you can click \"✅ Accept\"" % str(_js["d"]["member"]["user"]["username"])
														)
														
														_embed.set_thumbnail(
															url="https://cdn.discordapp.com/avatars/"+str(_js["d"]["member"]["user"]["id"])+"/"+str(_js["d"]["member"]["user"]["avatar"])+".png?size=512"
														)

														btn = [
															create_button(
																label="✅ Accept", 
																custom_id=str(_js["d"]["member"]["user"]["id"])+"-accept",
																style=ButtonStyle.green
															),
															create_button(
																label="❌ Reject", 
																custom_id=str(_js["d"]["member"]["user"]["id"])+"-reject",
																style=ButtonStyle.red
															)
														]

														msg = await _ch.send(embed=_embed, components=[
															create_actionrow(*btn)
														])

														# Create Waiting room data
														await _col.waitingtalk.insert_one({
															"userid": str(_js["d"]["member"]["user"]["id"]),
															"topicid": str(uuid),
															"name": str(_js["d"]["member"]["user"]["username"]),
															"msgid": str(msg.id)
														})

														for _data in await _col.waitingtalk.find({}).to_list(100):
															_val = _val + (", " if _val != "" else "") + str(_data["name"])

													else:
														_val = _js["d"]["message"]["embeds"][0]["fields"][0]["value"]
											
												elif _js["d"]["data"]["custom_id"] == "down_topic":
													_find = await _col.waitingtalk.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": str(uuid)})
													if _find:
														await _col.waitingtalk.delete_one({
															"userid": str(_js["d"]["member"]["user"]["id"]),
															"topicid": str(uuid)
														})

														for _data in await _col.waitingtalk.find({}).to_list(100):
															_val = (", " if _val != "" else "") + _val + str(_data["name"]) 

														if len(_val) == 0:
															_val = "-"

														_ch = bot.get_channel(id=int(ctid))
														_msg = await _ch.fetch_message(int(_find["msgid"]))
														await _msg.delete()


													else:
														_val = _js["d"]["message"]["embeds"][0]["fields"][0]["value"]

											_js["d"]["message"]["embeds"][0]["fields"][0]["value"] = _val if len(_val) >= 1 else "-"

											await bot.http.request(
												Route(
													"POST",
													f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
												),
												json={
													"type": 7,
													"data": _js["d"]["message"] 
												}
											)	

										else:
											await bot.http.request(
												Route(
													"POST",
													f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
												),
												json={
													"type": 7,
													"data": _js["d"]["message"] 
												}
											)	
									else:
										await bot.http.request(
											Route(
												"POST",
												f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
											),
											json={
												"type": 7,
												"data": _js["d"]["message"] 
											}
										)	

								elif _js["t"] == "INTERACTION_CREATE" and _js["d"]["type"] >= 3 and str(_js["d"]["channel_id"]) == ctid:
									if _js["d"]["data"]["custom_id"].split("-")[-1] == "accept" or _js["d"]["data"]["custom_id"].split("-")[-1] == "reject":
										_guild = bot.get_guild(int(_js["d"]["guild_id"]))
										_mem_check = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
										_role_mod = discord.utils.get(_mem_check.roles, id=int(_vcch["techtalk"]["roles"]["mod"]))
										_role_admin = discord.utils.get(_mem_check.roles, id=int(_vcch["techtalk"]["roles"]["admin"]))

										if not _role_mod is None or not _role_admin is None:
											if _js["d"]["data"]["custom_id"].split("-")[-1] == "accept":
												if await _col.waitingtalk.find_one({"userid": str(_js["d"]["data"]["custom_id"].split("-")[0]), "topicid": str(uuid)}):
													
													_mem = discord.utils.get(_guild.members, id=int(_js["d"]["data"]["custom_id"].split("-")[0]))
													_role = discord.utils.get(_guild.roles, id=int(_vcch["techtalk"]["roles"]["handup"]))

													if not await _col.users.find_one({"userid": str(_js["d"]["data"]["custom_id"].split("-")[0]), "topicid": str(uuid)}):
														await _col.users.insert_one({
															"userid": str(_js["d"]["data"]["custom_id"].split("-")[0]),
															"topicid": uuid,
															"status": "TALKING",
															"ismuted": True
														})
													else:
														await _col.users.update_one({
															"userid": str(_js["d"]["data"]["custom_id"].split("-")[0]),
															"topicid": uuid,
														},
														{
															"$set": {
																"status": "TALKING"
															}
														})

													await bot.http.request(
														Route(
															"POST",
															f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
														),
														json={
															"type": 7, 
															"data": {
																"flags": 64,
																"embeds": _js["d"]["message"]["embeds"],
																"tts": False,
																"components": [{
																	"type": 1,
																	"components": [
																		create_button(
																			label="✅ Accepted",
																			style=3,
																			disabled=True
																		)
																	]
																}]
															}
														}
													)

													await _mem.add_roles(_role)
													await _mem.edit(mute=False)

											elif _js["d"]["data"]["custom_id"].split("-")[-1] == "reject":
												await _col.waitingtalk.delete_one({
													"userid": str(_js["d"]["data"]["custom_id"].split("-")[0]),
													"topicid": uuid,
												})

												await bot.http.request(
													Route(
														"POST",
														f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
													),
													json={
														"type": 7, 
														"data": {
														"flags": 64,
														"embeds": _js["d"]["message"]["embeds"],
															"tts": False,
															"components": [{
																"type": 1,
																"components": [
																	create_button(
																		label="❌ Rejected",
																		style=4,
																		disabled=True
																	)
																]
															}]
														}
													}
												)

										else:
											await bot.http.request(
												Route(
													"POST",
													f"/interactions/{_js['d']['id']}/{_js['d']['token']}/callback"
												),
												json={
													"type": 7, 
													"data": _js["d"]["message"]
												}
											)

								elif _js["t"] == "GUILD_MEMBER_UPDATE":
									_guild = bot.get_guild(int(_js["d"]["guild_id"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["user"]["id"]))
									_find = discord.utils.get(_mem.roles, id=int(_vcch["techtalk"]["roles"]["handup"]))

									if not _find:
										# print(_js["d"])
										if await _db.DEVThailandStage.users.find_one({"userid": str(_js["d"]["user"]["id"]), "topicid": uuid}):
											await _db.DEVThailandStage.users.update_one({
												"userid": str(_js["d"]["user"]["id"]),
												"topicid": uuid
											},
											{
												"$set": {
													"status": "NULL",
													"ismuted": True
												}
											})

											await _col.waitingtalk.delete_one({
												"userid": str(_js["d"]["user"]["id"]),
												"topicid": uuid
											})

											# Mute Microphone
											await _mem.edit(mute=True)

								elif _js["t"] == "VOICE_STATE_UPDATE" and str(_js["d"]["channel_id"]) == vcid:
									if _js["d"]["self_mute"] or _js["d"]["deaf"]:
										_find = await _db.DEVThailandStage.users.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": uuid})
										if not _find is None:
											if _find["ismuted"] == True and not _js["d"]["mute"]:
												await _db.DEVThailandStage.users.update_one({
													"userid": str(_js["d"]["member"]["user"]["id"]),
													"topicid": uuid
												},
												{
													"$set": {
														"ismuted": False
													}
												})
											else:
												await _db.DEVThailandStage.users.update_many({
													"userid": str(_js["d"]["member"]["user"]["id"]),
													"topicid": uuid
												},
												{
													"$set": {
														"status": "NULL",
														"ismuted": True
													}
												})
												

												await _col.waitingtalk.delete_one({
													"userid": str(_js["d"]["member"]["user"]["id"]),
													"topicid": uuid
												})

												# Remove Role
												_guild = bot.get_guild(int(_js["d"]["guild_id"]))
												_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
												_role = discord.utils.get(_mem.roles, id=int(_vcch["techtalk"]["roles"]["handup"]))

												if _role:
													await _mem.remove_roles(_role)
													await _mem.edit(mute=True)

												# await _msgdata.edit(components=[Button(label="Hand up ✋", disabled=False, custom_id=uuid)])


								elif _js["t"] == "VOICE_STATE_UPDATE" and str(_js["d"]["channel_id"]) != vcid and _js["d"]["channel_id"] != None:
									_guild = bot.get_guild(int(_js["d"]["guild_id"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
									if await _db.DEVThailandStage.waitingtalk.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": uuid}):
										await _col.waitingtalk.delete_one({
											"userid": str(_js["d"]["member"]["user"]["id"]),
											"topicid": uuid
										})

										# Remove Role
										_role = discord.utils.get(_guild.roles, id=int(_vcch["techtalk"]["roles"]["handup"]))

										if _role:
											await _mem.remove_roles(_role)

										await _mem.edit(mute=False)

									if await _db.DEVThailandStage.users.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": uuid, "status": "READYLEAVE"}):
										await _db.DEVThailandStage.users.update_one({
											"userid": str(_js["d"]["member"]["user"]["id"]),
										},
										{
											"$set": {
												"status": "SALFLEAVE"
											}
										})

										# Remove Role
										_role = discord.utils.get(_guild.roles, id=int(_vcch["techtalk"]["roles"]["handup"]))

										if _role:
											await _mem.remove_roles(_role)

										await _mem.edit(mute=False)
										
								elif _js["t"] == "VOICE_STATE_UPDATE" and _js["d"]["channel_id"] == None:
									_guild = bot.get_guild(int(_js["d"]["guild_id"]))
									_mem = discord.utils.get(_guild.members, id=int(_js["d"]["member"]["user"]["id"]))
									_find =  await _db.DEVThailandStage.users.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": uuid, "status": "READYLEAVE"})

									if await _db.DEVThailandStage.users.find_one({"userid": str(_js["d"]["member"]["user"]["id"]), "topicid": uuid}):
										await _db.DEVThailandStage.users.update_one({
											"userid": str(_js["d"]["member"]["user"]["id"]),
										},
										{
											"$set": {
												"status": "FORCELEAVE"
											}
										})

										# Remove Role
										_role = discord.utils.get(_guild.roles, id=_vcch["techtalk"]["roles"]["handup"])
										await _mem.remove_roles(_role)

								elif _js["t"] == "MESSAGE_UPDATE" and str(_js["d"]["channel_id"]) == chid:
									if _js["d"]["components"][0]["components"][0]["label"] == "Ended":
										await _db.DEVThailandStage.users.update_one({
											"topicid": uuid
										},
										{
											"$set": {
												"status": "SALFLEAVE"
											}
										})
											

										bot.loop.create_task(__unmute(_uid=uuid))
										return


				except asyncio.TimeoutError:
					pass

			except Exception as e:
				print("[Error Task]: %s" % e)

async def __unmute(_uid):
	global _vcch

	_db = await __connectmongodb()

	_find = await _db.DEVThailandStage.topic.find_one({
		"topicid": _uid
	})

	if not _find is None:
		for _data in await _db.DEVThailandStage.users.find({"topicid": _uid}).to_list(100):
			_guild = bot.get_guild(int(_vcch["techtalk"]["guildserver"]))
			_mem = discord.utils.get(_guild.members, id=int(_data["userid"]))

			await _mem.edit(mute=False)

			_db.DEVThailandStage.users.delete_one({
				"userid": _data["userid"],
				"topicid": _uid
			})

async def __isended(_uid, _msgdata):
	_db = await __connectmongodb()
	is_update = False
	lastest_update = ""

	while True:
		_find = await _db.DEVThailandStage.topic.find_one({
			"topicid": _uid
		})

		if not is_update:
			lastest_update = _find["topicdetails"]["update_at"]
			is_update = True

		try:
			if _find["topicdetails"]["end"].replace(microsecond=0).timestamp() <= datetime.datetime.now().replace(microsecond=0).timestamp() and not _find["isforcestart"]:
				await _db.DEVThailandStage.topic.delete_one({
					"topicid":  _uid
				})

				await _msgdata.edit(components=[
					create_actionrow(create_button(
						label="Ended",
						style=2,
						custom_id=_uid,
						disabled=True
					))
				])

				break

			if _find["topicdetails"]["update_at"].timestamp() != lastest_update.timestamp():
				if not _find["isforcestart"] and _find["topicisstart"]:
					await _db.DEVThailandStage.topic.update_one({
						"topic_id":  _uid
					},
					{
						"$set": {
							"isforcestart": False,
							"topicisstart": False
						}
					})

					await _msgdata.edit(components=[
						create_actionrow(create_button(
							label="Ended",
							style=2,
							custom_id=_uid,
							disabled=True
						))
					])

					break

			await asyncio.sleep(1)

		except Exception as e:
			await _msgdata.edit(components=[
				create_actionrow(create_button(
					label="Ended",
					style=2,
					custom_id=_uid,
					disabled=True
				))
			])
			pass

async def __connectmongodb():
	global _config
	_ = ""

	if _config["mongodb"]["auth"]["enabled"]:
		_ = "%s:%s@%s:%s" % (_config["mongodb"]["auth"]["user"],_config["mongodb"]["auth"]["passwd"],_config["mongodb"]["host"],_config["mongodb"]["port"])
	else:
		_ = "%s:%s" % (_config["mongodb"]["host"],_config["mongodb"]["port"])
		
	try:
		client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://"+_, serverSelectionTimeoutMS=5000)
		await client.server_info()

		dblist = await client.list_database_names()

		if not _config["mongodb"]["db"] in dblist:
			logmain.error("Nothing found database %s Createing...." % _)
			await __createdb(client=client, col="topic")
			await __createdb(client=client, col="users")
			await __createdb(client=client, col="waitingtalk")

		return client
	except Exception as e:
		logmain.error("Failed to connect server: %s:%s" % (_config["mongodb"]["host"],_config["mongodb"]["port"]))
		logmain.error("Exiting....")

		os._exit(1)

async def __createdb(client, col):
	global _config

	await client[_config["mongodb"]["db"]][col].insert_one({
		"created": True
	})
	await client[_config["mongodb"]["db"]][col].delete_one({
		"created": True
	})
	
async def __vailddatetime(date):
	try:
		datetime.datetime.strptime(date, "%d/%m/%Y %H:%M")

		return True
	except Exception as e:
		return False

if __name__ == "__main__":
	logmain.info("Starting bot.....")

	with open(os.path.join(os.getcwd(), "config.json"), "r", encoding="utf-8") as f:
		_config = json.load(f)
		bot.run(_config["token"])