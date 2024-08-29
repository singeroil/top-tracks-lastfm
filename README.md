# Last.fm Top Tracks Generator

This Python script fetches and generates top tracks data from Last.fm for a specified user and period. It exports the results in various formats, including XLSX, CSV, and Reddit-style table.

## Features

- Fetch top tracks data for weekly, monthly, or yearly periods.
- Export results in XLSX, CSV, or Reddit-style table formats.
- Customizable date ranges and number of top tracks per period.

## Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/singeroil/top-tracks-lastfm.git
    ```
    
2. **Navigate to the Project Directory**

    ```bash
    cd top-tracks-lastfm
    ```
    
3. **Create a Virtual Environment (Optional but Recommended)**

    ```bash
    python -m venv venv
    ```
    
4. **Activate the Virtual Environment**

    - On Windows:
    ```bash
    venv\Scripts\activate
    ```
    
    - On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```
    
5. **Install the Required Packages**

    ```bash
    pip install -r requirements.txt
    ```
    
6. **Set Up Your API Key**

    Create a `credentials.py` file in the project directory with the following content:

    ```python
    API_KEY = 'your_lastfm_api_key_here'
    ```
    
    Replace `your_lastfm_api_key_here` with your Last.fm API key. Ensure this file is added to your `.gitignore` to keep your API key secure.

7. **Usage**

    Run the script using:

    ```bash
    python top-tracks-lastfm.py
    ```
    
    Follow the prompts to:

    - Enter the Last.fm username.
    - Select the period (Weekly, Monthly, or Yearly).
    - Specify the number of top tracks per period (1-10).
    - Choose the date range (From today, All time, or Custom time).
    - Select the file format (XLSX, CSV, or Reddit Table).

    **Example**

    ```bash
    python top-tracks-lastfm.py
    ```
    
    - Enter Last.fm username: `example_user`
    - Select the period: `1` (Weekly)
    - Enter number of top tracks per period: `5`
    - Select the date range: `1` (From today)
    - Select the file format: `1` (XLSX)

8. **License**

    This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.