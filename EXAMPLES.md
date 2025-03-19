# wlmaker-pro Usage Examples

This document provides detailed examples of how to use wlmaker-pro for various reconnaissance tasks.

## Basic Usage

### Single Target Scan

Scan a single domain with default settings:

```bash
python3 wlmaker-v02.py https://example.com
```

This will:
- Crawl https://example.com using Katana
- Fetch historical URLs using waybackurls
- Extract parameters, directories, subdomains, etc.
- Save results as text files in `output/example_com/`

### Multiple Targets

Scan multiple domains from a file:

```bash
python3 wlmaker-v02.py --file targets.txt
```

Where `targets.txt` contains one URL per line:
```
https://example.com
https://test.example.org
https://subdomain.example.net
```

## Output Formats

### JSON Output

Save results in JSON format:

```bash
python3 wlmaker-v02.py https://example.com --format json
```

Sample output in `params.json`:
```json
[
  "id",
  "page",
  "query",
  "search",
  "token"
]
```

### XML Output

Save results in XML format:

```bash
python3 wlmaker-v02.py https://example.com --format xml
```

Sample output in `params.xml`:
```xml
<?xml version="1.0" ?>
<params>
  <item>id</item>
  <item>page</item>
  <item>query</item>
  <item>search</item>
  <item>token</item>
</params>
```

### Multiple Formats

Save in all available formats simultaneously:

```bash
python3 wlmaker-v02.py https://example.com --format all
```

## Authentication and Headers

### Using Cookies

Scan a site with authentication cookies:

```bash
python3 wlmaker-v02.py https://example.com --cookies "sessionid=abc123; auth=xyz456"
```

### Using Custom Headers

Scan with an API token or other custom headers:

```bash
python3 wlmaker-v02.py https://example.com --headers "Authorization=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." "User-Agent=Mozilla/5.0"
```

## Crawling Configuration

### Setting Crawl Depth

Control how deep Katana will crawl:

```bash
python3 wlmaker-v02.py https://example.com --depth 5
```

### Setting Timeouts

Set a timeout for Katana:

```bash
python3 wlmaker-v02.py https://example.com --timeout 30
```

Set a timeout for waybackurls:

```bash
python3 wlmaker-v02.py https://example.com --wayback-timeout 300
```

### Controlling Crawl Scope

Limit crawling to strict domain matching:

```bash
python3 wlmaker-v02.py https://example.com --scope strict
```

Include subdomains in the crawl:

```bash
python3 wlmaker-v02.py https://example.com --scope subdomain
```

### Excluding Patterns

Exclude certain paths from crawling:

```bash
python3 wlmaker-v02.py https://example.com --exclude "logout|.pdf|/static/"
```

## Proxy and SSL

### Using a Proxy

Route requests through a proxy:

```bash
python3 wlmaker-v02.py https://example.com --proxy http://127.0.0.1:8080
```

### Disable SSL Verification

For sites with SSL issues:

```bash
python3 wlmaker-v02.py https://example.com --disable-ssl-verify
```

## Performance

### Setting Thread Count

Control parallel processing:

```bash
python3 wlmaker-v02.py --file targets.txt --threads 10
```

## Complete Examples

### Full Reconnaissance with All Options

```bash
python3 wlmaker-v02.py https://example.com \
  --depth 3 \
  --timeout 20 \
  --wayback-timeout 180 \
  --format all \
  --proxy http://127.0.0.1:8080 \
  --scope subdomain \
  --exclude "logout|admin|.zip" \
  --cookies "session=abc123" \
  --headers "Authorization=Bearer token123" \
  --threads 5 \
  --disable-ssl-verify
```

### Batch Processing for Bug Bounty

```bash
# Create target file
echo "target1.com
target2.com
target3.com" > targets.txt

# Run the tool
python3 wlmaker-v02.py --file targets.txt \
  --format json \
  --depth 2 \
  --scope subdomain \
  --threads 3
```

## Using the Output

### With ffuf for Parameter Fuzzing

```bash
ffuf -u "https://example.com/?FUZZ=test" -w output/example_com/params_wordlist.txt
```

### With Subdomain Takeover Tools

```bash
cat output/example_com/subdomains_wordlist.txt | subjack -a
```

### With Directory Brute-forcing

```bash
ffuf -u "https://example.com/FUZZ" -w output/example_com/directories_wordlist.txt
```

## Checking Results

The summary file provides a quick overview of what was found:

```
Target: https://example.com
Parameters found: 42
Directories found: 28
Subdomains found: 15
Extracted directory paths: 67
API endpoints found: 8
``` 