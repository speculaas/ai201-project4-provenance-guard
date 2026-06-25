# Sample Requests

Copy-paste curl commands for local testing. Start the server first:

```bash
python app.py
```

## Submit Text

```bash
curl -s -X POST http://localhost:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "The sun dipped below the horizon, painting the sky in hues of amber and rose. I sat on the porch, coffee in hand, watching the neighborhood slowly go quiet.", "creator_id": "test-user-1"}' \
  | python -m json.tool
```

Save the `content_id` from the response for appeal testing.

## Appeal a Decision

Replace `PASTE_CONTENT_ID_HERE` with a `content_id` from a prior submission:

```bash
curl -s -X POST http://localhost:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "PASTE_CONTENT_ID_HERE", "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."}' \
  | python -m json.tool
```

## View Audit Log

```bash
curl -s http://localhost:5000/log | python -m json.tool
```

## Rate Limit Test

Sends 12 rapid requests (limit is 10/minute). Expect `200` for the first 10, then `429`:

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
```

## API Discovery

```bash
curl -s http://localhost:5000/ | python -m json.tool
```
