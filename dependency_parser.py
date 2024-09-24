import ast
import os
import yaml
import platform
import subprocess
import sys
import pkgutil
import logging
import requests  # For querying PyPI API
import xmlrpc.client  # For searching PyPI
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Manual mapping of import names to actual PyPI package names
manual_package_mapping = {
    'cv2': 'opencv-python',
    'skimage': 'scikit-image',
    'bs4': 'beautifulsoup4',
}

def load_config():
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)

def is_virtual_env(path):
    """Checks if the folder is a virtual environment by looking for 'bin' or 'Scripts' directory."""
    return (os.path.isdir(os.path.join(path, 'bin')) or 
            os.path.isdir(os.path.join(path, 'Scripts')))

def find_python_files(paths, include_folders, ignore_dirs):
    python_files = []
    for path in paths:
        for root, dirs, files in os.walk(path):
            # Skip ignored directories and virtual environments
            if any(ignored in root for ignored in ignore_dirs) or is_virtual_env(root):
                continue
            if any(folder in root for folder in include_folders):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
        # Include files directly in the specified paths, but skip ignored directories
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            if file.endswith('.py') and full_path not in ignore_dirs:
                python_files.append(full_path)
    logging.info(f"Found {len(python_files)} Python files to parse.")
    return python_files

def extract_dependencies(python_files):
    dependencies = set()
    for file in python_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                node = ast.parse(f.read(), filename=file)
                for n in ast.walk(node):
                    if isinstance(n, ast.Import):
                        for alias in n.names:
                            module_name = alias.name.split('.')[0]
                            dependencies.add(module_name)
                    elif isinstance(n, ast.ImportFrom):
                        if n.module:
                            module_name = n.module.split('.')[0]
                            dependencies.add(module_name)
            except SyntaxError as e:
                logging.warning(f"Syntax error in file {file}: {e}")
    logging.info(f"Extracted {len(dependencies)} dependencies.")
    return dependencies

def get_standard_lib_modules():
    standard_lib_modules = set(sys.builtin_module_names)
    if hasattr(sys, 'base_prefix'):
        prefix = sys.base_prefix
    else:
        prefix = sys.prefix
    std_lib_dir = os.path.join(prefix, 'lib', 'python{}'.format(sys.version[:3]))
    if os.path.isdir(std_lib_dir):
        for _, modname, ispkg in pkgutil.iter_modules([std_lib_dir]):
            standard_lib_modules.add(modname)
    # Add commonly known built-in modules that might not be caught
    standard_lib_modules.update({'collections', 'os', 'sys', 're', 'math', 'json', 'time', 'datetime', 'random', 'itertools', 'functools', 'subprocess', 'threading', 'logging', 'multiprocessing', 'ctypes', 'pickle', 'asyncio', 'typing', 'unittest', 'queue', 'pathlib', 'socket', 'email', 'string', 'struct', 'heapq', 'copy', 'enum', 'inspect'})
    return standard_lib_modules

def filter_dependencies(dependencies):
    standard_lib_modules = get_standard_lib_modules()
    filtered_dependencies = set()
    for dep in dependencies:
        if dep not in standard_lib_modules:
            filtered_dependencies.add(dep)
    logging.info(f"Filtered out {len(dependencies) - len(filtered_dependencies)} standard library modules.")
    return filtered_dependencies

@lru_cache(maxsize=None)
def check_pypi_package(package_name):
    """Check if the package exists on PyPI by querying the PyPI JSON API."""
    url = f'https://pypi.org/pypi/{package_name}/json'
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error(f"Error checking PyPI for package '{package_name}': {e}")
        return False

def search_pypi_package(module_name):
    """Search PyPI for packages that might provide the module."""
    client = xmlrpc.client.ServerProxy('https://pypi.org/pypi')
    try:
        search_results = client.search({'name': module_name, 'summary': module_name}, 'or')
        # Filter results to those that have exact module_name in name
        for result in search_results:
            if module_name.lower() == result['name'].lower():
                return result['name']
        # If no exact match, return the first result
        if search_results:
            return search_results[0]['name']
        else:
            return None
    except Exception as e:
        logging.error(f"Error searching PyPI for module '{module_name}': {e}")
        return None

