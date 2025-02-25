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

- Uses **Katana** to perform active crawling.
- Uses **Waybackurls** to fetch historical URLs.
- Extracts:
  - **GET parameters**
  - **Directories**
  - **Subdomains**
  - **Extracted directories**
- Saves all extracted data into structured wordlists.
- Avoids redundant execution by checking existing output files.

---

## Prerequisites

- **Python 3.x** installed
- Required tools:
  - [Katana](https://github.com/projectdiscovery/katana) (Install with `go install github.com/projectdiscovery/katana/cmd/katana@latest`)
  - [Waybackurls](https://github.com/tomnomnom/waybackurls) (Install with `go install github.com/tomnomnom/waybackurls@latest`)

---

## Installation

1. Clone the repository or download the script.
2. Ensure **Katana** and **Waybackurls** are installed and available in your `$PATH`.
3. Run the script:
   ```sh
   python3 script.py
   ```

## Usage

### Running the Script

Run the script and enter the target URL when prompted:

```sh
python3 script.py
```

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
