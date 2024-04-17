import os
import json
from datetime import datetime

config_dir = 'dev/config_files'
os.makedirs(config_dir, exist_ok=True)

current_utc_time = datetime.utcnow()
formatted_time = current_utc_time.strftime('%H:%M:%S UTC %a %b %d %Y')
formatted_time

def extract_router_interface_ips(intent_data):
    """
    Extrait les adresses IP des interfaces du routeur à partir des données d'intention fournies.

    Args:
        intent_data (dict): Les données d'intention contenant des informations sur les routeurs et leurs interfaces.

    Returns:
        dict: Un dictionnaire qui fait correspondre les noms des routeurs à un dictionnaire de noms d'interface et leurs adresses IP correspondantes.
    """

    router_interface_ips = {}
    
    for router in intent_data['routers']:
        interface_ips = {}
        for interface in router['interfaces']:
            # Assuming interface names are unique per router
            interface_ips[interface['name']] = interface['ip_address']
        router_interface_ips[router['name']] = interface_ips
    return router_interface_ips

def extract_router_as(intent_data):

    router_remote_as = {}
    for router in intent_data['routers']:
        if 'bgp' in router:
            router_remote_as[router['name']] = router['bgp']['local_as']

    return router_remote_as

def extract_router_ospf(intent_data):

    router_ospf = {}
    for router in intent_data['routers']:
        if 'router_id' in router:
            router_ospf[router['name']] = router['router_id']

    return router_ospf

def generate_line_config():

    return """
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
end
"""

def generate_static_config_1(timestamp=formatted_time):
    return f"""
! Last configuration change at {timestamp}
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
!
boot-start-marker
boot-end-marker
!
"""

def generate_static_config_2():
    return f"""
!
no aaa new-model
no ip icmp rate-limit unreachable
ip cef
!
!
no ip domain lookup
no ipv6 cef
!
multilink bundle-name authenticated
!
ip tcp synwait-time 5
!
"""

def generate_vrf_config(vrfs, bgp):
    """
    Génère la configuration VRF pour les VRFs donnés.

    Args:
        vrfs (list): Une liste de dictionnaires représentant les VRFs.
            Chaque dictionnaire doit contenir les clés suivantes:
            - 'nom_vrf': Le nom du VRF.
            - 'route_distinguisher_client': Le route distinguisher du client.
            - 'route_target': La route target du VRF.

        bgp (dict): Un dictionnaire contenant les informations BGP.
            Doit contenir la clé 'local_as' représentant l'AS local.

    Returns:
        str: La configuration VRF générée.
    """
    config = ""
    for vrf in vrfs:
        config += f"!\n"
        config += f"ip vrf {vrf['nom_vrf']}\n"
        config += f" description {vrf['nom_vrf']}\n"
        config += f" rd {bgp['local_as']}:{vrf['route_distinguisher_client']}\n"
        for rt_export in vrf['route_target export']:
            config += f" route-target export {rt_export}\n"
        for rt_import in vrf['route_target import']:
            config += f" route-target import {rt_import}\n"
        config += f"!\n"
        # config += f" address-family ipv4\n exit-address-family\n"
        config += f"!\n"
    return config

def generate_interface_config(interfaces, router_ospf, current_router_name):
    """
    Génère la configuration des interfaces pour un routeur.

    Args:
        interfaces (list): Liste des interfaces du routeur.
        router_ospf (dict): Dictionnaire contenant les informations de configuration OSPF pour chaque routeur.
        current_router_name (str): Nom du routeur actuel.

    Returns:
        str: Configuration générée pour les interfaces du routeur.
    """
    config = ""
    ospf_activated = False
    ospf_process_id = ""
    for interface in interfaces:
        config += f"interface {interface['name']}\n"
        if "vrf" in interface:
            config += f" ip vrf forwarding {interface['vrf']}\n"
        if "ip_address" in interface and "subnet_mask" in interface:
            config += f" ip address {interface['ip_address']} {interface['subnet_mask']}\n"
            config += f" no shutdown\n"
        config += " negotiation auto\n"
        if "ospf" in interface:
            config += f" ip ospf {interface['ospf']['process_id']} area {interface['ospf']['area']}\n"
            ospf_activated = True
            ospf_process_id = f"{interface['ospf']['process_id']}"
        if interface.get("mpls", False):
            config += " mpls ip\n"
        config += "!\n"
    if ospf_activated:
        config += f"router ospf {ospf_process_id}\n"
        config += f" router-id {router_ospf[current_router_name]}\n"
        config += f" redistribute connected subnets\n"
        config += "!\n"
    return config

