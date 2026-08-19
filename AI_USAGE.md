# AI Usage Log

This log records the implementation prompts used in this session, the tools used, and manual fixes.

## Implementation prompts

1. `set up a django + drf project in this folder, call it backend/. sqlite db. one app called circles. drf should use TokenAuthentication by default. give me a requirements.txt and a proper .gitignore. don't build any of the actual logic yet, I just want it running with manage.py runserver and the circles app registered and empty`
   - Tools: PowerShell, pip, django-admin, apply_patch, Django checks/migrations.
   - Manual fix: moved the initially misplaced `circles` directory into `backend/`.

2. `inside circles, I need these models: Circle ... Contribution ... no DecimalField, no float, anywhere. register the models in admin.py and show me the migration before running it`
   - Tools: apply_patch, makemigrations, file inspection.
   - Manual fix: migration was deliberately left unapplied until later testing.

3. `add /api/auth/register/ and /api/auth/login/ ... use the built in Token model ... wire up urls. give me curl commands to test both`
   - Tools: apply_patch and Django check.
   - Manual fix: switched PowerShell testing from native curl JSON to `ConvertTo-Json`/`Invoke-RestMethod`.

4. `add these, all need token auth: POST /api/circles/, POST /api/circles/join/, GET /api/circles/<id>/ ... use select_for_update ... explain why count/check without locking is broken`
   - Tools: apply_patch and Django check.
   - Manual fix: registered circle routes in the project URL configuration.

5. `once a circle hits 4 members, auto create round 1 ... POST /api/rounds/<id>/contribute/ ... use Decimal with ROUND_HALF_UP ... transaction.atomic() with select_for_update ... test 3333 and 3`
   - Tools: apply_patch, Django check, Python calculation.
   - Manual fix: none.

6. `POST /api/rounds/<id>/approve/ ... admin only ... floor payout ... close round ... mark recipient paid_out ... create next round ... explain select_for_update`
   - Tools: apply_patch and Django check.
   - Manual fix: none.

## Testing/troubleshooting prompts

Subsequent prompts asked for step-by-step PowerShell/curl testing, including registration, circle creation, joining, contributions, approval, and troubleshooting connection/JSON errors. They resulted in guidance only and no code changes.

Manual fixes during testing: omitted copied PowerShell prompt markers (`PS D:\ROSCA>` and `>>`), used `Invoke-RestMethod` because native `curl.exe` quoting was unreliable, assigned `$inviteCode` from the circle response, restarted the development server when it was stopped, and applied the pending circles migration with `python manage.py migrate`.
