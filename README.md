# wlmaker-pro

## Overview

**wlmaker-pro** is a powerful reconnaissance tool designed to automate the collection of URLs, parameters, directories, subdomains, and additional assets from live and archived web sources. Utilizing **Katana** for active crawling and **Waybackurls** for historical data, it extracts valuable information via regex and saves it into organized wordlists, JSON, or XML files for penetration testing workflows.

## Purpose

- Conduct **web reconnaissance** and **content discovery**.
- Extract **GET/POST parameters, directories, subdomains, static files, API endpoints, and fragments** from live and archived data.
- Generate structured outputs in multiple formats for **fuzzing and vulnerability testing** with tools like `ffuf` or `Burp Suite`.

## Features

- **Multi-target support**: Process a single URL or a list of domains from a file.
- **Active crawling**: Leverages **Katana** with configurable depth, timeout, scope, and exclusion settings.
- **Historical data**: Retrieves URLs from the Wayback Machine using **Waybackurls**.
- **Rich data extraction**:
  - **GET parameters** from URL query strings.
  - **POST parameters** from HTML forms and JavaScript API calls.
  - **Directories** and full paths (without leading `/`).
  - **Subdomains** for expanded attack surface mapping.
  - **Static files** with extended file type support (js, css, pdf, docx, xlsx, etc.).
  - **API endpoints** detected from common API path patterns.
  - **URL fragments** (e.g., `#something`).
- **Multiple output formats**: Save as wordlists, JSON files, or XML files.
- **Enhanced error handling**: Detailed logging to `error.log` with timestamps.
- **Proxy support**: Use proxies for anonymous crawling.
- **SSL verification control**: Option to disable SSL certificate verification.
- **Flexible scoping**: Control crawl scope with strict, fuzzy, or subdomain options.
- **Parallel execution**: Configurable multi-threaded processing for efficiency.
- **Progress tracking**: Displays a progress bar during processing.
- **Authenticated crawling**: Supports cookies and custom headers for restricted pages.
- **Summary reports**: Generates a summary of findings for each target.

## Prerequisites

- **Python 3.x**
- **Required Python packages** (install via `pip`):
  ```sh
  pip install tqdm beautifulsoup4 requests urllib3
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

Ensure **Katana** and **Waybackurls** are in your `$PATH`.

## Usage

Run the script with a single URL or a file containing multiple URLs.

### Basic Usage

For a single target:

```sh
  python3 wlmaker-v02.py https://example.com
```

### Examples

With authentication:

```sh
  python3 wlmaker-v02.py https://example.com --cookies "sessionid=abc123" --headers "Authorization=Bearer token123"
```

Multiple targets from a file:

```sh
  python3 wlmaker-v02.py --file targets.txt
```

(Example `targets.txt`:

```
https://example.com
https://test.com
```
)

With XML output and custom Katana options:

```sh
  python3 wlmaker-v02.py https://example.com --depth 3 --timeout 10 --format xml
```

With multiple output formats:

```sh
  python3 wlmaker-v02.py https://example.com --format all
```

Using a proxy with subdomain scope:

```sh
  python3 wlmaker-v02.py https://example.com --proxy http://127.0.0.1:8080 --scope subdomain
```

## Command-Line Options

- `--file`: Path to a file with a list of target URLs (one per line).
- `--cookies`: Cookies for authenticated crawling (e.g., "sessionid=abc123").
- `--headers`: Custom headers (e.g., "Authorization=Bearer token123").
- `--depth`: Crawl depth for Katana (e.g., `3`).
- `--timeout`: Timeout in seconds for Katana (e.g., `10`).
- `--wayback-timeout`: Timeout in seconds for waybackurls (default: 120).
- `--format`: Output format - 'txt', 'json', 'xml', or 'all' (default: 'txt').
- `--proxy`: Proxy to use for requests (e.g., "http://127.0.0.1:8080").
- `--scope`: Scope for crawling - 'strict', 'fuzzy', or 'subdomain'.
- `--exclude`: Pattern to exclude from crawling.
- `--threads`: Number of parallel targets to process (default: 5).
- `--disable-ssl-verify`: Disable SSL certificate verification.

## Output

Results are stored in an `output/<target>` directory for each domain (e.g., `output/example_com/`).

### Generated Files

#### Wordlist format (default or with `--format txt`):

- `params_wordlist.txt`: Extracted GET and POST parameters.
- `directories_wordlist.txt`: Individual directory names.
- `subdomains_wordlist.txt`: Discovered subdomains.
- `extracted_directories_wordlist.txt`: Full directory paths (no leading `/`).
- `static_files.txt`: Static files with various extensions.
- `fragments.txt`: URL fragments (e.g., `#something`).
- `api_endpoints.txt`: Detected API endpoints.

#### JSON format (with `--format json`):

- `params.json`, `directories.json`, `subdomains.json`, `extracted_dirs.json`, `api_endpoints.json`

#### XML format (with `--format xml`):

- `params.xml`, `directories.xml`, `subdomains.xml`, `extracted_dirs.xml`, `api_endpoints.xml`

#### Summary:

- `summary.txt`: Contains statistics about the findings.

### Sample Output

```
Crawling target with Katana...
Fetching URLs with waybackurls...
Processing targets: 100%|██████████| 1/1 [00:05<00:00,  5.12s/it]
Processing https://example.com completed.
```

## Customization

- Modify regex patterns in `extract_data()` to adjust extraction logic.
- Extend `run_katana()` with additional Katana options.
- Enhance `extract_post_params()` for complex forms or API endpoints.
- Add new output formats by creating additional output functions.

## Notes

- Use responsibly! Only test domains you have explicit permission to assess.
- Some sites may block crawling—consider using proxies or adjusting the scope.
- For authenticated pages, provide valid cookies/headers via `--cookies` and `--headers`.
- XML files are formatted with proper indentation for better readability.

## Changelog

### v0.2
- Added XML output format support
- Enhanced regex patterns for better data extraction
- Added API endpoint detection
- Improved POST parameter extraction to detect JavaScript API calls
- Added proxy support
- Added SSL verification control
- Added scope control for Katana
- Added exclusion pattern support
- Added configurable thread count
- Added wayback timeout configuration
- Improved error handling with detailed logging
- Added summary report generation
- Expanded static file type detection
- Better handling of UTF-8 encoding issues

### v0.1
- Initial release with basic functionality
- Text and JSON output support
- Basic parameter and directory extraction

## Support

For issues or suggestions, feel free to open an issue or reach out!
