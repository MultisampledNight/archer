# Archer
Just a normal Bot for Reaction Roles, thought for the German Arch Linux Discord
server.

## What are Reaction Roles?
With Reaction Roles, you can easily let your members on your Discord server give
roles on their own. For example, let's say there is a #coding-help channel on
your server, where people can help each other when they have coding problems.
Let's say, on your server are 2 languages dominant for some reason: `Python` and
`C`. Then you could set up Reaction Roles to give roles. For example, if a
question about Python gets asked in #coding-help, it might be just overseen if
it got no ping at all. But if the OP can directly ping the `Python` role, he can
receive quick responses. The persons who don't know about Python probably won't
give the Python role to themselves, so no person is woken up for nothing.

## Hosting instructions
If you want to use the bot on your own Server, you have to host it on your own.
Please note that the code is not one of the best. Thus, consider that the bot's
messages are _all_ German.

```sh
git clone https://github.com/MultisampledNight/archer
cd archer
python3 -m venv archer_venv
source archer_venv/bin/activate
pip install -r requirements.txt
```
Then, create a new file called `TOKEN` in the future working directory of the
bot. In there, store ONLY the token you get from the [Discord Developer
Portal](https://discord.com/developers/applications/) when creating a new
application. Make sure not to leak it.

Next, create a file `ADMIN-ID` in the same folder as the token and put your
Discord-ID into it. It will be used as a mod-role override.

Afterwards, in the same terminal where
you created the venv before, do:
```sh
python3 main.py
```
...and the bot should run now.


