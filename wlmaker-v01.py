import os
import re
import subprocess

def sanitize_filename(target):
    """Sanitize target to use in filenames."""
    return target.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")

def run_katana(target, output_file):
    """Run Katana to crawl the target and save output if not already present."""
    if not os.path.exists(output_file):
        print("Crawling target with Katana...")
        command = f"katana -u {target} -o {output_file}"
        subprocess.run(command, shell=True, check=True)
    else:
        print("Using existing Katana output file.")

def run_waybackurls(target, output_file):
    """Run waybackurls to fetch archived URLs and save output if not already present."""
    if not os.path.exists(output_file):
        print("Fetching URLs with waybackurls...")
        command = f"echo {target} | waybackurls > {output_file}"
        subprocess.run(command, shell=True, check=True)
    else:
        print("Using existing waybackurls output file.")

def extract_data(file_path):
    """Extract parameters, directories, and subdomains using regex."""
    param_pattern = re.compile(r'[?&](\w+)=')
    dir_pattern = re.compile(r'\/(\w+)/')
    subdomain_pattern = re.compile(r'https?://([a-zA-Z0-9.-]+)')
    directory_pattern = re.compile(r'https?://[^/]+(/[^?]+)')
    
    params = set()
    directories = set()
    subdomains = set()
    extracted_dirs = set()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            params.update(param_pattern.findall(line))
            directories.update(dir_pattern.findall(line))
            match = subdomain_pattern.search(line)
            if match:
                subdomains.add(match.group(1))
            dir_match = directory_pattern.search(line)
            if dir_match:
                extracted_dirs.add(dir_match.group(1).strip())
    
    return params, directories, subdomains, extracted_dirs

def save_wordlist(data, filename):
    """Save extracted data to a file without extra newlines."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(data)))

def main(target):
    sanitized_target = sanitize_filename(target)
    katana_output = f"katana_output_{sanitized_target}.txt"
    wayback_output = f"wayback_output_{sanitized_target}.txt"
    
    run_katana(target, katana_output)
    run_waybackurls(target, wayback_output)
    
    params, directories, subdomains, extracted_dirs = extract_data(katana_output)
    wb_params, wb_directories, wb_subdomains, wb_extracted_dirs = extract_data(wayback_output)
    
    save_wordlist(params.union(wb_params), f"params_wordlist_{sanitized_target}.txt")
    save_wordlist(directories.union(wb_directories), f"directories_wordlist_{sanitized_target}.txt")
    save_wordlist(subdomains.union(wb_subdomains), f"subdomains_wordlist_{sanitized_target}.txt")
    save_wordlist(extracted_dirs.union(wb_extracted_dirs), f"extracted_directories_wordlist_{sanitized_target}.txt")
    
    print("Wordlists generated successfully!")

if __name__ == "__main__":
    target_url = input("Enter target URL: ")
    main(target_url)

