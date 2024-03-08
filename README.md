# ngbot
New generation Telegram bot

*How to use*

1. Download Dockerfile
2. Create config.yml:
```
    ---
    api_url: 'https://api.telegram.org/bot'
    token: '<telegram token without bot_>'
    log: '/var/log/ngbot/'
```   
3. Build docker image from Dockerfile:
`docker build --no-cache -t ngbot .`
4. Run container from image:
`docker run -d ngbot`
