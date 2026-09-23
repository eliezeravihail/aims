# A default timeout for a session

Our services make many calls through one `requests.Session`. Every call has to repeat `timeout=`, and a call where
someone forgot it can hang forever.

Let us set a default timeout once, so every request made through that session uses it unless the call passes its
own `timeout`.
