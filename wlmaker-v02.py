import os
import re
import subprocess
import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import requests
import json
from tqdm import tqdm
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suppress XML parsing warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Configure logging
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def sanitize_filename(target):
    """Sanitize the domain for use in folder names."""
    domain = urlparse(target).netloc
    return domain.replace(".", "_")

def is_valid_url(url):
    """Check if the URL is valid."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url)

def run_katana(target, output_file, cookies=None, headers=None, depth=None, timeout=None, scope=None, exclude=None, proxy=None):
    """Run Katana to crawl the target and save output."""
    if not os.path.exists(output_file):
        print(f"Crawling {target} with Katana...")
        command = f"katana -u {target} -o {output_file}"
        if cookies:
            command += f" -H 'Cookie: {cookies}'"
        if headers:
            for key, value in headers.items():
                command += f" -H '{key}: {value}'"
        if depth:
            command += f" -d {depth}"
        if timeout:
            command += f" -timeout {timeout}"
        if scope:
            command += f" -scope {scope}"
        if exclude:
            command += f" -exclude-pattern '{exclude}'"
        if proxy:
            command += f" -proxy {proxy}"
        
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Katana execution failed for {target}: {e}")
            print(f"Error running Katana on {target}. See error.log for details.")
            with open(output_file, 'w') as f:
                f.write(f"# Error running Katana on {target}\n")
    else:
        print(f"Using existing Katana output for {target}.")

def run_waybackurls(target, output_file, timeout=None):
    """Run waybackurls to fetch archived URLs and save output."""
    if not os.path.exists(output_file):
        print(f"Fetching URLs for {target} with waybackurls...")
        command = f"echo {target} | waybackurls > {output_file}"
        try:
            subprocess.run(command, shell=True, check=True, timeout=timeout)
        except subprocess.CalledProcessError as e:
            logging.error(f"Waybackurls execution failed for {target}: {e}")
            print(f"Error running waybackurls on {target}. See error.log for details.")
        except subprocess.TimeoutExpired:
            logging.error(f"Waybackurls execution timed out for {target}")
            print(f"Waybackurls timed out for {target}. Consider increasing the timeout.")
    else:
        print(f"Using existing waybackurls output for {target}.")

def extract_data(file_path, target_dir):
    """Extract parameters, directories, and subdomains using regex."""
    # Enhanced patterns
    param_pattern = re.compile(r'[?&]([a-zA-Z0-9_\-\.]+)=')
    dir_pattern = re.compile(r'/([a-zA-Z0-9_\-\.]+)/')
    subdomain_pattern = re.compile(r'https?://([a-zA-Z0-9][a-zA-Z0-9\-\.]*\.[a-zA-Z0-9\-\.]+)')
    directory_pattern = re.compile(r'https?://[^/]+(/[^?#]+)')
    static_file_pattern = re.compile(r'\.(?:js|css|pdf|jpg|jpeg|png|gif|svg|xml|json|csv|doc|docx|xls|xlsx|ppt|pptx|zip|tar|gz|rar|exe|dll|so|txt)(?:\?|#|$)')
    fragment_pattern = re.compile(r'#([a-zA-Z0-9_\-\.]+)')
    api_endpoint_pattern = re.compile(r'https?://[^/]+/(?:api|v\d+|graphql|rest|data|service)/([^?#]+)')
    
    params = set()
    directories = set()
    subdomains = set()
    extracted_dirs = set()
    static_files = set()
    fragments = set()
    api_endpoints = set()
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Parse URL to extract query parameters more accurately
            url_obj = urlparse(line)
            if url_obj.query:
                query_params = parse_qs(url_obj.query)
                # Filter out empty parameters
                params.update([k for k in query_params.keys() if k])
            
            # Extract other patterns
            params.update([p for p in param_pattern.findall(line) if p])
            directories.update([d for d in dir_pattern.findall(line) if d])
            
            match = subdomain_pattern.search(line)
            if match:
                subdomains.add(match.group(1))
            
            dir_match = directory_pattern.search(line)
            if dir_match:
                path = dir_match.group(1).strip()
                if path.startswith('/'):
                    path = path[1:]  # Remove leading slash
                if path:  # Only add non-empty paths
                    extracted_dirs.add(path)
            
            if static_file_pattern.search(line):
                static_files.add(line)
            
            frag_match = fragment_pattern.search(line)
            if frag_match and frag_match.group(1):
                fragments.add(frag_match.group(1))
            
            api_match = api_endpoint_pattern.search(line)
            if api_match and api_match.group(1):
                api_endpoints.add(api_match.group(1))
    
    # Save API endpoints
    save_wordlist(api_endpoints, os.path.join(target_dir, "api_endpoints.txt"))
    save_wordlist(static_files, os.path.join(target_dir, "static_files.txt"))
    save_wordlist(fragments, os.path.join(target_dir, "fragments.txt"))
    
    return params, directories, subdomains, extracted_dirs, api_endpoints

def extract_post_params(url, cookies=None, headers=None):
    """Extract POST parameters from HTML forms."""
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10, verify=False)
        
        # Check content type to determine parser
        content_type = response.headers.get('content-type', '').lower()
        if 'xml' in content_type:
            soup = BeautifulSoup(response.text, 'xml')
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            
        post_params = set()
        
        # Extract from regular forms
        forms = soup.find_all('form', method=lambda x: x and x.lower() == 'post')
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'], {'name': True})
            for inp in inputs:
                post_params.add(inp['name'])
        
        # Extract from potential API calls in JavaScript
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for fetch, axios, ajax patterns
                ajax_pattern = re.compile(r'(?:fetch|axios\.post|ajax|\.post)\s*\(\s*[\'"]([^\'"]+)[\'"]')
                for endpoint in ajax_pattern.findall(script.string):
                    if not endpoint.startswith(('http://', 'https://')):
                        base_url = urlparse(url)
                        full_url = f"{base_url.scheme}://{base_url.netloc}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
                        post_params.add(full_url)  # Save the complete URL as it's likely an API endpoint
        
        return post_params
    except Exception as e:
        logging.error(f"Error extracting POST params from {url}: {e}")
        return set()

def save_wordlist(data, filename):
    """Save extracted data to a file without extra newlines."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(data)))

