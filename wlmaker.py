import os
import re
import subprocess

def run_katana(target, output_file):
    """Run Katana to crawl the target and save output if not already present."""
    if not os.path.exists(output_file):
        print("Crawling target with Katana...")
        command = f"katana -u {target} -o {output_file}"
        subprocess.run(command, shell=True, check=True)
    else:
        print("Using existing Katana output file.")

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
                extracted_dirs.add(dir_match.group(1))
    
    return params, directories, subdomains, extracted_dirs

def save_wordlist(data, filename):
    """Save extracted data to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in sorted(data):
            f.write(item + '\n')

def main(target):
    output_file = "katana_output.txt"
    run_katana(target, output_file)
    
    params, directories, subdomains, extracted_dirs = extract_data(output_file)
    
    save_wordlist(params, "params_wordlist.txt")
    save_wordlist(directories, "directories_wordlist.txt")
    save_wordlist(subdomains, "subdomains_wordlist.txt")
    save_wordlist(extracted_dirs, "extracted_directories_wordlist.txt")
    
    print("Wordlists generated successfully!")

if __name__ == "__main__":
    target_url = input("Enter target URL: ")
    main(target_url)

