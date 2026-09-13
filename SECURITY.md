# Security Policy and Best Practices

## 🔒 API Key and Secret Management

This project handles sensitive API keys (Groq, FinMind, etc.). Please follow these security guidelines:

### ✅ DO:
- **Use GitHub Secrets**: Store all API keys in GitHub Repository Settings → Secrets → Actions
- **Use Environment Variables**: Access secrets via `os.getenv()` in your code
- **Keep `.env` files local**: Never commit `.env`, `.env.local`, or any file containing actual credentials
- **Review PRs carefully**: Especially those modifying `.github/workflows/` or source code that accesses secrets
- **Rotate keys regularly**: Change API keys every 3-6 months

### ❌ DON'T:
- **Never hardcode API keys** in source code
- **Never commit `.env` files** to the repository
- **Never print secrets** in logs or console output
- **Never merge untrusted PRs** that modify workflow files without thorough review

## 🛡️ GitHub Secrets Protection

GitHub provides robust protection for secrets:

1. **Encrypted Storage**: Secrets are encrypted at rest
2. **Log Masking**: Automatic redaction of secret values in workflow logs (shown as `***`)
3. **Fork Protection**: Secrets are NOT exposed to workflows triggered by forks

## ⚠️ Public Repository Risks

Since this is a public repository, be aware of:

### 1. Malicious Pull Requests
- Attackers may submit PRs that exfiltrate secrets
- **Defense**: Always review code changes, especially in workflow files

### 2. Third-party Actions
- Only use trusted, well-maintained GitHub Actions
- Pin actions to specific commits when possible

### 3. Accidental Exposure
- If you accidentally commit a secret, **immediately revoke it** at the provider
- GitHub history can be mined even after removal

## 📋 Required Secrets

The following secrets must be configured in GitHub Settings:

| Secret Name | Description | Provider |
|-------------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM inference | Groq Cloud |
| `FINMIND_API_TOKEN` | FinMind API token for market data | FinMind |
| `AI_API_KEY` | General AI service key | Various |
| `GH_TOKEN` | GitHub Personal Access Token (repo scope only) | GitHub |

## 🔐 Setting Up Locally

1. Create a `.env` file (already in `.gitignore`):
   ```bash
   cp .env.example .env
   ```

2. Add your keys:
   ```
   GROQ_API_KEY=your_groq_key_here
   FINMIND_API_TOKEN=your_finmind_token_here
   ```

3. Run the application - it will read from environment variables

## 🚨 If You Suspect a Leak

1. **Immediately revoke** the compromised key at the provider
2. Generate a new key
3. Update GitHub Secrets
4. Review recent workflow runs for suspicious activity
5. Consider enabling branch protection rules

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OpenSSF Scorecard](https://securityscorecards.dev/)
- [GitHub Security Lab](https://securitylab.github.com/)
