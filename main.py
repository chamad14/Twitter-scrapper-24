# import asyncio
# from playwright.async_api import async_playwright
# import json

# async def run():
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=False)
#         context = await browser.new_context(
#             storage_state={
#                 "cookies": [
#                     {
#                         "name": "auth_token",
#                         "value": "58bd0bebd9fd6b1a2f75f8a98e3c37341e1c2b1c",
#                         "domain": ".x.com",
#                         "path": "/",
#                         "httpOnly": True,
#                         "secure": True,
#                         "sameSite": "Lax"
#                     }
#                 ]
#             }
#         )
#         page = await context.new_page()
#         all_tweet_data = []  # List to hold all tweet data

#         async def intercept_request(route, request):
#             if "SearchTimeline?variables=" in request.url:
#                 headers = request.headers
#                 headers["Authorization"] = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
#                 await route.continue_(headers=headers)
#                 response = await route.fetch()  # Fetch the response
#                 response_body = await response.body()
#                 data = json.loads(response_body.decode('utf-8'))
#                 all_tweet_data.append(data)  # Append the data to the list
#                 print("Data fetched:", json.dumps(data, indent=2))
#             else:
#                 await route.continue_()

#         await context.route("**/*", intercept_request)

#         tweet_url = "https://x.com/search?q=Nahan&src=trend_click&vertical=trends"
#         await page.goto(tweet_url)

#         # Perform scrolling in a loop to load more content
#         for _ in range(10):  # Adjust the range to scroll more or less
#             await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
#             await page.wait_for_timeout(2000)  # Wait for new content to load
#             await page.evaluate("window.scrollBy(0, -200);")  # Scroll up slightly to trigger new content load

#         # Wait for the network to be idle after scrolling
#         await page.wait_for_load_state('networkidle', timeout=60000)  # Increased timeout

#         # Extract and save the data
#         with open('tweets.json', 'w') as f:
#             json.dump(all_tweet_data, f, indent=2)

#         # Cleanup
#         await context.unroute_all()  # Unroute before closing context or browser
#         await browser.close()

# asyncio.run(run())




#fetch per post
import asyncio
from playwright.async_api import async_playwright
import json
import pandas as pd

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state={
                "cookies": [
                    {
                        "name": "auth_token",
                        "value": "58bd0bebd9fd6b1a2f75f8a98e3c37341e1c2b1c",
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

        intercepted_data = []  # List to store the intercepted data

        # Intercept the network requests and add the Authorization header
        async def intercept_request(route, request):
            if "TweetDetail?variables=" in request.url:
                headers = request.headers
                headers["Authorization"] = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
                await route.continue_(headers=headers)
                response = await route.fetch()  # Fetch the response
                response_body = await response.body()
                data = json.loads(response_body.decode('utf-8'))
                intercepted_data.append(data)  # Save the data to the list
            else:
                await route.continue_()

        await context.route("**/*", intercept_request)

        tweet_url = "https://x.com/tanyarlfes/status/1821492866276893012"
        await page.goto(tweet_url)

        # Wait for a tweet to be loaded
        await page.wait_for_selector('article[data-testid="tweet"]')

        for _ in range(4):  # Scroll down 1 time
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(3000)  # Wait for 3 seconds after each scroll

        # Save the intercepted data to a JSON file
        with open("intercepted_data.json", "w") as json_file:
            json.dump(intercepted_data, json_file, indent=2)

        await browser.close()

    # Process the JSON file
    process_json("intercepted_data.json")

def process_json(json_file_path: str):
    with open(json_file_path, "r") as file:
        data = json.load(file)

    # Parse the intercepted data
    all_tweet_data = []
    for item in data:
        parsed_tweets = parse_tweet(item)
        all_tweet_data.extend(parsed_tweets)

    # Save the parsed tweet data to a CSV file
    if all_tweet_data:
        df = pd.DataFrame(all_tweet_data)
        df.to_csv("parsed_tweet_data.csv", index=False)
        print(f"Tweet data saved to parsed_tweet_data.csv")
    else:
        print("No tweet data found.")

def parse_tweet(data: dict) -> list:
    """Parse the intercepted tweet JSON dataset for the most important fields."""
    results = []

    # Path to the entries containing tweet data
    entries = data.get("data", {}).get("threaded_conversation_with_injections_v2", {}).get("instructions", [{}])[0].get("entries", [])
    
    for entry in entries:
        tweet_data = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
        
        if not isinstance(tweet_data, dict):
            continue
        
        legacy = tweet_data.get("legacy", {})
        entities = legacy.get("entities", {})
        core_user = tweet_data.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
        
        tweet_info = {
            "views": tweet_data.get("views", {}).get("count"),
            "bookmark_count": legacy.get("bookmark_count"),
            "hashtags": [hashtag.get("text") for hashtag in entities.get("hashtags", []) if isinstance(hashtag, dict)],
            "quote_count": legacy.get("quote_count"),
            "reply_count": legacy.get("reply_count"),
            "retweet_count": legacy.get("retweet_count"),
            "favorite_count": legacy.get("favorite_count"),
            "full_text": legacy.get("full_text"),
            "screen_name": core_user.get("screen_name")
        }
        
        results.append(tweet_info)
    
    return results

asyncio.run(run())

