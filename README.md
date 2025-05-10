# Golf Buddy 🏌️‍♂️

An AI-powered tool to help you find and analyze tee times at golf courses.

## Features

- 🤖 AI-powered tee time analysis
- 🔍 Automatic booking link detection
- 📊 Smart tee time extraction
- 🌐 Support for multiple golf course websites

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/golf_buddy.git
cd golf_buddy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Analyze Tee Times

Use AI to analyze and extract tee time information from a golf course website:

```bash
python src/main.py analyze-tee-times --url "https://example-golf-course.com"
```

Options:
- `--url`: URL of the golf course website to analyze
- `--follow/--no-follow`: Automatically follow booking links (default: true)

## Development

### Project Structure

```
golf_buddy/
├── src/
│   ├── main.py              # CLI interface
│   ├── tee_time_analyzer.py # AI-powered tee time analysis
│   └── scraper.py          # Web scraping utilities
├── tests/                  # Test files
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Running Tests

```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 