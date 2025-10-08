"""
Environment Configuration Validator
Validates all required environment variables and provides helpful error messages
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EnvVarType(Enum):
    """Types of environment variables"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    SECRET = "secret"


class EnvVarRequirement(Enum):
    """Requirement levels for environment variables"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    RECOMMENDED = "recommended"


@dataclass
class EnvVarConfig:
    """Configuration for an environment variable"""
    name: str
    description: str
    type: EnvVarType
    requirement: EnvVarRequirement
    default: Optional[str] = None
    example: Optional[str] = None
    validation_pattern: Optional[str] = None


class EnvironmentValidator:
    """Validates environment configuration"""

    # Core Application Configuration
    CORE_VARS = [
        EnvVarConfig(
            name="FLASK_ENV",
            description="Flask environment (development, production, staging)",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="development"
        ),
        EnvVarConfig(
            name="SECRET_KEY",
            description="Flask secret key for session management",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
        ),
        EnvVarConfig(
            name="DEBUG",
            description="Enable debug mode (True/False)",
            type=EnvVarType.BOOLEAN,
            requirement=EnvVarRequirement.REQUIRED,
            default="False"
        ),
    ]

    # Database Configuration
    DATABASE_VARS = [
        EnvVarConfig(
            name="SUPABASE_URL",
            description="Supabase project URL",
            type=EnvVarType.URL,
            requirement=EnvVarRequirement.REQUIRED,
            example="https://your-project.supabase.co"
        ),
        EnvVarConfig(
            name="SUPABASE_KEY",
            description="Supabase anon/public key",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        ),
        EnvVarConfig(
            name="SUPABASE_SERVICE_KEY",
            description="Supabase service role key (for admin operations)",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        ),
        EnvVarConfig(
            name="DATABASE_URL",
            description="PostgreSQL connection string",
            type=EnvVarType.URL,
            requirement=EnvVarRequirement.OPTIONAL,
            example="postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres"
        ),
    ]

    # JWT Configuration
    JWT_VARS = [
        EnvVarConfig(
            name="JWT_SECRET_KEY",
            description="JWT secret key for token signing",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
        ),
        EnvVarConfig(
            name="JWT_ACCESS_TOKEN_EXPIRES",
            description="JWT access token expiration in seconds",
            type=EnvVarType.INTEGER,
            requirement=EnvVarRequirement.REQUIRED,
            default="3600"
        ),
    ]

    # External Service Configuration
    EXTERNAL_SERVICES = [
        # Pusher (Real-time)
        EnvVarConfig(
            name="PUSHER_APP_ID",
            description="Pusher application ID",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="your-pusher-app-id"
        ),
        EnvVarConfig(
            name="PUSHER_KEY",
            description="Pusher public key",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="your-pusher-key"
        ),
        EnvVarConfig(
            name="PUSHER_SECRET",
            description="Pusher secret key",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="your-pusher-secret"
        ),
        EnvVarConfig(
            name="PUSHER_CLUSTER",
            description="Pusher cluster region",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            default="us2"
        ),

        # SendGrid (Email)
        EnvVarConfig(
            name="SENDGRID_API_KEY",
            description="SendGrid API key for email",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="SG.xxxxxxxxxxxxxxxxxxxxx"
        ),
        EnvVarConfig(
            name="FROM_EMAIL",
            description="Default sender email address",
            type=EnvVarType.EMAIL,
            requirement=EnvVarRequirement.REQUIRED,
            example="noreply@iswitchroofs.com"
        ),

        # Twilio (SMS)
        EnvVarConfig(
            name="TWILIO_ACCOUNT_SID",
            description="Twilio account SID",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        ),
        EnvVarConfig(
            name="TWILIO_AUTH_TOKEN",
            description="Twilio authentication token",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="your-twilio-auth-token"
        ),
        EnvVarConfig(
            name="TWILIO_PHONE_NUMBER",
            description="Twilio phone number",
            type=EnvVarType.PHONE,
            requirement=EnvVarRequirement.REQUIRED,
            example="+1234567890"
        ),

        # CallRail (Call Tracking)
        EnvVarConfig(
            name="CALLRAIL_API_KEY",
            description="CallRail API key",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.REQUIRED,
            example="your-callrail-api-key"
        ),
        EnvVarConfig(
            name="CALLRAIL_ACCOUNT_ID",
            description="CallRail account ID",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="ACCxxxxxxxxxxxxxxxxxxxxxxxxx"
        ),
        EnvVarConfig(
            name="CALLRAIL_COMPANY_ID",
            description="CallRail company ID",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.REQUIRED,
            example="COMxxxxxxxxxxxxxxxxxxxxxxxxx"
        ),

        # Sentry (Error Tracking)
        EnvVarConfig(
            name="SENTRY_DSN",
            description="Sentry DSN for error tracking",
            type=EnvVarType.URL,
            requirement=EnvVarRequirement.RECOMMENDED,
            example="https://xxxxx@sentry.io/xxxxx"
        ),
        EnvVarConfig(
            name="SENTRY_ENVIRONMENT",
            description="Sentry environment name",
            type=EnvVarType.STRING,
            requirement=EnvVarRequirement.RECOMMENDED,
            default="development"
        ),
    ]

    # Optional Services
    OPTIONAL_SERVICES = [
        EnvVarConfig(
            name="REDIS_URL",
            description="Redis connection URL for caching",
            type=EnvVarType.URL,
            requirement=EnvVarRequirement.OPTIONAL,
            default="redis://localhost:6379/0"
        ),
        EnvVarConfig(
            name="CLOUDFLARE_API_TOKEN",
            description="Cloudflare API token",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.OPTIONAL,
            example="your-cloudflare-token"
        ),
        EnvVarConfig(
            name="GOOGLE_LSA_API_KEY",
            description="Google Local Services Ads API key",
            type=EnvVarType.SECRET,
            requirement=EnvVarRequirement.OPTIONAL,
            example="your-google-lsa-key"
        ),
    ]

    @classmethod
    def get_all_vars(cls) -> List[EnvVarConfig]:
        """Get all environment variable configurations"""
        return (
            cls.CORE_VARS +
            cls.DATABASE_VARS +
            cls.JWT_VARS +
            cls.EXTERNAL_SERVICES +
            cls.OPTIONAL_SERVICES
        )

    @classmethod
    def validate_environment(cls, environment: str = "development") -> Tuple[bool, List[str], List[str]]:
        """
        Validate environment variables

        Args:
            environment: Environment name (development, staging, production)

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        all_vars = cls.get_all_vars()

        for var_config in all_vars:
            value = os.getenv(var_config.name)

            # Check required variables
            if var_config.requirement == EnvVarRequirement.REQUIRED:
                if not value:
                    errors.append(
                        f"❌ REQUIRED: {var_config.name} is not set\n"
                        f"   Description: {var_config.description}\n"
                        f"   Example: {var_config.example or 'N/A'}"
                    )
                elif value.startswith("your-") or value == "your-secret-key-here":
                    errors.append(
                        f"❌ INVALID: {var_config.name} contains placeholder value\n"
                        f"   Please set a real value"
                    )

            # Check recommended variables
            elif var_config.requirement == EnvVarRequirement.RECOMMENDED:
                if not value:
                    warnings.append(
                        f"⚠️  RECOMMENDED: {var_config.name} is not set\n"
                        f"   Description: {var_config.description}\n"
                        f"   Example: {var_config.example or 'N/A'}"
                    )

            # Validate specific types
            if value:
                if var_config.type == EnvVarType.URL and not value.startswith(("http://", "https://", "redis://", "postgresql://", "mysql://")):
                    errors.append(f"❌ INVALID: {var_config.name} must be a valid URL")

                elif var_config.type == EnvVarType.EMAIL and "@" not in value:
                    errors.append(f"❌ INVALID: {var_config.name} must be a valid email")

                elif var_config.type == EnvVarType.BOOLEAN and value.lower() not in ("true", "false", "1", "0"):
                    errors.append(f"❌ INVALID: {var_config.name} must be True or False")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @classmethod
    def print_validation_report(cls, environment: str = "development"):
        """Print environment validation report"""
        print("=" * 80)
        print(f"Environment Configuration Validation - {environment.upper()}")
        print("=" * 80)
        print()

        is_valid, errors, warnings = cls.validate_environment(environment)

        if errors:
            print("🚨 ERRORS (Must be fixed):")
            print("-" * 80)
            for error in errors:
                print(error)
                print()

        if warnings:
            print("⚠️  WARNINGS (Recommended to fix):")
            print("-" * 80)
            for warning in warnings:
                print(warning)
                print()

        if is_valid:
            print("✅ All required environment variables are configured!")
            if warnings:
                print(f"   ({len(warnings)} optional/recommended variables missing)")
        else:
            print(f"❌ Environment validation failed with {len(errors)} error(s)")

        print()
        print("=" * 80)

        return is_valid

    @classmethod
    def generate_env_template(cls, output_file: str = ".env.template"):
        """Generate .env template file with all variables"""
        with open(output_file, "w") as f:
            f.write("# iSwitch Roofs CRM - Environment Configuration Template\n")
            f.write("# Copy this file to .env and fill in your values\n")
            f.write(f"# Generated: {os.popen('date').read().strip()}\n")
            f.write("\n")

            sections = [
                ("Core Application", cls.CORE_VARS),
                ("Database Configuration", cls.DATABASE_VARS),
                ("JWT Configuration", cls.JWT_VARS),
                ("External Services", cls.EXTERNAL_SERVICES),
                ("Optional Services", cls.OPTIONAL_SERVICES),
            ]

            for section_name, vars_list in sections:
                f.write(f"# {section_name}\n")
                f.write("# " + "=" * 78 + "\n")

                for var in vars_list:
                    f.write(f"\n# {var.description}\n")
                    f.write(f"# Type: {var.type.value} | Requirement: {var.requirement.value}\n")
                    if var.example:
                        f.write(f"# Example: {var.example}\n")

                    value = var.default or ""
                    if var.requirement == EnvVarRequirement.REQUIRED and not var.default:
                        value = "REQUIRED"

                    f.write(f"{var.name}={value}\n")

                f.write("\n")

        print(f"✅ Generated environment template: {output_file}")


def main():
    """Main validation function"""
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get environment
    environment = os.getenv("FLASK_ENV", "development")

    # Validate and print report
    is_valid = EnvironmentValidator.print_validation_report(environment)

    # Generate template if requested
    if "--generate-template" in sys.argv:
        EnvironmentValidator.generate_env_template()

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
