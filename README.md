# 🤚 Bot discord Tech-Talk (Beta)
Bot discord for make techtalk like clubhouse but you can able not to verify community discord server.

![Example bot discord](https://media.discordapp.net/attachments/745354899994312704/865654567667630110/unknown.png)

# ✈️ Prepare
- Python 3.8
- Discord bot 
- MongoDB Server 4.0+
- Redis Server 15.0+

# 💻Installtion:
You can able to use this command:

    pip install -r requirements.txt

Before run python script. Please config file comfig.json:
```json
{
    "token": "Your token discord bot.",
    "mongodb": { 
        "host": "Host MongoDB.",
        "port": 27015,
        "auth": { 
            "enabled": false,
            "user": " Username MongoDB.",
            "passwd": "Password MongoDB.",
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
```

and lastest run python script:

    python main.py


# 🗨️ Topic commands
| Commands | Description |
| ------ | ------ |
| /techtalk topic create [start] [end] [topic]  | Create topic. **After Created. Bot will send UUID to edit & delete topic.**  |
| /techtalk topic delete [uuid] | Delete topic by UUID. |
| /techtalk topic list | Show topic list **Not get UUID**. |
| /techtalk topic uuid | Get topic UUID. **After select. bot will send UUID topic** | 
| /techtalk topic forcestart | Forcestart topic. |
| /techtalk topic forcestop | Forcestop topic. |

# 🗨️ Config commands
| Commands | Description |
| ------ | ------ |
| /techtalk config text [channel_text_id] | Config text channel for alert topic.  |
| /techtalk config voice [voice_channel_id]  | Config voice channel for control voice. |
| /techtalk config control [channel_text_id]  | Config text channel for accept hands up. |
| /techtalk config rolehandups [role_hand_up]  | Config role hand up. | 
| /techtalk config roleadmin [role_admin]  | Config role admin. |
| /techtalk config rolemod [role_moderator]  | Config role moderator. |

# 📷 Screenshot
![](https://media.discordapp.net/attachments/745354899994312704/865655749412519956/unknown.png?width=1080&height=377)
![](https://media.discordapp.net/attachments/745354899994312704/865655824729899028/unknown.png)
![](https://media.discordapp.net/attachments/745354899994312704/865655084675629116/unknown.png)

# Lastest 
Thank **DEV Thailand group** for quiz to build awsome project.

## ไม่มีอะไรล่ะ มีแค่บอกว่า **S O R A C U T E ~ 💗**
![](https://media1.tenor.com/images/e9f734ab809113e9dc6383abb1de9373/tenor.gif?itemid=21692129)
