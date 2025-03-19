# wlmaker-pro

An advanced tool for crawling and data extraction from web applications.

## Features

- Crawls web applications using Katana
- Extracts URLs from Wayback Machine
- Identifies parameters, directories, and subdomains
- Supports multiple output formats (txt, json, xml)
- Handles authentication with cookies and headers
- Configurable crawling depth and timeouts
- Proxy support
- SSL verification options
- Multi-threading support
- Comprehensive error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mmatinjafari/wlmaker-pro.git
cd wlmaker-pro
```

2. Run the installation script:
```bash
sudo ./install.sh
```

The script will:
- Create a Python virtual environment
- Install required dependencies
- Make the `wlmaker` command globally available

## Usage

Basic usage:
```bash
wlmaker https://example.com
```

### Common Use Cases

1. Basic crawling with default settings:
```bash
wlmaker https://example.com
```

2. Crawl with authentication:
```bash
wlmaker --cookies "session=abc123" --headers "Authorization: Bearer token123" https://example.com
```

3. Crawl with custom depth and timeout:
```bash
wlmaker --depth 3 --timeout 30 https://example.com
```

4. Output in multiple formats:
```bash
wlmaker --format all https://example.com
```

5. Process multiple URLs from a file:
```bash
wlmaker --file urls.txt
```

6. Use with proxy:
```bash
wlmaker --proxy http://127.0.0.1:8080 https://example.com
```

7. Crawl with specific scope:
```bash
wlmaker --scope strict https://example.com
```

### Output Files

The tool generates the following files in the `output/<domain>` directory:
- `params_wordlist.txt`: Extracted parameters
- `directories_wordlist.txt`: Discovered directories
- `subdomains_wordlist.txt`: Found subdomains
- `extracted_directories_wordlist.txt`: Directory paths
- `api_endpoints.txt`: API endpoints
- `static_files.txt`: Static file URLs
- `fragments.txt`: URL fragments
- `summary.txt`: Summary of findings
- JSON and XML versions of the above files (when using --format all)

## Options

```
usage: wlmaker [-h] [--file FILE] [--cookies COOKIES] [--headers HEADER:VALUE [HEADER:VALUE ...]]
               [--depth DEPTH] [--timeout TIMEOUT] [--wayback-timeout WAYBACK_TIMEOUT]
               [--format {txt,json,xml,all}] [--proxy PROXY] [--scope {strict,fuzzy,subdomain}]
               [--exclude EXCLUDE] [--threads THREADS] [--disable-ssl-verify] [--version]
               [url]

options:
  -h, --help            show this help message and exit
  --file FILE           File containing a list of URLs
  --cookies COOKIES     Cookies for authentication (e.g., sessionid=abc123)
  --headers HEADER:VALUE
                       Additional headers (e.g., "User-Agent: Mozilla/5.0")
  --depth DEPTH         Crawl depth for Katana
  --timeout TIMEOUT     Timeout in seconds for Katana
  --wayback-timeout WAYBACK_TIMEOUT
                       Timeout in seconds for waybackurls
  --format {txt,json,xml,all}
                       Output format: txt (default), json, xml, or all
  --proxy PROXY         Proxy to use for requests (e.g., http://127.0.0.1:8080)
  --scope {strict,fuzzy,subdomain}
                       Scope for crawling: strict, fuzzy, or subdomain
  --exclude EXCLUDE     Pattern to exclude from crawling
  --threads THREADS     Number of parallel targets to process
  --disable-ssl-verify  Disable SSL certificate verification
  --version, -v         Show version information
```

## Uninstallation

To remove the tool:
```bash
sudo ./uninstall.sh
```

## Requirements

- Python 3.x
- Katana
- waybackurls
- pip (Python package manager)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
