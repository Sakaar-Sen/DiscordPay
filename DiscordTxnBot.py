from eth_account import Account
import secrets
import discord
from discord.ext import commands
from web3 import Web3
from tinydb import TinyDB    
from tinydb import Query
import math
from web3.middleware import geth_poa_middleware
from dotenv import dotenv_values
from txnBotAbiFile import abi

config = dotenv_values(".env")


rpcURL = 'https://rpc.ankr.com/arbitrum'
#rpcURL = 'http://127.0.0.1:8545' #for local testing with ganache
web3 = Web3(Web3.HTTPProvider(rpcURL))

Todo = Query()   
db = TinyDB("tcbotkeysV2.json")

Arb = "0x912ce59144191c1204e64559fe8253a0e49e6548"

def get_balance(addy, token):
    _contract = ""
    if token == 'eth':
        return float(web3.from_wei(web3.eth.get_balance(addy), 'ether'))
    elif token == 'arb':
        _contract = Arb
    
    
    account = web3.to_checksum_address(addy)
    contract = web3.eth.contract(address=_contract, abi=abi)
    return float(web3.from_wei(contract.functions.balanceOf(account).call(), 'ether'))


def createWallet(id):
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    acct = Account.from_key(private_key)
    x = {"userid": id, "pvt_key": private_key, "pub_key": acct.address}
    db.insert(x)

    return [private_key, acct.address]



