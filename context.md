# Petlog Development Context

## Purpose
This document defines the development rules, guidelines, and practices that AI agents should follow when working on the petlog project. It serves as the primary reference for maintaining consistency and quality throughout the development process.

---

# Development Rules & Guidelines

## 1. Code Quality Standards

### Naming & Documentation
- **Use Clear, Meaningful Names**: Variable, function, and class names should be self-documenting
- **Minimize Comments**: Only comment complex logic or non-obvious design decisions
- **No Magic Numbers**: Use named constants with descriptive names instead of hardcoded values
- **Type Hints Required**: All Python functions must include type annotations

### Code Structure
- **Single Responsibility Principle**: Each function/class should have one clear purpose
- **Modular Design**: Break functionality into small, reusable components. Follow OOD / SOLID principles.
- **Configuration Over Hardcoding**: Use environment variables and config files for settings

## 2. Git Workflow & Commit Standards

### Commit Message Format
Use **Conventional Commits** format for GitHub Actions compatibility:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
- `feat(detection): add pet face recognition module`
- `fix(api): resolve video stream memory leak`
- `docs: update API endpoint documentation`
- `test(recorder): add unit tests for video recording`

### Branching Strategy
- **Never commit directly to main/master**
- **Feature branches**: `feature/description` or `feat/description`
- **Bug fixes**: `fix/description`
- **Documentation**: `docs/description`
- **Small, atomic commits**: Each commit should represent one logical change

### Pull Request Process
1. Create feature branch from main
2. Make small, focused commits
3. Write clear PR description with:
   - What was changed and why
   - Multiple solution options considered (if applicable)
   - Trade-offs and decisions made
4. Include UML diagrams in `architectures/` folder when relevant
5. Ensure all tests pass before requesting review

## 3. Testing Requirements

### Test Coverage
- **Unit tests required** for all new functionality
- **Integration tests** for API endpoints
- **Hardware tests** for Raspberry Pi specific features
- **Test before merge**: All tests must pass before PR approval

### Test Structure
- Use pytest framework
- Tests in `tests/` directory mirroring source structure
- Mock external dependencies (camera, hardware)
- Test both success and failure scenarios

## 4. Development Workflow

### Incremental Development
- **Break work into small tasks**: Each task should be completable in 1-2 hours
- **Atomic commits**: Each commit should build and run successfully
- **Continuous integration**: Commit frequently to avoid large merge conflicts

### Solution Planning
When implementing new features:
1. **Research and document** multiple approaches with pro and cons
2. **List pros and cons** for each option
3. **Explain trade-offs** clearly
4. **Choose approach** based on project constraints
5. **Document decision** in commit message or PR description

### Architecture Documentation
- **UML diagrams** for complex interactions go in `architectures/` folder
- **Use Mermaid format** for VS Code compatibility
- **Update diagrams** when architecture changes
- **Reference diagrams** in code comments when helpful

## 5. File Organization

### Directory Structure
```
petlog/
├── docs/                    # Technical documentation
├── arch/           # UML diagrams and architecture docs
├── src/                     # Source code
├── tests/                   # Test files
├── scripts/                 # Deployment and utility scripts
├── config/                  # Configuration files
└── requirements.txt         # Python dependencies
```

### Documentation
- **Technical decisions** → `docs/technical-decisions.md`
- **API documentation** → Auto-generated from FastAPI
- **Setup instructions** → `README.md`
- **Architecture diagrams** → `arch/`

## 6. Error Handling & Logging

### Error Handling
- **Graceful degradation**: System should continue operating when non-critical components fail
- **Specific exceptions**: Catch specific exceptions, not generic `Exception`
- **User-friendly messages**: Log technical details, show user-friendly messages

### Logging Standards
- **Structured logging**: Use consistent log format
- **Appropriate levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **No sensitive data**: Never log passwords, tokens, or personal information
- **Log rotation**: Prevent logs from consuming excessive storage

## 7. Performance & Resource Management

### Raspberry Pi Considerations
- **Memory efficiency**: Monitor memory usage, especially for video processing
- **CPU optimization**: Use hardware acceleration when available
- **Storage management**: Implement automatic cleanup for old recordings
- **Power efficiency**: Optimize for continuous operation

### Code Performance
- **Async operations**: Use async/await for I/O operations
- **Efficient algorithms**: Choose appropriate data structures and algorithms
- **Resource cleanup**: Properly close files, connections, and release resources

## 8. Security Guidelines

### Data Protection
- **No hardcoded secrets**: Use environment variables for sensitive data
- **Input validation**: Validate all user inputs and API parameters
- **Secure defaults**: Default to secure configurations
- **Regular updates**: Keep dependencies updated for security patches

### Access Control
- **Authentication required**: All API endpoints must be authenticated
- **HTTPS only**: No unencrypted communication
- **Principle of least privilege**: Grant minimum necessary permissions

---

# AI Agent Instructions

When working on this project:

1. **Follow all rules above** without exception
2. **Ask for clarification** if requirements are ambiguous
3. **Propose multiple solutions** for complex problems
4. **Explain your reasoning** for technical decisions
5. **Update documentation** when making changes
6. **Run tests** before submitting changes
7. **Use conventional commit messages** for GitHub Actions compatibility
8. **Create UML diagrams** for complex features in `architectures/` folder

## Quick Reference

- **Commit format**: `type(scope): description`
- **Branch naming**: `feat/description`, `fix/description`, `docs/description`
- **Test command**: `pytest tests/`
- **Documentation**: Technical decisions in `docs/`, architecture in `architectures/`
- **No direct commits to main**: Always use feature branches

This context file should be consulted before making any changes to ensure consistency with project standards and practices.
