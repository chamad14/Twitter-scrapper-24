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
                        "value": "auth token goes here",
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
                headers["Authorization"] = "Bearer *bearer token goes here*"
                await route.continue_(headers=headers)
                response = await route.fetch()  # Fetch the response
                response_body = await response.body()
                data = json.loads(response_body.decode('utf-8'))
                intercepted_data.append(data)  # Save the data to the list
            else:
                await route.continue_()

        await context.route("**/*", intercept_request)

        tweet_url = "tweet url goes here"
        await page.goto(tweet_url)

        # Wait for a tweet to be loaded
        await page.wait_for_selector('article[data-testid="tweet"]')

        for _ in range(1):  # Scroll down 1 time
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

