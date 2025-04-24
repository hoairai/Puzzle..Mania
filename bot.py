from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from datetime import datetime
import asyncio, json, os, pytz, re
from colorama import init, Fore, Style

# Khởi tạo colorama
init()

wib = pytz.timezone('Asia/Jakarta')

class PuzzleMania:
    def __init__(self) -> None:
        self.BASE_API = "https://auth.privy.io/api/v1/siwe"
        self.URL = "https://api.deform.cc/"
        self.PRIVY_APP_ID = "clphlvsh3034xjw0fvs59mrdc"
        self.PRIVY_CA_ID = "3b241d45-f5a5-4174-89b1-cd4ac2197e4f"
        self.PRIVY_CLIENT = "react-auth:2.4.1"
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://puzzlemania.0g.ai",
            "Referer": "https://puzzlemania.0g.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}0G Puzzle Mania - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def validate_private_key(self, key: str) -> bool:
        """Kiểm tra khóa riêng Ethereum hợp lệ (64 ký tự hex)."""
        return bool(re.match(r'^[0-9a-fA-F]{64}$', key.strip()))

    def validate_proxy(self, proxy: str) -> bool:
     """Kiem tra định dạng proxy hợp lệ, bao gom proxy có xác thực."""
     proxy_pattern = r'^(https?|socks[45])://(([a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@)?[a-zA-Z0-9.-]+)(:\d+)?(/.*)?$'
     return bool(re.match(proxy_pattern, proxy.strip()))

    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [p for p in content.splitlines() if self.validate_proxy(p)]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [p for p in f.read().splitlines() if self.validate_proxy(p)]

            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Valid Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )

        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxy: str) -> str:
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxy.startswith(scheme) for scheme in schemes):
            return proxy
        return f"http://{proxy}"

    def get_next_proxy_for_account(self, account: str) -> str:
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account: str) -> str:
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def generate_address(self, account: str) -> str:
        try:
            if not self.validate_private_key(account):
                self.log(f"{Fore.RED + Style.BRIGHT}Invalid Private Key Format.{Style.RESET_ALL}")
                return None
            account = Account.from_key(account)
            return account.address
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Generate Address: {e}{Style.RESET_ALL}")
            return None

    def generate_payload(self, account: str, address: str, nonce: str) -> dict:
        try:
            issued_at = datetime.utcnow().isoformat() + 'Z'  # Thời gian động
            message = (
                f"puzzlemania.0g.ai wants you to sign in with your Ethereum account:\n"
                f"{address}\n\n"
                f"By signing, you are proving you own this wallet and logging in. "
                f"This does not initiate a transaction or cost any fees.\n\n"
                f"URI: https://puzzlemania.0g.ai\n"
                f"Version: 1\n"
                f"Chain ID: 56\n"
                f"Nonce: {nonce}\n"
                f"Issued At: {issued_at}\n"
                f"Resources:\n- https://privy.io"
            )
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = signed_message.signature.hex()
            payload = {
                "message": message,
                "signature": f"0x{signature}",
                "chainId": "eip155:56",
                "walletClientType": "metamask",
                "connectorType": "injected",
                "mode": "login-or-sign-up"
            }
            return payload
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Generate Payload: {e}{Style.RESET_ALL}")
            return None

    def mask_account(self, account: str) -> str:
        if not account or len(account) < 12:
            return "******"
        return account[:6] + '*' * 6 + account[-6:]

    def print_question(self) -> int:
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())
                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else
                        "Run With Private Proxy" if choose == 2 else
                        "Run Without Proxy"
                    )
                    self.log(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                self.log(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, or 3.{Style.RESET_ALL}")
            except ValueError:
                self.log(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, or 3).{Style.RESET_ALL}")

    async def user_init(self, address: str, proxy: str = None, retries: int = 5) -> str:
        url = f"{self.BASE_API}/init"
        data = json.dumps({"address": address})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Privy-App-Id": self.PRIVY_APP_ID,
            "Privy-Ca-Id": self.PRIVY_CA_ID,
            "Privy-Client": self.PRIVY_CLIENT
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("nonce")
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}User Init Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def user_authenticate(self, account: str, address: str, nonce: str, proxy: str = None, retries: int = 5) -> dict:
        url = f"{self.BASE_API}/authenticate"
        payload = self.generate_payload(account, address, nonce)
        if not payload:
            return None
        data = json.dumps(payload)
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Privy-App-Id": self.PRIVY_APP_ID,
            "Privy-Ca-Id": self.PRIVY_CA_ID,
            "Privy-Client": self.PRIVY_CLIENT
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}User Authenticate Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def user_login(self, auth_token: str, proxy: str = None, retries: int = 5) -> str:
        data = json.dumps({
            "operationName": "UserLogin",
            "variables": {"data": {"externalAuthToken": auth_token}},
            "query": "mutation UserLogin($data: UserLoginInput!) {\n  userLogin(data: $data)\n}"
        })
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "X-apollo-Operation-Name": "UserLogin"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=self.URL, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("data", {}).get("userLogin")
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}User Login Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def user_data(self, access_token: str, proxy: str = None, retries: int = 5) -> dict:
        data = json.dumps({
            "operationName": "UserMe",
            "variables": {"campaignId": "f7e24f14-b911-4f11-b903-edac89a095ec"},
            "query": (
                "fragment RecordFields on CampaignSpot {\n  records {\n    id\n    status\n    properties\n    points\n    "
                "instanceCount\n    createdAt\n    updatedAt\n    activityId\n    activity {\n      id\n      title\n      "
                "description\n      type\n      __typename\n    }\n    mission {\n      id\n      title\n      description\n      "
                "__typename\n    }\n    communityGoal {\n      id\n      title\n      description\n      threshold\n      __typename\n    }\n    "
                "rewardRecords {\n      id\n      status\n      appliedRewardType\n      appliedRewardQuantity\n      "
                "appliedRewardMetadata\n      error\n      rewardId\n      reward {\n        id\n        quantity\n        type\n        "
                "properties\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\n"
                "query UserMe($campaignId: String!) {\n  userMe {\n    id\n    campaignSpot(campaignId: $campaignId) {\n      id\n      "
                "points\n      referralCode\n      referralCodeEditsRemaining\n      ...RecordFields\n      __typename\n    }\n    "
                "__typename\n  }\n}"
            )
        })
        headers = {
            **self.headers,
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "X-apollo-Operation-Name": "UserMe"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=self.URL, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("data", {}).get("userMe", {})
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}User Data Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def task_lists(self, access_token: str, proxy: str = None, retries: int = 5) -> dict:
        data = json.dumps({
            "operationName": "Campaign",
            "variables": {"campaignId": "f7e24f14-b911-4f11-b903-edac89a095ec"},
            "query": (
                "fragment ActivityFields on CampaignActivity {\n  id\n  createdAt\n  updatedAt\n  startDateTimeAt\n  "
                "endDateTimeAt\n  title\n  description\n  coverAssetUrl\n  type\n  identityType\n  recurringPeriod {\n    "
                "count\n    type\n    __typename\n  }\n  recurringMaxCount\n  properties\n  records {\n    id\n    status\n    "
                "createdAt\n    activityId\n    properties\n    rewardRecords {\n      id\n      status\n      appliedRewardType\n      "
                "appliedRewardQuantity\n      appliedRewardMetadata\n      error\n      rewardId\n      reward {\n        id\n        "
                "quantity\n        type\n        properties\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  "
                "tags {\n    id\n    name\n    __typename\n  }\n  reward {\n    id\n    title\n    description\n    quantity\n    "
                "type\n    imageUrl\n    properties\n    __typename\n  }\n  targetReward {\n    id\n    activityId\n    missionId\n    "
                "__typename\n  }\n  nft {\n    id\n    tokenId\n    name\n    description\n    image\n    properties\n    mintPrice\n    "
                "platformFee\n    maxSupply\n    maxMintCountPerAddress\n    nftContract {\n      id\n      address\n      type\n      "
                "chainId\n      __typename\n    }\n    __typename\n  }\n  isHidden\n  __typename\n}\n\n"
                "fragment MissionFields on CampaignMission {\n  id\n  createdAt\n  updatedAt\n  startDateTimeAt\n  "
                "endDateTimeAt\n  title\n  description\n  coverPhotoUrl\n  recurringPeriod {\n    count\n    type\n    "
                "__typename\n  }\n  recurringMaxCount\n  properties\n  tags {\n    id\n    name\n    __typename\n  }\n  "
                "rewards {\n    id\n    title\n    description\n    quantity\n    type\n    imageUrl\n    properties\n    "
                "awardMechanism\n    __typename\n  }\n  records {\n    id\n    status\n    createdAt\n    missionId\n    "
                "rewardRecords {\n      id\n      status\n      appliedRewardType\n      appliedRewardQuantity\n      "
                "appliedRewardMetadata\n      error\n      rewardId\n      reward {\n        id\n        quantity\n        type\n        "
                "properties\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  activities {\n    id\n    "
                "__typename\n  }\n  isHidden\n  __typename\n}\n\n"
                "fragment CampaignCommunityGoalFields on CampaignCommunityGoal {\n  id\n  title\n  description\n  "
                "additionalDetails\n  imageUrl\n  threshold\n  status\n  startDateTimeAt\n  endDateTimeAt\n  createdAt\n  "
                "updatedAt\n  isThresholdHidden\n  isHidden\n  ctaButtonCopy\n  ctaButtonUrl\n  __typename\n}\n\n"
                "query Campaign($campaignId: String!) {\n  campaign(id: $campaignId) {\n    id\n    standaloneActivities {\n      "
                "id\n      isHidden\n      __typename\n    }\n    communityGoals {\n      ...CampaignCommunityGoalFields\n      "
                "campaign {\n        id\n        __typename\n      }\n      activity {\n        ...ActivityFields\n        "
                "__typename\n      }\n      __typename\n    }\n    activities {\n      ...ActivityFields\n      __typename\n    }\n    "
                "missions {\n      ...MissionFields\n      __typename\n    }\n    __typename\n  }\n}"
            )
        })
        headers = {
            **self.headers,
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "X-apollo-Operation-Name": "Campaign"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=self.URL, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result.get("data", {}).get("campaign", {})
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}Task Lists Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def complete_task(self, identity_token: str, access_token: str, task_id: str, proxy: str = None, retries: int = 5) -> dict:
        data = json.dumps({
            "operationName": "VerifyActivity",
            "variables": {"data": {"activityId": task_id}},
            "query": (
                "mutation VerifyActivity($data: VerifyActivityInput!) {\n  verifyActivity(data: $data) {\n    record {\n      id\n      "
                "activityId\n      status\n      properties\n      createdAt\n      rewardRecords {\n        id\n        status\n        "
                "appliedRewardType\n        appliedRewardQuantity\n        appliedRewardMetadata\n        error\n        rewardId\n        "
                "reward {\n          id\n          quantity\n          type\n          properties\n          __typename\n        }\n        "
                "__typename\n      }\n      __typename\n    }\n    missionRecord {\n      id\n      missionId\n      status\n      "
                "createdAt\n      rewardRecords {\n        id\n        status\n        appliedRewardType\n        appliedRewardQuantity\n        "
                "appliedRewardMetadata\n        error\n        rewardId\n        reward {\n          id\n          quantity\n          type\n          "
                "properties\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"
            )
        })
        headers = {
            **self.headers,
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json",
            "Privy-Id-Token": identity_token,
            "X-apollo-Operation-Name": "VerifyActivity"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=self.URL, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                self.log(f"{Fore.RED + Style.BRIGHT}Complete Task Failed (Attempt {attempt + 1}/{retries}): {e}{Style.RESET_ALL}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
        return None

    async def process_get_nonce(self, address: str, use_proxy: bool) -> str:
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        nonce = None
        while nonce is None:
            nonce = await self.user_init(address, proxy)
            if not nonce:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} GET Nonce Failed {Style.RESET_ALL}"
                )
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
        return nonce

    async def process_get_token(self, account: str, address: str, use_proxy: bool) -> tuple:
        nonce = await self.process_get_nonce(address, use_proxy)
        if not nonce:
            return None, None
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        token = None
        while token is None:
            token = await self.user_authenticate(account, address, nonce, proxy)
            if not token:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} GET Identity & Auth Tokens Failed {Style.RESET_ALL}"
                )
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
            else:
                return token.get("identity_token"), token.get("token")
        return None, None

    async def process_get_access_token(self, account: str, address: str, use_proxy: bool) -> tuple:
        identity_token, auth_token = await self.process_get_token(account, address, use_proxy)
        if not (identity_token and auth_token):
            return None, None
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        access_token = None
        while access_token is None:
            access_token = await self.user_login(auth_token, proxy)
            if not access_token:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} GET Access Token Failed {Style.RESET_ALL}"
                )
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
        return identity_token, access_token

    async def process_accounts(self, account: str, address: str, use_proxy: bool):
        if not address:
            return
        identity_token, access_token = await self.process_get_access_token(account, address, use_proxy)
        if not (identity_token and access_token):
            return
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Status    :{Style.RESET_ALL}"
            f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
        )
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {proxy or 'None'} {Style.RESET_ALL}"
        )

        balance = "N/A"
        user = await self.user_data(access_token, proxy)
        if user:
            balance = user.get("campaignSpot", {}).get("points", 0)

        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Balance   :{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {balance} XP {Style.RESET_ALL}"
        )

        task_lists = await self.task_lists(access_token, proxy)
        if task_lists:
            self.log(f"{Fore.CYAN + Style.BRIGHT}Task Lists:{Style.RESET_ALL}")
            tasks = task_lists.get("activities", [])
            for task in tasks:
                if task:
                    task_id = task.get("id")
                    title = task.get("title")
                    complete = await self.complete_task(identity_token, access_token, task_id, proxy)
                    if complete and complete.get("data"):
                        self.log(
                            f"{Fore.MAGENTA + Style.BRIGHT}   >{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                            f"{Fore.GREEN + Style.BRIGHT}Is Completed{Style.RESET_ALL}"
                        )
                    else:
                        error_msg = complete.get("errors", [{}])[0].get("extensions", {})
                        message = error_msg.get("clientFacingMessage", "Not Eligible")
                        self.log(
                            f"{Fore.MAGENTA + Style.BRIGHT}   >{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                            f"{Fore.RED + Style.BRIGHT}Not Completed:{Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT} {message} {Style.RESET_ALL}"
                        )
        else:
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} Data Is None {Style.RESET_ALL}"
            )

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip() and self.validate_private_key(line.strip())]
            if not accounts:
                self.log(f"{Fore.RED + Style.BRIGHT}No Valid Accounts Found in accounts.txt.{Style.RESET_ALL}")
                return

            use_proxy_choice = self.print_question()
            use_proxy = use_proxy_choice in [1, 2]

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)

                separator = "=" * 25
                for account in accounts:
                    address = self.generate_address(account)
                    if not address:
                        continue
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )
                    await self.process_accounts(account, address, use_proxy)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}" * 72)
                delay = 12 * 60 * 60
                while delay > 0:
                    formatted_time = self.format_seconds(delay)
                    print(
                        f"{Fore.CYAN + Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    delay -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED + Style.BRIGHT}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = PuzzleMania()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] 0G Puzzle Mania - BOT{Style.RESET_ALL}"
        )
