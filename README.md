## Description
Introducing a cutting-edge Web3 payment bot designed exclusively for Discord, enabling seamless blockchain transactions and decentralized payments. Revolutionize the way you make payments and show appreciation to fellow users in your favorite servers using the power of Arbitrum.

# Features 
- Simple to use; With a few easy-to-remember commands, users can send and receive payments and participate in a generous and engaging community.
- The transactions are executed in real-time on the blockchain, meaning your payments are sent and received instantly.
- Automatically generates clickable transaction links (marked in blue) which redirect to the blockchain explorer within its response messages.
- Rigorous testing has been done using ganache to ensure the bot functions as intended without any bugs or vulnerabilities.
- Currently configured to run on Arbitrum but can be changed to run on any EVM-compatible chain like Ethereum, BSC, Optimism etc.
   
# Commands 

## help
![Screenshot 2023-07-23 134138](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/f79a2c8c-a3e7-4070-a7de-af91cccf182a)

## deposit
![Screenshot 2023-07-23 134013](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/c8a000a3-9688-479b-9d02-14f3548ad6db)

## withdraw
![Screenshot 2023-07-23 134023](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/bd9dc7e6-54ed-40dc-afb1-82d5411fe1fe)

## tip 
https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/d934d8f1-06cc-4d37-be76-ee0e52540495

# Error Handling 
Extensive error handling and checks have been implemented to ensure best performance. Few examples:
![Screenshot 2023-07-23 145206](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/849e015e-1c23-4143-80fe-b2e4dbc742e0)
![Screenshot 2023-07-23 145441](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/3e11c6e3-b890-48e7-83f6-230ce41ea663)
![Screenshot 2023-07-23 145145](https://github.com/Sakaar-Sen/Discord-Web3-Tipping-Bot/assets/52592149/3d870cb1-6788-41fa-a54c-583b0f3dd9e7)


# Setup
- Clone the repo 
```
   git clone https://github.com/Sakaar-Sen/DiscordPay.git
```
- Install the dependencies from requirements.txt
- Create a discord bot from https://discord.com/developers and paste the token in a variable called DISCORDTOKEN in the .env file.
- Configure the RPCURL variable depending on whether you want to test locally or on a real blockchain.
- Run DiscordTxnBot.py

### Recommendation for production use 
- Throughly test tokens other than $ETH if you wish to add them.
- Change the fees collected address and the fees percentage (Currently set to 0.02%).

# Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.




  

