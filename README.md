# MovieBot v2.0 (Safe Code Bot)

Features:
- Admin replies to a post with /attach → bot shortens links, generates code, posts safe comment (auto-deletes after 10 min) and saves to MongoDB.
- Auto XTG shortener
- Auto code generator D-001 ...
- Admin panel: /panel, /nextcode, /list, /delete, /backup
- Users DM bot with code → bot sends shortlinks + demo video
- Heroku / Railway / Render ready

Setup:
1. Create repo with files.
2. Fill `config.env` values or set Heroku config vars.
3. Deploy on Heroku (worker dyno) or run on VPS.
