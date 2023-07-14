# Twitch_Crawler

Twitch Crawler is a Python application that allows you to retrieve and analyze Twitch chat messages from multiple streams anonymously and without authorization. It provides a convenient way to monitor and analyze chat interactions, gather data for research purposes, or gain insights into viewer engagement.

## Features

- Real-time chat message retrieval: Twitch Crawler connects to the Twitch IRC chat servers and captures chat messages as they occur in real-time.
- Multi-channel support: You can specify a list of channels to monitor, and Twitch Crawler will retrieve chat messages from all the specified channels simultaneously.
- Easy integration: The application provides a WebSocket API that enables seamless integration with other systems or applications for further processing or visualization of the chat data.
- RESTful API: Twitch Crawler supports a RESTful API that allows you to retrieve livestream information based on a keyword-based search in the database. You can search for livestreams based on the game name, streamer information (name or user ID), and more.

## Installation

To install and set up Twitch Crawler, follow these steps:

1. Clone the GitHub repository: `git clone https://github.com/your-username/twitch-crawler.git`
2. Change into the project directory: `cd Twich_Crawler`
3. Create a `.env` file in the root directory with the following contents:

```plaintext
CLIENT_ID=your client Id
ACCESS_TOKEN=your access token
BASE_URL=https://api.twitch.tv/helix
IGDB_URL=https://api.igdb.com/v4

MONGO_DB=mongodb://localhost:27017/
MONGO_DB_NAME=twitch
MONGO_COLLECTION_NAME=games

HOST_TWITCH=irc.chat.twitch.tv
PORT_TWITCH=667

4. Create another .env file in the Twitch_Ctrl directory with the following contents:
```plaintext
SOCKET_URL=http://localhost:3000
5. Run in a command line:
```plaintext
docker-compose up
