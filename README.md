## SAmino
SAmino is unofficial client for [Aminoapps](https://aminoapps.com/) API in Python. 

## Installation
You can use either `python3 setup.py install` or `pip3 install samino` to install. This module is tested on Python 3.9+.

## Contributing
SAmino is open source module, anyone can contribute. Please see the [Github Repository](https://github.com/SirLez/SAmino)

## Features
- Faster than other [Aminoapps](https://aminoapps.com/) python modules
- Supports async and sockets, events
- Easy and sample to use
- No `Too many requests.`
- Continual updates and bug fixes
- Have alot of useful functions

## Examples
#### Get SessionID
```py
import samino

client = samino.Client()
client.login("< email >", "< password >")
print(client.sid)
```
#### Login with SessionID
```py
import samino

client = samino.Client()
client.sid_login("< sid >")
print(client.sid)
```
#### Send a message in chat
```py
import samino

client = samino.Client()
client.login("< email >", "< password >")
path = client.get_from_link("< chat link >")
local = samino.Local(path.comId)
local.send_message(path.objectId, "< message >")
```