def generate_bgp_config(bgp, router_interface_ips, router_remote_as, vrfs=None,current_router_name=""):
    """
    Génère la configuration BGP pour un routeur donné.

    Args:
        bgp (dict): Les informations BGP du routeur.
        router_interface_ips (dict): Les adresses IP des interfaces du routeur.
        router_remote_as (dict): Les numéros AS des voisins du routeur.
        vrfs (list, optional): Les VRF spécifiques au routeur. Defaults to None.
        current_router_name (str, optional): Le nom du routeur actuel. Defaults to "".

    Returns:
        str: La configuration BGP générée.
    """
    config = f"router bgp {bgp['local_as']}\n"
    config += f" bgp router-id {bgp['bgp_id']}\n"
    config += f" bgp log-neighbor-changes\n"

    # Configuration des voisins BGP globaux
    for neighbor in bgp.get('neighbors', []):
        # Vérification si le voisin n'est pas associé à un VRF (i.e., configuration globale)
        if 'vrf' not in neighbor or not neighbor['vrf']:
            neighbor_ip = ''
            # Récupération de l'IP du voisin basée sur son nom et interface si spécifiés
            if 'name' in neighbor and 'interface' in neighbor:
                neighbor_name = neighbor['name']
                neighbor_interface = neighbor['interface']
                neighbor_ip = router_interface_ips.get(neighbor_name, {}).get(neighbor_interface, "")
            elif 'neighbor_ip' in neighbor:
                neighbor_ip = neighbor['neighbor_ip']
            # Ajout de la configuration du voisin si son IP est définie
            if neighbor_ip :
                config += f" neighbor {neighbor_ip} remote-as {router_remote_as[neighbor_name]}\n"
                if 'update_source' in neighbor:
                    # Configuration spéciale pour les liaisons PE-PE
                    config += f" neighbor {neighbor_ip} update-source {neighbor['update_source']}\n"
        # Configuration des réseaux annoncés pour le voisin
        
     

    # Configuration de la famille d'adresses IPv4 globale
    config += "!\n address-family ipv4\n"
    for neighbor in bgp.get('neighbors', []):
        if "PE" not in current_router_name and bgp.get('ipv4') == True :
            if 'vrf' not in neighbor or not neighbor['vrf']:
                neighbor_ip = neighbor.get('neighbor_ip', '')
                if 'name' in neighbor and 'interface' in neighbor:
                    neighbor_name = neighbor['name']
                    neighbor_interface = neighbor['interface']
                    neighbor_ip = router_interface_ips.get(neighbor_name, {}).get(neighbor_interface, "")
                if neighbor_ip:
                    config += f"  neighbor {neighbor_ip} activate\n"
            if 'advertised_networks' in neighbor:
                for network in neighbor['advertised_networks']:
                    config += f"  network {network['network']} mask {network['mask']}\n"

    config += " exit-address-family\n"

    # Configuration des voisins BGP pour vpnv4
    config += "!\n address-family vpnv4\n"
    for neighbor in bgp.get('neighbors', []):
        if 'address_family' in neighbor and "vpnv4" in neighbor['address_family']:
            neighbor_ip = neighbor.get('neighbor_ip', '')
            if 'name' in neighbor and 'interface' in neighbor:
                neighbor_name = neighbor['name']
                neighbor_interface = neighbor['interface']
                neighbor_ip = router_interface_ips.get(neighbor_name, {}).get(neighbor_interface, "")
            if neighbor_ip:
                config += f"  neighbor {neighbor_ip} activate\n"
                config += f"  neighbor {neighbor_ip} send-community extended\n"
            if "route_reflector" in neighbor:
                config += f"  neighbor {neighbor_ip} route-reflector-client\n"
    config += " exit-address-family\n"
    
    # Configuration des voisins BGP spécifiques aux VRFs
    if vrfs:
        for vrf in vrfs:
            config += f"!\n address-family ipv4 vrf {vrf['nom_vrf']}\n"
            print("bgp",bgp.get('neighbors', []))
            for neighbor in bgp.get('neighbors', []):
                print()
                if neighbor.get('vrf') == vrf['nom_vrf']:
                    print(vrf['nom_vrf'])
                    neighbor_ip = neighbor.get('neighbor_ip', '')
                    if 'name' in neighbor and 'interface' in neighbor:
                        print("name in neighbor")
                        neighbor_name = neighbor['name']
                        neighbor_interface = neighbor['interface']
                        neighbor_ip = router_interface_ips.get(neighbor_name, {}).get(neighbor_interface, "")
                        print(neighbor_name, neighbor_interface, neighbor_ip)
                    if neighbor_ip:
                        print(1)
                        config += f"  neighbor {neighbor_ip} remote-as {router_remote_as[neighbor_name]}\n"
                        if 'update_source' in neighbor:
                            config += f"  neighbor {neighbor_ip} update-source {neighbor['update_source']}\n"
                        config += f"  neighbor {neighbor_ip} activate\n"
            config += " exit-address-family\n"
    
    config += "!\n"
    return config

def generate_config_files(intent_file_path):
    # Ouvrir le fichier JSON contenant les données d'intention réseau et charger ces données
    with open(intent_file_path, 'r') as file:
        intent_data = json.load(file)
    
    # Extraire les adresses IP des interfaces des routeurs
    router_interface_ips = extract_router_interface_ips(intent_data)
    # Extraire les numéros AS des voisins BGP
    router_remote_as = extract_router_as(intent_data)
    # Extraire les router ID OSPF des routeurs
    router_ospf = extract_router_ospf(intent_data)

    # Pour chaque routeur spécifié dans les données d'intention réseau
    for router in intent_data['routers']:
        config = f"hostname {router['name']}\n"

        config += generate_static_config_1()

        # Si une VRF est configurée sur le routeur, générer la configuration VRF
        if 'vrf' in router:
            config += generate_vrf_config(router['vrf'], router['bgp'])

        config += generate_static_config_2()

        current_router_name = router['name']
        
        config += generate_interface_config(router['interfaces'],router_ospf,current_router_name)
        
        # Si le routeur utilise BGP, générer la configuration BGP, utilisant les adresses IP des interfaces
        if 'bgp' in router:
            vrfs = router.get('vrf', None)
            print("***** vrf ******")
            print(vrfs)
            config += generate_bgp_config(router['bgp'], router_interface_ips, router_remote_as, vrfs,current_router_name)

        config += generate_line_config()

        # Sauvegarder la configuration générée dans un fichier, nommé d'après le routeur
        config_filename = os.path.join(config_dir, f"{router['name']}_config.txt")
        with open(config_filename, 'w') as config_file:
            config_file.write(config)
        print(f"Configuration for {router['name']} written to {config_filename}")


intent_file_path = 'dev/network_intent_v2.json'
generate_config_files(intent_file_path)