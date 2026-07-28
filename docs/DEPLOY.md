# Running this where you can reach it

The app runs on your own machine and is reached over a Cloudflare tunnel. That
is a decision, not a limitation we have not got around to — this page records
why, so it does not get relitigated.

## Why it is not on Vercel

Three limits, none of which has a workaround:

| Vercel Hobby | This app |
| --- | --- |
| 250 MB unzipped function bundle | `torch` alone is 529 MB; the full env is 1.4 GB |
| 60s function timeout | A hunt scrapes, embeds and scores for 2–4 minutes |
| Read-only filesystem, `/tmp` wiped between invocations | SQLite is the whole database |

Dropping `sentence-transformers` for a hosted embedding API would fix the first
two, and cost money per hunt. The point of this app is that a hunt is free.

## Why not Cloudflare Workers, Render, or Fly

- **Workers** run Python through Pyodide, which cannot load native wheels.
  `torch` and `sentence-transformers` are native. Containers are paid.
- **Render free** gives 512 MB RAM (the embedding model does not fit), spins
  down after 15 minutes idle (which kills scheduled hunting), and has no
  persistent disk below the paid tier (which loses the database on restart).
- **Fly / Oracle Always Free** would technically work. They also move the app
  onto a datacenter IP, and job boards throttle those hard. The whole value of
  this thing is what it manages to scrape.

## What to do instead

```bash
brew install cloudflared     # once
./share.sh
```

`share.sh` starts the app and prints a `*.trycloudflare.com` URL. Free, no
account, no card.

It refuses to run unless `APP_PASSWORD` is set in `.env`, because everything
behind that URL is personal — your resume, your connections export, your
drafts. With it set, the browser asks for the password once; the username is
ignored.

The URL changes each time you run it. If you want one that does not, put a
domain on Cloudflare and use a named tunnel with Cloudflare Access, which is
also free and gives you an email login instead of a shared password.

## What this costs you

The laptop has to be awake. That is already true — scheduled hunting, the
SQLite file and the local embedding model all live here.
