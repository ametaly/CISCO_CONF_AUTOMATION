import asyncio
import telnetlib3

async def send_commands(host, port, commands_file):
    reader, writer = await telnetlib3.open_connection(host, port, connect_minwait=1.0)

    for i in range(6):
        writer.write("\r")
    await asyncio.sleep(0.6)
    writer.write("en\r\n")  # Envoyer la commande 'en' et appuyer sur Entrée
    await asyncio.sleep(0.6)
    writer.write("en\r\n")  # Envoyer la commande 'en' et appuyer sur Entrée
    await asyncio.sleep(0.6)
    writer.write("en\r\n")  # Envoyer la commande 'en' et appuyer sur Entrée
    await asyncio.sleep(0.6)
    writer.write("conf t\r\n")  # Envoyer la commande 'conf t' et appuyer sur Entrée
    
    # Lecture des commandes depuis le fichier de configuration
    with open(commands_file, "r") as file:
        commands = file.readlines()
    
    for cmd in commands:
        cmd = cmd.strip()  # Remove any leading/trailing whitespace or newline characters
        if cmd:  # Only proceed if cmd is not empty
            print(f"{port} | Sending: {cmd}")
            writer.write(cmd + "\r\n")
            await writer.drain()  # Ensure command is sent
            await asyncio.sleep(0.3)

    print(f"{port} | Sending: wr")

    writer.write("wr" + "\r\n")
    await asyncio.sleep(0.3)
    writer.write("\r")
    await writer.drain()  # Ensure command is sent
    writer.close()

    
routers_gns3 = {
    "C":"5013",
    "CE1":"5000",
    "CE2":"5001",
    "CEN1":"5007",
    "CEN2":"5008",
    "D":"5012",
    "P1": "5014",
    "P2": "5003",
    "P3": "5009",
    "P4": "5005",
    "PE1": "5002",
    "PE2": "5006",
    "PE3": "5011",
    "PE4": "5010",
    }

for router_name, port in routers_gns3.items():
    print(f"\nDeploying configuration to {router_name} on port {port}\n")
    asyncio.run(send_commands("localhost", port, f"dev/config_files/{router_name}_config.txt"))
    print(f"\nConfiguration deployed to {router_name} on port {port}\n")
