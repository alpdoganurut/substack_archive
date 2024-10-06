
Download HTML content and videos from Substack URLs

```
positional arguments:
positional-single-url
Single URL to download. Overrides the URLs file if set.

options:
-h, --help                              Show this help message and exit
-u PATH, --urls PATH                    Path to the file containing URLs. Default is "./urls.txt"
-su URL, --single-url URL               Single URL to download. Overrides the URLs file if set.
-dd PATH, --download-directory PATH     Directory to save downloaded files. Default is "./downloads"
-nh, --no-headless                      Show browser window if set. Default is False
-nvd, --no-video-download               Download videos if set. Default is False
-ncd, --no-comment-download             Download comments if set. Default is False
-oh, --override-html                    Override existing HTML files if set. Default is False
-n, --numbered                          Number files if set. Default is False
-nsd, --no-separate-directories         Do not create separate directories for assets if set. Default is False
-d DELAY, --delay DELAY                 Delay between page loads. Default is 0.1 seconds
```

### Required Python Packages

```
pip install requests
pip install bs4
pip install playwright
```

### Example Usage

Download content from a single URL:
```
$ python substack_downloader.py https://example.substack.com/p/example-post
$ python substack_downloader.py -su https://example.substack.com/p/example-post
```

Download content from a list of URLs:
```
$ python substack_downloader.py
$ python substack_downloader.py -u custom_urls_path.txt
```

