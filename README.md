# Golf Buddy 🏌️‍♂️

A command-line tool to help golfers find and analyze tee times from golf course websites.

## Features

- **Smart Tee Time Analysis**: Uses AI to analyze golf course websites and extract available tee times
- **Markdown Processing**: Converts web content to clean, readable markdown for better analysis
- **Interactive CLI**: User-friendly command-line interface with helpful prompts
- **Link Following**: Automatically follows booking links to find tee times
- **Detailed Output**: Shows tee time details including:
  - Available times
  - Number of players
  - Pricing information
  - Additional notes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AshKash/golf_buddy.git
cd golf_buddy
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Basic Commands

1. Say hello to Golf Buddy:
```bash
python src/main.py hello
```

2. Check tee times (basic scraping):
```bash
python src/main.py check-tee-times
```

3. Analyze tee times with AI:
```bash
python src/main.py analyze-tee-times
```

### Options

- `--url`: Specify the golf course website URL
- `--follow/--no-follow`: Control whether to automatically follow booking links (default: true)

## Project Structure

```
golf_buddy/
├── src/
│   ├── main.py              # CLI entry point
│   ├── tee_time_analyzer.py # AI-powered tee time analysis
│   ├── web_processor.py     # Web page fetching and markdown conversion
│   ├── html_to_md.py        # HTML to Markdown conversion
│   └── scraper.py           # Basic web scraping utilities
├── requirements.txt         # Project dependencies
└── README.md               # This file
```

## How It Works

1. **Web Page Fetching**: Uses Playwright to fetch and render web pages, ensuring all dynamic content is loaded
2. **Content Processing**: Converts HTML to clean Markdown for better analysis
3. **AI Analysis**: Uses GPT-4 to analyze the content and extract tee time information
4. **Result Display**: Shows the next available tee time or suggests relevant booking links

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 