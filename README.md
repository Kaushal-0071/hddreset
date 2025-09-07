
<div align="center">

# hddreset

[![Simple Analytics](https://simpleanalytics.com/Kaushal-0071/hddreset.svg)](https://simpleanalytics.com/Kaushal-0071/hddreset)
[![Code Size](https://img.shields.io/github/languages/code-size/Kaushal-0071/hddreset)](https://github.com/Kaushal-0071/hddreset)
[![GitHub License](https://img.shields.io/github/license/Kaushal-0071/hddreset)](https://github.com/Kaushal-0071/hddreset/blob/main/LICENSE)

</div>

This repository contains the source code for `hddreset`, a tool designed to securely wipe hard drives. It provides functionality for generating bootable ISO images that facilitate the disk wiping process.

## Features

-   Generates bootable ISO images.
-   Includes core wiping utilities.
-   Uses cryptography for secure certificate generation.
-   Configurable build process.

## Table of Contents

-   [Installation](#installation)
-   [Usage](#usage)
-   [Dependencies](#dependencies)
-   [Contributing](#contributing)
-   [License](#license)
-   [Contact](#contact)

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/Kaushal-0071/hddreset.git
    cd hddreset
    ```

2.  Create a virtual environment:

    ```bash
    python3 -m venv venv
    ```

3.  Activate the virtual environment:

    ```bash
    source venv/bin/activate
    ```

4.  Install the required dependencies:

    ```bash
    pip install pycdlib Pillow
    ```

## Usage

1. Build the ISO image

    ```bash
    python3 build_iso.py
    ```

2. Run build script to build the project

    ```bash
    ./build.sh
    ```

## Dependencies

-   `pycdlib`: Used for creating ISO images.
-   `Pillow`: Required for image processing tasks.

## Contributing

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with descriptive messages.
4.  Submit a pull request.

