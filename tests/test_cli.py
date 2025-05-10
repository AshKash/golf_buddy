#!/usr/bin/env python3
"""
Test suite for the Golf Buddy CLI.
"""

import os
import pytest
from click.testing import CliRunner
from src.main import cli
from unittest.mock import patch, MagicMock

# Test URLs
TEST_URLS = [
    "https://example.com",
    "https://test-golf-course.com",
    "https://another-course.com"
]

@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()

@pytest.fixture(autouse=True)
def set_headless_true():
    """Set headless mode to True for all tests."""
    os.environ['GOLF_BUDDY_HEADLESS'] = 'true'
    yield
    os.environ.pop('GOLF_BUDDY_HEADLESS', None)

def test_cli_help(runner):
    """Test that the CLI help message is displayed correctly."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Golf Buddy - Your AI-powered tee time finder" in result.output
    assert "analyze-tee-times" in result.output
    assert "convert-to-markdown" in result.output

def test_analyze_tee_times_help(runner):
    """Test that the analyze-tee-times help message is displayed correctly."""
    result = runner.invoke(cli, ['analyze-tee-times', '--help'])
    assert result.exit_code == 0
    assert "Use AI to analyze and extract tee time information" in result.output
    assert "--follow" in result.output
    assert "--no-follow" in result.output

def test_convert_to_markdown_help(runner):
    """Test that the convert-to-markdown help message is displayed correctly."""
    result = runner.invoke(cli, ['convert-to-markdown', '--help'])
    assert result.exit_code == 0
    assert "Convert a webpage to clean markdown format" in result.output
    assert "--output" in result.output
    assert "-o" in result.output

@patch('src.tee_time_analyzer.fetch_and_extract_tee_times')
def test_analyze_tee_times_success(mock_fetch, runner):
    """Test successful tee time analysis."""
    mock_fetch.return_value = None
    result = runner.invoke(cli, ['analyze-tee-times', 'https://example.com'])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with('https://example.com', True)

@patch('src.tee_time_analyzer.fetch_and_extract_tee_times')
def test_analyze_tee_times_no_follow(mock_fetch, runner):
    """Test tee time analysis with no-follow option."""
    mock_fetch.return_value = None
    result = runner.invoke(cli, ['analyze-tee-times', '--no-follow', 'https://example.com'])
    assert result.exit_code == 0
    mock_fetch.assert_called_once_with('https://example.com', False)

def test_analyze_tee_times_no_urls(runner):
    """Test that an error is shown when no URLs are provided."""
    result = runner.invoke(cli, ['analyze-tee-times'])
    assert result.exit_code != 0
    assert "Missing argument 'URLS...'" in result.output

@patch('src.web_processor.get_visible_rendered_html')
def test_convert_to_markdown_success(mock_get_html, runner):
    """Test successful markdown conversion."""
    mock_get_html.return_value = "# Test Content"
    result = runner.invoke(cli, ['convert-to-markdown', 'https://example.com'])
    assert result.exit_code == 0
    assert "# Test Content" in result.output
    mock_get_html.assert_called_once_with('https://example.com')

@patch('src.web_processor.get_visible_rendered_html')
def test_convert_to_markdown_with_output(mock_get_html, runner, tmp_path):
    """Test markdown conversion with output file."""
    mock_get_html.return_value = "# Test Content"
    output_file = tmp_path / "output.md"
    result = runner.invoke(cli, ['convert-to-markdown', 'https://example.com', '-o', str(output_file)])
    assert result.exit_code == 0
    assert output_file.read_text() == "# Test Content"
    mock_get_html.assert_called_once_with('https://example.com')

def test_convert_to_markdown_invalid_url(runner):
    """Test that an error is shown for invalid URLs."""
    result = runner.invoke(cli, ['convert-to-markdown', 'not-a-url'])
    assert result.exit_code != 0
    assert "Error processing URL" in result.output

def test_convert_to_markdown_no_url(runner):
    """Test that an error is shown when no URL is provided."""
    result = runner.invoke(cli, ['convert-to-markdown'])
    assert result.exit_code != 0
    assert "Missing argument 'URL'" in result.output

def test_analyze_tee_times_single_url(runner):
    """Test analyze-tee-times command with a single URL."""
    result = runner.invoke(cli, ['analyze-tee-times', TEST_URLS[0]])
    assert result.exit_code == 0
    assert f"Analyzing tee times from {TEST_URLS[0]}" in result.output

def test_analyze_tee_times_multiple_urls(runner):
    """Test analyze-tee-times command with multiple URLs."""
    result = runner.invoke(cli, ['analyze-tee-times', *TEST_URLS])
    assert result.exit_code == 0
    for url in TEST_URLS:
        assert f"Analyzing tee times from {url}" in result.output

def test_analyze_tee_times_follow_option(runner):
    """Test analyze-tee-times command with --no-follow option."""
    result = runner.invoke(cli, ['analyze-tee-times', '--no-follow', TEST_URLS[0]])
    assert result.exit_code == 0
    assert f"Analyzing tee times from {TEST_URLS[0]}" in result.output

def test_convert_to_markdown_file(runner, tmp_path):
    """Test convert-to-markdown command with file output."""
    output_file = tmp_path / "output.md"
    result = runner.invoke(cli, ['convert-to-markdown', TEST_URLS[0], '-o', str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
    assert output_file.read_text().strip()  # Should have some content

def test_convert_to_markdown_invalid_output_path(runner):
    """Test convert-to-markdown command with an invalid output path."""
    result = runner.invoke(cli, ['convert-to-markdown', TEST_URLS[0], '-o', '/invalid/path/output.md'])
    assert result.exit_code != 0
    assert "Error" in result.output 