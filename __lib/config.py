import os
import json

async def getconfig(filename):
	with open(os.path.join(os.getcwd(), filename), "r", encoding="utf-8") as f:
		return json.load(f)

async def saveconfig(filename, _js):
	with open(os.path.join(os.getcwd(), filename), "w", encoding="utf-8") as f:
		json.dump(_js, f, indent=2)
