
from web3 import Web3
import random
import os
import time
from datetime import datetime, timedelta, timezone

# 指定 EVM 链（以 Ethereum 为例）
RPC_URL = "https://tea-sepolia.g.alchemy.com/public"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# 读取私钥列表
def load_private_keys(file_path="pk.txt"):
    try:
        with open(file_path, "r") as f:
            keys = [line.strip() for line in f if line.strip()]
        print(f"成功加载 {len(keys)} 个私钥")
        return keys
    except Exception as e:
        print(f"加载私钥文件失败: {e}")
        return []

private_keys = load_private_keys()

# 读取接收地址列表
def load_receive_addrs(file_path="receive.txt"):
    try:
        if not os.path.exists(file_path):
            print("地址文件不存在")
            return []
        with open(file_path, "r") as f:
            receives = [line.strip() for line in f if line.strip()]
        if receives:
            print(f"成功加载 {len(receives)} 个地址")
        else:
            print("地址文件为空")
        return receives
    except Exception as e:
        print(f"加载地址文件失败: {e}")
        return []
        
receives_addrs = load_receive_addrs()
c_receive = web3.to_checksum_address("0xD8c4bcA831FDa39e310EF8580Ec092492D8B66CB")
start = 1

def input_positive_int(prompt="请输入转账次数(正整数)："):
    while True:
        user_input = input(prompt)
        try:
            value = int(user_input)
            if value > 0:
                return value
            else:
                print("❌ 输入必须是一个大于 0 的整数，请重新输入。")
        except ValueError:
            print("❌ 无效输入，请输入一个整数。")
numinit = input_positive_int()
# 获取随机接收地址
def get_random_recipient():
    if receives_addrs:
        return web3.to_checksum_address(random.choice(receives_addrs))

    print("文件中无有效地址，从区块中随机选取地址")
    try:
        latest_block = web3.eth.get_block("latest", full_transactions=False)
        tx_hash_list = latest_block.transactions
        for tx_hash in tx_hash_list:
            try:
                tx = web3.eth.get_transaction(tx_hash)
                to_addr = tx.get("to")
                if to_addr and web3.is_address(to_addr):
                    to_addr = web3.to_checksum_address(to_addr)
                    code = web3.eth.get_code(to_addr)
                    if not code or code == b"" or code == b"0x":
                        return to_addr
            except Exception as inner_e:
                print(f"处理交易 {tx_hash.hex()} 失败: {inner_e}")
        print("区块中未找到有效地址，生成随机地址作为接收方")
    except Exception as e:
        print(f"获取区块失败: {e}")

    return web3.to_checksum_address("0x" + os.urandom(20).hex())


def send_transaction(from_account, private_key,recipient):
    try:
        #recipient = get_random_recipient()
        amount = round(random.uniform(0.001, 0.005), 3)  # 保留 2 位小数
        amount_wei = web3.to_wei(amount, "ether")
        
        tx_data = {
            "nonce": web3.eth.get_transaction_count(from_account, 'pending'),
            "to": recipient,
            "value": amount_wei,
            "gasPrice": web3.eth.gas_price * 2,
        }
        
        try:
            gas = 21000
            tx_data["gas"] = gas
            print(f"✅ 估算 Gas 成功: {gas}")
        except Exception as e:
            fallback_gas = 21000  # 最小转账交易 gas，适用于普通转账
            tx_data["gas"] = fallback_gas
            print(f"⚠️ 估算 Gas 失败: {e}，使用备用 gas: {fallback_gas}")
        
        signed_tx = web3.eth.account.sign_transaction(tx_data, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        #print(f"交易suc")
        print(f"[{web3.eth.block_number}] 发送 {amount:.3f} ETH 到 {recipient}，交易哈希: {tx_hash.hex()}")
    except Exception as e:
        print(f"交易失败: {e}")

while True:
    if start != 1:
        now = datetime.now(timezone.utc) + timedelta(hours=8)
        
        start_hour = random.randint(7, 8)
        start_minute = random.randint(0, 59)
        start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        if start_time < now:
            start_time += timedelta(days=1)
        
        time_to_wait = (start_time - now).total_seconds()
        print(f"将在 {start_time} (UTC+8) 开始执行...")
        time.sleep(time_to_wait)

    # 依次使用随机私钥进行交易
    random.shuffle(private_keys)
    for private_key in private_keys:
        from_account = web3.eth.account.from_key(private_key).address
        num = numinit + random.randint(10, 19)
        print(f"使用私钥 {from_account} 进行 {num} 次转账")
        recipient = get_random_recipient()
        for i in range(num):
            if random.random() < 0.1:
                send_transaction(from_account, private_key,c_receive)
                time.sleep(random.randint(21, 45))
                continue
            if random.random() < 0.15:
                time.sleep(random.randint(10, 20))
                recipient = get_random_recipient()                
            send_transaction(from_account, private_key,recipient)
            time.sleep(random.randint(21, 45))   # 避免 nonce 冲突
        time.sleep(random.randint(55, 111))
    print("今日任务完成，等待明天...")
    start = 2
    # 计算到明天 9:00 之间的等待时间
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    next_day = now + timedelta(days=1)
    next_start_time = next_day.replace(hour=8, minute=0, second=0, microsecond=0)
    sleep_time = (next_start_time - now).total_seconds()
    print(f"休眠至 {next_start_time} (UTC+8)...")
    time.sleep(sleep_time)
