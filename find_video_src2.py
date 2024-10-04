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
urls_text = """
https://www.computerenhance.com/p/no-really-why-cant-we-have-raw-udp
https://www.computerenhance.com/p/the-problem-with-risc-v-v-mask-bits
https://www.computerenhance.com/p/why-isnt-there-a-createprocess-that
https://www.computerenhance.com/p/turns-are-better-than-radians
https://www.computerenhance.com/p/table-of-contents
https://www.computerenhance.com/p/performance-aware-programming-series
https://www.computerenhance.com/p/welcome-to-the-performance-aware
https://www.computerenhance.com/p/waste
https://www.computerenhance.com/p/instructions-per-clock
https://www.computerenhance.com/p/monday-q-and-a-2023-02-05
https://www.computerenhance.com/p/single-instruction-multiple-data
https://www.computerenhance.com/p/caching
https://www.computerenhance.com/p/monday-q-and-a-2-2023-02-12
https://www.computerenhance.com/p/multithreading
https://www.computerenhance.com/p/python-revisited
https://www.computerenhance.com/p/monday-q-and-a-3-2023-02-20
https://www.computerenhance.com/p/the-haversine-distance-problem
https://www.computerenhance.com/p/clean-code-horrible-performance
https://www.computerenhance.com/p/instruction-decoding-on-the-8086
https://www.computerenhance.com/p/decoding-multiple-instructions-and
https://www.computerenhance.com/p/monday-q-and-a-4-2023-03-06
https://www.computerenhance.com/p/opcode-patterns-in-8086-arithmetic
https://www.computerenhance.com/p/monday-q-and-a-5-2023-03-13
https://www.computerenhance.com/p/8086-decoder-code-review
https://www.computerenhance.com/p/monday-q-and-a-6-2023-03-20
https://www.computerenhance.com/p/using-the-reference-decoder-as-a
https://www.computerenhance.com/p/simulating-non-memory-movs
https://www.computerenhance.com/p/homework-poll
https://www.computerenhance.com/p/new-schedule-experiment
https://www.computerenhance.com/p/simulating-add-jmp-and-cmp
https://www.computerenhance.com/p/simulating-conditional-jumps
https://www.computerenhance.com/p/response-to-a-reporter-regarding
https://www.computerenhance.com/p/monday-q-and-a-7-2023-04-10
https://www.computerenhance.com/p/simulating-memory
https://www.computerenhance.com/p/simulating-real-programs
https://www.computerenhance.com/p/monday-q-and-a-8-2023-04-17
https://www.computerenhance.com/p/other-common-instructions
https://www.computerenhance.com/p/the-stack
https://www.computerenhance.com/p/monday-q-and-a-9-2023-04-24
https://www.computerenhance.com/p/performance-excuses-debunked
https://www.computerenhance.com/p/estimating-cycles
https://www.computerenhance.com/p/monday-q-and-a-10-2023-05-08
https://www.computerenhance.com/p/from-8086-to-x64
https://www.computerenhance.com/p/8086-internals-poll
https://www.computerenhance.com/p/how-to-play-trinity
https://www.computerenhance.com/p/monday-q-and-a-11-2023-05-15
https://www.computerenhance.com/p/8086-simulation-code-review
https://www.computerenhance.com/p/part-one-q-and-a-and-homework-showcase
https://www.computerenhance.com/p/the-first-magic-door
https://www.computerenhance.com/p/monday-q-and-a-12-2023-05-22
https://www.computerenhance.com/p/generating-haversine-input-json
https://www.computerenhance.com/p/monday-q-and-a-13-2023-05-29
https://www.computerenhance.com/p/writing-a-simple-haversine-distance
https://www.computerenhance.com/p/monday-q-and-a-14-2023-06-05
https://www.computerenhance.com/p/initial-haversine-processor-code
https://www.computerenhance.com/p/monday-q-and-a-15-2023-06-12
https://www.computerenhance.com/p/introduction-to-rdtsc
https://www.computerenhance.com/p/monday-q-and-a-16-2023-06-19
https://www.computerenhance.com/p/how-does-queryperformancecounter
https://www.computerenhance.com/p/monday-q-and-a-17-2023-06-26
https://www.computerenhance.com/p/instrumentation-based-profiling
https://www.computerenhance.com/p/monday-q-and-a-18-2023-07-03
https://www.computerenhance.com/p/profiling-nested-blocks
https://www.computerenhance.com/p/monday-q-and-a-19-2023-07-10
https://www.computerenhance.com/p/profiling-recursive-blocks
https://www.computerenhance.com/p/monday-q-and-a-20-2023-07-17
https://www.computerenhance.com/p/a-first-look-at-profiling-overhead
https://www.computerenhance.com/p/new-q-and-a-process
https://www.computerenhance.com/p/a-tale-of-two-radio-shacks
https://www.computerenhance.com/p/comparing-the-overhead-of-rdtsc-and
https://www.computerenhance.com/p/monday-q-and-a-21-2023-07-31
https://www.computerenhance.com/p/the-four-programming-questions-from
https://www.computerenhance.com/p/microsoft-intern-interview-question
https://www.computerenhance.com/p/microsoft-intern-interview-question-ab7
https://www.computerenhance.com/p/microsoft-intern-interview-question-a3f
https://www.computerenhance.com/p/efficient-dda-circle-outlines
https://www.computerenhance.com/p/q-and-a-22-2023-08-15
https://www.computerenhance.com/p/measuring-data-throughput
https://www.computerenhance.com/p/q-and-a-23-2023-08-21
https://www.computerenhance.com/p/repetition-testing
https://www.computerenhance.com/p/q-and-a-24-2023-08-28
https://www.computerenhance.com/p/monitoring-os-performance-counters
https://www.computerenhance.com/p/q-and-a-25-2023-09-04
https://www.computerenhance.com/p/page-faults
https://www.computerenhance.com/p/q-and-a-26-2023-09-11
https://www.computerenhance.com/p/probing-os-page-fault-behavior
https://www.computerenhance.com/p/game-development-post-unity
https://www.computerenhance.com/p/q-and-a-27-2023-09-18
https://www.computerenhance.com/p/four-level-paging
https://www.computerenhance.com/p/q-and-a-28-2023-09-25
https://www.computerenhance.com/p/analyzing-page-fault-anomalies
https://www.computerenhance.com/p/q-and-a-29-2023-10-02
https://www.computerenhance.com/p/powerful-page-mapping-techniques
https://www.computerenhance.com/p/q-and-a-30-2023-10-09
https://www.computerenhance.com/p/faster-reads-with-large-page-allocations
https://www.computerenhance.com/p/q-and-a-31-2023-10-23
https://www.computerenhance.com/p/memory-mapped-files
https://www.computerenhance.com/p/q-and-a-32-2023-10-30
https://www.computerenhance.com/p/inspecting-loop-assembly
https://www.computerenhance.com/p/q-and-a-33-2023-11-06
https://www.computerenhance.com/p/intuiting-latency-and-throughput
https://www.computerenhance.com/p/q-and-a-34-2023-11-13
https://www.computerenhance.com/p/analyzing-dependency-chains
https://www.computerenhance.com/p/q-and-a-35-2023-11-20
https://www.computerenhance.com/p/linking-directly-to-asm-for-experimentation
https://www.computerenhance.com/p/q-and-a-36-2023-11-27
https://www.computerenhance.com/p/cpu-front-end-basics
https://www.computerenhance.com/p/a-few-quick-notes
https://www.computerenhance.com/p/q-and-a-37-2023-12-04
https://www.computerenhance.com/p/branch-prediction
https://www.computerenhance.com/p/q-and-a-38-2023-12-11
https://www.computerenhance.com/p/code-alignment
https://www.computerenhance.com/p/byte-positions-are-better-than-line
https://www.computerenhance.com/p/q-and-a-39-2024-01-09
https://www.computerenhance.com/p/msvc-pdbs-are-filled-with-stale-debug
https://www.computerenhance.com/p/q-and-a-40-2024-01-18
https://www.computerenhance.com/p/the-rat-and-the-register-file
https://www.computerenhance.com/p/reader-poll-sponsored-job-offers
https://www.computerenhance.com/p/q-and-a-41-2024-01-23
https://www.computerenhance.com/p/q-and-a-42-2024-01-29
https://www.computerenhance.com/p/execution-ports-and-the-scheduler
https://www.computerenhance.com/p/q-and-a-43-2024-02-06
https://www.computerenhance.com/p/increasing-read-bandwidth-with-simd
https://www.computerenhance.com/p/q-and-a-44-2024-02-26
https://www.computerenhance.com/p/cache-size-and-bandwidth-testing
https://www.computerenhance.com/p/q-and-a-45-2024-03-04
https://www.computerenhance.com/p/non-power-of-two-cache-size-testing
https://www.computerenhance.com/p/q-and-a-46-2024-03-11
https://www.computerenhance.com/p/latency-and-throughput-again
https://www.computerenhance.com/p/q-and-a-47-2024-03-18
https://www.computerenhance.com/p/unaligned-load-penalties
https://www.computerenhance.com/p/q-and-a-48-2024-03-25
https://www.computerenhance.com/p/the-apple-m-series-gofetch-attack
https://www.computerenhance.com/p/q-and-a-49-2024-04-02
https://www.computerenhance.com/p/q-and-a-50-2024-04-08
https://www.computerenhance.com/p/cache-sets-and-indexing
https://www.computerenhance.com/p/does-x86-need-to-die
https://www.computerenhance.com/p/q-and-a-51-2024-04-18
https://www.computerenhance.com/p/a-brief-note-on-the-ftc-non-compete
https://www.computerenhance.com/p/q-and-a-52-2024-04-29
https://www.computerenhance.com/p/non-temporal-stores
https://www.computerenhance.com/p/q-and-a-53-2024-05-06
https://www.computerenhance.com/p/prefetching
https://www.computerenhance.com/p/q-and-a-54-2024-05-13
https://www.computerenhance.com/p/q-and-a-55-2024-05-20
https://www.computerenhance.com/p/podcast-appearances-new-video-on
https://www.computerenhance.com/p/q-and-a-56-2024-06-10
https://www.computerenhance.com/p/the-worlds-first-cg-commercial
https://www.computerenhance.com/p/prefetching-wrap-up
https://www.computerenhance.com/p/q-and-a-57-2024-06-17
https://www.computerenhance.com/p/me-and-prime-talk-game-engine-basics
https://www.computerenhance.com/p/2x-faster-file-reads
https://www.computerenhance.com/p/q-and-a-58-2024-06-24
https://www.computerenhance.com/p/overlapping-file-reads-with-computation
https://www.computerenhance.com/p/analog-computing-adventures
https://www.computerenhance.com/p/q-and-a-59-2024-07-15
https://www.computerenhance.com/p/a-closer-look-at-the-prefetching
https://www.computerenhance.com/p/q-and-a-60-2024-07-22
https://www.computerenhance.com/p/a-brief-note-on-the-crowdstrike-outage
https://www.computerenhance.com/p/esoterica-next-gen-x64-cores-and
https://www.computerenhance.com/p/q-and-a-61-2024-07-30
https://www.computerenhance.com/p/testing-memory-mapped-files
https://www.computerenhance.com/p/q-and-a-62-2024-08-08
https://www.computerenhance.com/p/q-and-a-63-2024-08-19
https://www.computerenhance.com/p/q-and-a-64-2024-08-26
https://www.computerenhance.com/p/zen-cuda-and-tensor-cores-part-i
https://www.computerenhance.com/p/q-and-a-65-2024-09-09
https://www.computerenhance.com/p/the-case-of-the-missing-increment
https://www.computerenhance.com/p/q-and-a-66-2024-10-01
"""

