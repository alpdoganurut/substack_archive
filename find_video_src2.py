# import requests
# from bs4 import BeautifulSoup
# import os
# import subprocess
import asyncio
import json
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import os
import subprocess

from playwright.async_api import async_playwright

# region Configuration
base_url = 'https://www.computerenhance.com'

# List of URLs separated by new lines
_urls_text = """
https://www.computerenhance.com/p/q-and-a-63-2024-08-19
"""
__urls_text = """
https://www.computerenhance.com/p/waste
"""
___urls_text = """
https://www.computerenhance.com/p/prefetching
"""

# Cookies information
_cookies = {
    "__cf_bm": "k8CTBk7jtBaEIbpgFfDzQpzw8Cn7EcKIp6aBGctRsIw-1727880734-1.0.1.1-fJ3EYjeio2gPOuhuqmwc2CTr9F0rp_2iw5rJCwOdNAASWW2vilnc7Yb4P0DHFt_UJR1nlzSwz2nb9_Jpb5c48w",
    "muxData": "mux_viewer_id=07ece308-4c28-403f-98e4-88acb2cca19a&msn=0.01910097529289989&sid=43e7d51b-1277-4034-800c-b7c426f228ac&sst=1727878898471&sex=1727881355010",
    "_gcl_au": "1.1.1035451740.1727867673",
    "ab_experiment_sampled": "%22false%22",
    "ab_testing_id": "%228bf92594-fb4c-4ba2-9979-912a8728657d%22",
    "AWSALBTG": "K58IEmj1YuNjP3X5rlUfIaNb5oFA/7isDdrvUlCHe8mTRJ/zLmD91ZnfpoCOob2DJowtwWbEkuhYmBx3n2hA+V9lGyNYmfvFA4GF5QrvwQqAHcwXKGSJagDuQei5KMRZCcgLKBOO1AAnc5zL23c6QqfKFUPsCiViJSgIgXIC0sbO",
    "AWSALBTGCORS": "K58IEmj1YuNjP3X5rlUfIaNb5oFA/7isDdrvUlCHe8mTRJ/zLmD91ZnfpoCOob2DJowtwWbEkuhYmBx3n2hA+V9lGyNYmfvFA4GF5QrvwQqAHcwXKGSJagDuQei5KMRZCcgLKBOO1AAnc5zL23c6QqfKFUPsCiViJSgIgXIC0sbO",
    "connect.sid": "s%3ARDsTzFN9t5vm2EZz1tsN6TxD6J1DWulF.WR8ldeCmUUkNZwLpOPpX2TFA%2FV04%2FCk7xB5GndMYkZs",
    "cookie_storage_key": "fc096c2a-3f49-46af-8391-9c0f283c0f50"
}
cookie_domain = ".computerenhance.com"

log_output_path = f"video_download_log{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.txt"
error_output_path = "video_download_error.txt"

urls_path = "urls.txt"

is_headless = True
delay_between_page_loads = 0.1
is_download_video = True


# endregion


# region Error File Handling
def append_to_log_file(msg):
    with open(log_output_path, "a") as log_output_file:
        log_output_file.write(f"{msg}\n")


def append_to_error_file(url):
    print(f"Adding error for {url}")
    if is_url_in_error_file(url):
        return
    with open(error_output_path, "a") as error_output_file:
        error_output_file.write(f"{url}\n")


def remove_error_for_url(url):
    # Remove line from error file
    if not os.path.exists(error_output_path):
        return

    with open(error_output_path, "r") as error_output_file:
        lines = error_output_file.readlines()
    with open(error_output_path, "w") as error_output_file:
        for line in lines:
            if line.strip("\n") != url:
                error_output_file.write(line)
            else:
                print(f"Removed error for {url}")


def is_url_in_error_file(url):
    if not os.path.exists(error_output_path):
        return False

    with open(error_output_path, "r") as error_output_file:
        lines = error_output_file.readlines()
        for line in lines:
            if line.strip("\n") == url:
                return True
    return False


# endregion


