import asyncio
import requests
from telethon import TelegramClient
import os
import time
import vk_api
import telebot
from telebot import types

# Get your bot token from BotFather
TOKEN = '7252231680:AAGh6ctCFUN3RgUKXPzYQlXD1Ggoco-H0JQ'

# Create a bot instance
bot = telebot.TeleBot(TOKEN)

# Telegram credentials
api_id = 23678385 
api_hash = 'd85d9821b3ced9ccf021eb51e4799fe5'
session_name = 'my_session1'
bot_username = '@gigachat_bot'

# Chad GPT credentials
CHAD_API_KEY = 'chad-0bc5e8e3c01040e4ba9e00ebc9bd04a93o1kwtun'

# VK credentials
VK_TOKEN = 'vk1.a.uFIDrOm9oR8pwirrvZVoY2SgIgtUV92P0syH7DP9hUW0OLSN7IvakdIPv_xxPEdx8mficmpIFcsOZ0xdOuKRd-iHgzc3WtncRGjL9XCntVUQ9NhKJ3RqMRAWMN09MFBpZk09pPiHgF3G0tJ6ZoOCCaA80USvq1Z9oDcCoOcSIXa2mnXxQJDh0Br-HBhEIGUZUKvNQEY6NqyaB8QIHrs3PA'
VK_GROUP_ID = '228650394'

client = TelegramClient(session_name, api_id, api_hash, system_version="4.16.30-vxCUSTOM")

# Function to send a message to a channel
def send_to_channel(message, name_pic, channel_id):
    img = open(name_pic, 'rb') # Replace with your image path
    bot.send_photo(channel_id, img)
    bot.send_message(channel_id, message.strip())

def generate_text(theme):
    request_json = {
        "message": theme,
        "api_key": CHAD_API_KEY
    }
    response = requests.post(url='https://ask.chadgpt.ru/api/public/gpt-4o-mini', json=request_json)
    
    if response.status_code != 200:
        print(f'Error! HTTP response code: {response.status_code}')
        return None
    
    resp_json = response.json()
    if resp_json['is_success']:
        resp_msg = resp_json['response']
        used_words = resp_json['used_words_count']
        print(f'Bot response: {resp_msg}\nWords used: {used_words}')
        return resp_msg
    else:
        error = resp_json['error_massage']
        print(f'Error: {error}')
        return None

async def generate_image(chat, theme):
    await client.send_message(chat, f"Creating an image about: {theme}")
    print('Generating image...')
    
    start_time = time.time()
    timeout = 120  # Maximum time to wait in seconds
    
    while time.time() - start_time < timeout:
        async for message in client.iter_messages(chat, limit=1):
            if message.photo:
                # Get the directory path where the script is located
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # Create a file name using the current time for uniqueness
                file_name = f"generated_image_{int(time.time())}.jpg"
                # Form the full file path
                file_path = os.path.join(script_dir, file_name)
                # Save the image
                await client.download_media(message.photo, file=file_path)
                print(f"Image saved: {file_path}")
                return file_path
        await asyncio.sleep(5)
    
    print("Timeout reached. Image not received.")
    return None

def post_to_vk(text, image_path):
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    upload = vk_api.VkUpload(vk_session)
    photo = upload.photo_wall(image_path, group_id=int(VK_GROUP_ID))[0]
    
    attachments = f'photo{photo["owner_id"]}_{photo["id"]}'
    
    vk = vk_session.get_api()
    vk.wall.post(owner_id=f'-{VK_GROUP_ID}', message=text.replace('\n', ' ').strip(), attachments=attachments)
    print("Post successfully published on VK")

async def main():
    await client.start()
    
    chats = [dialog for dialog in await client.get_dialogs() if dialog.entity.username == bot_username.lstrip('@')]
    
    if chats:
        chat = chats[0]
        try:
            with open('темы.txt', 'r', encoding='utf-8') as f:
                themes = f.read().splitlines()
        except FileNotFoundError:
            print("File 'темы.txt' not found.")
            return
        except IOError:
            print("Error reading file 'темы.txt'.")
            return

        if not themes:
            print("File 'темы.txt' is empty.")
            return

        for theme in themes:
            theme = theme.strip()
            if not theme:
                continue # Skip empty lines 

            print(f"Processing theme: {theme}")

            text = generate_text(theme)
            if text:
                image_path = await generate_image(chat, theme)
                if image_path:
                    try:
                        channel_id = '@itmatearturdenis'  # Replace with your channel ID
                        message = text
                        name_pic = image_path
                        send_to_channel(message, name_pic, channel_id) # Call the function to send a message to a channel

                        post_to_vk(text, image_path)
                        print(f"Post for theme '{theme}' successfully published")
                    except Exception as e:
                        print(f"Error publishing post for theme '{theme}': {str(e)}")
                    finally:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            print(f"Image '{image_path}' successfully deleted")
                else:
                    print(f'Failed to generate image for theme: {theme}')
            else:
                print(f'Failed to generate text for theme: {theme}')

            await asyncio.sleep(5) # Delay between theme processing (to avoid overloading the bot)

        print("Processing all themes completed.")
    else:
        print('Bot not found')

async def run():
    await client.start()
    await main()
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run())