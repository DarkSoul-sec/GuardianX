from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    API_PREFIX: str

    # Authentication mode for this deployment.
    #   local: first-run administrator setup, no public signup, no email
    #          verification gate, SMTP is not a startup requirement.
    #   cloud: public signup with email verification (multi-user/GuardianX Cloud).
    AUTH_MODE: str = "local"

    # Public base URL used to build email verification / password-reset links.
    # This MUST point at your deployed frontend origin (no trailing slash).
    PUBLIC_APP_URL: str = "http://localhost:5173"

    DEBUG: bool

    HOST: str
    PORT: int

    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: SecretStr

    SECRET_KEY: SecretStr
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Email delivery. SMTP is optional: when EMAIL_SMTP_HOST is empty the
    # mailer falls back to logging the message body, which is handy for local
    # development and automated tests. In production (DEBUG=false) SMTP is
    # required and the app fails fast at startup if it is missing.
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: SecretStr | None = None
    EMAIL_FROM: str = "GuardianX <noreply@localhost>"
    # STARTTLS (port 587) or implicit SSL (port 465). Pick one — enabling both
    # is a configuration error.
    EMAIL_USE_TLS: bool = True
    EMAIL_USE_SSL: bool = False
    EMAIL_SMTP_TIMEOUT_SECONDS: int = 15

    # Lifespan of one-time auth tokens (email verification, password reset).
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30

    # Comma-separated list of allowed browser origins.
    # Examples: "http://localhost:5173" or
    # "http://localhost:5173,https://app.example.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Scan execution concurrency.
    SCAN_MAX_WORKERS: int = 3

    # LOCAL DEVELOPMENT ONLY: permit scanning private, loopback, link-local
    # and reserved addresses. Keep this disabled (the default) in any public
    # deployment — it disables SSRF / internal-scan protection.
    ALLOW_PRIVATE_NETWORK_SCANS: bool = False

    # Seconds between scheduler polls for due scheduled scans.
    SCHEDULE_TICK_SECONDS: int = 60

    # Simple in-memory rate limiting for the API.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 240

    # Structured logging.
    # LOG_FORMAT: "json" for machine-readable single-line JSON, "text" otherwise.
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # AI Copilot provider configuration.
    # Leave AI_PROVIDER empty to auto-select: openai, gemini, then rules.
    AI_PROVIDER: str | None = None
    AI_TIMEOUT_SECONDS: int = 60

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    GEMINI_API_KEY: str | None = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    # VirusTotal Intelligence integration (Bring Your Own API Key).
    # Keys are supplied per user through Settings > Integrations and stored
    # encrypted; there is intentionally no shared platform key.
    VIRUSTOTAL_API_URL: str = "https://www.virustotal.com/api/v3"
    VIRUSTOTAL_TIMEOUT_SECONDS: int = 15
    VIRUSTOTAL_MAX_RETRIES: int = 3
    # Client-side throttling: burst requests per minute sent to the VT API
    # per user key.
    VIRUSTOTAL_RATE_LIMIT_PER_MINUTE: int = 60
    # In-process response cache: how long / how many entries to keep.
    VIRUSTOTAL_CACHE_TTL_SECONDS: int = 900
    VIRUSTOTAL_CACHE_MAX_ENTRIES: int = 512

    # Threat Intelligence platform response cache. Cached VirusTotal reports
    # are served for 24 hours to stay within BYOAPI quotas.
    INTELLIGENCE_CACHE_TTL_SECONDS: int = 86400
    INTELLIGENCE_CACHE_MAX_ENTRIES: int = 2048

    # Phishing detection module.
    # Detection lists and scoring weights are configurable. Empty list values
    # fall back to the defaults defined in app.detection.phishing.config.
    PHISHING_SUSPICIOUS_KEYWORDS: list[str] = []
    PHISHING_TRUSTED_DOMAINS: list[str] = []
    PHISHING_BLACKLIST_SERVERS: list[str] = []
    PHISHING_RISKY_TLDS: list[str] = []
    # Comma-separated "check:weight" scoring overrides, e.g. "virustotal:30,blacklist:10".
    PHISHING_SCORE_WEIGHTS: str = ""
    # Comma-separated risk thresholds medium,high,critical, e.g. "25,50,75".
    PHISHING_RISK_THRESHOLDS: str = ""
    PHISHING_NEW_DOMAIN_DAYS: int = 90
    PHISHING_SUSPICIOUS_DOMAIN_DAYS: int = 365
    PHISHING_CERTIFICATE_RENEW_DAYS: int = 30
    PHISHING_NETWORK_TIMEOUT_SECONDS: int = 10
    PHISHING_AI_SUMMARY_ENABLED: bool = True

    # Threat Intelligence Center.
    # Sources default to the public NVD / CISA / FIRST endpoints; override
    # to point at proxies or self-hosted mirrors.
    THREAT_INTEL_NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    THREAT_INTEL_KEV_API_URL: str = (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
    )
    THREAT_INTEL_EPSS_API_URL: str = "https://api.first.org/data/v1/epss"
    THREAT_INTEL_TIMEOUT_SECONDS: int = 15
    THREAT_INTEL_CACHE_TTL_SECONDS: int = 1800
    # Upper bound for a single NVD results page.
    THREAT_INTEL_MAX_RESULTS: int = 200

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.DATABASE_USER}:"
            f"{self.DATABASE_PASSWORD.get_secret_value()}@"
            f"{self.DATABASE_HOST}:"
            f"{self.DATABASE_PORT}/"
            f"{self.DATABASE_NAME}"
        )

    @property
    def CORS_ORIGIN_LIST(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def _validate_email_config(self) -> "Settings":
        if self.EMAIL_USE_TLS and self.EMAIL_USE_SSL:
            raise ValueError(
                "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled. "
                "Pick STARTTLS on port 587 (EMAIL_USE_TLS=true) or implicit "
                "SSL on port 465 (EMAIL_USE_SSL=true)."
            )

        if self.AUTH_MODE not in {"local", "cloud"}:
            raise ValueError(
                f"Invalid AUTH_MODE={self.AUTH_MODE!r}. Use 'local' or 'cloud'."
            )

        if (
            self.AUTH_MODE == "cloud"
            and not self.DEBUG
            and not self.EMAIL_SMTP_HOST
        ):
            raise ValueError(
                "Refusing to run GuardianX in cloud mode (DEBUG=false) without "
                "SMTP: emails would never be delivered. Set EMAIL_SMTP_HOST "
                "(and EMAIL_SMTP_USER/EMAIL_SMTP_PASSWORD as required by your "
                "provider) or run with DEBUG=true for development log-only "
                "delivery. Local mode (AUTH_MODE=local) does not require SMTP."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
