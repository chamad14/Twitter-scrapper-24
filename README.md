twitter scraper made with playwright. this scraper is made to scrape all the comment like favorite and any other data that contains in a tweet.

at main.py you'll find these

browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state={
                "cookies": [
                    {
                        "name": "auth_token",
                        "value": "your auth token goes here",
                        "domain": ".x.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax"
                    }
                ]
            }
        )
        page = await context.new_page()

how to get auth token:
1. go to x.com
2. login with any method as you desire
3. after logging in, open dev tools, go to application tab and go to cookies
4. there's a cookie name x.com and you will find the auth-token cookie
5. copy that cookie value

and then you'll find this too

async def intercept_request(route, request):
            if "TweetDetail?variables=" in request.url:
                headers = request.headers
                headers["Authorization"] = "Bearer bearer token goes here"
                await route.continue_(headers=headers)
                response = await route.fetch()  # Fetch the response
                response_body = await response.body()
                data = json.loads(response_body.decode('utf-8'))

                intercepted_data.append(data)  # Save the data to the list
            else:
                await route.continue_()

how to get bearer token
1. same step open dev tools
2. go to network tabs
3. select any request (xhr) then go to the header tab and you'll find your bearer token there
<img width="586" alt="Screenshot 2024-08-12 at 01 11 52" src="https://github.com/user-attachments/assets/55491283-3aa4-4702-8b2f-32c817004987">

type ur tweet url here
tweet_url = "your tweet url here"

and adjust for how many scrolling you want more scrolling == more tweets
for _ in range(4):  # Scroll down 1 time
