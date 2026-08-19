# ROSCA

Backend + mobile app for a rotating savings and credit circle (ROSCA). A
circle has up to 4 members. Members take turns being the "recipient" for a
round — everyone else contributes, and once all non-recipient members have
paid in, the admin approves the round and the payout goes out. Then the next
person in line becomes recipient for the next round.

Backend is Django + DRF, token auth. Mobile is Expo/React Native, plain
`fetch` against the API, no offline storage — the auth token just lives in
memory for now.

## Backend setup

From `backend/`:

```
python -m venv venv
venv\Scripts\activate        # on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Runs on `http://localhost:8000`. `db.sqlite3` is already checked in with
some data in it from earlier testing — delete it and re-run `migrate` if you
want a clean slate.

## Mobile setup

From `mobile/`:

```
npm install
npx expo start
```

Press `w` for web, or scan the QR code with Expo Go. The API client is
hardcoded to `http://localhost:8000/api/` — if you're testing on a physical
phone instead of an emulator/web, `localhost` won't resolve to your laptop,
swap it for your machine's LAN IP in `src/api/client.ts`.

## Curl walkthrough (multiple users)

This runs through creating a circle, filling it with 4 members, running a
contribution round, and approving the payout. Swap in the token/id values
you get back at each step — nothing here is scripted with jq, just copy the
values by hand as you go.

Register 4 users:

```
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d '{"username":"alice","password":"pass1234"}'
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d '{"username":"bob","password":"pass1234"}'
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d '{"username":"carol","password":"pass1234"}'
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d '{"username":"dave","password":"pass1234"}'
```

Each response gives you a `token` and `user_id`. Keep them straight, you'll
need all four tokens below.

Alice creates the circle (she becomes admin, and is auto-added as member
#1):

```
curl -X POST http://localhost:8000/api/circles/ \
  -H "Authorization: Token <alice_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Circle","contribution_amount":100,"penalty_rate":10}'
```

Grab `invite_code` from the response. Bob, Carol and Dave join with it:

```
curl -X POST http://localhost:8000/api/circles/join/ \
  -H "Authorization: Token <bob_token>" \
  -H "Content-Type: application/json" \
  -d '{"invite_code":"<invite_code>"}'
```

(same for carol_token and dave_token). Once the 4th member joins, the
backend auto-creates round 1 with alice (member #1) as recipient.

Check circle state:

```
curl http://localhost:8000/api/circles/<circle_id>/ -H "Authorization: Token <alice_token>"
```

You'll get back `current_round` with a `member_statuses` list — alice shows
as `recipient`, bob/carol/dave show as `waiting`. Note the round's `id`.

Bob, carol and dave contribute:

```
curl -X POST http://localhost:8000/api/rounds/<round_id>/contribute/ -H "Authorization: Token <bob_token>"
curl -X POST http://localhost:8000/api/rounds/<round_id>/contribute/ -H "Authorization: Token <carol_token>"
curl -X POST http://localhost:8000/api/rounds/<round_id>/contribute/ -H "Authorization: Token <dave_token>"
```

After the last one, re-check the circle — round status flips to
`PENDING_APPROVAL`. Alice (admin) approves it:

```
curl -X POST http://localhost:8000/api/rounds/<round_id>/approve/ -H "Authorization: Token <alice_token>"
```

Round closes, payout amount comes back in the response, and a new round 2
gets created with bob as recipient. Check the circle again to see it.

## Assumptions

The spec for CircleDetail left a couple of things open, so here's what I
went with:

- **"Current round" isn't a field the model tracks explicitly** — a circle
  just has a list of rounds. I'm treating "the current round" as whichever
  one has the highest `round_number`, since a new round only gets created
  once the previous one is approved, so there's never more than one
  in-flight round at a time.
- **Who gets the Contribute button.** The spec says "anyone who isn't the
  recipient," but the contribute endpoint only lets you submit for
  yourself — there's no member id in that request, it acts on whoever the
  auth token belongs to. So the button only shows on your own row, not on
  every non-recipient row in the list. Didn't think it made sense to show a
  button that would just 400 if you tapped it on someone else's row.
