# wlmaker-pro

## Overview

This script automates the process of gathering URLs, parameters, directories, and subdomains using **Katana** and **Waybackurls**. It collects URLs from live crawling and archived sources, extracts valuable assets using regex, and saves them into organized wordlists.

---

## Purpose

- Perform **web reconnaissance** and **content discovery**.
- Extract **parameters, directories, and subdomains** from live and historical data.
- Generate wordlists for **further testing and fuzzing** in penetration testing.

---

## Features

- Uses **Katana** to perform active crawling of live websites.
- Uses **Waybackurls** to fetch historical URLs from the Wayback Machine.
- Extracts:
  - **GET parameters**: Useful for finding input points to test for vulnerabilities like XSS or SQL injection.
  - **Directories**: Helps in discovering hidden or sensitive paths for further enumeration.
  - **Subdomains**: Identifies potential attack surfaces across the domain ecosystem.
  - **Extracted directories**: Provides a clean list of paths for fuzzing or manual inspection.
- Saves all extracted data into structured wordlists for use in tools like `ffuf` or `Burp Suite`.
- Avoids redundant execution by checking existing output files to save time.

---

## Prerequisites

- **Python 3.x** installed
- No additional Python dependencies required (uses only standard libraries: `os`, `re`, `subprocess`, `argparse`).
- Required tools:
  - [Katana](https://github.com/projectdiscovery/katana) (Install with `go install github.com/projectdiscovery/katana/cmd/katana@latest`)
  - [Waybackurls](https://github.com/tomnomnom/waybackurls) (Install with `go install github.com/tomnomnom/waybackurls@latest`)

---

## Installation

1. Clone the repository or download the script.
2. Ensure **Katana** and **Waybackurls** are installed and available in your `$PATH`.
3. Run the script:
   ```sh
   `python3 wlmaker-pro.py`
   ```

## Examples

<<<<<<< HEAD
- Basic usage:
=======
### Running the Script

Run the script and enter the target URL when prompted:
>>>>>>> df4c89e3addf3ebd3aa89f4938c887020e4255be

````sh
`python3 wlmaker-pro.py
Enter target URL: https://example.com`
- With cookies and headers (for authenticated pages):
```sh
python3 wlmaker-pro.py https://example.com --cookies "sessionid=abc123; user=xyz789" --headers "Authorization=Bearer token123"
```
<<<<<<< HEAD
````
=======

#### Example

```sh
Enter target URL: https://example.com
```

## Output

### Wordlists Generated

The script generates the following wordlists:

- **`params_wordlist_<target>.txt`** → Extracted GET parameters
- **`directories_wordlist_<target>.txt`** → Extracted directories
- **`subdomains_wordlist_<target>.txt`** → Extracted subdomains
- **`extracted_directories_wordlist_<target>.txt`** → Cleaned list of directories

#### Sample Output

```sh
Crawling target with Katana...
Fetching URLs with waybackurls...
Wordlists generated successfully!
```

## Customization

- Modify regex patterns in `extract_data()` to tailor the extraction logic.
- Add support for additional crawling tools.

## Notes

- **Use responsibly!** Only test on domains you have explicit permission to assess.
- Some websites may block automated crawling—consider using a proxy or delay between requests.

## Roadmap for Improvement

- Add multi-threading to speed up processing.
- Include custom user-agents and headers for stealth.
- Implement proxy support for anonymity.
- Save JSON output for better integration with other tools.

## Support

For any issues or suggestions, feel free to reach out!
>>>>>>> df4c89e3addf3ebd3aa89f4938c887020e4255be
