from oak_runner.auth.credentials.fetch import EnvironmentVariableFetchStrategy
from oak_runner.auth.models import (
    SecurityOption,
    SecurityRequirement,
    EnvVarKeys,
    AuthType,
)


def test_environment_variable_fetch_strategy_api_key(monkeypatch):
    """Ensure that an API key can be loaded from the environment using the strategy."""

    # ---------------------------------------------------------------------
    # Test setup
    # ---------------------------------------------------------------------
    env_var_name = "MY_API_KEY_ENV"
    env_var_value = "test-api-key-123"

    # Set the environment variable and guarantee cleanup afterwards
    monkeypatch.setenv(env_var_name, env_var_value)

    # Mapping tells the strategy which env var to use for the scheme & key
    env_mapping = {
        "myApiKey": {
            EnvVarKeys.API_KEY: env_var_name,
        }
    }

    # Minimal AuthRequirement dict expected by `populate`
    auth_requirement = {
        "type": AuthType.API_KEY,
        "security_scheme_name": "myApiKey",
        "name": "X-API-KEY",
        "location": "header",
    }

    # SecurityOption used when performing the actual fetch
    security_option = SecurityOption(
        requirements=[SecurityRequirement(scheme_name="myApiKey", scopes=[])]
    )

    # ---------------------------------------------------------------------
    # Exercise
    # ---------------------------------------------------------------------
    strategy = EnvironmentVariableFetchStrategy(
        env_mapping=env_mapping,
        auth_requirements=[auth_requirement]
    )
    credentials = strategy.fetch([security_option])

    # ---------------------------------------------------------------------
    # Verify
    # ---------------------------------------------------------------------
    assert len(credentials) == 1

    credential = credentials[0]
    assert credential.auth_value is not None, "Auth value should be resolved from env"
    assert credential.auth_value.api_key == env_var_value
    assert credential.security_scheme is not None
    assert credential.security_scheme.name == "X-API-KEY"


def test_environment_variable_missing_key():
    """If the required environment variable is missing, auth_value should be None."""

    env_mapping = {
        "myApiKey": {
            EnvVarKeys.API_KEY: "MISSING_ENV_VAR",
        }
    }

    auth_requirement = {
        "type": AuthType.API_KEY,
        "security_scheme_name": "myApiKey",
        "name": "X-API-KEY",
        "location": "header",
    }

    security_option = SecurityOption(
        requirements=[SecurityRequirement(scheme_name="myApiKey", scopes=[])]
    )

    strategy = EnvironmentVariableFetchStrategy(
        env_mapping=env_mapping,
        auth_requirements=[auth_requirement]
    )
    credentials = strategy.fetch([security_option])

    assert len(credentials) == 1
    assert credentials[0].auth_value is None, "Auth value should be None when env var is absent"  