# region Utils
def download_file_if_doesnt_exists(url, directory):
    filename = os.path.basename(url)
    path = os.path.join(directory, filename)
    # Sanitize
    path = path.replace("%", "_")

    # Check if file exists before downloading
    if not os.path.exists(path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
            print(f'Downloaded: {filename}')
        else:
            print(f'Failed to download: {filename}')

    relative_path = os.path.relpath(str(path))

    return relative_path


async def open_new_page(context, url):
    page = await context.new_page()
    # page.evaluate('window.blur()')  # Take focus away from the window

    await page.goto(url)

    try:
        await page.goto(url)
    except Exception as e:
        append_to_log_file(f"{url}\tERROR\tCouldn't load page\t{e}")
        append_to_error_file(url)
        print(f"Failed to load URL: {url}")
        raise e

    soup = await create_soup(page)

    # Do shit to make sure page loaded
    await page.wait_for_load_state('domcontentloaded')
    # await page.bring_to_front()
    # await page.wait_for_timeout(load_wait_duration)

    # Check if any element contains "Too Many Requests"
    if soup.find_all(string=lambda text: "Too Many Requests" in text):
        print("Error: 'Too Many Requests'")
        append_to_log_file(f"{url}\tERROR\tToo Many Requests")
        append_to_error_file(url)
        return None

    # Find the element with the specified attribute
    paywall_element = await page.query_selector('[data-component-name="Paywall"]')

    # Check if the element exists
    if paywall_element and await paywall_element.is_visible():
        append_to_log_file(f"{url}\tERROR\tPaywall")
        print(f"Paywall error for {url}")
        return None

    await asyncio.sleep(delay_between_page_loads)

    return page


async def create_soup(page): return BeautifulSoup(await page.content(), 'html.parser')


def download_html(soup, file_name_with_extension):
    with open(file_name_with_extension, 'w', encoding='utf-8') as file:
        file.write(str(soup))
        print(f'HTML file saved as: {file_name_with_extension}')


async def download_html_assets_and_disable_js(soup):
    # Subdirectories for assets
    css_directory = os.path.join(os.getcwd(), 'css_files')
    img_directory = os.path.join(os.getcwd(), 'img_files')

    # Create directories if they don't exist
    os.makedirs(css_directory, exist_ok=True)
    os.makedirs(img_directory, exist_ok=True)

    # Download CSS files and replace paths
    for link in soup.find_all('link', rel='stylesheet'):
        css_url = urljoin(base_url, link['href'])

        css_filepath = download_file_if_doesnt_exists(css_url, css_directory)

        # Update the href in the <link> tag to point to the new local file
        link['href'] = css_filepath

        # Download image files and replace paths
    for img in soup.find_all('img'):
        # Check for the standard "src" attribute
        img_url = img.get('src')

        data = None
        # Check if "data-attrs" contains a JSON string with a "src" field
        data_attrs = img.get('data-attrs')
        if data_attrs:
            try:
                data = json.loads(data_attrs)
                img_url = img_url or data.get('src')
            except json.JSONDecodeError:
                print('Warning: Failed to decode JSON in data-attrs')

        # Download main src image if available
        if img_url:
            img_url_full = urljoin(base_url, img_url)
            local_img_path = download_file_if_doesnt_exists(img_url_full, img_directory)
            img['src'] = local_img_path

            # If "data-attrs" has a "src" field, update it as well
            if data_attrs:
                try:
                    data['src'] = local_img_path
                    img['data-attrs'] = json.dumps(data)
                except json.JSONDecodeError:
                    print('Warning: Failed to encode JSON in data-attrs')

        # Remove the "srcset" attribute if present
        if img.has_attr('srcset'):
            del img['srcset']

        # If <picture> is a parent, remove it and keep the <img>
        if img.parent.name == 'picture':
            picture_parent = img.parent
            picture_parent.replace_with(img)
    # Remove all <script> tags
    for script in soup.find_all('script'):
        script.decompose()


def convert_context_cookies_to_header_string(cookies_dict):
    return {'Cookie': ("; ".join([f"{name}={value}" for name, value in cookies_dict.items()]))}


# endregion


async def process_and_download_html(file_name, context, url):
    full_file_name = f"{file_name}.html"

    if os.path.exists(full_file_name) and not is_url_in_error_file(url):
        print(f"Skipping {full_file_name} as it already exists and not in error file.")
        return True

    page = await open_new_page(context, url)

    if not page:
        return False

    soup = await create_soup(page)
    await page.close()

    await download_html_assets_and_disable_js(soup)

    # Remove elements with class names starting with "_video-wrapper"
    for video_wrapper in soup.select('[class^="_video-wrapper"]'):
        video_wrapper.decompose()

    # Remove elements with class names starting with "footer"
    for footer in soup.select('[class^="footer"]'):
        footer.decompose()

    # Remove elements with class names containing "_sidebar_"
    for sidebar_element in soup.find_all(class_=lambda class_name: class_name and '_sidebar_' in class_name):
        sidebar_element.decompose()

    # Download the HTML file
    download_html(soup, full_file_name)

    return True


async def download_comments_html(file_name, context, url):
    full_file_name = f"{file_name}.html"

    if os.path.exists(full_file_name) and not is_url_in_error_file(url):
        print(f"Skipping {full_file_name} as it already exists and not in error file.")
        return True

    page = await open_new_page(context, url)

    if not page:
        return False

    await load_and_expand_all_comments(page)

    soup = await create_soup(page)
    await page.close()

    # Remove elements with class "main-menu-content"
    for menu_element in soup.select('.main-menu-content'):
        menu_element.decompose()

    await download_html_assets_and_disable_js(soup)

    download_html(soup, full_file_name)

    return True


async def load_and_expand_all_comments(page):
    try:
        # Loop to keep clicking the "Load More" button until it no longer exists
        while True:
            # Find and click the button
            load_more_button = await page.query_selector('button.button.collapsed-reply.outline')

            if load_more_button:
                # Click the button
                await load_more_button.click()
                print("Clicked 'Load More' button")

                # Wait for content to load (adjust as necessary)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
            else:
                print("No more 'Load More' buttons found")
                break

        # Find all "Expand full comment" elements
        expand_buttons = await page.query_selector_all('div.show-all-toggle')

        # print count
        print(f"Found {len(expand_buttons)} 'Expand full comment' elements")

        for button in expand_buttons:
            if button and await button.is_visible():
                # Click each button to expand the comment
                print("Clicking 'Expand full comment'")
                # Scroll to the button to ensure it's in view
                # await button.scroll_into_view_if_needed()
                # await page.evaluate('(button) => button.click()', expand_button)
                await button.click(force=True)
                print("Clicked 'Expand full comment' button")

                # Wait a short time for content to expand
                await page.wait_for_timeout(500)

    except Exception as e:
        print(f"An error occurred: {e}")


async def download_video_file(file_name, context, url, active_cookies):
    if os.path.exists(f"{file_name}.mp4"):
        print(f"Skipping {file_name}.mp4 as it already exists.")
        append_to_log_file(f"{url}\tEXISTS\t{file_name}.mp4")
        return True

    page = await open_new_page(context, url)

    if not page:
        return False

    soup = await create_soup(page)
    await page.close()

    # Find the .m3u8 source URL
    hls_url = None
    sources = soup.find_all('source')
    for source in sources:
        if source.get('type') == 'application/x-mpegURL':
            hls_url = source.get('src')
            # If the URL is relative, make it absolute
            # if not hls_url.startswith('http'):
            # hls_url = os.path.join(base_url, hls_url)
            hls_url = base_url + hls_url
            break

    if hls_url:
        print(f"Found .m3u8 URL: {hls_url}")

        cookies_dict = {cookie['name']: cookie['value'] for cookie in active_cookies}
        # Now use the cookies in the requests.get() call

        m3u8_response = requests.get(hls_url, headers=convert_context_cookies_to_header_string(cookies_dict))

        # Download the .m3u8 content
        # m3u8_response = requests.get(hls_url, cookies=cookies)

        if m3u8_response.status_code == 200:
            # Save the .m3u8 content to a file
            m3u8_file = f'{file_name}.m3u8'
            with open(m3u8_file, 'wb') as file:
                file.write(m3u8_response.content)
            print(f".m3u8 file saved as: {m3u8_file}")

            # Convert the .m3u8 to a single video file using ffmpeg
            output_file = f'{file_name}.mp4'
            print(f"Converting {m3u8_file} to {output_file} using ffmpeg...")
            command = [
                "ffmpeg",
                "-protocol_whitelist", "https,file,crypto,data,http,tcp,tls",
                "-i", m3u8_file,
                "-c", "copy",
                output_file
            ]

            subprocess.run(command)

            # Append to log_output
            append_to_log_file(f"{url}\tSUCCESS\t{hls_url}\t{output_file}")
            print(f"Video file saved as: {output_file}")
        else:
            append_to_log_file(f"{url}\tERROR\t{hls_url}\t{m3u8_response.status_code}")
            append_to_error_file(url)

            print(f"Failed to download .m3u8 file from {hls_url}. Status code: {m3u8_response.status_code}")
            return False
    else:
        append_to_log_file(f"{url}\tWARNING\tNo .m3u8 Found\t{hls_url}")
        print("No .m3u8 source URL found in the HTML content.")

    return True


async def login_manually(browser, url):
    async with async_playwright() as p:
        # Launch the browser
        # browser = await p.chromium.launch(headless=False)  # Keep headless=False to allow manual login
        page = await browser.new_page()

        # Navigate to the login page
        await page.goto(url)

        print("Please complete the login manually...")

        # Wait for user to manually complete login
        login_url = input("Press enter your login url and press ENTER...\n")

        print("Login URL: ", login_url)

        # Go to the login page
        await page.goto(login_url)
        await page.wait_for_load_state('domcontentloaded')

        # Get cookies after manual login
        cookies = await page.context.cookies()
        print("Cookies after login:", cookies)

        return cookies


async def process():
    # Read urls from file
    with open(urls_path, 'r') as file:
        urls_text = file.read()

    # Convert the URLs to a list, stripping any extra whitespace
    urls = [url.strip() for url in urls_text.strip().splitlines() if url.strip()]

    # Append the date and the url list
    append_to_log_file(f"\n\n---\nStarting new download process. {datetime.now()}\n---\n")
    append_to_log_file(f"URLs:\n{urls_text}\n")

    # Use Playwright to fetch and render each URL
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",  # Prevents detection
                "--no-sandbox",  # Helps with compatibility
                "--disable-gpu",  # Optional, if headless detection is based on GPU rendering
            ]
        )

        cookies = await login_manually(browser, base_url)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        )

        # Set cookies in the Playwright context
        await context.add_cookies(cookies)

        # for name, value in cookies.items():
        #     await context.add_cookies([{'name': name, 'value': value, 'domain': cookie_domain, 'path': '/'}])

        # Process each URL with index
        for index, url in enumerate(urls):
            print(f"\n> Processing URL: {url}")

            file_name = f"{index} - {url.split('/')[-1]}"

            comments_file_name = file_name + "_comments"
            comments_url = url + "/comments"

            is_success = not is_download_video or await download_video_file(file_name, context, url, cookies)

            is_success &= await process_and_download_html(file_name, context, url)

            is_success &= await download_comments_html(comments_file_name, context, comments_url)

            if is_success:
                remove_error_for_url(url)
                remove_error_for_url(comments_url)

        # Close the browser
        await browser.close()


