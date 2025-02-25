# wlmaker-pro

## Overview

**wlmaker-pro** is a powerful reconnaissance tool designed to automate the collection of URLs, parameters, directories, subdomains, and additional assets from live and archived web sources. Utilizing **Katana** for active crawling and **Waybackurls** for historical data, it extracts valuable information via regex and saves it into organized wordlists or JSON files for penetration testing workflows.

## Purpose

- Conduct **web reconnaissance** and **content discovery**.
- Extract **GET/POST parameters, directories, subdomains, static files, and fragments** from live and archived data.
- Generate structured outputs for **fuzzing and vulnerability testing** with tools like `ffuf` or `Burp Suite`.

## Features

- **Multi-target support**: Process a single URL or a list of domains from a file.
- **Active crawling**: Leverages **Katana** with configurable depth and timeout settings.
- **Historical data**: Retrieves URLs from the Wayback Machine using **Waybackurls**.
- **Rich data extraction**:
  - **GET parameters** from URL query strings.
  - **POST parameters** from HTML forms.
  - **Directories** and full paths (without leading `/`).
  - **Subdomains** for expanded attack surface mapping.
  - **Static files** (e.g., `.js`, `.css`, `.pdf`).
  - **URL fragments** (e.g., `#something`).
- **Output flexibility**: Save as wordlists or JSON files.
- **Parallel execution**: Multi-threaded processing for efficiency.
- **Error handling**: Logs errors to `error.log` without halting execution.
- **Progress tracking**: Displays a progress bar during processing.
- **Authenticated crawling**: Supports cookies and custom headers for restricted pages.

## Prerequisites

- **Python 3.x**
- **Required Python packages** (install via `pip`):
  ```sh
  pip install tqdm beautifulsoup4 requests
  ```
- **Required tools** (install via go):
  ```sh
  go install github.com/projectdiscovery/katana/cmd/katana@latest
  go install github.com/tomnomnom/waybackurls@latest
  ```

## Installation

Clone the repository or download the script:

```sh
  git clone https://github.com/yourusername/wlmaker-pro.git
  cd wlmaker-pro
```

Install Python dependencies:

```sh
  pip install -r requirements.txt
```

(Create a `requirements.txt` with `tqdm`, `beautifulsoup4`, `requests` if needed.)
Ensure **Katana** and **Waybackurls** are in your `$PATH`.

## Usage

Run the script with a single URL or a file containing multiple URLs.

### Basic Usage

For a single target:

```sh
  python3 wlmaker-pro.py https://example.com
```

### Examples

With authentication:

```sh
  python3 wlmaker-pro.py https://example.com --cookies "sessionid=abc123" --headers "Authorization=Bearer token123"
```

Multiple targets from a file:

```sh
  python3 wlmaker-pro.py --file targets.txt
```

(Example `targets.txt`:

```
https://example.com
https://test.com
```

)

With JSON output and custom Katana options:

```sh
  python3 wlmaker-pro.py https://example.com --depth 3 --timeout 10 --json
```

## Command-Line Options

- `--file`: Path to a file with a list of target URLs (one per line).
- `--cookies`: Cookies for authenticated crawling (e.g., "sessionid=abc123").
- `--headers`: Custom headers (e.g., "Authorization=Bearer token123").
- `--depth`: Crawl depth for Katana (e.g., `3`).
- `--timeout`: Timeout in seconds for Katana (e.g., `10`).
- `--json`: Save output in JSON format instead of wordlists.

## Output

Results are stored in an `output/<target>` directory for each domain (e.g., `output/example_com/`).

### Generated Files

#### Wordlist format (default):

- `params_wordlist.txt`: Extracted GET and POST parameters.
- `directories_wordlist.txt`: Individual directory names.
- `subdomains_wordlist.txt`: Discovered subdomains.
- `extracted_directories_wordlist.txt`: Full directory paths (no leading `/`).
- `static_files.txt`: Static files (e.g., `.js`, `.css`).
- `fragments.txt`: URL fragments (e.g., `#something`).

#### JSON format (with `--json`):

- `params.json`, `directories.json`, `subdomains.json`, `extracted_dirs.json`.

### Sample Output

```
Crawling target with Katana...
Fetching URLs with waybackurls...
Processing targets: 100%|██████████| 1/1 [00:05<00:00,  5.12s/it]
Processing https://example.com completed.
```

## Customization

- Modify regex patterns in `extract_data()` to adjust extraction logic.
- Extend `run_katana()` with additional Katana options (e.g., `--proxy`).
- Enhance `extract_post_params()` for complex forms or API endpoints.

## Notes

- Use responsibly! Only test domains you have explicit permission to assess.
- Some sites may block crawling—consider proxies or delays if needed.
- For authenticated pages, provide valid cookies/headers via `--cookies` and `--headers`.

## Roadmap

- Add proxy support for anonymous crawling.
- Implement automatic login for authenticated pages.
- Integrate additional tools (e.g., `httpx` for live URL filtering).
- Support custom regex patterns via command-line arguments.

## Support

For issues or suggestions, feel free to open an issue or reach out!
