# Contributing to MoonbeamAI

Thank you for your interest in contributing to MoonbeamAI! We welcome contributions from the community and are excited to see what you'll bring to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of financial markets and NLP (helpful but not required)

### Setting Up Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/moonbeamAI.git
   cd moonbeamAI
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## 📝 How to Contribute

### Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed information**:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. **Search existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Explain the use case** and why it would be valuable
4. **Consider backwards compatibility**

### Contributing Code

#### Types of Contributions Welcome
- 🐛 **Bug fixes**
- 🚀 **New features**
- 📊 **Performance improvements**
- 🧪 **Test coverage improvements**
- 📚 **Documentation updates**
- 🎨 **UI/UX improvements**
- 🔧 **Code refactoring**

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**:
   ```bash
   pytest tests/
   ```

4. **Run code quality checks**:
   ```bash
   black .
   flake8 .
   mypy .
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

#### Commit Message Guidelines

Use clear, descriptive commit messages:

- `Add: New feature or functionality`
- `Fix: Bug fixes`
- `Update: Improvements to existing features`
- `Refactor: Code restructuring without functional changes`
- `Docs: Documentation updates`
- `Test: Adding or updating tests`

Examples:
- `Add: WebSocket support for real-time signals`
- `Fix: Handle empty ticker extraction gracefully`
- `Update: Improve sentiment aggregation algorithm`

## 🏗️ Code Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Maximum line length: 88 characters
- Use type hints where possible

### Code Organization
- Keep functions focused and small
- Use descriptive variable and function names
- Add docstrings for all public functions
- Follow the existing project structure

### Example Code Style
```python
from typing import Dict, List, Optional
import asyncio


class ExampleAgent:
    """Agent that demonstrates code style."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the agent with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.is_active = False
    
    async def process_data(
        self, 
        input_data: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            input_data: The data to process
            options: Optional processing parameters
            
        Returns:
            Processing results dictionary
        """
        # Implementation here
        return {"processed": True}
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=.

# Run specific test file
pytest tests/test_api_endpoints.py

# Run tests matching pattern
pytest tests/ -k "test_sentiment"
```

### Writing Tests
- Add tests for all new functionality
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies
- Aim for >90% code coverage

### Test Structure
```python
import pytest
from unittest.mock import AsyncMock, patch

from your_module import YourClass


class TestYourClass:
    """Test suite for YourClass."""
    
    @pytest.fixture
    def sample_data(self):
        """Provide sample test data."""
        return {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_process_success(self, sample_data):
        """Test successful processing."""
        instance = YourClass()
        result = await instance.process(sample_data)
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_process_failure(self):
        """Test error handling."""
        instance = YourClass()
        with pytest.raises(ValueError):
            await instance.process(None)
```

## 📚 Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Include type hints
- Document complex algorithms

### README Updates
- Keep the README current with new features
- Add examples for new functionality
- Update installation instructions if needed

## 🔍 Review Process

### Pull Request Guidelines
- **One feature per PR** - keep changes focused
- **Write a clear description** of what your PR does
- **Reference related issues** using `Fixes #123` syntax
- **Add tests** for new functionality
- **Update documentation** as needed

### Review Criteria
- Code follows style guidelines
- Tests pass and cover new functionality
- Documentation is updated
- No breaking changes (unless discussed)
- Performance implications considered

## 🆘 Getting Help

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Discord**: [Coming Soon] Real-time chat with the community

## 📋 Development Priorities

### High Priority
- Improved sentiment analysis models
- Better error handling and logging
- Performance optimizations
- More comprehensive tests

### Medium Priority
- Additional news sources
- Real-time visualization dashboard
- Backtesting framework
- API rate limiting

### Low Priority
- Mobile app interface
- Cloud deployment guides
- Advanced analytics features

## 🏷️ Labels and Tags

We use labels to categorize issues and PRs:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 🎉 Recognition

Contributors will be:
- Listed in the CONTRIBUTORS.md file
- Mentioned in release notes for significant contributions
- Invited to join the core contributor team for consistent contributors

## 📜 Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

---

Thank you for contributing to MoonbeamAI! Your efforts help make financial technology more accessible and powerful for everyone. 🚀 