def save_json(data, filename):
    """Save data in JSON format."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(data), f, indent=4)

def save_xml(data, filename, root_name='data'):
    """Save data in XML format."""
    root = ET.Element(root_name)
    
    for item in sorted(data):
        try:
            element = ET.SubElement(root, 'item')
            # Escape special characters and ensure valid XML
            element.text = str(item).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        except Exception as e:
            logging.error(f"Error adding item to XML: {str(e)}")
            continue
    
    try:
        # Pretty print XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    except Exception as e:
        logging.error(f"Error saving XML file {filename}: {str(e)}")
        # Fallback to simple XML format
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

def process_target(target, cookies=None, headers=None, depth=None, timeout=None, 
                  output_format='txt', proxy=None, scope=None, exclude=None, 
                  wayback_timeout=None):
    """Process a single target."""
    try:
        if not is_valid_url(target):
            raise ValueError(f"Invalid URL: {target}")
        
        sanitized_target = sanitize_filename(target)
        target_dir = os.path.join("output", sanitized_target)
        os.makedirs(target_dir, exist_ok=True)
        
        katana_output = os.path.join(target_dir, "katana_output.txt")
        wayback_output = os.path.join(target_dir, "wayback_output.txt")
        
        run_katana(target, katana_output, cookies, headers, depth, timeout, scope, exclude, proxy)
        run_waybackurls(target, wayback_output, wayback_timeout)
        
        katana_exists = os.path.exists(katana_output) and os.path.getsize(katana_output) > 0
        wayback_exists = os.path.exists(wayback_output) and os.path.getsize(wayback_output) > 0
        
        params, directories, subdomains, extracted_dirs, api_endpoints = set(), set(), set(), set(), set()
        wb_params, wb_directories, wb_subdomains, wb_extracted_dirs, wb_api_endpoints = set(), set(), set(), set(), set()
        
        if katana_exists:
            params, directories, subdomains, extracted_dirs, api_endpoints = extract_data(katana_output, target_dir)
        
        if wayback_exists:
            wb_params, wb_directories, wb_subdomains, wb_extracted_dirs, wb_api_endpoints = extract_data(wayback_output, target_dir)
        
        post_params = set()
        if katana_exists:
            with open(katana_output, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try:
                        url = line.strip()
                        if url and not url.startswith('#'):
                            post_params.update(extract_post_params(url, cookies, headers))
                    except Exception as e:
                        logging.error(f"Error processing URL for POST params: {line.strip()}, Error: {e}")
        
        all_params = params.union(wb_params).union(post_params)
        all_directories = directories.union(wb_directories)
        all_subdomains = subdomains.union(wb_subdomains)
        all_extracted_dirs = extracted_dirs.union(wb_extracted_dirs)
        all_api_endpoints = api_endpoints.union(wb_api_endpoints)
        
        output_files = {
            'params': {'data': all_params, 'txt': 'params_wordlist.txt', 'json': 'params.json', 'xml': 'params.xml'},
            'directories': {'data': all_directories, 'txt': 'directories_wordlist.txt', 'json': 'directories.json', 'xml': 'directories.xml'},
            'subdomains': {'data': all_subdomains, 'txt': 'subdomains_wordlist.txt', 'json': 'subdomains.json', 'xml': 'subdomains.xml'},
            'extracted_dirs': {'data': all_extracted_dirs, 'txt': 'extracted_directories_wordlist.txt', 'json': 'extracted_dirs.json', 'xml': 'extracted_dirs.xml'},
            'api_endpoints': {'data': all_api_endpoints, 'txt': 'api_endpoints.txt', 'json': 'api_endpoints.json', 'xml': 'api_endpoints.xml'}
        }
        
        for data_type, file_info in output_files.items():
            if output_format == 'txt' or output_format == 'all':
                save_wordlist(file_info['data'], os.path.join(target_dir, file_info['txt']))
            if output_format == 'json' or output_format == 'all':
                save_json(file_info['data'], os.path.join(target_dir, file_info['json']))
            if output_format == 'xml' or output_format == 'all':
                save_xml(file_info['data'], os.path.join(target_dir, file_info['xml']), data_type)
        
        with open(os.path.join(target_dir, "summary.txt"), 'w', encoding='utf-8') as f:
            f.write(f"Target: {target}\n")
            f.write(f"Parameters found: {len(all_params)}\n")
            f.write(f"Directories found: {len(all_directories)}\n")
            f.write(f"Subdomains found: {len(all_subdomains)}\n")
            f.write(f"Extracted directory paths: {len(all_extracted_dirs)}\n")
            f.write(f"API endpoints found: {len(all_api_endpoints)}\n")
        
        print(f"Processing {target} completed.")
    except Exception as e:
        logging.error(f"Error processing {target}: {str(e)}")
        print(f"Error processing {target}: {e}")

def show_best_practices():
    """Display stylized help menu for wlmaker-pro."""
    # Check if terminal supports colors
    if os.environ.get('TERM') and 'color' in os.environ.get('TERM'):
        # ANSI color codes
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'
    else:
        # No colors if terminal doesn't support them
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = BOLD = UNDERLINE = END = ''

    # Force color output
    os.environ['FORCE_COLOR'] = '1'
    os.environ['PYTHON_FORCE_COLOR'] = '1'

    logo = f"""
{BLUE} _    _ _                  _             {END}
{BLUE}| |  | | |                | |            {END}
{BLUE}| |  | | |_ __ ___   __ _| | _____ _ __ {END}
{BLUE}| |/\\| | | '_ ` _ \\ / _` | |/ / _ \\ '__|{END}
{BLUE}\\  /\\  / | | | | | | (_| |   <  __/ |   {END}
{BLUE} \\/  \\/|_|_| |_| |_|\\__,_|_|\\_\\___|_|   {END}
                                {YELLOW}v0.2 by @mmatinjafari{END}
{CYAN}WⓁmaker-pro - Advanced Web Crawler & Parameter Extractor{END}
        {CYAN}https://github.com/mmatinjafari/wlmaker-pro{END}

"""
    usage = f"""
{BLUE}Usage:{END} wlmaker [-u [--url]] [-f[--file=]] [options]

{GREEN}Example:{END} wlmaker https://example.com
         wlmaker --file urls.txt --format all

{YELLOW}Best Practice Command:{END}
  wlmaker -u domain.com --format all --depth 3 --timeout 30 --scope strict --cookies "session=xyz" --headers "User-Agent: Mozilla/5.0"

{MAGENTA}Core Arguments:{END}
  -u,  --url            Target URL to scan
  -f,  --file           File containing list of URLs
  -h,  --help           Show this help message
  -v,  --version        Show version information

{CYAN}Output Options:{END}
  --format              Output format (txt, json, xml, all)
  --threads             Number of parallel targets to process

{GREEN}Crawling Options:{END}
  --depth              Crawl depth for Katana
  --timeout            Timeout in seconds for Katana
  --scope              Crawling scope (strict, fuzzy, subdomain)
  --exclude            Pattern to exclude from crawling

{YELLOW}Authentication:{END}
  --cookies            Cookies for authentication
  --headers            Custom headers for requests
  --proxy             Proxy for requests
  --disable-ssl-verify Disable SSL verification

{BLUE}Additional Features:{END}
  --wayback-timeout    Timeout for waybackurls fetching

{MAGENTA}Output Files Generated:{END}
  + params_wordlist.txt          - Extracted parameters
  + directories_wordlist.txt     - Discovered directories
  + subdomains_wordlist.txt     - Found subdomains
  + api_endpoints.txt           - API endpoints
  + static_files.txt           - Static file URLs
  + fragments.txt             - URL fragments
  + summary.txt              - Summary of findings
  + *.json                  - JSON format outputs
  + *.xml                  - XML format outputs

{CYAN}Tools Used:{END}
  + Katana               https://github.com/projectdiscovery/katana
  + Waybackurls         https://github.com/tomnomnom/waybackurls
"""
    print(logo + usage)

def main():
    parser = argparse.ArgumentParser(description='An advanced tool for crawling and data extraction.')
    # Add both positional and optional URL arguments
    parser.add_argument('url', nargs='?', help='Target URL (e.g., https://example.com)')
    parser.add_argument('-u', '--url', dest='url_opt', help='Target URL (e.g., https://example.com)')
    parser.add_argument('--file', help='File containing a list of URLs')
    parser.add_argument('--cookies', help='Cookies for authentication (e.g., sessionid=abc123)')
    parser.add_argument('--headers', metavar='HEADER:VALUE', help='Additional headers (e.g., "User-Agent: Mozilla/5.0")', nargs='+')
    parser.add_argument('--depth', help='Crawl depth for Katana', type=int)
    parser.add_argument('--timeout', help='Timeout in seconds for Katana', type=int)
    parser.add_argument('--wayback-timeout', help='Timeout in seconds for waybackurls', type=int, default=120)
    parser.add_argument('--format', choices=['txt', 'json', 'xml', 'all'], default='txt', 
                        help='Output format: txt (default), json, xml, or all')
    parser.add_argument('--proxy', help='Proxy to use for requests (e.g., http://127.0.0.1:8080)')
    parser.add_argument('--scope', choices=['strict', 'fuzzy', 'subdomain'], 
                        help='Scope for crawling: strict, fuzzy, or subdomain')
    parser.add_argument('--exclude', help='Pattern to exclude from crawling')
    parser.add_argument('--threads', help='Number of parallel targets to process', type=int, default=5)
    parser.add_argument('--disable-ssl-verify', help='Disable SSL certificate verification', action='store_true')
    parser.add_argument('--version', '-v', action='version', version='wlmaker-pro v0.2')
    args = parser.parse_args()

    # Show best practices if no arguments provided
    if not args.url and not args.url_opt and not args.file:
        show_best_practices()
        return

    # Process arguments
    if not args.url and not args.url_opt and not args.file:
        parser.error("Please provide a URL or a file with URLs")

    cookies = args.cookies
    headers = {}
    if args.headers:
        for header in args.headers:
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            else:
                print(f"Warning: Ignoring invalid header format: {header}")

    depth = args.depth
    timeout = args.timeout
    output_format = args.format
    proxy = args.proxy
    scope = args.scope
    exclude = args.exclude
    threads = args.threads
    wayback_timeout = args.wayback_timeout
    
    if args.disable_ssl_verify:
        # Disable SSL warnings
        requests.packages.urllib3.disable_warnings()

    if args.file:
        with open(args.file, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
    else:
        # Use either the positional url argument or the -u/--url argument
        target_url = args.url or args.url_opt
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url
        targets = [target_url]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(
            process_target, 
            target, 
            cookies, 
            headers, 
            depth, 
            timeout, 
            output_format,
            proxy,
            scope,
            exclude,
            wayback_timeout
        ) for target in targets]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing targets"):
            future.result()

if __name__ == "__main__":
    main()
