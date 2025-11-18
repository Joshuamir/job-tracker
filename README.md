# 🤖 Job Tracker Bot

Automated job scraping bot that monitors career websites and sends instant Telegram notifications when new Project Manager positions are posted. Runs automatically every 30 minutes via GitHub Actions.

## ✨ Features

- ✅ Automatically scrapes company career websites for PM positions
- ✅ Tracks multiple job title variations (Project Manager, Programme Manager, TPM, etc.)
- ✅ Sends instant Telegram notifications for new job postings
- ✅ Prevents duplicate notifications
- ✅ Runs every 30 minutes via GitHub Actions (free tier compatible)
- ✅ Persistent job tracking with JSON database
- ✅ Configurable search keywords and scraping settings
- ✅ Error handling with retry logic and exponential backoff
- ✅ Manual workflow triggering for testing
- ✅ Comprehensive logging with timestamps

## 🚀 Quick Setup

### 1. Fork/Clone this Repository

Fork this repository to your GitHub account or clone it locally.

### 2. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts to create your bot:
   - Choose a name for your bot (e.g., "My Job Tracker")
   - Choose a username (must end with 'bot', e.g., "myjobtracker_bot")
4. **Save the bot token** - you'll need it later (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3. Get Your Telegram Chat ID

**Method 1: Using the GetIDs Bot (Easiest)**
1. Search for **@getidsbot** in Telegram
2. Start a chat and it will display your chat ID
3. Save your chat ID (it's a number like `123456789`)

**Method 2: Using the API**
1. Send a message to your bot (the one you created with BotFather)
2. Visit this URL in your browser (replace `YOUR_BOT_TOKEN` with your actual token):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":` in the response - that's your chat ID

### 4. Add GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1:**
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from BotFather (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

   **Secret 2:**
   - Name: `TELEGRAM_CHAT_ID`
   - Value: Your chat ID (e.g., `123456789`)

### 5. Add Companies to Track

Edit the `companies.xlsx` file to add or modify companies:

1. Open `companies.xlsx` in Excel or Google Sheets
2. Add rows with:
   - **Company Name**: Name of the company
   - **Career Website URL**: Direct link to their careers/jobs page
   - **Notes**: Optional notes about the company

Example:
| Company Name | Career Website URL | Notes |
|--------------|-------------------|-------|
| Microsoft | https://careers.microsoft.com/professionals/us/en/search-results | Tech giant |
| Amazon | https://www.amazon.jobs/en/search | E-commerce leader |

### 6. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. The bot will now run automatically every 30 minutes

## ⚙️ Configuration

### Customize Search Keywords

Edit `config.yaml` to customize job search terms:

```yaml
search_keywords:
  - "Project Manager"
  - "Programme Manager"
  - "Program Manager"
  - "PM"
  - "Technical Project Manager"
  - "TPM"
  - "Senior Project Manager"
  - "Junior Project Manager"
  - "Agile Project Manager"  # Add your own!
```

### Adjust Scraping Settings

Modify timeout, retry attempts, and delays:

```yaml
scraping:
  timeout: 10  # Seconds to wait for response
  retry_attempts: 3  # Number of retries
  retry_delay: 2  # Initial delay between retries
  request_delay: 2  # Delay between different websites
```

### Notification Preferences

Control notification behavior:

```yaml
notifications:
  enabled: true  # Set to false to disable notifications
  send_summary: true  # Send summary after each run
  max_jobs_per_notification: 10  # Max jobs per run
```

## 🔍 How It Works

1. **Scheduled Run**: GitHub Actions triggers the bot every 30 minutes
2. **Read Companies**: Bot reads company URLs from `companies.xlsx`
3. **Scrape Websites**: Each career page is scraped for job listings
4. **Keyword Matching**: Job titles are checked against search keywords
5. **Detect New Jobs**: Current jobs are compared with `jobs_database.json`
6. **Send Notifications**: New jobs trigger instant Telegram alerts
7. **Update Database**: Database is updated and committed back to the repository

## 🧪 Manual Testing

Test the bot without waiting for the scheduled run:

1. Go to **Actions** tab in your repository
2. Click **Job Scraper Bot** workflow
3. Click **Run workflow** → **Run workflow**
4. Check the workflow logs to see results
5. You should receive a Telegram notification if new jobs are found

## 📁 Project Structure

```
job-tracker/
├── .github/
│   └── workflows/
│       └── scrape_jobs.yml      # GitHub Actions workflow
├── src/
│   ├── scraper.py               # Main scraping logic
│   ├── notifier.py              # Telegram notifications
│   └── utils.py                 # Helper functions
├── companies.xlsx               # List of companies to track
├── config.yaml                  # Configuration settings
├── jobs_database.json           # Job tracking database (auto-generated)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🐛 Troubleshooting

### Not Receiving Notifications?

1. **Check Secrets**: Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly in GitHub Settings → Secrets
2. **Test Your Bot**: Send a message to your bot in Telegram to make sure it's active
3. **Check Logs**: Go to Actions tab and view the workflow logs for errors
4. **Verify Chat ID**: Make sure you're using the correct chat ID (should be just numbers)

### Bot Not Running?

1. **Check Actions Tab**: Make sure GitHub Actions are enabled in your repository
2. **Check Workflow File**: Ensure `.github/workflows/scrape_jobs.yml` exists and is correct
3. **Repository Settings**: Go to Settings → Actions → General and ensure workflows are allowed

### Scraping Errors?

1. **Check URLs**: Verify company career page URLs are correct and accessible
2. **Timeout Issues**: Increase timeout in `config.yaml` if websites are slow
3. **Rate Limiting**: Some websites may block automated requests - this is expected
4. **View Logs**: Check the Actions logs to see specific error messages

### No New Jobs Found?

1. **Check Keywords**: Make sure your search keywords in `config.yaml` match actual job titles
2. **Website Structure**: Some career pages may not be compatible with the scraper
3. **First Run**: On first run, all jobs are "new" - check if database was created
4. **Manual Test**: Try running manually to see immediate results

## 🔒 Security Best Practices

- ✅ **Never commit secrets** - Always use GitHub Secrets for sensitive data
- ✅ **Use environment variables** - Credentials are loaded from environment, not code
- ✅ **Secure bot token** - Treat your bot token like a password
- ✅ **Review permissions** - Limit workflow permissions if you're not committing back to repo
- ✅ **Monitor logs** - Regularly check GitHub Actions logs for suspicious activity

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add support for more job sites
- Improve scraping algorithms
- Enhance notification formatting
- Fix bugs or add features

## 💡 Tips & Best Practices

- **Start Small**: Begin with 2-3 companies and test before adding more
- **Check Regularly**: Monitor the Actions tab to ensure the bot runs successfully
- **Customize Keywords**: Add industry-specific terms relevant to your job search
- **Respect Websites**: The bot includes delays between requests - don't remove them
- **Keep Updated**: Pull latest changes from the repository periodically

## 📧 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review the GitHub Actions logs for error messages
3. Open an issue in this repository with details about the problem

---

**Happy Job Hunting! 🎯**

Made with ❤️ for job seekers everywhere