def sendTXN(acc1, pvtKey, acc2, amt, token):
    
    web3 = Web3(Web3.HTTPProvider(rpcURL))
    
    account_1 = acc1
    private_key1 = pvtKey
    account_2 = web3.to_checksum_address(acc2)

    nonce = web3.eth.get_transaction_count(account_1)
    if token == 'eth':
        tx = {
            'nonce': nonce,
            'to': account_2,
            'value': web3.to_wei(amt, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('10', 'gwei')
        }

        signed_tx = web3.eth.account.sign_transaction(tx, private_key1)

        try:
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return web3.to_hex(tx_hash)
        except:
            return None
    
    elif token == 'arb':
        _contract = Arb
    
    
    contract = web3.eth.contract(address=_contract, abi=abi)

    nonce = web3.eth.get_transaction_count(acc1)  

    token_txn = contract.functions.transfer(
        account_2,
        web3.to_wei(amt, 'ether'),
    ).buildTransaction({
        'chainId': 42161,
        'gas': 25000,
        'gasPrice': web3.to_wei('1', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = web3.eth.account.sign_transaction(token_txn, pvtKey)
   
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return web3.to_hex(tx_hash)
    except:
        return None
        
def truncate(f, n): 
    return math.floor(f * 10 ** n) / 10 ** n


intents = discord.Intents.all()
client = commands.Bot(command_prefix='.', intents=intents)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):

    user_id = message.author.id

    dbresult = db.get(Todo.userid == user_id)

    if dbresult == None:
        res = createWallet(user_id)
        pvt_key = res[0]
        pub_key = res[1]
    else:
        pvt_key = dbresult['pvt_key']
        pub_key = dbresult['pub_key']

    
    msg = message.content.lower()
    server = True

    if message.guild == None:
        server = False


    if ">tip" in msg: 
        if server == False:
            embed=discord.Embed(title="Beep Boop", description="Use command in Server.", color= 0xf59236)
            await message.reply(embed=embed)
            return

        msg_listed = list(msg.split())
        try:
            user_id_r = msg_listed[1]
            user_id_r = user_id_r.strip("<@")
            user_id2 = user_id_r.strip(">")
        except:
            embed=discord.Embed(title="Error!", description="\nTo send a tip use format \n```>tip @user <amount> <token>```", color = 0x13e8e1)
            await message.reply(embed=embed)
            return
        
        try:
            amt = float(msg_listed[2])
        except:
            embed=discord.Embed(title="Error!", description="\nTo send a tip use format \n```>tip @user <amount> <token>```",  color = 0x13e8e1)
            await message.reply(embed=embed)
            return
        
        try:
            token = msg_listed[3].lower()
        except:
            embed=discord.Embed(title="Error!", description="Please specify a token. \nTo send a tip use format \n```>tip @user <amount> <token>```",  color = 0x13e8e1)
            await message.reply(embed=embed)
            return


        if token != 'eth':
            embed=discord.Embed(title="Oops", description="Token not supported...yet", color= 0xe63232)
            await message.reply(embed=embed)
            return 
        
        bal = get_balance(pub_key, token)

        if bal < 0.0021:
            embed=discord.Embed(title="Beep Boop!", description="You need to have atleast 0.0021 $Eth to make transactions.", color = 0xf59236)
            await message.reply(embed=embed)
            return


        if amt > bal:
            embed=discord.Embed(title="Beep Boop!", description="Insufficient Balance", color = 0xf59236)
            y = token.upper()
            embed.add_field(name="Current Balance", value="**{0}** {1}".format(truncate(bal, 4), y)) #token
            await message.reply(embed=embed)
            return

        user_id2 = int(user_id2)
        dbresult2 = db.get(Todo.userid == user_id2)

        if dbresult2 == None:
            res2 = createWallet(user_id2)
            pub_key2 = res2[1]
        else:
            pub_key2 = dbresult2['pub_key']


        
        response = sendTXN(pub_key, pvt_key, pub_key2, amt, token)

        
        if response == None:
            embed=discord.Embed(title="Oopsie", description="Txn failed. Try again later!", color = 0xe63232)
            await message.reply(embed=embed)

        else:
            embed=discord.Embed(title="LET'S GOOO!", description="<@{0}> sent <@{1}> {2} {3}".format(user_id, user_id2, amt, token.upper()), color = 0x8318c9)
            embed.add_field(name="Transaction ID", value="[{0}]({1})".format(response, "https://arbiscan.io/tx/{}".format(response)), inline=True)
            embed.set_footer(text="Running on Arbitrum")
            await message.reply(embed=embed)
       
        

    if ">help" in msg:
        embed=discord.Embed(title="Help", description="A Discord tipping bot that runs on **Arbitrum**. Now transact on your favorite platform with lightening speed and security!", color = 0xed4add)
        embed.add_field(name="How To Use", value="To **Tip** use format: `>tip @user <amount> <token>`\nTo **Withdraw** use format: `>withdraw <amount> <token> <destination-address>`", inline=False)
        embed.add_field(name="List of commands supported", value="```>balance\n>deposit\n>withdraw\n>tip```", inline=False)
        embed.add_field(name="Supported Tokens", value="```$ETH\n```")
        await message.reply(embed=embed)


    if ">deposit" in msg:
        if server:
            embed=discord.Embed(title="Beep Boop", description="Use command in DMs.", color= 0xf59236)
            await message.reply(embed=embed)
        else:
            embed=discord.Embed(title="Deposit", description="This is your unique address that is associated with your discord user id. Deposit **Supported Tokens** to this address on **Arbitrum** only.", color = 0x637ef2)
            embed.add_field(name="Deposit Address", value="`{}`".format(pub_key), inline=True)
            await message.reply(embed=embed)
        

    if ">withdraw" in msg: 
        if server:
            embed=discord.Embed(title="Beep Boop", description="Use command in DMs.", color= 0xf59236)
            await message.reply(embed=embed)

        else:
            try:
                msg_listed = list(msg.split())
                amt = float(msg_listed[1])
            except:
                embed=discord.Embed(title="Withdraw", description="Failed", color = 0xe63232)
                embed.add_field(name="Reason", value='Amount not specified.', inline=False)
                embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> <token> <destination-address>`\nExample \n`!withdraw 5 eth 0xFE3...D551`", inline=False)
                await message.reply(embed=embed)
                return

            try:
                token = msg_listed[2].lower()
                print(token)
            except:
                embed=discord.Embed(title="Withdraw", description="Failed", color = 0xe63232)
                embed.add_field(name="Reason", value='Token not specified.', inline=False)
                embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> <token> <destination-address>`\nExample \n`!withdraw 5 eth 0xFE3...D551`", inline=False)
                await message.reply(embed=embed)
                return

            if token != 'eth' and token != 'arb':
                embed=discord.Embed(title="Withdraw", description="Failed", color = 0xe63232)
                embed.add_field(name="Reason", value='Token not supported.', inline=False)
                embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> <token> <destination-address>`\nExample \n`!withdraw 5 eth 0xFE3...D551`", inline=False)
                await message.reply(embed=embed)
                return
            
            bal = get_balance(pub_key, token)
            
            if amt > bal:
                embed=discord.Embed(title="Withdraw", description="Failed", color = 0xe63232)
                embed.add_field(name="Reason", value='Insufficient Balance.', inline=False)
                embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> <token> <destination-address>`\nExample \n`!withdraw 5 eth 0xFE3...D551`", inline=False)
                await message.reply(embed=embed)
                return
            
            try:
                addy = msg_listed[3]
            except:
                embed=discord.Embed(title="Withdraw", description="Failed", color = 0xe63232)
                embed.add_field(name="Reason", value='Address not specified.', inline=False)
                embed.add_field(name="How To Use", value="Use format \n`>withdraw <amount> <token> <destination-address>`\nExample \n`!withdraw 5 eth 0xFE3...D551`", inline=False)
                await message.reply(embed=embed)
                return

            tipaddy = '0xFE33d65AF0b79c837f75D34b5dC840fD560eD551'

            print(amt)
            print(addy)
            sendamt = 0.98*amt
            feeamt = amt - sendamt

            try:
                res = sendTXN(pub_key, pvt_key, addy, sendamt, token)
                res2 = sendTXN(pub_key, pvt_key, tipaddy, feeamt, token)
            except:
                embed=discord.Embed(title="Withdraw", description="Failed", color= 0xe63232)
                embed.add_field(name="Reason", value='Ran into an error. Make sure you are using the correct format + have enough balance for token and gas + Address mentioned is correct. Try again!', inline=False)
                await message.reply(embed=embed)
                return
            
            if res == None:
                embed=discord.Embed(title="Withdraw", description="Failed", color= 0xe63232)
                embed.add_field(name="Reason", value='Ran into an error. Make sure you have enough $eth for gas or try again later.', inline=False)
                await message.reply(embed=embed)
            else:
                embed=discord.Embed(title="Withdraw", description="Successful", color = 0x0ee647)
                embed.add_field(name="TXN ID", value='[{0}]({1})'.format(res, "https://arbiscan.io/tx/{}".format(res)), inline=True)
                embed.set_footer(text="Running on Arbitrum")
                await message.reply(embed=embed)

    
    if ">balance" in msg:
        try:
            msglisted = list(msg.split())
            token = msglisted[1]
        except:
            embed=discord.Embed(title="Balance", description="Please specify a token", color= 0xe63232)
            embed.add_field(name="Example", value='```>balance eth```', inline=False)
            embed.set_footer(text="Use command >help in DMs to see the list of supported tokens")
            await message.reply(embed=embed)
            return
        
        if token == 'eth' or token == 'arb':
            bal = get_balance(pub_key, token)
            embed=discord.Embed(title="Current Balance", description="**{0}** {1}".format(truncate(bal,4),token.upper()), color=0xc300ff)
            await message.reply(embed=embed)
       

client.run(config['DISCORDTOKEN'])