# gabbro-healthcheck-watcher

Just a little script to be run on a vps and listen to pings from my home server. If it goes too long without a ping it notifies me that my server is probably down.

## Usage

Copy .env file and fill it in

```shell
cp template.env .env
```

Run with docker compose

```shell
docker compose up -d
```
