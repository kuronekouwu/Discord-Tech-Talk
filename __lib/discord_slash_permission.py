import json
import os

from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission

def getdata():
	# Create Guild 
	guilds = []
	permissions = []
	_permission = {}

	if len(_permission) == 0:
		with open(os.path.join(os.getcwd(), "discord_config.json"), "r", encoding="utf-8") as f:
			_config = json.load(f)
			for __guilds in _config["slashcommands"]["guilds"]:
				guilds.append(int(__guilds, 10))

			for __permissions in _config["slashcommands"]["permissions"]:
				permissions.append(
					create_permission(
						id=int(__permissions["id"], 10),
						id_type=SlashCommandPermissionType.ROLE if __permissions["type"] == "role" else SlashCommandPermissionType.USER,
						permission=__permissions["is_use"]
					)
				)
					
			for _data in guilds:
				_permission.update({
					_data : permissions 
				})
				
	return [guilds, _permission]