# Cookies information
cookies = {
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

is_headless = True
delay_between_page_loads = 0.1
is_download_video = False


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
    await page.goto(url)

    try:
        await page.goto(url)
    except Exception as e:
        append_to_log_file(f"{url}\tERROR\tCouldn't load page\t{e}")
        append_to_error_file(url)
        print(f"Failed to load URL: {url}")
        raise e

    soup = await create_soup(page)

    # Check if any element contains "Too Many Requests"
    if soup.find_all(string=lambda text: "Too Many Requests" in text):
        print("Error: 'Too Many Requests'")
        append_to_log_file(f"{url}\tERROR\tToo Many Requests")
        append_to_error_file(url)
        return None

    # Do shit to make sure page loaded
    await page.wait_for_load_state('domcontentloaded')
    # await page.bring_to_front()
    # await page.wait_for_timeout(load_wait_duration)

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


async def download_video_file(file_name, context, url):
    if os.path.exists(f"{file_name}.mp4"):
        print(f"Skipping {file_name}.mp4 as it already exists.")
        append_to_log_file(f"{url}\tEXISTS\t{file_name}.mp4")
        return

    page = await open_new_page(context, url)
    soup = await create_soup(page)

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

        # Download the .m3u8 content
        m3u8_response = requests.get(hls_url, cookies=cookies)

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


async def process():
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

        # Set cookies in the Playwright context
        for name, value in cookies.items():
            await context.add_cookies([{'name': name, 'value': value, 'domain': cookie_domain, 'path': '/'}])

        # Convert the URLs to a list, stripping any extra whitespace
        urls = [url.strip() for url in urls_text.strip().splitlines() if url.strip()]

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
