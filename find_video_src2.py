import asyncio
import json
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import os
import subprocess

from playwright.async_api import async_playwright

# region Configuration
log_output_path = f"video_download_log{datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.txt"
error_output_path = "video_download_error.txt"

urls_path = "urls.txt"

is_headless = True
delay_between_page_loads = 0.1
is_download_video = False
is_override_htmls = True


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

    # Attempt to find and click the "Sign in" button
    sign_in_button = await page.query_selector('text="Sign in"')  # Using "text" selector to find the button
    if sign_in_button:
        await sign_in_button.click()
        print(f"Clicked on 'Sign in' button for {url}")

    # Wait for a possible change in the page after clicking the sign-in button
    await page.wait_for_timeout(3000)  # Wait for 3 seconds or adjust as necessary

    # Check if the paywall element exists
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


async def download_html_assets_and_disable_js(url, soup):
    # Subdirectories for assets
    css_directory = os.path.join(os.getcwd(), 'css_files')
    img_directory = os.path.join(os.getcwd(), 'img_files')

    # Create directories if they don't exist
    os.makedirs(css_directory, exist_ok=True)
    os.makedirs(img_directory, exist_ok=True)

    base_url = get_base_url(url)

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


def get_base_url(full_url):
    # Parse the URL
    parsed_url = urlparse(full_url)

    # Extract the base URL
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"


# endregion


async def process_and_download_html(file_name, context, url):
    full_file_name = f"{file_name}.html"

    if not is_override_htmls and os.path.exists(full_file_name) and not is_url_in_error_file(url):
        print(f"Skipping {full_file_name} as it already exists and not in error file.")
        return True

    page = await open_new_page(context, url)

    if not page:
        return False

    soup = await create_soup(page)
    await page.close()

    await download_html_assets_and_disable_js(url, soup)

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

    if not is_override_htmls and os.path.exists(full_file_name) and not is_url_in_error_file(url):
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

    await download_html_assets_and_disable_js(url, soup)

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


async def download_video_file(file_name, context, url):
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
            hls_url = get_base_url(url) + hls_url
            break

    if hls_url:
        print(f"Found .m3u8 URL: {hls_url}")

        m3u8_response = await context.request.get(hls_url)

        if m3u8_response.ok:
            # Save the .m3u8 content to a file
            m3u8_file = f'{file_name}.m3u8'
            with open(m3u8_file, 'wb') as file:
                file.write(await m3u8_response.body())
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


async def login_manually(context):
    page = await context.new_page()

    is_logged_in = False
    while not is_logged_in:
        # Wait for user to manually complete login
        login_url = input("\nPress enter your login url and press ENTER...\n")

        # Go to the login page
        await page.goto(login_url)
        await page.wait_for_load_state('domcontentloaded')

        # Check if page has "Bad request" in content
        if "Bad request" in await page.content():
            print("\nBad request error")
            continue

        # Check if page url has error in it
        if "error" in page.url:
            print("Error in URL, probably expired login url\nRetry\n")
            continue

        is_logged_in = True

    await page.close()

    print("Logged In\n")


async def set_working_directory_for_executable():
    # This function sets the working directory to the location of the executable

    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as a normal script
        base_path = os.path.dirname(os.path.abspath(__file__))
    # Set the working directory to the executable's location
    os.chdir(base_path)
    # Now the current directory is set to where the executable was launched
    current_directory = os.getcwd()
    print(current_directory)


async def process():
    # Check if urls file exists
    if not os.path.exists(urls_path):
        print(
            f"\nERROR: URLs file not found: {urls_path}. "
            f"Create a txt files containing urls (one per line) and try again.")
        return

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

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        )

        await login_manually(context)

        # for name, value in cookies.items():
        #     await context.add_cookies([{'name': name, 'value': value, 'domain': cookie_domain, 'path': '/'}])

        # Process each URL with index
        for index, url in enumerate(urls):
            print(f"\n> Processing URL: {url}")

            file_name = f"{index} - {url.split('/')[-1]}"

            comments_file_name = file_name + "_comments"
            comments_url = url + "/comments"

            is_success = not is_download_video or await download_video_file(file_name, context, url)

            is_success &= await process_and_download_html(file_name, context, url)

            is_success &= await download_comments_html(comments_file_name, context, comments_url)

            if is_success:
                remove_error_for_url(url)
                remove_error_for_url(comments_url)

        # Close the browser
        await browser.close()


asyncio.run(process())
