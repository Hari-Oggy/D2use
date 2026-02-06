# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the security team at [security@example.com]
3. Include details about the vulnerability
4. Allow 48 hours for initial response

## Security Features

This project includes the following security measures:

### File Handling

- **ZIP Bomb Detection**: Prevents decompression attacks
- **File Size Limits**: Configurable maximum download sizes
- **Path Sanitization**: Prevents directory traversal attacks

### API Security

- **Rate Limiting**: Built-in retry logic respects API limits
- **Token Security**: Environment-based API key management
- **Input Validation**: Pydantic schema validation

### Data Security

- **No Data Logging**: Sensitive data is not logged
- **Temporary Files**: Cleaned up after processing
- **Local Processing**: LLM runs locally, no cloud data transmission

## Best Practices for Users

1. **Keep API keys secret**: Never commit `.env` to version control
2. **Update regularly**: Install security patches promptly
3. **Review datasets**: Validate downloaded data before use
4. **Use HTTPS**: Ensure LM Studio runs on localhost only

## Known Limitations

- Web scraper may access URLs specified by search results
- Downloaded datasets are stored locally without encryption
- LM Studio connection is unencrypted (localhost only)

---

_Last updated: January 2026_
