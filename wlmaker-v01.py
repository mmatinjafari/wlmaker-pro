import os
import re
import subprocess
import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm

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
            command += f" -t {timeout}"
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
                params.update(query_params.keys())
            
            # Extract other patterns
            params.update(param_pattern.findall(line))
            directories.update(dir_pattern.findall(line))
            
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
            if frag_match:
                fragments.add(frag_match.group(1))
            
            api_match = api_endpoint_pattern.search(line)
            if api_match:
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
        element = ET.SubElement(root, 'item')
        element.text = item
    
    # Pretty print XML
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_str)

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
        
        params, directories, subdomains, extracted_dirs, api_endpoints = extract_data(katana_output, target_dir)
        wb_params, wb_directories, wb_subdomains, wb_extracted_dirs, wb_api_endpoints = extract_data(wayback_output, target_dir)
        
        # Extract POST parameters from Katana URLs
        post_params = set()
        with open(katana_output, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    url = line.strip()
                    if url:
                        post_params.update(extract_post_params(url, cookies, headers))
                except Exception as e:
                    logging.error(f"Error processing URL for POST params: {line.strip()}, Error: {e}")
        
        all_params = params.union(wb_params).union(post_params)
        all_directories = directories.union(wb_directories)
        all_subdomains = subdomains.union(wb_subdomains)
        all_extracted_dirs = extracted_dirs.union(wb_extracted_dirs)
        all_api_endpoints = api_endpoints.union(wb_api_endpoints)
        
        # Save data based on chosen format
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
        
        # Generate a summary report
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

def main():
    parser = argparse.ArgumentParser(description='An advanced tool for crawling and data extraction.')
    parser.add_argument('url', nargs='?', help='Target URL (e.g., https://example.com)')
    parser.add_argument('--file', help='File containing a list of URLs')
    parser.add_argument('--cookies', help='Cookies for authentication (e.g., sessionid=abc123)')
    parser.add_argument('--headers', help='Additional headers (e.g., Authorization=Bearer token123)', nargs='*', default=[])
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
    args = parser.parse_args()

    # Process arguments
    cookies = args.cookies
    headers = dict(h.split('=', 1) for h in args.headers) if args.headers else None
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
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings()

    if args.file:
        with open(args.file, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
    elif args.url:
        targets = [args.url]
    else:
        print("Please provide a URL or a file with URLs.")
        return

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
