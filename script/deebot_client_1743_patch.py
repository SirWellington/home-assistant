"""Port DeebotUniverse/client.py PR #1743 into the installed deebot-client.

deebot-client 18.6.0 (the last release) does not yet contain PR #1743, which
adds token-based credential renewal (AccountCredentials + login_with_account).
The ecovacs integration in this fork depends on it to avoid Ecovacs' password
login endpoint, which rejects affected accounts with code 1013 ("device
verification required") on every call.

Run after deebot-client is installed: python3 scripts/deebot_client_1743_patch.py
Fails without writing anything if any expected string is not found exactly once.
"""

import shutil
from pathlib import Path

import deebot_client

SITE = Path(deebot_client.__file__).parent
BACKUP = Path("/tmp/deebot-backup")

CHANGES: dict[str, list[tuple[str, str]]] = {
    "models.py": [
        (
            "@dataclass(frozen=True)\n"
            "class Credentials:\n"
            '    """Credentials representation."""\n'
            "\n"
            "    token: str\n"
            "    user_id: str\n"
            "    expires_at: int = 0",
            "@dataclass(frozen=True)\n"
            "class Credentials:\n"
            '    """Credentials representation."""\n'
            "\n"
            "    token: str\n"
            "    user_id: str\n"
            "    expires_at: int = 0\n"
            "\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class AccountCredentials:\n"
            '    """Account credentials as returned by the login or device verification api.\n'
            "\n"
            "    The access token can mint new portal credentials without the password.\n"
            '    """\n'
            "\n"
            "    access_token: str\n"
            "    user_id: str",
        ),
    ],
    "authentication.py": [
        (
            "from .models import Credentials",
            "from .models import AccountCredentials, Credentials",
        ),
        (
            "    def __init__(\n"
            "        self,\n"
            "        config: RestConfiguration,\n"
            "        account_id: str,\n"
            "        password_hash: str,\n"
            "    ) -> None:\n"
            "        self._config = config\n"
            "        self._account_id = account_id\n"
            "        self._password_hash = password_hash",
            "    def __init__(\n"
            "        self,\n"
            "        config: RestConfiguration,\n"
            "        account_id: str,\n"
            "        password_hash: str,\n"
            "        *,\n"
            "        on_account_credentials: Callable[[AccountCredentials], None] | None = None,\n"
            "    ) -> None:\n"
            "        self._config = config\n"
            "        self._account_id = account_id\n"
            "        self._password_hash = password_hash\n"
            "        self._on_account_credentials = on_account_credentials",
        ),
        (
            "        try:\n"
            '            user_id = str(data["uid"])\n'
            '            access_token = str(data["accessToken"])\n'
            "        except KeyError as ex:\n"
            "            raise AuthenticationError(error) from ex\n"
            "\n"
            "        auth_code = await self.__call_auth_api(access_token, user_id)\n"
            "\n"
            "        login_token_resp = await self.__call_login_by_it_token(user_id, auth_code)",
            "        try:\n"
            '            user_id = str(data["uid"])\n'
            '            access_token = str(data["accessToken"])\n'
            "            account = AccountCredentials(\n"
            '                access_token=str(data["accessToken"]), user_id=str(data["uid"])\n'
            "            )\n"
            "        except KeyError as ex:\n"
            "            raise AuthenticationError(error) from ex\n"
            "\n"
            "        if self._on_account_credentials is not None:\n"
            "            self._on_account_credentials(account)\n"
            "        return await self.login_with_account(account)\n"
            "\n"
            "    async def login_with_account(self, account: AccountCredentials) -> Credentials:\n"
            '        """Mint portal credentials from account credentials, without the password."""\n'
            "        user_id = account.user_id\n"
            "        auth_code = await self.__call_auth_api(account.access_token, user_id)\n"
            "\n"
            "        login_token_resp = await self.__call_login_by_it_token(user_id, auth_code)",
        ),
        (
            "    def __init__(\n"
            "        self,\n"
            "        config: RestConfiguration,\n"
            "        account_id: str,\n"
            "        password_hash: str,\n"
            "    ) -> None:\n"
            "        self._auth_client = _AuthClient(\n"
            "            config,\n"
            "            account_id,\n"
            "            password_hash,\n"
            "        )\n"
            "\n"
            "        self._lock = asyncio.Lock()\n"
            "        self._on_credentials_changed: set[\n"
            "            Callable[[Credentials], Coroutine[Any, Any, None]]\n"
            "        ] = set()\n"
            "        self._credentials: Credentials | None = None",
            "    def __init__(\n"
            "        self,\n"
            "        config: RestConfiguration,\n"
            "        account_id: str,\n"
            "        password_hash: str,\n"
            "        *,\n"
            "        account_credentials: AccountCredentials | None = None,\n"
            "    ) -> None:\n"
            "        self._auth_client = _AuthClient(\n"
            "            config,\n"
            "            account_id,\n"
            "            password_hash,\n"
            "            on_account_credentials=self._set_account_credentials,\n"
            "        )\n"
            "\n"
            "        self._lock = asyncio.Lock()\n"
            "        self._on_credentials_changed: set[\n"
            "            Callable[[Credentials], Coroutine[Any, Any, None]]\n"
            "        ] = set()\n"
            "        self._on_account_credentials_changed: set[\n"
            "            Callable[[AccountCredentials], Coroutine[Any, Any, None]]\n"
            "        ] = set()\n"
            "        self._credentials: Credentials | None = None\n"
            "        self._account_credentials = account_credentials",
        ),
        (
            "    async def authenticate(self, *, force: bool = False) -> Credentials:\n"
            '        """Authenticate on ecovacs servers."""\n'
            "        async with self._lock:\n"
            "            credentials = self._credentials\n"
            "            if credentials is None or force or credentials.expires_at < time.time():\n"
            '                _LOGGER.debug("Performing login")\n'
            "                credentials = await self._auth_client.login()\n"
            "                self._set_credentials(credentials)\n"
            "\n"
            "            return credentials",
            "    @property\n"
            "    def account_credentials(self) -> AccountCredentials | None:\n"
            '        """Return the account credentials, if some are known."""\n'
            "        return self._account_credentials\n"
            "\n"
            "    async def authenticate(self, *, force: bool = False) -> Credentials:\n"
            '        """Authenticate on ecovacs servers."""\n'
            "        async with self._lock:\n"
            "            credentials = self._credentials\n"
            "            if credentials is None or force or credentials.expires_at < time.time():\n"
            "                credentials = await self._login()\n"
            "                self._set_credentials(credentials)\n"
            "\n"
            "            return credentials\n"
            "\n"
            "    async def _login(self) -> Credentials:\n"
            '        """Login, preferring the password-free token based renewal.\n'
            "\n"
            "        The password login endpoint rejects some accounts with code 1013\n"
            '        ("Please update to the latest version to continue"), while portal\n'
            "        credentials can still be minted from the stored account credentials.\n"
            '        """\n'
            "        if (account := self._account_credentials) is not None:\n"
            '            _LOGGER.debug("Performing token based login")\n'
            "            try:\n"
            "                return await self._auth_client.login_with_account(account)\n"
            "            except AuthenticationError:\n"
            "                _LOGGER.debug(\n"
            '                    "Token based login failed, falling back to password login",\n'
            "                    exc_info=True,\n"
            "                )\n"
            '        _LOGGER.debug("Performing login")\n'
            "        return await self._auth_client.login()",
        ),
        (
            "    def subscribe(\n"
            "        self, callback: Callable[[Credentials], Coroutine[Any, Any, None]]\n"
            "    ) -> Callable[[], None]:\n"
            '        """Add callback on new credentials and return subscribe callback."""',
            "    def _set_account_credentials(self, account: AccountCredentials) -> None:\n"
            '        """Store account credentials received during a login."""\n'
            "        if account == self._account_credentials:\n"
            "            return\n"
            "        self._account_credentials = account\n"
            "\n"
            "        for on_account_changed in self._on_account_credentials_changed:\n"
            "            create_task(self._tasks, on_account_changed(account))\n"
            "\n"
            "    def subscribe(\n"
            "        self, callback: Callable[[Credentials], Coroutine[Any, Any, None]]\n"
            "    ) -> Callable[[], None]:\n"
            '        """Add callback on new credentials and return subscribe callback."""',
        ),
        (
            "        def unsubscribe() -> None:\n"
            "            self._on_credentials_changed.remove(callback)\n"
            "\n"
            "        self._on_credentials_changed.add(callback)\n"
            "        return unsubscribe\n"
            "\n"
            "    async def post_authenticated(",
            "        def unsubscribe() -> None:\n"
            "            self._on_credentials_changed.remove(callback)\n"
            "\n"
            "        self._on_credentials_changed.add(callback)\n"
            "        return unsubscribe\n"
            "\n"
            "    def subscribe_account_credentials(\n"
            "        self, callback: Callable[[AccountCredentials], Coroutine[Any, Any, None]]\n"
            "    ) -> Callable[[], None]:\n"
            '        """Add callback on new account credentials and return unsubscribe function."""\n'
            "\n"
            "        def unsubscribe() -> None:\n"
            "            self._on_account_credentials_changed.remove(callback)\n"
            "\n"
            "        self._on_account_credentials_changed.add(callback)\n"
            "        return unsubscribe\n"
            "\n"
            "    async def post_authenticated(",
        ),
    ],
}


def main() -> None:
    contents: dict[str, str] = {}
    problems: list[str] = []

    for name, replacements in CHANGES.items():
        path = SITE / name
        text = path.read_text(encoding="utf-8")
        contents[name] = text
        for i, (old, _new) in enumerate(replacements):
            count = text.count(old)
            if count != 1:
                problems.append(f"{name} replacement {i}: found {count} occurrence(s)")

    if problems:
        print("ABORTED - no files written:")
        for p in problems:
            print("  " + p)
        raise SystemExit(1)

    BACKUP.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        shutil.copy2(SITE / name, BACKUP / name)
        new_text = text
        for old, new in CHANGES[name]:
            new_text = new_text.replace(old, new, 1)
        (SITE / name).write_text(new_text, encoding="utf-8")
        print(f"patched {name} (backup at {BACKUP / name})")

    print("done")


if __name__ == "__main__":
    main()
