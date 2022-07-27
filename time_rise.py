from pyrogram import Client, filters
import time

app = Client("my_account", api_id=17996398, api_hash="6fbe219f0f1dd44e27e2dea64f3b771e")

config = {"api_id": 17996398, "api_hash": "6fbe219f0f1dd44e27e2dea64f3b771e"}

@app.on_message()
def echo(client, message):
    if not message.text == 'AAA^@!HJCGABISJDI@&!LKA:SKD<AW' and message.text == 'active bro':
        while True:
            app.send_message(-792645565, 'AAA^@!HJCGABISJDI@&!LKA:SKD<AW')
            time.sleep(30)

def on_ready():
    print('𝐎Б𝐏𝐀Б𝐎𝐓ЧИ𝐊 𝟑𝐀П𝐘Щ𝐄𝐇')

if __name__ == '__main__':
    on_ready()
    app.run()