def validate_dependencies(dependencies):
    """Attempt to map dependencies to PyPI package names."""
    validated_dependencies = set()
    for dep in dependencies:
        # Ignore internal modules
        if dep.startswith("_"):
            logging.warning(f"Warning: Ignoring invalid dependency '{dep}'")
            continue
        # Use manual mapping if available
        if dep in manual_package_mapping:
            package_name = manual_package_mapping[dep]
            validated_dependencies.add(package_name)
            logging.info(f"Using manual mapping for module '{dep}' to package '{package_name}'")
            continue
        # Check if a package with the module name exists on PyPI
        if check_pypi_package(dep):
            validated_dependencies.add(dep)
        else:
            # Attempt to search for the package
            package_name = search_pypi_package(dep)
            if package_name and check_pypi_package(package_name):
                logging.info(f"Mapping module '{dep}' to package '{package_name}'")
                validated_dependencies.add(package_name)
            else:
                logging.warning(f"Warning: '{dep}' not found on PyPI. Manual mapping may be required.")
    logging.info(f"Validated {len(validated_dependencies)} out of {len(dependencies)} dependencies.")
    return validated_dependencies

def detect_system_type(config):
    sys_type = platform.system().lower()
    if 'linux' in sys_type and config.get('gpu_required'):
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return 'linux-gpu'
            else:
                return 'linux-cpu'
        except FileNotFoundError:
            return 'linux-cpu'
    elif sys_type == 'windows' and config.get('gpu_required'):
        # Check for NVIDIA GPU on Windows
        try:
            result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if result.returncode == 0:
                return 'windows-gpu'
            else:
                return 'windows-cpu'
        except FileNotFoundError:
            return 'windows-cpu'
    else:
        return sys_type

def adjust_dependencies(dependencies, system_type):
    adjusted_deps = set()
    torch_version = ''
    # Adjust torch dependency based on system_type
    if 'torch' in dependencies or 'ultralytics' in dependencies:
        dependencies.discard('torch')  # Remove 'torch' from dependencies
        if system_type.endswith('gpu'):
            # For GPU systems, specify CUDA-enabled version
            if system_type.startswith('linux'):
                torch_version = "torch==2.0.1+cu117 -f https://download.pytorch.org/whl/torch_stable.html"
            elif system_type.startswith('windows'):
                torch_version = "torch==2.0.1+cu117 -f https://download.pytorch.org/whl/torch_stable.html"
            else:
                torch_version = "torch"
        else:
            # For CPU systems
            torch_version = "torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html"
        adjusted_deps.add(torch_version)

    # Handle torchvision dependency
    if 'torchvision' in dependencies or 'ultralytics' in dependencies:
        dependencies.discard('torchvision')
        if system_type.endswith('gpu'):
            if system_type.startswith('linux'):
                torchvision_version = "torchvision==0.15.2+cu117 -f https://download.pytorch.org/whl/torch_stable.html"
            elif system_type.startswith('windows'):
                torchvision_version = "torchvision==0.15.2+cu117 -f https://download.pytorch.org/whl/torch_stable.html"
            else:
                torchvision_version = "torchvision"
        else:
            torchvision_version = "torchvision==0.15.2+cpu -f https://download.pytorch.org/whl/torch_stable.html"
        adjusted_deps.add(torchvision_version)

    # Handle ultralytics dependency
    if 'ultralytics' in dependencies:
        dependencies.discard('ultralytics')
        adjusted_deps.add('ultralytics')

    # Add the rest of the dependencies
    for dep in dependencies:
        adjusted_deps.add(dep)

    return adjusted_deps

def generate_requirements_txt(dependencies):
    # Create the results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    try:
        with open('results/requirements.txt', 'w') as f:
            for dep in dependencies:
                if ' -f ' in dep:
                    # For dependencies with find-links, write in a way pip understands
                    package_part, url_part = dep.split(' -f ')
                    f.write(f"{package_part.strip()} \\\n    --find-links {url_part.strip()}\n")
                else:
                    f.write(f"{dep}\n")
        logging.info("Successfully generated requirements.txt in 'results' directory.")
    except Exception as e:
        logging.error(f"Failed to write requirements.txt: {e}")

if __name__ == "__main__":
    # Load configuration from config.yml
    config = load_config()

    # Detect system type and adjust GPU requirements
    system_type = detect_system_type(config)

    # Find all Python files from the specified directories
    python_files = find_python_files(config['project_paths'], config['include_folders'], config.get('ignore_dirs', []))

    # Extract all the dependencies from the Python files
    dependencies = extract_dependencies(python_files)

    # Filter out standard library modules
    dependencies = filter_dependencies(dependencies)

    # Validate that dependencies are valid PyPI packages
    validated_dependencies = validate_dependencies(dependencies)

    # Adjust the dependencies based on system type and GPU availability
    adjusted_dependencies = adjust_dependencies(validated_dependencies, system_type)

    # Generate the requirements.txt
    generate_requirements_txt(adjusted_dependencies)

    print(f"Requirements file generated for {system_type}.")
