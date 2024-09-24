
# PyEnv

## Introduction

Managing dependencies in Python projects can be challenging, especially when aiming for minimal and precise `requirements.txt` and `environment.yml` files. **PyEnv** is a tool designed to automate this process. Inspired by the common struggle of creating optimized requirement files, PyEnv parses your project files and generates environment configurations tailored to your system specifications.

## Features

- **Automatic Dependency Extraction**: Parses Python files to identify all imported modules.
- **System-Specific Optimization**: Adjusts dependencies based on your operating system and whether a GPU is available.
- **Minimal Dependencies**: Generates `requirements.txt` with only the necessary packages, avoiding bloated environments.
- **Configurable Parsing**: Allows customization of project directories and included folders through `config.yml`.

## Dependencies

This project requires the following Python packages:

- `pyyaml`: For working with YAML configuration files.
- `setuptools`: For packaging and distribution.
- `wheel`: Helps create Python packages and manage dependencies.

These dependencies are automatically installed when running the setup script.

## How to Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

Alternatively, you can run the `setup.sh` script, which handles the environment creation and installs all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

The `chmod +x setup.sh` command ensures that the script has executable permissions before it is run.

## How to Use

### 1. Clone the Repository

```bash
git clone https://github.com/Pranjalab/PyEnv.git
cd PyEnv
```

### 2. Configure the Project

Edit the `config.yml` file to specify your project paths, included folders, system type, and GPU requirements.

```yaml
# config.yml
project_paths:
  - /path/to/your/project
  - /path/to/another/project
include_folders:
  - src
  - lib
system_type: auto  # Options: windows, mac, linux-cpu, linux-gpu, or 'auto' to detect automatically
gpu_required: true
ignore_dirs:
  - venv
  - build
  - dist
  - .git
```

- **project_paths**: List of directories containing your Python project(s).
- **include_folders**: Specific folders within the project paths to include in the parsing.
- **system_type**: Your operating system and whether you require GPU support.
- **gpu_required**: Set to `true` if your project requires GPU-specific packages.
- **ignore_dirs**: Directories to ignore during the parsing (e.g., virtual environments, build directories, `.git` folders).

### 3. Run the Main Script

Execute the `dependency_parser.py` script to generate `requirements.txt` and `environment.yml`:

```bash
python dependency_parser.py
```

### 4. Set Up the Environment

Run the `setup.sh` script to create and activate a virtual environment and install all necessary dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

This script will:

- Create a new virtual environment using Python's `venv`.
- Activate the environment.
- Install all required Python packages from `requirements.txt`.

### 5. Start Using Your Environment

Your environment is now set up with all the necessary dependencies. You can start developing or running your project:

```bash
source venv/bin/activate
python dependency_parser.py
```

## Handling Unresolved Dependencies

In some cases, the script might not automatically resolve the correct PyPI package name for a module (e.g., `cv2`, `bs4`). To handle such cases, you can manually map the import name to the PyPI package name using the `manual_package_mapping` dictionary in `dependency_parser.py`.

### Adding a New Mapping

1. Open the `dependency_parser.py` file and locate the `manual_package_mapping` dictionary.
   
   ```python
   manual_package_mapping = {
       'cv2': 'opencv-python',
       'skimage': 'scikit-image',
       'bs4': 'beautifulsoup4',
   }
   ```

2. Add a new entry for the module that is not automatically detected. For example, if you import `my_module` but the PyPI package is `my-package`, add:

   ```python
   manual_package_mapping = {
       'cv2': 'opencv-python',
       'skimage': 'scikit-image',
       'bs4': 'beautifulsoup4',
       'my_module': 'my-package',
   }
   ```

3. Save the file and run the script again to generate the updated `requirements.txt`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! If you have ideas for improvements or find bugs, please open an issue or submit a pull request.

1. **Fork the Repository**
2. **Create a Feature Branch**: `git checkout -b feature/YourFeature`
3. **Commit Your Changes**: `git commit -m 'Add some feature'`
4. **Push to the Branch**: `git push origin feature/YourFeature`
5. **Open a Pull Request**

Please make sure to update tests as appropriate.

## **Contributors**

---

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/pranjalab">
        <img src="https://github.com/pranjalab.png?size=100" width="100px;" alt="Pranjal Bhaskare"/>
        <br/>
        <b>Pranjal Bhaskare</b>
      </a>
      <br/>
  </tr>
</table>
