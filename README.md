# 🤚 Discord Bot for Tech-Talk (Beta)
This is the Discord bot that make the tech talk like Clubhouse, but you can't to verify community Discord server.

Before Installtion, I'll thank **DEV Thailand group** for quiz to build this awesome project.
If you would like to join the group, you can join via this link: https://discord.gg/7BpTK7qsXc

![Example Discord Bot](https://media.discordapp.net/attachments/745354899994312704/865654567667630110/unknown.png)

# ✈️ Prepare
- [Python 3.8](https://www.python.org/downloads/)
- Discord Bot 
- MongoDB Server 4.0+
- Redis Server 15.0+

# 💻Installtion:
You can use this command:

    pip install -r requirements.txt

Before running the Python script. Please config file: [config.json](config.json):
```json
{
    "token": "Your token discord bot.",
    "mongodb": { 
        "host": "Host MongoDB.",
        "port": 27015,
        "auth": { 
            "enabled": false,
            "user": "MongoDB Username",
            "passwd": "MongoDB Password",
            "dbauth": "Database Authenticaation."
        },
        "db": "Database."
    },
    "redis": {
        "host": "Host Redis.",
        "port": 6730
    }
}
```

and discord_config.json:
```json
{
  "techtalk": {
    "textchannel": "Text Channel for topic alerts",
    "voicechannel": "Voice Channel for voice control",
    "controlchannel": "Text Channel for hands up accept",
    "guildserver": "Guild Server",
    "roles": {
      "handup": "Role hand up.",
      "admin": "Role admin.",
      "mod": "Role moderator."
    }
  },
 "slashcommands": {
    "guilds": [
      " Set Guilds ID."
    ],
    "permissions": [
      {
        "id": "ID User & Role.", 
        "type": "Type User or Role. [ role, user ]",
        "is_use": true
      },
      {
        "id": "ID User & Role.", 
        "type": "Type User or Role. [ role, user ]",
        "is_use": true
      },
    ]
  },
   "limit_show_hand_ups": 10
}
```

and finally, run the python script:

    python main.py


# 🗨️ Topic commands
| Commands | Description |
| ------ | ------ |
| /techtalk topic create [start] [end] [topic]  | Create topic. **After Created. Bot will send UUID to edit & delete topic.**  |
| /techtalk topic delete [uuid] | Delete topic by UUID. |
| /techtalk topic list | Show topic list **Not get UUID**. |
| /techtalk topic uuid | Get topic UUID. **After selection. bot will send UUID topic** | 
| /techtalk topic forcestart | Forcestart topic. |
| /techtalk topic forcestop | Forcestop topic. |

# 🗨️ Config commands
| Commands | Description |
| ------ | ------ |
| /techtalk config text [channel_text_id] | Config text channel for topic alerts.  |
| /techtalk config voice [voice_channel_id]  | Config voice channel for voice control. |
| /techtalk config control [channel_text_id]  | Config text channel for hands up accept. |
| /techtalk config rolehandups [role_hand_up]  | Config role hand up. | 
| /techtalk config roleadmin [role_admin]  | Config role admin. |
| /techtalk config rolemod [role_moderator]  | Config role moderator. |
| /techtalk config guild  | Config guild server. |

# 📷 Screenshot
![](https://media.discordapp.net/attachments/745354899994312704/865655749412519956/unknown.png?width=1080&height=377)
![](https://media.discordapp.net/attachments/745354899994312704/865655824729899028/unknown.png)
![](https://media.discordapp.net/attachments/745354899994312704/865655084675629116/unknown.png)


## ไม่มีอะไรล่ะ มีแค่บอกว่า **S O R A C U T E ~ 💗**
![](https://media1.tenor.com/images/e9f734ab809113e9dc6383abb1de9373/tenor.gif?itemid=21692129)
