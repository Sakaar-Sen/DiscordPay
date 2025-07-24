import secrets
import discord
from discord.ext import commands
from web3 import Web3
import sqlite3
import math
from web3.middleware import geth_poa_middleware
from dotenv import dotenv_values
from eth_account import Account

config = dotenv_values(".env")
rpcURL = 'https://rpc.ankr.com/arbitrum'
web3 = Web3(Web3.HTTPProvider(rpcURL))
DB_FILE = "wallets.db"
FEE_ADDRESS = "0xFE33d65AF0b79c837f75D34b5dC840fD560eD551"
FEE_PERCENTAGE = 0.02

def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            pvt_key TEXT NOT NULL,
            pub_key TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

db_conn = setup_database()

def get_balance(addy, token):
    if token == 'eth':
        return float(web3.from_wei(web3.eth.get_balance(addy), 'ether'))
    return 0.0

def create_wallet(user_id):
    cursor = db_conn.cursor()
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    acct = Account.from_key(private_key)
    
    cursor.execute(
        "INSERT INTO wallets (user_id, pvt_key, pub_key) VALUES (?, ?, ?)",
        (user_id, private_key, acct.address)
    )
    db_conn.commit()
    return private_key, acct.address

def get_wallet(user_id):
    cursor = db_conn.cursor()
    cursor.execute("SELECT pvt_key, pub_key FROM wallets WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def send_txn(pvtKey, from_acc, to_acc, amt, token):
    web3 = Web3(Web3.HTTPProvider(rpcURL))
    
    account_1 = web3.to_checksum_address(from_acc)
    account_2 = web3.to_checksum_address(to_acc)
    nonce = web3.eth.get_transaction_count(account_1)

    if token == 'eth':
        tx = {
            'nonce': nonce,
            'to': account_2,
            'value': web3.to_wei(amt, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('10', 'gwei')
        }
        signed_tx = web3.eth.account.sign_transaction(tx, pvtKey)
    else:
        return None

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return web3.to_hex(tx_hash)
    except Exception as e:
        print(f"Transaction failed: {e}")
        return None

def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = commands.Bot(command_prefix='>', intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = message.author.id
    wallet = get_wallet(user_id)

    if wallet is None:
        pvt_key, pub_key = create_wallet(user_id)
    else:
        pvt_key, pub_key = wallet

    msg = message.content.lower()
    is_in_server = message.guild is not None

    if msg.startswith(">tip"):
        if not is_in_server:
            embed = discord.Embed(title="Beep Boop", description="Use command in Server.", color=0xf59236)
            await message.reply(embed=embed)
            return

        parts = msg.split()
        try:
            receiver_id_str = parts[1].strip('<@!>')
            receiver_id = int(receiver_id_str)
            amt = float(parts[2])
            token = parts[3].lower()
        except (IndexError, ValueError):
            embed = discord.Embed(title="Error!", description="\nTo send a tip use format \n```>tip @user <amount> <token>```", color=0x13e8e1)
            await message.reply(embed=embed)
            return

        if token != 'eth':
            embed = discord.Embed(title="Oops", description="Token not supported. Only `eth` is supported.", color=0xe63232)
            await message.reply(embed=embed)
            return

        bal = get_balance(pub_key, 'eth')
        if bal < 0.0021:
            embed=discord.Embed(title="Beep Boop!", description="You need to have atleast 0.0021 $Eth to make transactions.", color = 0xf59236)
            await message.reply(embed=embed)
            return

        token_bal = get_balance(pub_key, token)
        if amt > token_bal:
            embed = discord.Embed(title="Beep Boop!", description="Insufficient Balance", color=0xf59236)
            y = token.upper()
            embed.add_field(name="Current Balance", value="**{0}** {1}".format(truncate(token_bal, 4), y))
            await message.reply(embed=embed)
            return

        receiver_wallet = get_wallet(receiver_id)
        if receiver_wallet is None:
            _, pub_key2 = create_wallet(receiver_id)
        else:
            _, pub_key2 = receiver_wallet

        response = send_txn(pvt_key, pub_key, pub_key2, amt, token)

        if response is None:
            embed = discord.Embed(title="Oopsie", description="Txn failed. Try again later!", color=0xe63232)
            await message.reply(embed=embed)
        else:
            embed = discord.Embed(title="LET'S GOOO!", description="<@{0}> sent <@{1}> {2} {3}".format(user_id, receiver_id, amt, token.upper()), color=0x8318c9)
            embed.add_field(name="Transaction ID", value="[{0}]({1})".format(response, "https://arbiscan.io/tx/{}".format(response)), inline=True)
            embed.set_footer(text="Running on Arbitrum")
            await message.reply(embed=embed)

    elif msg.startswith(">help"):
        embed = discord.Embed(title="Help", description="A Discord tipping bot that runs on **Arbitrum**. Now transact on your favorite platform with lightening speed and security!", color=0xed4add)
        embed.add_field(name="How To Use", value="To **Tip** use format: `>tip @user <amount> eth`\nTo **Withdraw** use format: `>withdraw <amount> eth <destination-address>`", inline=False)
        embed.add_field(name="List of commands supported", value="```>balance eth\n>deposit\n>withdraw\n>tip```", inline=False)
        embed.add_field(name="Supported Tokens", value="```$ETH```")
        await message.reply(embed=embed)

    elif msg.startswith(">deposit"):
        if is_in_server:
            embed = discord.Embed(title="Beep Boop", description="Use command in DMs.", color=0xf59236)
            await message.reply(embed=embed)
        else:
            embed = discord.Embed(title="Deposit", description="This is your unique address that is associated with your discord user id. Deposit **ETH** to this address on **Arbitrum** only.", color=0x637ef2)
            embed.add_field(name="Deposit Address", value="`{}`".format(pub_key), inline=True)
            await message.reply(embed=embed)

    elif msg.startswith(">balance"):
        parts = msg.split()
        if len(parts) != 2:
            embed = discord.Embed(title="Balance", description="Please specify a token", color=0xe63232)
            embed.add_field(name="Example", value='```>balance eth```', inline=False)
            await message.reply(embed=embed)
            return

        token = parts[1].lower()
        if token == 'eth':
            bal = get_balance(pub_key, token)
            embed = discord.Embed(title="Current Balance", description="**{0}** {1}".format(truncate(bal, 4), token.upper()), color=0xc300ff)
            await message.reply(embed=embed)
        else:
            embed = discord.Embed(title="Oops", description="Token not supported. Only `eth` is supported.", color=0xe63232)
            await message.reply(embed=embed)

    elif msg.startswith(">withdraw"):
        if is_in_server:
            embed = discord.Embed(title="Beep Boop", description="Use command in DMs.", color=0xf59236)
            await message.reply(embed=embed)
            return

        parts = msg.split()
        try:
            amt = float(parts[1])
            token = parts[2].lower()
            destination_address = parts[3]
        except (IndexError, ValueError):
            embed = discord.Embed(title="Withdraw", description="Failed", color=0xe63232)
            embed.add_field(name="Reason", value='Incorrect format.', inline=False)
            embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> eth <destination-address>`\nExample \n`>withdraw 5 eth 0xFE3...D551`", inline=False)
            await message.reply(embed=embed)
            return

        if not web3.is_address(destination_address):
            embed = discord.Embed(title="Withdraw", description="Failed", color=0xe63232)
            embed.add_field(name="Reason", value='The destination address is not valid.', inline=False)
            embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> eth <destination-address>`\nExample \n`>withdraw 5 eth 0xFE3...D551`", inline=False)
            await message.reply(embed=embed)
            return

        if token != 'eth':
            embed = discord.Embed(title="Withdraw", description="Failed", color=0xe63232)
            embed.add_field(name="Reason", value='Token not supported. Only `eth` is supported.', inline=False)
            embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> eth <destination-address>`\nExample \n`>withdraw 5 eth 0xFE3...D551`", inline=False)
            await message.reply(embed=embed)
            return

        bal = get_balance(pub_key, token)
        if amt > bal:
            embed = discord.Embed(title="Withdraw", description="Failed", color=0xe63232)
            embed.add_field(name="Reason", value='Insufficient Balance.', inline=False)
            embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> eth <destination-address>`\nExample \n`>withdraw 5 eth 0xFE3...D551`", inline=False)
            await message.reply(embed=embed)
            return

        fee_amount = amt * FEE_PERCENTAGE
        send_amount = amt - fee_amount

        response = send_txn(pvt_key, pub_key, destination_address, send_amount, token)

        if response is None:
            embed = discord.Embed(title="Withdraw", description="Failed", color=0xe63232)
            embed.add_field(name="Reason", value='Ran into an error. Make sure you have enough $eth for gas or try again later.', inline=False)
            await message.reply(embed=embed)
        else:
            send_txn(pvt_key, pub_key, FEE_ADDRESS, fee_amount, token)
            embed = discord.Embed(title="Withdraw", description="Successful", color=0x0ee647)
            embed.add_field(name="TXN ID", value='[{0}]({1})'.format(response, "https://arbiscan.io/tx/{}".format(response)), inline=True)
            embed.set_footer(text="Running on Arbitrum")
            await message.reply(embed=embed)

client.run(config['DISCORDTOKEN'])