asyncio.run(process())

cookies = [{'name': 'ab_experiment_sampled', 'value': '%22false%22', 'domain': '.www.computerenhance.com', 'path': '/',
            'expires': 1759585381.917436, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
           {'name': 'ab_testing_id', 'value': '%22101a4b0a-1ad6-4fce-8e59-60db6faef198%22',
            'domain': '.www.computerenhance.com', 'path': '/', 'expires': 1759585391.148748, 'httpOnly': True,
            'secure': True, 'sameSite': 'Lax'}, {'name': '__cf_bm',
                                                 'value': 'nPTpWO4TiWjti7acYxC4rArwk6bmJSSCekf8aByeenQ-1728049382-1.0.1.1-Oqt4QRuk18RdFvVxB_hXpbGN7xRxIlBWqx5Ychf4EWgVSIoz3OE32G9rdk4wAaV5wt16iQvFirxJjhRLPjUkSQ',
                                                 'domain': '.www.computerenhance.com', 'path': '/',
                                                 'expires': 1728051181.917592, 'httpOnly': True, 'secure': True,
                                                 'sameSite': 'None'},
           {'name': 'ajs_anonymous_id', 'value': '%2264ddae8b-6c33-4dc5-be1b-40b7940bafe4%22',
            'domain': 'www.computerenhance.com', 'path': '/', 'expires': 1759585382, 'httpOnly': False, 'secure': False,
            'sameSite': 'Lax'},
           {'name': 'cookie_storage_key', 'value': '5b9e0f8c-a278-44bb-88b2-f35b1f7af106', 'domain': '.substack.com',
            'path': '/', 'expires': 1735825382.727762, 'httpOnly': False, 'secure': True, 'sameSite': 'None'},
           {'name': '__cf_bm',
            'value': 'iAcAxC6l7yG_V3d6KNz.ETWl0f79B0FwA4fO6f1TV14-1728049382-1.0.1.1-U87NOguG3x6ZyyOnk1t7X.H515_pGN_2uttK2vCaLE.cSp8QmclPUtlKTMmFm66QrBQihH7hpQtpj7hBvAlrGg',
            'domain': '.substack.com', 'path': '/', 'expires': 1728051182.727814, 'httpOnly': True, 'secure': True,
            'sameSite': 'None'}, {'name': 'cookie_storage_key', 'value': 'b8ff909f-40e1-4120-90cd-a6585685fafa',
                                  'domain': '.www.computerenhance.com', 'path': '/', 'expires': 1735825383.088525,
                                  'httpOnly': False, 'secure': True, 'sameSite': 'None'}, {'name': 'visit_id',
                                                                                           'value': '%7B%22id%22%3A%2255399e8c-920f-49ff-9dad-899a16d09ad6%22%2C%22timestamp%22%3A%222024-10-04T13%3A43%3A03.068Z%22%7D',
                                                                                           'domain': '.www.computerenhance.com',
                                                                                           'path': '/',
                                                                                           'expires': 1728051191.148713,
                                                                                           'httpOnly': True,
                                                                                           'secure': False,
                                                                                           'sameSite': 'Strict'},
           {'name': '_gcl_au', 'value': '1.1.308697437.1728049385', 'domain': '.computerenhance.com', 'path': '/',
            'expires': 1735825384, 'httpOnly': False, 'secure': False, 'sameSite': 'Lax'},
           {'name': 'IDE', 'value': 'AHWqTUm9tAiK7QSDm6Ymk7QYcNiicyMrVSaNn-GTpBYBQ6TY8dzaR_cVlCNsUxQm',
            'domain': '.doubleclick.net', 'path': '/', 'expires': 1762609385.123756, 'httpOnly': True, 'secure': True,
            'sameSite': 'None'},
           {'name': 'ab_experiment_sampled', 'value': '%22false%22', 'domain': '.substack.com', 'path': '/',
            'expires': 1759585388.698582, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
           {'name': 'ab_testing_id', 'value': '%22cee3f52b-95db-44ef-9d30-51d339678802%22', 'domain': '.substack.com',
            'path': '/', 'expires': 1759585388.908877, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'},
           {'name': 'visit_id',
            'value': '%7B%22id%22%3A%22513cc7a5-6288-4e72-aa37-7f191a98d271%22%2C%22timestamp%22%3A%222024-10-04T13%3A43%3A08.632Z%22%7D',
            'domain': '.substack.com', 'path': '/', 'expires': 1728051188.908769, 'httpOnly': True, 'secure': False,
            'sameSite': 'Strict'}, {'name': 'substack.sid',
                                    'value': 's%3AcfMHh5KZL1GlydTh5PcOlS3dR3VNl_tV.TPnx4HJVJQ76q973reC3petUDnhGLvdZDd2jPrTgQ%2FE',
                                    'domain': '.substack.com', 'path': '/', 'expires': 1735825387.909055,
                                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'}, {'name': 'AWSALBTG',
                                                                                           'value': 's8y3SXL76u9yTXDltvamnh2XFejE+y46FY2Q0pICKpBOinQuKHapgd1XN/un2paJW/jiH0EudNzuOMgWKXlni/ax36vcumIaFyeuXyESzA8g1Ar764g3DnljoliYUkPJArPvPblA2a8imF41bOHF/dzC+APYcGUsuhMlBYZVEsHT',
                                                                                           'domain': 'substack.com',
                                                                                           'path': '/',
                                                                                           'expires': 1728654187.908079,
                                                                                           'httpOnly': False,
                                                                                           'secure': False,
                                                                                           'sameSite': 'Lax'},
           {'name': 'ajs_anonymous_id', 'value': '%224ae273aa-4db9-4ce0-96b1-e9d61a4380f8%22',
            'domain': '.substack.com', 'path': '/', 'expires': 1759585388.908592, 'httpOnly': False, 'secure': False,
            'sameSite': 'Strict'}, {'name': 'connect.sid',
                                    'value': 's%3AYfVijkohgb8XTXcQedGNbYoeGHpuHAqr.SUTm2M2gZubxUdR%2FqHLp8y%2BPV9k5wrJsIV9Zv27E98o',
                                    'domain': 'www.computerenhance.com', 'path': '/', 'expires': 1735825391.148783,
                                    'httpOnly': True, 'secure': False, 'sameSite': 'Lax'},
           {'name': 'ajs_anonymous_id', 'value': '%224ae273aa-4db9-4ce0-96b1-e9d61a4380f8%22',
            'domain': '.www.computerenhance.com', 'path': '/', 'expires': 1759585391.148655, 'httpOnly': False,
            'secure': False, 'sameSite': 'Strict'},
           {'name': 'substack.lli', 'value': '0', 'domain': '.substack.com', 'path': '/', 'expires': 1735825390.344925,
            'httpOnly': False, 'secure': True, 'sameSite': 'None'}, {'name': 'AWSALBTGCORS',
                                                                     'value': '/wQeXLCqFSuzpuf1iQV+rA45XSwoITbNFaVTk2mOzB773OgpjnYeFgwSP32b+sM9pJJOUZdLNKE5knw6Qbl7wutSoE88TGvbqP8+c280NcfgS4PZw6W0i2IcGrSYvEmHnsdaQ7QasXe6U0cxv+/eLU1/iaG/WsK1XG51cLb4tdcx',
                                                                     'domain': 'substack.com', 'path': '/',
                                                                     'expires': 1728654190.391756, 'httpOnly': False,
                                                                     'secure': True, 'sameSite': 'None'},
           {'name': '_dd_s', 'value': 'rum=0&expire=1728050289906', 'domain': 'www.computerenhance.com', 'path': '/',
            'expires': 1728050290, 'httpOnly': False, 'secure': False, 'sameSite': 'Strict'}, {'name': 'AWSALBTG',
                                                                                               'value': '6OQf+QOjAPXwxON0NZ4roCvjg8WK6/1SorUkri3Aj7OQ6gdfAPUjlwrM6cO8EX2JX4MOg0t1RDiGU0guPSBhyBDudkRkQAI+wGLq0q3z7fAETlhOkD9XdL6XfwEk3ufL57IVFP7faxyyzJMngzgELPFv51J58f+c5v9fvwPpOsh1',
                                                                                               'domain': 'www.computerenhance.com',
                                                                                               'path': '/',
                                                                                               'expires': 1728654190.148413,
                                                                                               'httpOnly': False,
                                                                                               'secure': False,
                                                                                               'sameSite': 'Lax'},
           {'name': 'AWSALBTGCORS',
            'value': '6OQf+QOjAPXwxON0NZ4roCvjg8WK6/1SorUkri3Aj7OQ6gdfAPUjlwrM6cO8EX2JX4MOg0t1RDiGU0guPSBhyBDudkRkQAI+wGLq0q3z7fAETlhOkD9XdL6XfwEk3ufL57IVFP7faxyyzJMngzgELPFv51J58f+c5v9fvwPpOsh1',
            'domain': 'www.computerenhance.com', 'path': '/', 'expires': 1728654190.148559, 'httpOnly': False,
            'secure': True, 'sameSite': 'None'}]
