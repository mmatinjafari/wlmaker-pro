import os
import re
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import json
from tqdm import tqdm

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

def run_katana(target, output_file, cookies=None, headers=None, depth=None, timeout=None):
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
        subprocess.run(command, shell=True, check=True)
    else:
        print(f"Using existing Katana output for {target}.")

def run_waybackurls(target, output_file):
    """Run waybackurls to fetch archived URLs and save output."""
    if not os.path.exists(output_file):
        print(f"Fetching URLs for {target} with waybackurls...")
        command = f"echo {target} | waybackurls > {output_file}"
        subprocess.run(command, shell=True, check=True)
    else:
        print(f"Using existing waybackurls output for {target}.")

def extract_data(file_path, target_dir):
    """Extract parameters, directories, and subdomains using regex."""
    param_pattern = re.compile(r'[?&](\w+)=')
    dir_pattern = re.compile(r'/(\w+)/')
    subdomain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
    directory_pattern = re.compile(r'https?://[^/]+(/[^?]+)')
    static_file_pattern = re.compile(r'\.(js|css|pdf|jpg|png|gif|svg|xml|json)$')
    fragment_pattern = re.compile(r'#(\w+)')
    
    params = set()
    directories = set()
    subdomains = set()
    extracted_dirs = set()
    static_files = set()
    fragments = set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
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
                extracted_dirs.add(path)
            static_match = static_file_pattern.search(line)
            if static_match:
                static_files.add(line.strip())
            frag_match = fragment_pattern.search(line)
            if frag_match:
                fragments.add(frag_match.group(1))
    
    # Save static files and fragments
    save_wordlist(static_files, os.path.join(target_dir, "static_files.txt"))
    save_wordlist(fragments, os.path.join(target_dir, "fragments.txt"))
    
    return params, directories, subdomains, extracted_dirs

def extract_post_params(url, cookies=None, headers=None):
    """Extract POST parameters from HTML forms."""
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form', method='post')
        post_params = set()
        for form in forms:
            inputs = form.find_all('input', {'name': True})
            for inp in inputs:
                post_params.add(inp['name'])
        return post_params
    except Exception as e:
        print(f"Error extracting POST params from {url}: {e}")
        return set()

def save_wordlist(data, filename):
    """Save extracted data to a file without extra newlines."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(data)))

def save_json(data, filename):
    """Save data in JSON format."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(data), f, indent=4)

def process_target(target, cookies=None, headers=None, depth=None, timeout=None, json_output=False):
    """Process a single target."""
    try:
        if not is_valid_url(target):
            raise ValueError(f"Invalid URL: {target}")
        
        sanitized_target = sanitize_filename(target)
        target_dir = os.path.join("output", sanitized_target)
        os.makedirs(target_dir, exist_ok=True)
        
        katana_output = os.path.join(target_dir, "katana_output.txt")
        wayback_output = os.path.join(target_dir, "wayback_output.txt")
        
        run_katana(target, katana_output, cookies, headers, depth, timeout)
        run_waybackurls(target, wayback_output)
        
        params, directories, subdomains, extracted_dirs = extract_data(katana_output, target_dir)
        wb_params, wb_directories, wb_subdomains, wb_extracted_dirs = extract_data(wayback_output, target_dir)
        
        # Extract POST parameters from Katana URLs
        post_params = set()
        with open(katana_output, 'r', encoding='utf-8') as f:
            for line in f:
                post_params.update(extract_post_params(line.strip(), cookies, headers))
        
        all_params = params.union(wb_params).union(post_params)
        
        if json_output:
            save_json(all_params, os.path.join(target_dir, "params.json"))
            save_json(directories.union(wb_directories), os.path.join(target_dir, "directories.json"))
            save_json(subdomains.union(wb_subdomains), os.path.join(target_dir, "subdomains.json"))
            save_json(extracted_dirs.union(wb_extracted_dirs), os.path.join(target_dir, "extracted_dirs.json"))
        else:
            save_wordlist(all_params, os.path.join(target_dir, "params_wordlist.txt"))
            save_wordlist(directories.union(wb_directories), os.path.join(target_dir, "directories_wordlist.txt"))
            save_wordlist(subdomains.union(wb_subdomains), os.path.join(target_dir, "subdomains_wordlist.txt"))
            save_wordlist(extracted_dirs.union(wb_extracted_dirs), os.path.join(target_dir, "extracted_directories_wordlist.txt"))
        
        print(f"Processing {target} completed.")
    except Exception as e:
        with open("error.log", "a") as log:
            log.write(f"Error processing {target}: {e}\n")
        print(f"Error processing {target}: {e}")

def main():
    parser = argparse.ArgumentParser(description='An advanced tool for crawling and data extraction.')
    parser.add_argument('url', nargs='?', help='Target URL (e.g., https://example.com)')
    parser.add_argument('--file', help='File containing a list of URLs')
    parser.add_argument('--cookies', help='Cookies for authentication (e.g., sessionid=abc123)')
    parser.add_argument('--headers', help='Additional headers (e.g., Authorization=Bearer token123)', nargs='*', default=[])
    parser.add_argument('--depth', help='Crawl depth for Katana', type=int)
    parser.add_argument('--timeout', help='Timeout in seconds for Katana', type=int)
    parser.add_argument('--json', help='Save output in JSON format', action='store_true')
    args = parser.parse_args()

    cookies = args.cookies
    headers = dict(h.split('=') for h in args.headers) if args.headers else None
    depth = args.depth
    timeout = args.timeout
    json_output = args.json

    if args.file:
        with open(args.file, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
    elif args.url:
        targets = [args.url]
    else:
        print("Please provide a URL or a file with URLs.")
        return

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_target, target, cookies, headers, depth, timeout, json_output) for target in targets]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing targets"):
            future.result()

if __name__ == "__main__":
    main()